#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
find_whatsapp.py — 从客户池 / 官网里挖 WhatsApp 号码

两种来源，分开记证据，绝不把"电话"当"WhatsApp"直接写库：

  来源A 官网实抓（高置信）：抓首页 + 联系页 HTML，找 wa.me / api.whatsapp.com / whatsapp:// 链接。
         这是客户自己挂的 WhatsApp 按钮，等于官方声明。
  来源B 号码规则推断（中/低置信）：按各国手机号段规则判断池里 `电话` 字段是不是手机。
         手机 ≠ 一定开了 WhatsApp，需人工点链接验一次。

用法：
  python tools/find_whatsapp.py --infer                  # 只做离线推断，不联网，秒出
  python tools/find_whatsapp.py --crawl --market 越南     # 抓官网（需联网/代理）
  python tools/find_whatsapp.py --crawl                  # 抓全池有官网的
  python tools/find_whatsapp.py --crawl --commit         # 把"高置信"写回 master-lead-pool.csv

输出：leads/_whatsapp_candidates.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE = os.environ.get("MB_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # MB_HOME 可指定工作目录，默认脚本上一级
POOL = os.path.join(BASE, "master-lead-pool.csv")
OUT = os.path.join(BASE, "leads", "_whatsapp_candidates.csv")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

BLANK = re.compile(r"^(该市场不使用|待核实|待验证|明确无|⚠️)")

# 停放页 / 域名中介特征：抓到这些说明该线索的官网已经废了
PARKED = ("hugedomains.com", "sedo.com", "godaddy.com/domainsearch", "afternic.com",
          "dan.com", "domainmarket.com", "buydomains.com", "namecheap.com/domains",
          "this domain is for sale", "domain is parked", "buy this domain")

# ── 各国手机号段规则：(国家, 区号, 手机号首位的正则, 国内号码位数, 说明) ─────────
# 只列"能可靠区分手机/固话"的市场；判断不了的标 unknown，绝不猜。
MOBILE_RULES = {
    "越南":     dict(cc="84",  mob=r"^(3|5|7|8|9)",  nd=9,  note="固话 2 开头"),
    "土耳其":   dict(cc="90",  mob=r"^5",            nd=10, note="手机 5xx，固话 2xx/3xx/4xx"),
    "泰国":     dict(cc="66",  mob=r"^[689]",        nd=9,  note="固话 2 开头"),
    "马来西亚": dict(cc="60",  mob=r"^1",            nd=9,  note="手机 01x"),
    "印尼":     dict(cc="62",  mob=r"^8",            nd=10, note="固话 2 开头"),
    "菲律宾":   dict(cc="63",  mob=r"^9",            nd=10, note=""),
    "印度":     dict(cc="91",  mob=r"^[6789]",       nd=10, note=""),
    "巴基斯坦": dict(cc="92",  mob=r"^3",            nd=10, note=""),
    "孟加拉":   dict(cc="880", mob=r"^1",            nd=10, note=""),
    "阿联酋":   dict(cc="971", mob=r"^5",            nd=9,  note=""),
    "沙特":     dict(cc="966", mob=r"^5",            nd=9,  note=""),
    "埃及":     dict(cc="20",  mob=r"^1[012]",       nd=10, note=""),
    "尼日利亚": dict(cc="234", mob=r"^[789]",        nd=10, note=""),
    "肯尼亚":   dict(cc="254", mob=r"^[17]",         nd=9,  note=""),
    "南非":     dict(cc="27",  mob=r"^[678]",        nd=9,  note=""),
    "巴西":     dict(cc="55",  mob=r"^9",            nd=11, note="手机 9 位，固话 8 位"),
    "墨西哥":   dict(cc="52",  mob=r"^1",            nd=10, note="近年取消 1 前缀，多数无法区分"),
    "哥伦比亚": dict(cc="57",  mob=r"^3",            nd=10, note=""),
    "智利":     dict(cc="56",  mob=r"^9",            nd=9,  note=""),
    "秘鲁":     dict(cc="51",  mob=r"^9",            nd=9,  note=""),
    "阿根廷":   dict(cc="54",  mob=r"^9",            nd=11, note=""),
    "德国":     dict(cc="49",  mob=r"^1[5-7]",       nd=11, note="手机 15x/16x/17x"),
    "英国":     dict(cc="44",  mob=r"^7",            nd=10, note=""),
    "法国":     dict(cc="33",  mob=r"^[67]",         nd=9,  note=""),
    "西班牙":   dict(cc="34",  mob=r"^[67]",         nd=9,  note=""),
    "意大利":   dict(cc="39",  mob=r"^3",            nd=10, note="手机以 3 开头，无前缀 0"),
    "荷兰":     dict(cc="31",  mob=r"^6",            nd=9,  note=""),
    "比利时":   dict(cc="32",  mob=r"^4",            nd=9,  note=""),
    "波兰":     dict(cc="48",  mob=r"^[5-8]",        nd=9,  note=""),
    "俄罗斯":   dict(cc="7",   mob=r"^9",            nd=10, note=""),
    "乌克兰":   dict(cc="380", mob=r"^[5-79]",       nd=9,  note=""),
    "日本":     dict(cc="81",  mob=r"^(70|80|90)",   nd=10, note=""),
    "韩国":     dict(cc="82",  mob=r"^10",           nd=10, note="手机 010"),
    "中国台湾": dict(cc="886", mob=r"^9",            nd=9,  note=""),
    "澳大利亚": dict(cc="61",  mob=r"^4",            nd=9,  note=""),
    # 北美：号码可携带，固话也能转 WhatsApp，无法从号段判断 → 只认官网证据
    "美国":     dict(cc="1",   mob=None,             nd=10, note="号段不可区分，只能靠官网/人工验证"),
    "加拿大":   dict(cc="1",   mob=None,             nd=10, note="同美国"),
}

CONTACT_HINT = re.compile(
    r"(contact|kontakt|iletisim|ilişim|lien-?he|lienhe|contato|contacto|contatt|"
    r"hubungi|about|hakkimizda|hakkımızda|gioi-thieu|ve-chung-toi|support|impressum)",
    re.I)

WA_PAT = [
    re.compile(r"wa\.me/(\+?\d[\d\s\-\(\)\.]{5,20})", re.I),
    re.compile(r"api\.whatsapp\.com/send\?[^\"'<>]*?phone=(\+?\d[\d\s\-\(\)\.]{5,20})", re.I),
    re.compile(r"web\.whatsapp\.com/send\?[^\"'<>]*?phone=(\+?\d[\d\s\-\(\)\.]{5,20})", re.I),
    re.compile(r"whatsapp://send\?[^\"'<>]*?phone=(\+?\d[\d\s\-\(\)\.]{5,20})", re.I),
]
TEL_PAT = re.compile(r"tel:(\+?\d[\d\s\-\(\)\.]{6,22})", re.I)


# ── 号码处理 ────────────────────────────────────────────────────────────────
def digits_only(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def to_e164(raw: str, country: str) -> str:
    """把各种写法归一成 +<cc><national>。<cc> 从国家规则取。"""
    d = digits_only(raw)
    if not d:
        return ""
    rule = MOBILE_RULES.get(country)
    cc = rule["cc"] if rule else ""
    if not cc:
        return "+" + d if len(d) > 10 else d
    # 已经带国家码
    if d.startswith(cc):
        return "+" + d
    # 常见写法：00 开头国际
    if d.startswith("00"):
        return "+" + d[2:]
    # 本地写法：去掉前导 0
    d2 = d.lstrip("0")
    if rule and len(d2) == rule["nd"]:
        return f"+{cc}{d2}"
    # 兜底：实在不像就给 +cc 拼上去，交给人工核
    return f"+{cc}{d2}"


def mobile_verdict(e164: str, country: str) -> tuple[str, str]:
    """返回 (结论, 说明)：mobile / landline / unknown"""
    rule = MOBILE_RULES.get(country)
    if not rule:
        return "unknown", "该国无号段规则"
    if not rule["mob"]:
        return "unknown", rule["note"]
    cc = rule["cc"]
    if not e164.startswith("+" + cc):
        return "unknown", "区号不符"
    nat = e164[len(cc) + 1:]
    if len(nat) != rule["nd"]:
        return "unknown", f"位数 {len(nat)}≠{rule['nd']}，可能含分机"
    m = re.match(rule["mob"], nat)
    if m:
        tag = m.group(1) if m.groups() else m.group(0)
        extra = f"；{rule['note']}" if rule["note"] else ""
        return "mobile", f"首位 {tag} 命中手机号段{extra}"
    return "landline", f"首位 {nat[:1]} 属固话/服务号段{('；' + rule['note']) if rule['note'] else ''}"


def wa_link(e164: str) -> str:
    return "https://wa.me/" + digits_only(e164)


# ── 抓取 ────────────────────────────────────────────────────────────────────
def _opener():
    px = (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
          or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"))
    h = urllib.request.ProxyHandler({"http": px, "https": px}) if px else urllib.request.ProxyHandler({})
    # 代理多为 MITM 证书，必须用不校验的上下文，否则大量站点 SSL 失败
    op = urllib.request.build_opener(h, urllib.request.HTTPSHandler(context=CTX))
    op.addheaders = [("User-Agent", UA), ("Accept-Language", "en,vi;q=0.8,tr;q=0.7")]
    return op


CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def fetch(url: str, timeout: int = 12) -> tuple[str, str, str]:
    """返回 (最终URL, HTML, 错误)"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with _opener().open(req, timeout=timeout) as r:
            raw = r.read(400_000)
            enc = "utf-8"
            m = re.search(r'charset=["\']?([\w-]+)', r.headers.get("Content-Type", "") or "", re.I)
            if m:
                enc = m.group(1)
            try:
                html = raw.decode(enc, "ignore")
            except LookupError:
                html = raw.decode("utf-8", "ignore")
            return r.geturl(), html, ""
    except Exception as e:  # noqa: BLE001
        return url, "", f"{type(e).__name__}: {str(e)[:70]}"


def norm_site(site: str) -> str:
    s = (site or "").strip()
    if not s:
        return ""
    if not re.match(r"^https?://", s, re.I):
        s = "https://" + s
    return s


def sniff(site: str, country: str, deep: bool = True) -> dict:
    """抓一个官网，返回证据字典"""
    res = {"match": "", "num": "", "evid": "", "conf": "", "link": "", "note": ""}
    url = norm_site(site)
    if not url:
        res["note"] = "无官网"
        return res

    home, html, err = fetch(url)
    if err:
        res["note"] = "抓取失败 " + err
        return res
    if any(p in (home + html[:4000]).lower() for p in PARKED):
        res["note"] = "域名停放/已过期，官网失效 → 该客户需重新核实"
        return res

    pages = [(home, html)]
    if deep:
        links = re.findall(r'href=["\']([^"\']{2,200})["\']', html, re.I)
        cand, seen = [], set()
        for l in links:
            if not CONTACT_HINT.search(l) or l.startswith(("mailto:", "tel:", "javascript:")):
                continue
            full = urllib.parse.urljoin(home, l)
            if full in seen or not full.startswith("http"):
                continue
            seen.add(full)
            cand.append(full)
            if len(cand) >= 2:
                break
        for u in cand:
            f, h, e = fetch(u, timeout=10)
            if not e:
                pages.append((f, h))

    # 1) WhatsApp 官方链接优先
    for purl, phtml in pages:
        for pat in WA_PAT:
            m = pat.search(phtml)
            if m:
                e164 = to_e164(m.group(1), country)
                if len(digits_only(e164)) >= 8:
                    res.update(match="官网 WhatsApp 按钮", num=e164, evid="wa.me/api.whatsapp.com 链接",
                               conf="高", link=wa_link(e164), note=f"来源 {purl}")
                    return res

    # 2) 页面里 "WhatsApp" 字样附近的号码
    for purl, phtml in pages:
        txt = re.sub(r"<[^>]+>", " ", phtml)
        for m in re.finditer(r"whats\s*app[^0-9+]{0,60}((\+?\d[\d\s\-\(\)\.]{6,20}))", txt, re.I):
            e164 = to_e164(m.group(1), country)
            if len(digits_only(e164)) >= 8:
                v, _ = mobile_verdict(e164, country)
                if v != "landline":
                    res.update(match="页面 WhatsApp 文案", num=e164, evid="正文'WhatsApp'旁号码",
                               conf="高", link=wa_link(e164), note=f"来源 {purl}")
                    return res

    # 3) tel: 链接里的手机号
    for purl, phtml in pages:
        for m in TEL_PAT.finditer(phtml):
            e164 = to_e164(m.group(1), country)
            v, why = mobile_verdict(e164, country)
            if v == "mobile":
                res.update(match="官网 tel: 手机号", num=e164, evid=f"类手机：{why}",
                           conf="中", link=wa_link(e164), note=f"来源 {purl}")
                return res

    res["note"] = f"官网无 WhatsApp 痕迹（查了 {len(pages)} 页）"
    return res


# ── 主流程 ──────────────────────────────────────────────────────────────────
def load_pool(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def run(args):
    rows = load_pool(POOL)
    mkt = (args.market or "").strip()
    if mkt:
        rows = [r for r in rows if mkt in r.get("国家", "")]
    if args.grade:
        rows = [r for r in rows if r.get("等级", "") in args.grade.split(",")]
    if args.limit:
        rows = rows[: args.limit]

    out = []
    dead = []
    crawled = 0
    if args.crawl:
        todo = [r for r in rows if (r.get("官网") or "").strip()]
        print(f"待抓 {len(todo)} 个官网（线程 {args.threads}）…")
        with ThreadPoolExecutor(max_workers=args.threads) as ex:
            futs = {ex.submit(sniff, r["官网"], r["国家"], not args.shallow): r for r in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                r = futs[fut]
                try:
                    info = fut.result()
                except Exception as e:  # noqa: BLE001
                    info = {"match": "", "num": "", "evid": "", "conf": "", "link": "", "note": f"异常 {e}"}
                crawled += 1
                if i % 10 == 0 or i == len(todo):
                    print(f"  {i}/{len(todo)} …")
                if info["conf"] in ("高", "中"):
                    out.append(_rec(r, info))
                elif "停放" in (info["note"] or ""):
                    dead.append({"公司名": r.get("公司名", ""), "国家": r.get("国家", ""),
                                 "等级": r.get("等级", ""), "官网": r.get("官网", ""),
                                 "问题": info["note"]})

    # 离线推断：池里的 电话 / WhatsApp 字段
    for r in rows:
        cur = (r.get("WhatsApp") or "").strip()
        if cur and not BLANK.match(cur):
            continue  # 已有号码的不重复报
        ph = (r.get("电话") or "").strip()
        if not ph or BLANK.match(ph):
            continue
        e164 = to_e164(ph, r["国家"])
        v, why = mobile_verdict(e164, r["国家"])
        if v == "mobile":
            out.append(_rec(r, {"match": "池内电话=手机号", "num": e164,
                                "evid": f"类手机：{why}", "conf": "中",
                                "link": wa_link(e164), "note": "未经验证，点链接看是否开通"}))
        elif v == "unknown" and r["国家"] in ("美国", "加拿大", "墨西哥"):
            continue  # 北美/墨西哥固话也常开 WhatsApp，但无从判断，不制造噪音
        elif v == "landline":
            pass  # 固话基本不可能，不输出

    # 去重（同公司同号只留高置信）
    best: dict[tuple, dict] = {}
    rank = {"高": 0, "中": 1, "低": 2}
    for o in out:
        k = (o["公司名"], o["号码"])
        if k not in best or rank[o["置信度"]] < rank[best[k]["置信度"]]:
            best[k] = o
    # 合并历史候选（增量：重跑不清空上一轮挖到的）
    if os.path.exists(OUT) and not args.fresh:
        try:
            with open(OUT, encoding="utf-8-sig") as f:
                for o in csv.DictReader(f):
                    if o.get("置信度") in ("高", "中") and o.get("号码"):
                        k = (o.get("公司名", ""), o.get("号码", ""))
                        if k not in best or rank[o["置信度"]] < rank[best[k]["置信度"]]:
                            best[k] = o
        except Exception:
            pass
    final = sorted(best.values(), key=lambda x: (rank[x["置信度"]], x["国家"], x["公司名"]))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cols = ["编号", "公司名", "国家", "等级", "官网", "匹配来源", "号码", "证据", "置信度", "wa链接", "备注"]
    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for o in final:
            w.writerow({c: o.get(c, "") for c in cols})

    if dead:
        dp = os.path.join(BASE, "leads", "_site_dead.csv")
        old_dead = []
        if os.path.exists(dp):
            with open(dp, encoding="utf-8-sig") as f:
                old_dead = list(csv.DictReader(f))
        keys = {(d.get("官网", "")) for d in old_dead}
        with open(dp, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["公司名", "国家", "等级", "官网", "问题"])
            w.writeheader()
            w.writerows(old_dead + [d for d in dead if d["官网"] not in keys])
        print(f"官网失效（停放/过期）：{len(dead)} 家 → leads/_site_dead.csv")

    hi = [o for o in final if o["置信度"] == "高"]
    mid = [o for o in final if o["置信度"] == "中"]
    print(f"\n=== 结果 ===")
    if args.crawl:
        print(f"抓取官网 {crawled} 个")
    print(f"高置信（官网自挂 WhatsApp）：{len(hi)} 家")
    print(f"中置信（官网/池内手机号，待点验）：{len(mid)} 家")
    print(f"候选表 → {OUT}")

    if args.commit:
        if not hi:
            print("没有高置信号码，不写库。")
            return
        _commit(hi, rows)


def _rec(r: dict, info: dict) -> dict:
    return {"编号": r.get("排名", ""), "公司名": r.get("公司名", ""), "国家": r.get("国家", ""),
            "等级": r.get("等级", ""), "官网": r.get("官网", ""), "匹配来源": info["match"],
            "号码": info["num"], "证据": info["evid"], "置信度": info["conf"] or "低",
            "wa链接": info["link"], "备注": info["note"]}


def _commit(hi: list[dict], rows: list[dict]):
    """只把高置信号码写进 WhatsApp 列：同公司名 + 同国家才落，且只填空不覆盖"""
    import shutil, datetime
    bak = POOL.replace(".csv", f".bak-{datetime.datetime.now():%Y%m%d-%H%M%S}.csv")
    shutil.copy2(POOL, bak)
    idx = {(r["公司名"].strip(), r["国家"].strip()): r for r in rows}
    filled = 0
    for h in hi:
        k = (h["公司名"].strip(), h["国家"].strip())
        r = idx.get(k)
        if not r:
            continue
        cur = (r.get("WhatsApp") or "").strip()
        if cur and not BLANK.match(cur):
            continue
        r["WhatsApp"] = h["号码"]
        filled += 1
    if not filled:
        print("无可写入项。")
        return
    with open(POOL, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"已写入 {filled} 家高置信 WhatsApp → 备份 {os.path.basename(bak)}")


def main():
    ap = argparse.ArgumentParser(description="挖 WhatsApp 号码（官网实抓 + 号段推断）")
    ap.add_argument("--infer", action="store_true", help="只做离线号段推断（不联网）")
    ap.add_argument("--crawl", action="store_true", help="抓官网找 wa.me 链接")
    ap.add_argument("--market", default="", help="只看某市场，如 越南")
    ap.add_argument("--grade", default="", help="只看某等级，如 A 或 A,B")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 家（试跑用）")
    ap.add_argument("--threads", type=int, default=8, help="抓取线程数，默认 8")
    ap.add_argument("--shallow", action="store_true", help="只抓首页，不追联系页（更快）")
    ap.add_argument("--fresh", action="store_true", help="清空历史候选后重算（默认增量合并）")
    ap.add_argument("--commit", action="store_true", help="把高置信号码写回线索池（自动备份）")
    args = ap.parse_args()
    if not (args.infer or args.crawl):
        args.infer = True
    run(args)


if __name__ == "__main__":
    main()
