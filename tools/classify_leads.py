# -*- coding: utf-8 -*-
"""
地图线索甄别器（工厂真伪识别 + 母粒需求判断 + 7 维预评分）

输入：maps_scrape.py 产出的 leads/<date>-map-<region>.json
      （可选）site_deepdive.py 产出的 leads/<date>-deepdive-<region>.json，用 --deepdive 合入官网/邮箱/产品

输出：
      leads/<date>-candidates-<region>.csv        合格客户（21 基础列 + 7 维，可直接入库）
      leads/<date>-candidates-<region>.evidence.json  每家的判断依据（行业/需求/信号/缺口）
      leads/<date>-rejected-<region>.csv          被剔除的（含原因，便于复核不误杀）

用法：
    python tools/classify_leads.py leads/2026-11-16-map-Ohio.json --country 美国
    python tools/classify_leads.py leads/xxx.json --country 德国 --deepdive leads/xxx-deepdive.json
    python tools/classify_leads.py leads/xxx.json --country 美国 --strict   # 必须有工艺词才算工厂

设计原则（红线）：
  - 只按抓到的文本判定，**不猜、不补**；判不出行业就标「待确认」并降级，不硬塞。
  - 每次剔除都留原因，防止误杀；宁可少而准，不要多而脏。
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys
from difflib import SequenceMatcher

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KW_FILE = os.path.join(BASE, "tools", "data", "map_keywords.json")

BASE_COLS = [
    "排名", "国家", "公司名", "行业", "城市", "总分", "等级", "官网", "邮箱", "电话",
    "联系人", "职位", "WhatsApp", "Zalo", "LINE", "KakaoTalk", "官网产品",
    "跟进状态", "最后联系日", "切入建议", "来源",
]
DIM_COLS = ["产品匹配度", "需求强度", "规模匹配度", "决策人可触达性",
            "联系渠道质量", "地域适配", "采购周期/频率"]

# ---------- 工艺识别词典（多语种，命中即认定是塑料加工厂） ----------
PROCESS_TOKENS = {
    "inj": ["injection mold", "injection mould", "inject molding", "injection molder", "注塑", "射出", "사출",
            "spritzguss", "spritzgie", "inyecc", "moldeo por inyección", "moulage par injection", "stampaggio",
            "spuitgiet", "wtrysk", "ฉีดพลาสติก", "acuan suntikan", "vstřikování", "formsprutning",
            "έγχυση", "حقن البلاستيك", "injecție",
            # 只写 Molding 的公司极多（Ohio Precision Molding 这类），必须认
            "molding", "moulding", "molder", "moulder"],
    "roto": ["rotomold", "rotomould", "rotational mold", "rotational mould", "rotocast", "滚塑", "旋转成型",
             "roto molding", "roto moulding"],
    "ext": ["extrusion", "extrud", "挤出", "押出", "압출", "wytłacz", "ekstru", "extruz",
            "vytlačování", "extrudering", "διέλαση", "بثق"],
    "blow": ["blow mold", "blow mould", "吹塑", "중공", "블로우", "blasform", "soplado", "soffiaggio",
             "sopro", "şişirme", "เป่าขึ้นรูป", "vyfukování", "blåsformning", "suflare", "εμφύσηση", "نفخ"],
    "film": ["blown film", "film extrusion", "薄膜", "吹膜", "フィルム", "필름", "folie", "fólie",
             "folha", "pellicule", "film plastico", "ฟิล์ม", "filem"],
    "pkg": ["packaging", "包装", "包裝", "포장", "verpackung", "emballage", "imballagg", "embalaje",
            "opakowania", "kemasan", "บรรจุ", "ambalaj", "obaly", "förpackning", "συσκευασία", "تغليف"],
    "auto": ["automotive", "auto parts", "automobile", "汽车", "車載", "자동차", "otomotiv", "automotriz",
             "automobile", "fordons", "αυτοκινήτ", "للسيارات"],
    "cable": ["cable", "wire harness", "电线", "电缆", "케이블", "전선", "kabel", "kablo", "cavi", "cabos",
              "καλώδι", "كابلات", "dây cáp"],
    "pipe": ["pipe", "tube", "管材", "パイプ", "배관", "rohr", "tubo", "tuyau", "rury", "pipa", "ท่อ",
             "trubky", "plaströr", "σωλήν", "أنابيب", "ống nhựa"],
    "profile": ["profile", "型材", "プロファイル", "프로파일", "profil"],
    "appliance": ["appliance", "家电", "家電", "가전", "haushaltsgerät", "electrodomést", "électroménager",
                  "elettrodomestici", "eletrodomést", "agd", "เครื่องใช้ไฟฟ้า", "spotřebiče", "vitvaror"],
    "medical": ["medical", "医疗", "医療", "의료", "medizin", "médic", "medic", "medis", "การแพทย์",
                "ιατρικ", "طبي"],
}

# 各语种工艺词补充（关键词是本地语言，识别词典必须同步覆盖，否则整类市场漏判）
_EXTRA_PROCESS = {
    "inj": ["ép phun", "enjeksiyon", "stampaggio", "inyección", "injection", "injeção", "spuitgiet",
            "wtrysk", "injeksi", "suntikan", "vstřikování", "formsprutning", "injecție", "έγχυση", "حقن"],
    "ext": ["ép đùn", "đùn nhựa", "ekstrüzyon", "estrusione", "extrusión", "extrusion", "extrusão",
            "extrusie", "wytłacz", "ekstrusi", "penyemperitan", "vytlačování", "extrudering",
            "extrudare", "διέλαση", "بثق"],
    "blow": ["thổi nhựa", "şişirme", "soffiaggio", "soplado", "soufflage", "sopro", "blaasvorm",
             "dmuchanie", "tiupan", "vyfukování", "blåsformning", "suflare", "εμφύσηση", "نفخ"],
    "film": ["màng nhựa", "plastik film", "film plastico", "film plástico", "film plastique",
             "filme plástico", "kunststoffolie", "folia", "film plastik", "ฟิล์มพลาสติก", "filem",
             "fólie", "plastfilm", "folie plastic", "φιλμ πλαστικού", "أفلام"],
    "pkg": ["bao bì nhựa", "ambalaj", "imballagg", "envase", "embalaje", "emballage", "embalagem",
            "verpakking", "opakowania", "kemasan", "บรรจุภัณฑ์", "pembungkusan", "obaly",
            "förpackning", "ambalaje", "συσκευασία", "تغليف"],
    "auto": ["linh kiện nhựa ô tô", "otomotiv", "componenti plastici automotive",
             "piezas plásticas automotrices", "pièces plastiques automobile",
             "peças plásticas automotivas", "kunststof automotive", "motoryzacyj",
             "komponen plastik otomotif", "ชิ้นส่วนพลาสติกรถยนต์", "bahagian plastik automotif",
             "plastové díly automotive", "plastdetaljer fordonsindustri", "piese plastic auto",
             "αυτοκινήτ", "للسيارات"],
    "cable": ["dây cáp điện", "ケーブル", "電線", "kablo", "cavi", "cables", "câbles", "cabos", "kabels", "kable",
              "kabel listrik", "สายไฟ", "กาบ", "kabely", "kablar", "cablu", "καλώδι", "كابلات"],
    "pipe": ["ống nhựa", "boru", "tubi", "tuberías", "tubes", "tubos", "buizen", "rury", "pipa",
             "ท่อพลาสติก", "paip", "trubky", "plaströr", "țevi", "σωλήν", "أنابيب"],
    "profile": ["thanh profile nhựa", "profil", "profili", "perfiles", "profilés", "perfis",
                "profielen", "profile", "profil plastik", "โปรไฟล์", "profily", "plastprofiler",
                "προφίλ", "بروفيل"],
    "appliance": ["linh kiện nhựa gia dụng", "beyaz eşya", "elettrodomestici", "electrodomést",
                  "électroménager", "eletrodomést", "huishoudelijke apparaten", "agd",
                  "komponen plastik elektronik", "เครื่องใช้ไฟฟ้า", "bahagian plastik perkakas",
                  "spotřebiče", "vitvaror", "electrocasnice", "συσκευ", "أجهزة"],
    "medical": ["nhựa y tế", "medikal", "medicale", "médico", "médical", "medisch", "medyczne",
                "medis", "พลาสติกการแพทย์", "perubatan", "medicín", "medicinsk", "medical",
                "ιατρικ", "طبي"],
    "roto": ["quay ly tâm", "rotasyonel", "rotazionale", "rotacional", "rotomoulage",
             "rotomoldagem", "rotatiegieten", "rotomolding", "rotasi", "rotacyjne"],
}
for _k, _v in _EXTRA_PROCESS.items():
    PROCESS_TOKENS.setdefault(_k, [])
    PROCESS_TOKENS[_k].extend([t for t in _v if t not in PROCESS_TOKENS[_k]])

PLASTIC_TOKENS = ["plastic", "plastics", "塑料", "塑膠", "樹脂", "树脂", "플라스틱", "kunststoff",
                  "plástico", "plastico", "plastique", "plastica", "plastik", "tworzyw", "nhựa",
                  "พลาสติก", "plast", "plastů", "plastové", "πλαστικ", "بلاستيك"]

# 强排除：命中即剔除（同行/上游/设备/回收，不可能是色母粒客户）
STRONG_NEG = {
    "同行（色母粒/色粉/助剂）": ["masterbatch", "色母", "母粒", "色粉", "master batch", "compounding",
                          "compound manufacturer", "pigment", "颜料", "마스터배치", "コンパウンド",
                          "farbmittel", "colorant", "colorante", "pigmento", "barviva"],
    "回收/再生料": ["recycling", "recycle", "scrap plastic", "回收", "再生料", "リサイクル", "재활용",
                 "reciclaje", "reciclagem", "recyclage", "riciclaggio", "recykling", "daur ulang",
                 "รีไซเคิล", "recyklace", "återvinning", "ανακύκλωση", "إعادة تدوير"],
    "设备/模具制造": ["machine", "machinery", "injection molding machine", "注塑机", "机械", "设备",
                 "模具", "mold maker", "mould maker", "tooling", "tool & die", "tool and die", "금형",
                 "werkzeugbau", "maschinenbau", "maquinaria", "macchine", "makine", "kalıp"],
    "非塑料（金属/玻璃/纸）": ["metal stamping", "steel fabrication", "aluminum extrusion", "glass manufacturer",
                      "paper mill", "五金", "冲压", "钣金"],
}
# 弱排除：只在「没命中任何工艺词」时才剔除（有些真工厂的文字里也会出现 supplier/wholesale）
WEAK_NEG = {
    "贸易/经销/代理": ["distributor", "wholesale", "trading company", "importer", "stockist", "supplier",
                  "供应商", "经销商", "贸易", "批发", "đại lý", "großhandel", "händler", "mayorista",
                  "distribuidor", "distributeur", "distributore", "atacadista", "toptan", "유통", "무역"],
}


# 本地语言排除词补充（贸易/回收在各市场写法不同）
_EXTRA_NEG = {
    "回收/再生料": ["tái chế", "geri dönüşüm", "recikl", "pārstrāde", "ανακύκλ", "إعادة تدوير"],
    "贸易/经销/代理": ["nhà phân phối", "toptancı", "distribütör", "bayi", "concessionario",
                  "groothandel", "hurtownia", "distribuidor", "nhập khẩu"],
}
for _cat, _toks in _EXTRA_NEG.items():
    if _cat in STRONG_NEG:
        STRONG_NEG[_cat].extend([t for t in _toks if t not in STRONG_NEG[_cat]])
    elif _cat in WEAK_NEG:
        WEAK_NEG[_cat].extend([t for t in _toks if t not in WEAK_NEG[_cat]])

INDUSTRY_ORDER = ["cable", "auto", "appliance", "medical", "film", "pipe", "profile", "blow", "roto", "inj", "ext", "pkg"]

MARKET_CHANNEL = {
    "越南": ("Zalo", "WhatsApp"),
    "韩国": ("KakaoTalk", "WhatsApp"),
    "日本": ("LINE", "WhatsApp"),
    "泰国": ("LINE", "WhatsApp"),
}


def norm_name(s):
    s = (s or "").lower()
    s = re.sub(r"[\s\-_.,&'()]+", "", s)
    for suf in ["incorporated", "inc", "llc", "ltd", "limited", "gmbh", "co", "corp", "corporation",
                "company", "kk", "kabushikikaisha", "srl", "spa", "sa", "bv", "nv", "pty", "plc",
                "pte", "sdnbhd", "tbk", "as", "ab", "oy", "spzoo"]:
        if s.endswith(suf) and len(s) > len(suf) + 2:
            s = s[: -len(suf)]
    return s


def load_kw():
    with open(KW_FILE, encoding="utf-8") as f:
        return json.load(f)


def hit(text, terms):
    for t in terms:
        if t in text:
            return t
    return None


def detect(text):
    """返回 (industries_hit{ind:token}, strong_neg[(cat,term)], weak_neg[(cat,term)], plastic_hit)"""
    inds = {}
    for ind, toks in PROCESS_TOKENS.items():
        t = hit(text, toks)
        if t:
            inds[ind] = t
    sneg = []
    for cat, toks in STRONG_NEG.items():
        t = hit(text, toks)
        if t:
            sneg.append((cat, t))
    wneg = []
    for cat, toks in WEAK_NEG.items():
        t = hit(text, toks)
        if t:
            wneg.append((cat, t))
    return inds, sneg, wneg, hit(text, PLASTIC_TOKENS)


def parse_reviews(raw):
    """从 Maps 卡片文本里取评论数，如 '4.7(128)' -> 128。取不到返回 None。"""
    m = re.search(r"\((\d{1,5})\)", raw or "")
    return int(m.group(1)) if m else None


def guess_city(text, market_cities):
    for c in market_cities:
        first = c.split()[0]
        if first and first.lower() in text.lower():
            return c
    return ""


def score_and_decide(rec, inds, sneg, wneg, plastic_hit, industry, kw, market, strict):
    """产出 7 维分 + 等级 + 需求判断 + 依据。所有缺数据处标缺口，不臆造。"""
    gaps, reasons = [], []
    tel = (rec.get("tel") or "").strip()
    site = (rec.get("site") or "").strip()
    emails = rec.get("emails") or []
    socials = rec.get("socials") or []
    products = rec.get("products") or []

    ind_meta = kw["industries"].get(industry or "", {})
    tier = ind_meta.get("tier", "")
    color = ind_meta.get("color_need", 0)
    fr = ind_meta.get("fr_need", 0)

    # 产品匹配度
    if tier == "A":
        match, why_m = 5, f"行业={ind_meta['label']}（A 级高价行业）"
    elif tier == "B":
        match, why_m = 4, f"行业={ind_meta['label']}（B 级通用加工）"
    elif industry:
        match, why_m = 3, f"行业={industry}"
    else:
        match, why_m = 2, "仅匹配『plastic』泛词，行业未确认"
        gaps.append("行业未确认")
    reasons.append(why_m)

    # 需求强度（配色 + 阻燃）
    if color or fr:
        need = min(5, max(1, round((color + fr) / 6 * 5 + 0.2)))
        if color >= 3 and fr >= 3:
            reasons.append("配色+阻燃双刚需（如线缆护套/家电外壳）")
        elif color >= 3:
            reasons.append("配色刚需（换色频繁，需 ΔE 稳定）")
        elif fr >= 2:
            reasons.append("有阻燃需求（UL94/灼热丝）")
    else:
        need = 2
        gaps.append("需求未确认")

    # 规模：地图不给员工数 → 用「评论数（活跃度代理）+ 官网产品线深度」估，绝不假装知道人数
    rv = rec.get("_reviews")
    if rv is None:
        scale = 4 if len(products) >= 2 else 3
        gaps.append("规模待核实（无评论数）")
    elif rv >= 50:
        scale = 5
    elif rv >= 10:
        scale = 4
    elif rv >= 3:
        scale = 3
    else:
        scale = 2
    if scale >= 4 and len(products) >= 2:
        scale = 5

    # 决策人可触达性（地图无实名 -> 上限 3）
    dm = 1 + (1 if tel else 0) + (1 if site else 0)
    dm = min(dm, 3)
    if not tel and not site:
        gaps.append("无任何联系方式")

    # 联系渠道质量
    if tel and (site or emails):
        ch = 4
    elif tel:
        ch = 3
    elif site or emails:
        ch = 2
    else:
        ch = 1
    if socials:
        ch = min(5, ch + 1)
    if not socials:
        gaps.append("社交号未验证")

    # 地域适配
    geo = 4 if rec.get("_city") else 3
    # 采购周期：按「配色+阻燃双需求」推断消耗频次（双刚需=连续用料，单需求=间歇），非臆造
    if (color + fr) >= 5:
        cycle = 4
    else:
        cycle = 3
        gaps.append("采购周期未知")

    dims = [match, need, scale, dm, ch, geo, cycle]
    total = sum(dims)

    # 分级：A 必须同时满足「高匹配 + 强需求 + 可触达」，缺两项以上最多 B
    if total >= 26 and match >= 5 and need >= 4 and ch >= 3 and len(gaps) <= 3:
        grade = "A"
    elif total >= 17:
        grade = "B"
    else:
        grade = "C"

    # 切入建议
    label = ind_meta.get("label", industry or "塑料加工")
    if industry == "cable":
        tip = "主推阻燃母粒（UL94 V-0/VW-1）+ 芯线分色母粒，强调护套料阻燃一致性"
    elif industry == "appliance":
        tip = "主推 UL94 V-0 阻燃母粒 + 高光免喷涂色母，强调批次色差 ΔE≤1"
    elif industry == "auto":
        tip = "主推低 ΔE 内饰色母 + IATF 批次记录，强调耐候/耐刮擦"
    elif industry == "medical":
        tip = "主推医用级色母（ISO 13485 配套）+ 阻燃，强调无重金属/生物相容"
    elif industry in ("film", "pkg"):
        tip = "主推食品接触级色母（FDA/EU 10/2011）+ 开口爽滑功能母粒"
    elif industry in ("pipe", "profile"):
        tip = "主推耐候抗 UV 色母，强调户外色牢度与批次稳定"
    elif industry in ("inj", "ext", "blow"):
        tip = "主推定制配色（来样/潘通/RAL 打色）+ 小批量起订，强调打色速度"
    else:
        tip = "先确认工艺与产品，再定主推（配色 or 阻燃）"

    conf = "高" if len(inds) >= 2 else ("中" if inds else "低")
    return {
        "dims": dims, "total": total, "grade": grade,
        "industry": industry, "industry_label": label,
        "tier": tier, "color_need": color, "fr_need": fr,
        "reasons": reasons, "gaps": gaps, "confidence": conf,
        "tip": tip,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("map_json")
    ap.add_argument("--country", required=True)
    ap.add_argument("--deepdive", help="深挖结果 json，用于补官网/邮箱/产品")
    ap.add_argument("--strict", action="store_true", help="必须有工艺词，纯『plastic』不算工厂")
    ap.add_argument("--out-prefix", help="输出前缀（默认按输入文件名推导）")
    args = ap.parse_args()

    kw = load_kw()
    market = kw["markets"].get(args.country) or next(
        (v for k, v in kw["markets"].items() if v["country"].lower() == args.country.lower()), None)
    mkey = next((k for k, v in kw["markets"].items() if v is market), args.country)
    if not market:
        sys.exit(f"market 未收录: {args.country}")

    rows = json.load(open(args.map_json, encoding="utf-8"))
    deep = {}
    if args.deepdive and os.path.exists(args.deepdive):
        for d in json.load(open(args.deepdive, encoding="utf-8")):
            deep[norm_name(d.get("name"))] = d

    today = datetime.date.today().isoformat()
    stem = os.path.basename(args.map_json).replace(".json", "")
    region = stem.split("-map-")[-1] if "-map-" in stem else mkey
    prefix = args.out_prefix or f"{today}-candidates-{region}"

    cands, rejects, evidence, unknown = [], [], [], []
    seen = {}
    dup = 0
    MFG_TOKENS = ["制造商", "manufacturer", "factory", "制造", "werken", "fabbrica", "fábrica", "üretim"]

    for r in rows:
        name = (r.get("name") or "").strip()
        if not name:
            continue
        d = deep.get(norm_name(name), {})
        merged = dict(r)
        for k in ("site", "emails", "socials", "products", "snippet", "status", "site_candidates"):
            if d.get(k):
                merged[k] = d[k]

        text = " ".join([name, r.get("raw", ""), " ".join(merged.get("products") or [])]).lower()
        inds, sneg, wneg, plastic_hit = detect(text)
        # 公司名本身就是工艺证据（如 Rotocast / Ohio Precision Molding）→ 可推翻「模具制造商」这类品类误判
        name_inds, _, _, _ = detect(name.lower())

        def reject(reason, term=""):
            rejects.append({"公司名": name, "剔除原因": reason, "命中词": term,
                            "地址": r.get("addr", ""), "原始查询": r.get("src_query", "")})

        # ---- 剔除逻辑（按优先级，留原因） ----
        if sneg:
            cat, term = sneg[0]
            # 品类写「模具制造商/机械」但名字是工艺词 → 是真加工厂，保留
            # 品类写「模具/机械」，但只要名字或正文出现真工艺（如土耳其 kalıp 常指自用模具）→ 保留
            if not (cat.startswith("设备/模具") and (name_inds or inds)):
                reject(cat, term)
                continue
        if wneg and not inds:
            cat, term = wneg[0]
            reject(cat, term)
            continue
        if not inds and not plastic_hit:
            # 品类只写「制造商」而无线索 → 不硬判为非塑料，进待确认，交人工/深挖
            if hit(text, MFG_TOKENS):
                unknown.append({"公司名": name, "原因": "品类仅『制造商』，无工艺/材质证据",
                                "地址": r.get("addr", ""), "原始查询": r.get("src_query", ""),
                                "电话": r.get("tel", "")})
            else:
                reject("非塑料加工")
            continue
        if args.strict and not inds:
            reject("无工艺证据（仅泛词命中）", plastic_hit or "")
            continue

        # 批内去重（公司名归一）
        nn = norm_name(name)
        if nn in seen:
            dup += 1
            continue
        seen[nn] = name

        industry = next((i for i in INDUSTRY_ORDER if i in inds), "")
        merged["_city"] = guess_city(" ".join([r.get("addr", ""), r.get("src_query", "")]), market["cities"])
        merged["_reviews"] = parse_reviews(r.get("raw"))
        res = score_and_decide(merged, inds, sneg, wneg, plastic_hit, industry, kw, market, args.strict)

        # 社交三态（按市场，不编号码）
        primary, secondary = MARKET_CHANNEL.get(mkey, ("WhatsApp", "LinkedIn"))
        phone = (r.get("tel") or "").strip()
        soc = {"WhatsApp": "", "Zalo": "该市场不使用—", "LINE": "该市场不使用—", "KakaoTalk": "该市场不使用—"}
        soc[primary] = "待验证⚠️" if phone else ""
        if secondary in soc:
            soc[secondary] = "待验证⚠️" if phone else ""

        cands.append({
            "排名": "",
            "国家": mkey,
            "公司名": name,
            "行业": res["industry_label"],
            "城市": merged["_city"] or "",
            "总分": str(res["total"]),
            "等级": res["grade"],
            "官网": (merged.get("site") or "").strip(),
            "邮箱": "; ".join((merged.get("emails") or [])[:2]),
            "电话": phone,
            "联系人": "",
            "职位": "",
            "WhatsApp": soc["WhatsApp"],
            "Zalo": soc["Zalo"],
            "LINE": soc["LINE"],
            "KakaoTalk": soc["KakaoTalk"],
            "官网产品": "; ".join((merged.get("products") or [])[:5]),
            "跟进状态": "未联系",
            "最后联系日": "",
            "切入建议": res["tip"],
            "来源": f"Google Maps · 查询『{r.get('src_query','')}』" + (" · 深挖补全" if d else ""),
            **{c: str(v) for c, v in zip(DIM_COLS, res["dims"])},
        })
        evidence.append({
            "公司名": name,
            "行业键": res["industry"],
            "行业": res["industry_label"],
            "等级": res["grade"],
            "总分": res["total"],
            "维度": dict(zip(DIM_COLS, res["dims"])),
            "判断依据": res["reasons"],
            "信号命中": {k: v for k, v in inds.items()},
            "数据缺口": res["gaps"],
            "置信度": res["confidence"],
            "原始查询": r.get("src_query", ""),
            "地址": r.get("addr", ""),
        })

    # 排序：A→B→C，同级别按分降序
    order = {"A": 0, "B": 1, "C": 2}
    cands.sort(key=lambda x: (order.get(x["等级"], 3), -int(x["总分"])))
    for i, c in enumerate(cands, 1):
        c["排名"] = str(i)

    os.makedirs(os.path.join(BASE, "leads"), exist_ok=True)
    out_csv = os.path.join(BASE, "leads", prefix + ".csv")
    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=BASE_COLS + DIM_COLS)
        w.writeheader()
        w.writerows(cands)

    out_ev = os.path.join(BASE, "leads", prefix + ".evidence.json")
    json.dump(evidence, open(out_ev, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    out_rej = os.path.join(BASE, "leads", prefix.replace("candidates", "rejected") + ".csv")
    with open(out_rej, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["公司名", "剔除原因", "命中词", "地址", "原始查询"])
        w.writeheader()
        w.writerows(rejects)

    out_unk = os.path.join(BASE, "leads", prefix.replace("candidates", "unsure") + ".csv")
    with open(out_unk, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["公司名", "原因", "地址", "原始查询", "电话"])
        w.writeheader()
        w.writerows(unknown)

    from collections import Counter
    g = Counter(c["等级"] for c in cands)
    rc = Counter(r["剔除原因"] for r in rejects)
    print(f"输入 {len(rows)} 家 → 合格 {len(cands)} 家（A{g.get('A',0)}/B{g.get('B',0)}/C{g.get('C',0)}）"
          f"，剔除 {len(rejects)} 家，待确认 {len(unknown)} 家，批内重名 {dup} 家")
    if rc:
        print("剔除分布：" + "；".join(f"{k} {v}" for k, v in rc.most_common()))
    print(f"  合格表: {out_csv}")
    print(f"  证据表: {out_ev}")
    print(f"  剔除表: {out_rej}")
    print(f"  待确认: {out_unk}")
    print("\nTop 8：")
    for c in cands[:8]:
        print(f"  {c['等级']} {c['总分']:>2} | {c['公司名'][:34]:<34} | {c['行业'][:10]:<10} | {c['城市'][:14]:<14} | {c['电话'] or '无电话'}")
    if len(cands) < 30:
        print(f"\n⚠️ 合格仅 {len(cands)} 家，未达 30 家铁律 → 换关键词/换城市继续补搜")


if __name__ == "__main__":
    main()
