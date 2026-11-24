#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Google Maps 客户抓取器 v2（色母粒海外获客 · 第 2 步）

用法:
    python tools/maps_scrape.py "Ohio" "custom injection molding,plastic extrusion,blow molding"
    python tools/maps_scrape.py "Texas" "injection molding Houston,plastic extrusion Dallas,blow molding"

策略: Maps 的 feed 是虚拟列表、滚动不便，因此改用「多关键词分片搜索」——
      每个查询抓 10-20 家，合并去重，轻松凑满 30+ 候选。
输出: leads/<date>-map-<region>.json
"""
import subprocess
import json
import os
import re
import sys
import datetime

BU_NAME = os.environ.get("BU_NAME", "mainchk")
WORKDIR = r"D:\masterbatch-leadgen"

JS_EXTRACT = r"""
(function(){
  var seen = {}, cards = [];
  document.querySelectorAll('a[href*="/maps/place/"]').forEach(function(a){
    var name = (a.getAttribute('aria-label') || a.textContent || '').trim();
    if (!name || name.length < 2 || seen[name]) return;
    seen[name] = 1;
    var box = a.parentElement, depth = 0;
    while (box && depth < 6) {
      if ((box.innerText || '').length > 60) break;
      box = box.parentElement; depth++;
    }
    var txt = (box ? box.innerText : '').replace(/\n+/g, ' | ');
    // 电话：兼容国际格式（+49/+81/+82/+84/+86…），不局限于美国 +1
    var ph = (txt.match(/(\+\d{1,3}[\s.-]?)?\(?\d{1,4}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}([\s.-]?\d{2,4})?/) || [''])[0];
    var am = txt.match(/(\d+[\w\s.,#-]{4,60}(Rd|Road|St|Street|Ave|Avenue|Blvd|Dr|Drive|Ct|Court|Pkwy|Parkway|Way|Ln|Lane|Hwy|Ste|Str\.|Straße|Strasse|Weg|Platz|Chome|Chōme|Dong|Ro|gil)[\w\s.,#-]{0,25})/i);
    cards.push({name: name, tel: ph.trim(), addr: am ? am[0].trim() : '', raw: txt.slice(0, 260)});
  });
  var feed = document.querySelector('div[role="feed"]');
  return JSON.stringify({cards: cards, scroll: feed ? (feed.scrollTop + '/' + feed.scrollHeight) : 'no-feed'});
})()
"""


def run_bu(code, timeout=300):
    env = os.environ.copy()
    env["BU_NAME"] = BU_NAME
    env.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        p = subprocess.run(
            ["browser-use"], input=code, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, env=env, shell=True,
        )
        return (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def scrape_all(queries, region, per_query_wait=9):
    """一次浏览器会话内循环跑完所有关键词，只付一次连接开销。
    返回 [(query, cards), ...]"""
    code = (
        "import time, json\n"
        "queries = " + json.dumps(queries, ensure_ascii=False) + "\n"
        "region = " + json.dumps(region, ensure_ascii=False) + "\n"
        "for idx, q in enumerate(queries):\n"
        "    u = 'https://www.google.com/maps/search/' + (q + ' ' + region).replace(' ', '+') + '/'\n"
        "    js(\"window.location.href='about:blank'\")\n"
        "    time.sleep(1)\n"
        "    js(\"window.location.href='\" + u + \"'\")\n"
        "    time.sleep(" + str(per_query_wait) + ")\n"
        "    tabs = list_tabs()\n"
        "    mt = [t for t in tabs if '/maps' in str(t.get('url',''))]\n"
        "    if mt: switch_tab(mt[-1]['targetId'])\n"
        "    time.sleep(1.5)\n"
        "    cur = str(js('location.href'))\n"
        "    ok = (q.split(' ')[-1].lower() in cur.lower().replace('+',' ')) or (q.split(' ')[0].lower() in cur.lower().replace('+',' '))\n"
        "    if not ok:\n"
        "        time.sleep(6)\n"
        "    print('CHUNK:' + json.dumps({'q': q, 'data': js(r\"\"\"" + JS_EXTRACT + "\"\"\")}))\n"
        "    time.sleep(1)\n"
    )
    out = run_bu(code, timeout=max(300, len(queries) * (per_query_wait + 12)))
    results = []
    for line in out.splitlines():
        if line.startswith("CHUNK:"):
            try:
                obj = json.loads(line[6:])
                payload = obj.get("data")
                if isinstance(payload, str):
                    payload = json.loads(payload)
                results.append((obj.get("q", ""), (payload or {}).get("cards", [])))
            except Exception:
                continue
    return results


def main():
    if len(sys.argv) < 3:
        print('用法: python tools/maps_scrape.py "地区" "关键词1,关键词2,关键词3"')
        sys.exit(1)

    region = sys.argv[1]
    queries = [q.strip() for q in sys.argv[2].split(",") if q.strip()]
    market = re.sub(r"[^A-Za-z0-9]", "", region) or "market"

    print(f"地区: {region} | 查询 {len(queries)} 组（单会话批量执行）")
    batches = scrape_all(queries, region)

    pool = {}
    for kw, cards in batches:
        new = 0
        for c in cards:
            key = re.sub(r"[^a-z0-9]", "", c["name"].lower())
            if key and key not in pool:
                c["src_query"] = kw
                pool[key] = c
                new += 1
        print(f"  [{kw}] {len(cards)} 卡, 新增 {new}, 累计 {len(pool)}")

    if not batches:
        print("⚠️ 本轮没有拿到任何数据（Chrome 未连接或页面未刷新），请检查主通道")

    result = list(pool.values())
    os.makedirs(os.path.join(WORKDIR, "leads"), exist_ok=True)
    today = datetime.date.today().isoformat()
    outfile = os.path.join(WORKDIR, "leads", f"{today}-map-{market}.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n去重后共 {len(result)} 家 -> {outfile}")
    for c in result[:12]:
        print(f"  - {c['name']} | {c.get('tel','')} | {c.get('addr','')[:38]}")


if __name__ == "__main__":
    main()
