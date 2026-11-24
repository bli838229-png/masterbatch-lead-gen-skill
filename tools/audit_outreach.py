# -*- coding: utf-8 -*-
"""首次开发信六条禁令自检 —— 发信前跑一遍，别凭手感

禁令出处：用户 2026-11-16 定的六条（首次开发邮件不要犯的错误）
  R1 不写一大段公司发展历史（尤其别放在第一段，第一段要讲客户）
  R2 不一上来就强调价格便宜
  R3 不罗列十几种产品
  R4 不直接问客户每月采购多少吨
  R5 不用明显的群发营销语言
  R6 没有证据不声称符合汽车/电缆行业认证（IATF16949 / UL / RoHS / REACH…）

用法
----
python tools/audit_outreach.py                 # 全池体检，只报有问题的
python tools/audit_outreach.py --all           # 连正常的也列（看清覆盖了多少家）
python tools/audit_outreach.py --rank 1 2 3    # 只查指定排名
python tools/audit_outreach.py --csv reports/outreach-audit.csv

退出码：0 = 无违规；1 = 有违规（可直接当流水线卡点用）
"""
import argparse
import csv
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outreach_copy import pick as pick_copy  # noqa: E402

BASE = os.environ.get("MB_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "master-lead-pool.csv")

# ---------------- 规则定义 ----------------

HIST_EN = re.compile(
    r"\b(since\s+19\d\d|since\s+20\d\d|founded\s+in|established\s+in|"
    r"for\s+(?:over\s+)?\d+\s+years|has\s+been\s+(?:\w+ing|making|producing)|"
    r"\d+\s+years\s+of\s+experience|history\s+of)\b", re.I)
HIST_ZH = re.compile(r"(1993\s*年|成立|创立|创建|多年来|余年|年的历史|深耕)")

PRICE_EN = re.compile(
    r"\b(cheap(?:er|est)?|low(?:er)?\s+price|best\s+price|competitive\s+price|"
    r"price\s+advantage|discount|save\s+(?:you\s+)?money|cut\s+(?:your\s+)?cost|"
    r"cost[- ]effective|bargain)\b", re.I)
PRICE_ZH = re.compile(r"(便宜|低价|优惠|价格优势|降价|省钱|成本更低|性价比高)")

PROD_TOKENS = [
    "black masterbatch", "white masterbatch", "colour masterbatch", "color masterbatch",
    "additive masterbatch", "filler masterbatch", "flame retardant", "antioxidant",
    "anti-static", "antistatic", "uv masterbatch", "pigment", "compound", "talc",
    "calcium carbonate", "rpET",
]
PROD_ZH = ["黑色母粒", "白色母粒", "色母粒", "填充母粒", "阻燃母粒", "抗氧剂",
           "抗静电", "紫外线", "颜料", "滑石粉", "碳酸钙", "再生"]

QTY_EN = re.compile(
    r"\b(?:per|a|each)\s+month\b|\bmonthly\b|"
    r"\bhow\s+(?:many|much)\b[^.?]{0,60}\b(?:tons?|tonnes?|kg|kilos?|volume|consume|consumption|purchase|buy)\b|"
    r"\b(?:tons?|tonnes?)\s+(?:per|a)\s+month\b", re.I)
QTY_ZH = re.compile(r"(每月|月均|月用量|月采购|多少吨|一个月.{0,6}吨)")

SPAM_EN = [
    r"dear\s+sir\s*(?:or\s+madam|/madam)?",
    r"to\s+whom\s+it\s+may\s+concern",
    r"hope\s+this\s+(?:email|mail)\s+finds\s+you\s+well",
    r"we\s+are\s+a\s+leading",
    r"leading\s+(?:manufacturer|supplier|company|exporter)",
    r"world[- ]class",
    r"high\s+quality\s+and\s+(?:competitive|low)",
    r"we\s+have\s+exported\s+to\s+\d+\s+countries",
    r"exported\s+to\s+(?:more\s+than\s+)?\d+\s+countries",
    r"looking\s+for\s+(?:distributors?|agents?|partners?)",
    r"we\s+specialize[sd]?\s+in",
    r"our\s+company\s+is\s+(?:a|one\s+of)",
    r"one[- ]stop",
    r"trusted\s+supplier",
    r"win[- ]win",
    r"prompt\s+delivery\s+and\s+(?:good|best)\s+service",
    r"please\s+(?:kindly\s+)?find\s+(?:enclosed|attached)\s+our\s+(?:catalogue|catalog|price\s+list)",
]
SPAM_ZH = [r"您好.{0,4}冒昧", r"行业领先", r"世界一流", r"质优价廉",
           r"一站式", r"期待与您合作", r"诚信经营", r"寻找(?:代理|经销商)"]

# 行业认证：只有汽车 / 电缆行业才谈得上，且必须有证据
CERT_EN = re.compile(
    r"\b(IATF\s*16949|ISO/?TS\s*16949|TS\s*16949|VDA\s*6\.?\d?|"
    r"UL\s*(?:94|listed|recognized|yellow\s*card|758)|"
    r"RoHS|REACH|IEC\s*\d+|halogen[- ]free|cable[- ]grade|automotive[- ]grade|"
    r"OEM[- ]approved|PPAP)\b", re.I)
CERT_EVIDENCE = re.compile(
    r"\b(SGS|test\s+report|third[- ]party\s+lab|certificate|on\s+file|can\s+send|"
    r"report\s+with\s+(?:every|each)|data\s+sheet)\b", re.I)

AUTO_CABLE = re.compile(r"(汽车|汽配|车用|线缆|电缆|电线|automotive|automobile|cable|wire)", re.I)


def sentences(text):
    parts = re.split(r"(?<=[.!?。！？])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


GREET = re.compile(r"^(Hi|Hello|Dear|Merhaba|Halo|Salam)\b", re.I)
# 「我们公司自称」检测：we/our/us/我们 + 你自己的品牌名（用 profile.json 里的 name 填在此处）
OURS = re.compile(r"\b(we|our|us)\b|我们", re.I)
# R2 里属于「真·报价话术」的词，出现在任何位置都算违规
PRICE_OFFER = re.compile(
    r"\b(?:best|lowest|competitive|attractive)\s+price|price\s+advantage|"
    r"\b(?:lower|cheaper)\s+than\b|we\s+can\s+(?:offer|give)\s+you\s+(?:a\s+)?(?:better|lower|cheaper)|"
    r"\bdiscount\b|报价最低|价格最优", re.I)


def check(copy, industry, name=""):
    """返回 [(规则号, 规则名, 证据)]；只看我们自己的措辞，客户事实不算"""
    hit = []
    raw_en = copy["m_en"]
    zh = copy["m_zh"]
    # 客户公司名里的词（World Class Plastics 之类）不是营销腔，先抹掉再扫
    en = re.sub(re.escape(name), " ", raw_en, flags=re.I) if name else raw_en
    paras = paragraphs(raw_en)
    first_body = paras[1] if len(paras) > 1 and GREET.match(paras[0]) else (paras[0] if paras else "")

    # R1 公司历史大段：只算「我们」的历史，且要成段/成串才叫大段
    own_hist = [s for s in sentences(raw_en)
                if HIST_EN.search(s) and OURS.search(s) and not GREET.match(s)]
    if len(own_hist) >= 2 or sum(len(s) for s in own_hist) > 220:
        hit.append((1, "公司历史大段", f"{len(own_hist)} 句/共 {sum(len(s) for s in own_hist)} 字符：" + own_hist[0][:60]))
    elif first_body and OURS.search(first_body) and HIST_EN.search(first_body):
        hit.append((1, "公司历史大段", "第一段先讲自己：" + first_body[:70]))

    # R2 价格：第一段就谈价，或出现明确报价话术（"not a cheap option" 这类反讽不算）
    m = PRICE_EN.search(first_body) or PRICE_ZH.search(paragraphs(zh)[1] if len(paragraphs(zh)) > 1 else "")
    if m and not re.search(r"not\s+(?:a\s+)?cheap|cheap\b[^.]{0,40}\bbecomes\s+expensive", first_body, re.I):
        hit.append((2, "强调价格便宜", "第一段：" + m.group(0)))
    m = PRICE_OFFER.search(en)
    if m:
        hit.append((2, "强调价格便宜", m.group(0)))
    for s_zh in re.split(r"(?<=[。！？])", zh):
        if PRICE_ZH.search(s_zh) and not re.search(r"便宜[^。]{0,24}(?:变贵|更贵|代价)|不是[^。]{0,8}便宜", s_zh):
            hit.append((2, "强调价格便宜", PRICE_ZH.search(s_zh).group(0) + "：" + s_zh.strip()[:40]))
            break

    # R3 产品罗列：单句里 ≥4 个不同产品词
    for s in sentences(en):
        toks = {t for t in PROD_TOKENS if t.lower() in s.lower()}
        if len(toks) >= 4:
            hit.append((3, "罗列产品", f"一句里 {len(toks)} 个品类：" + " / ".join(sorted(toks))))
            break
    if zh.count("母粒") >= 5:
        hit.append((3, "罗列产品", f"中文出现 {zh.count('母粒')} 次母粒品类"))

    # R4 月采购量
    m = QTY_EN.search(en) or QTY_ZH.search(zh)
    if m:
        hit.append((4, "追问月采购量", m.group(0)))

    # R5 群发营销腔（客户名已抹掉）
    for pat in SPAM_EN:
        m = re.search(pat, en, re.I)
        if m:
            hit.append((5, "群发营销语言", m.group(0)))
            break
    for pat in SPAM_ZH:
        m = re.search(pat, zh)
        if m:
            hit.append((5, "群发营销语言", m.group(0)))
            break

    # R6 行业认证：只在「我们声称自己符合」时才要求证据；描述客户需求（"UL 94 V-0 是入场券"）不算
    COND = re.compile(r"\b(consider|where|if|subject\s+to|when|available|would|could)\b", re.I)
    own_cert = [s for s in sentences(raw_en)
                if CERT_EN.search(s) and OURS.search(s) and not COND.search(s)]
    claimed = sorted({m.group(0) for s in own_cert for m in CERT_EN.finditer(s)})
    if claimed:
        has_ev = bool(CERT_EVIDENCE.search(raw_en))
        if not has_ev:
            hit.append((6, "认证无证据", "、".join(claimed) + "（无 SGS/报告/证书佐证）"))
        elif not AUTO_CABLE.search(industry) and not AUTO_CABLE.search(raw_en):
            hit.append((6, "认证无证据", "、".join(claimed) + "（与客户行业无关，反而像群发）"))

    return hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="正常客户也列出来")
    ap.add_argument("--rank", nargs="*", type=int, help="只查指定排名")
    ap.add_argument("--csv", help="把明细写成 CSV")
    ap.add_argument("--src", help="换数据源（如当日 leads/2026-11-16-US.csv），默认 master-lead-pool.csv")
    ap.add_argument("--json", help="体检手写草稿 JSON（outreach/*-drafts.json，字段 m_en/m_zh/行业）")
    a = ap.parse_args()

    if a.json:  # 手写草稿模式：直接读 JSON，不走 outreach_copy
        import json as _j
        data = _j.load(open(a.json, encoding="utf-8"))
        items = data.get("companies", data if isinstance(data, list) else [])
        bad = 0
        for it in items:
            hits = check({"m_en": it.get("m_en", ""), "m_zh": it.get("m_zh", "")},
                         it.get("industry", ""), it.get("name", ""))
            label = f"{it.get('id','')} {it.get('short') or it.get('name','')}"
            print(f"  {'✗' if hits else '✓'} {label}")
            for no, nm, ev in hits:
                bad += 1
                print(f"      R{no} {nm}：{ev[:70]}")
            print(f"      正文 {len(it.get('m_en','').split())} 词 / 主题 {len(it.get('sj_en',''))} 字符")
        print(f"\n草稿 {len(items)} 封：{'全部通过' if not bad else f'{bad} 处违规'}")
        return 1 if bad else 0

    with open(a.src or SRC, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("公司名") or "").strip()]
    rows.sort(key=lambda r: int(float(r.get("排名") or 9999)))
    if a.rank:
        rows = [r for r in rows if int(float(r.get("排名") or 0)) in set(a.rank)]

    detail, per_rule = [], {}
    clean = 0
    for r in rows:
        rank = int(float(r.get("排名") or 0))
        c = pick_copy(rank=rank, name=r["公司名"].strip(), industry=(r.get("行业") or "").strip(),
                      city=(r.get("城市") or "").strip(), country=r["国家"].strip(),
                      contact=(r.get("联系人") or "").strip(), grade=r["等级"].strip(),
                      prod=(r.get("官网产品") or "").strip(), no_pers=True)
        hits = check(c, (r.get("行业") or ""), r["公司名"].strip())
        if not hits:
            clean += 1
            if a.all:
                print(f"  ok   #{rank:<4} {r['等级']} {r['公司名'][:34]}")
            continue
        for no, nm, ev in hits:
            per_rule.setdefault((no, nm), []).append(rank)
            detail.append({"排名": rank, "等级": r["等级"].strip(), "公司": r["公司名"].strip(),
                           "规则": f"R{no}", "问题": nm, "证据": ev})

    RULE_NAME = {1: "R1 公司历史大段", 2: "R2 强调价格便宜", 3: "R3 罗列产品",
                 4: "R4 追问月采购量", 5: "R5 群发营销语言", 6: "R6 认证无证据"}

    print(f"\n体检 {len(rows)} 家：{clean} 家干净，{len(rows) - clean} 家命中")
    print("-" * 64)
    for no in sorted(RULE_NAME):
        ranks = per_rule.get((no, RULE_NAME[no].split(" ", 1)[1]), [])
        ranks = sorted(ranks) if ranks else []
        flag = "✗" if ranks else "✓"
        print(f"{flag} {RULE_NAME[no]:<16} {len(ranks):>3} 家" + (f"   {ranks[:12]}{'…' if len(ranks) > 12 else ''}" if ranks else ""))
    if detail:
        print("-" * 64)
        for d in detail[:40]:
            print(f"#{d['排名']:<4} {d['等级']} {d['公司'][:30]:<32} {d['规则']} {d['问题']}：{d['证据'][:60]}")
        if len(detail) > 40:
            print(f"… 另有 {len(detail) - 40} 条，用 --csv 导出看全")

    if a.csv:
        with open(a.csv, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["排名", "等级", "公司", "规则", "问题", "证据"])
            w.writeheader()
            w.writerows(detail)
        print(f"\n明细已写入 {a.csv}")

    return 1 if detail else 0


if __name__ == "__main__":
    sys.exit(main())
