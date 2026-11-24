#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
官网深挖器（色母粒海外获客 · 第 6 步 · 浏览器深挖）

用法:
    python tools/site_deepdive.py [输入json路径] [最多处理家数]
输入: leads/<date>-map-<market>.json （或任意含 name 字段的 json 列表）
输出: leads/<date>-deepdive-<market>.json  (每家: name/tel/site/emails/socials/snippet)

每家流程: Google 搜「公司名 + 官网」→ 取首个非平台链接 → 打开官网
         → 抓正文摘要 + 邮箱正则 + footer 社交链接(facebook/zalo/wa.me/linkedin)
"""
import subprocess
import json
import os
import re
import sys
import datetime

BU_NAME = os.environ.get("BU_NAME", "mainchk")
WORKDIR = r"D:\masterbatch-leadgen"

JS_FIND_SITE = r"""
(function(){
  var bad = /google|youtube|facebook|linkedin|wikipedia|yelp\.|bbb\.org|indeed|glassdoor|mapquest|thomasnet|manta|dnb\.com|zoominfo|bloomberg|instagram|twitter|x\.com|lightsource\.ai|kompass|europages|opencorporates|crunchbase|pitchbook|alibaba|made-in-china|globalsources/i;
  var out = [];
  document.querySelectorAll('a[href^="http"]').forEach(function(a){
    var h = a.href;
    if (/google\./.test(h)) return;
    if (bad.test(h)) return;
    if (out.indexOf(h) === -1) out.push(h);
  });
  return JSON.stringify(out.slice(0, 10));
})()
"""

# 品牌名匹配：域名里是否含公司名关键词（去掉行业泛词）
STOP_WORDS = {
    "plastic", "plastics", "injection", "molding", "moulding", "company", "companies",
    "industries", "industry", "products", "product", "manufacturing", "manufacturer",
    "inc", "llc", "corp", "corporation", "co", "the", "and", "group", "solutions",
    "services", "service", "technologies", "technology", "precision", "custom",
    "american", "national", "international", "advanced", "systems", "mfg",
}


def brand_score(name, url):
    """公司名压缩串 vs 域名主体：先比原始串，再比去行业泛词后的串"""
    base = re.sub(r"[^a-z0-9]", "", name.lower())
    domain = re.sub(r"^https?://(www\.)?", "", url).split("/")[0].lower()
    d = re.sub(r"[^a-z0-9]", "", domain.split(".")[0])
    if len(base) < 3 or not d:
        return 0

    def hit(s):
        if len(s) >= 5 and s[:5] in d:
            return 2
        if len(s) >= 4 and s[:4] in d:
            return 1
        return 0

    sc = hit(base)
    if sc:
        return sc

    stripped = base
    for sw in ("plastics", "plastic", "injection", "molding", "moulding",
               "products", "product", "industries", "industry", "company",
               "manufacturing", "precision", "custom", "group", "solutions"):
        stripped = stripped.replace(sw, "")
    return hit(stripped)


def pick_site(name, candidates):
    """从候选链接里按品牌名匹配挑官网，全不匹配则返回空（避免张冠李戴）"""
    if not candidates:
        return ""
    scored = sorted(((brand_score(name, u), u) for u in candidates), reverse=True)
    best_score, best_url = scored[0]
    return best_url if best_score > 0 else ""

JS_PAGE_DIG = r"""
(function(){
  var body = (document.body.innerText || '');
  var emails = body.match(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g) || [];
  // 电话：国际格式通用（+49 / +81 / +82 / +84 / +86 / +1 …），不再局限于美国
  var tels = body.match(/(\+\d{1,3}[\s.-]?)?\(?\d{1,4}\)?[\s.-]?\d{2,4}[\s.-]?\d{2,4}([\s.-]?\d{2,4})?/g) || [];
  var socials = [];
  document.querySelectorAll('a[href]').forEach(function(a){
    var h = a.href || '';
    if (/facebook\.com|zalo\.me|wa\.me|linkedin\.com|instagram\.com/i.test(h)) socials.push(h);
  });
  var uniq = function(arr){ var s={},o=[]; arr.forEach(function(x){ if(!s[x]){s[x]=1;o.push(x);} }); return o; };
  // 找产品页链接（用于抓"官网产品"，开发信锚点唯一来源）
  var pLinks = [];
  var kw = /product|catalog|catalogue|produit|produkte|prodotti|productos|製品|제품|产品|capabilit/i;
  document.querySelectorAll('a[href]').forEach(function(a){
    var h = a.href || '';
    var t = (a.innerText || '') + ' ' + h;
    if (kw.test(t) && h.indexOf(location.hostname) > -1 && pLinks.indexOf(h) === -1
        && !/\.(pdf|jpg|png|zip)$/i.test(h)) pLinks.push(h);
  });
  return JSON.stringify({
    title: document.title,
    url: location.href,
    emails: uniq(emails).slice(0,8),
    tels: uniq(tels).slice(0,5),
    socials: uniq(socials).slice(0,8),
    productLinks: pLinks.slice(0,4),
    snippet: body.replace(/\s+/g,' ').slice(0,1200)
  });
})()
"""

# 抓产品页：提取产品名与树脂型号，作为开发信"官网锚点"
JS_PRODUCTS = r"""
(function(){
  var pick = function(sel){
    var out=[];
    document.querySelectorAll(sel).forEach(function(e){
      var t=(e.innerText||'').replace(/\s+/g,' ').trim();
      if(t.length>=3 && t.length<=70 && out.indexOf(t)===-1) out.push(t);
    });
    return out;
  };
  var NAV = /^(home|about|about us|contact|contact us|products?|services?|news|blog|careers?|privacy|terms|menu|search|login)$/i;
  var items = [];
  pick('h1,h2,h3,h4').concat(pick('li')).forEach(function(t){
    if(!NAV.test(t) && items.indexOf(t)===-1) items.push(t);
  });
  return JSON.stringify({
    url: location.href,
    title: document.title,
    items: items.slice(0,40),
    text: (document.body.innerText||'').replace(/\s+/g,' ').slice(0,1500)
  });
})()
"""


def run_bu(code, timeout=300):
    env = os.environ.copy()
    env["BU_NAME"] = BU_NAME
    env.setdefault("PYTHONIOENCODING", "utf-8")
    p = subprocess.run(
        ["browser-use"], input=code, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout, env=env, shell=True,
    )
    return (p.stdout or "") + (p.stderr or "")


def find_site(name, region=""):
    """搜公司官网，返回候选链接列表"""
    q = (name + " " + region + " official website").replace(" ", "+")
    code = (
        "import time\n"
        "js(\"window.location.href='https://www.google.com/search?q=" + q + "'\")\n"
        "time.sleep(6)\n"
        "print('SITES:' + str(js(r\"\"\"" + JS_FIND_SITE + "\"\"\")))\n"
    )
    out = run_bu(code)
    for line in out.splitlines():
        if line.startswith("SITES:"):
            try:
                return json.loads(line[6:])
            except Exception:
                return []
    return []


def dig(site):
    code = (
        "import time\n"
        "js(\"window.location.href='" + site + "'\")\n"
        "time.sleep(7)\n"
        "print('PAGE:' + str(js(r\"\"\"" + JS_PAGE_DIG + "\"\"\")))\n"
    )
    out = run_bu(code)
    for line in out.splitlines():
        if line.startswith("PAGE:"):
            try:
                return json.loads(line[5:])
            except Exception:
                return None
    return None


def dig_products(url):
    """打开产品页，提取产品名/树脂型号（开发信"官网锚点"的唯一数据来源）"""
    code = (
        "import time\n"
        "js(\"window.location.href='" + url.replace("'", "%27") + "'\")\n"
        "time.sleep(6)\n"
        "print('PROD:' + str(js(r\"\"\"" + JS_PRODUCTS + "\"\"\")))\n"
    )
    out = run_bu(code)
    for line in out.splitlines():
        if line.startswith("PROD:"):
            try:
                return json.loads(line[5:])
            except Exception:
                return None
    return None


def main():
    today = datetime.date.today().isoformat()
    if len(sys.argv) > 1:
        infile = sys.argv[1]
    else:
        cands = sorted(
            [f for f in os.listdir(os.path.join(WORKDIR, "leads")) if "map-" in f and f.endswith(".json")],
            reverse=True,
        )
        if not cands:
            print("找不到 map-*.json，请先跑 maps_scrape.py")
            sys.exit(1)
        infile = os.path.join(WORKDIR, "leads", cands[0])

    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    with open(infile, encoding="utf-8") as f:
        rows = json.load(f)[:limit]

    print(f"深挖 {len(rows)} 家，来源 {infile}")
    results = []
    for i, row in enumerate(rows, 1):
        name = row.get("name", "").strip()
        if not name:
            continue
        print(f"[{i}/{len(rows)}] {name}")
        cands = find_site(name)
        site = pick_site(name, cands)
        rec = {"name": name, "tel": row.get("tel", ""), "addr": row.get("addr", ""),
               "site": site, "site_candidates": cands[:5],
               "emails": [], "socials": [], "products": [], "product_page": "",
               "snippet": "", "status": "no-site"}
        if not site and cands:
            rec["status"] = "site-unverified"
        if site:
            info = dig(site)
            if info:
                rec.update({
                    "site": info.get("url", site),
                    "emails": info.get("emails", []),
                    "socials": info.get("socials", []),
                    "snippet": info.get("snippet", ""),
                    "tels": info.get("tels", []),
                    "title": info.get("title", ""),
                    "status": "ok",
                })
                print(f"    官网={site[:60]} 邮箱={len(rec['emails'])} 社交={len(rec['socials'])}")

                # 第二跳：抓产品页 → 官网产品（开发信锚点）
                p_links = info.get("productLinks") or []
                if p_links:
                    prod = dig_products(p_links[0])
                    if prod and prod.get("items"):
                        seen, items = set(), []
                        for t in prod["items"]:
                            k = t.lower()
                            if k not in seen:
                                seen.add(k)
                                items.append(t)
                        rec["products"] = items[:12]
                        rec["product_page"] = prod.get("url", p_links[0])
                        print(f"    产品页={len(rec['products'])} 项: {', '.join(rec['products'][:3])[:60]}")
                if not rec["products"]:
                    print("    ⚠️ 未抓到产品页（官网产品待人工补）")
            else:
                rec["status"] = "page-fail"
        else:
            if cands:
                print(f"    官网未确认（{len(cands)} 个候选，需人工核实）")
            else:
                print("    未找到官网")
        results.append(rec)

    market = re.search(r"map-(\w+)\.json", os.path.basename(infile))
    tag = market.group(1) if market else "market"
    outfile = os.path.join(WORKDIR, "leads", f"{today}-deepdive-{tag}.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    ok = sum(1 for r in results if r["status"] == "ok")
    with_email = sum(1 for r in results if r["emails"])
    with_social = sum(1 for r in results if r["socials"])
    with_prod = sum(1 for r in results if r.get("products"))
    print(f"\n完成: {ok}/{len(results)} 家官网可访问, {with_email} 家有邮箱, {with_social} 家有社交链接")
    print(f"官网产品: {with_prod}/{ok} 家抓到产品页（覆盖率 {with_prod/max(ok,1):.0%}，低于 80% 需换产品页路径或人工补）")
    print(f"输出: {outfile}")


if __name__ == "__main__":
    main()
