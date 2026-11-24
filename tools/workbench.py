# -*- coding: utf-8 -*-
"""本地客户工作台（单文件服务）

数据全部存本地：
  - 权威客户数据 = master-lead-pool.csv（国家/等级/状态/联系方式）
  - 开发信内容   = logs/_leads_<日期>.json（wa_opener/email_body 等，按公司名+国家匹配）
  - 跟进状态     = 本地 SQLite 数据库（workbench.db），点选即落盘，不依赖浏览器 localStorage

启动：python tools/workbench.py   → 浏览器打开 http://127.0.0.1:8610
说明：只监听 127.0.0.1（本机），不对外网暴露；所有数据留在本机磁盘。
"""
import csv
import glob
import json
import os
import re
import smtplib
import sqlite3
import sys
import threading
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

BASE = os.environ.get("MB_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(BASE, "master-lead-pool.csv")
DB = os.path.join(BASE, "workbench.db")
LOGS = os.path.join(BASE, "logs")
SMTP_CFG = os.path.join(BASE, "smtp_config.json")
HOST = "127.0.0.1"
# 端口可通过环境变量 MB_PORT 覆盖（默认 8610）。若本机已有旧工作台占着端口，
# 可用 `MB_PORT=8611 python tools/workbench.py` 另开一个隔离实例，避免读到旧数据。
PORT = int(os.environ.get("MB_PORT", "8610"))

VALID_STATUS = ["未联系", "已发信", "已回复", "已报价", "已寄样", "成交", "无效"]

# ---------- SMTP 配置（本地明文，仅本机） ----------
def load_smtp_cfg():
    if os.path.exists(SMTP_CFG):
        try:
            return json.load(open(SMTP_CFG, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_smtp_cfg(cfg):
    json.dump(cfg, open(SMTP_CFG, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def detect_smtp(address):
    """根据发件邮箱域名推断 SMTP 服务器/端口/加密方式"""
    addr = (address or "").strip().lower()
    if addr.endswith("@gmail.com"):
        return {"host": "smtp.gmail.com", "port": 587, "tls": True}
    if addr.endswith("@qq.com"):
        return {"host": "smtp.qq.com", "port": 465, "ssl": True}
    if addr.endswith("@163.com"):
        return {"host": "smtp.163.com", "port": 465, "ssl": True}
    if addr.endswith("@126.com"):
        return {"host": "smtp.126.com", "port": 465, "ssl": True}
    if addr.endswith("@outlook.com") or addr.endswith("@hotmail.com"):
        return {"host": "smtp.office365.com", "port": 587, "tls": True}
    if addr.endswith("@sina.com"):
        return {"host": "smtp.sina.com", "port": 465, "ssl": True}
    # 默认走 587 STARTTLS，用户可手动改 host/port
    return {"host": "", "port": 587, "tls": True}


def send_one_email(cfg, to_addr, subject, body, from_name=None, server=None):
    """用 smtplib 发一封邮件。cfg 需含 user/pass（以及可选 host/port/ssl/tls）。
    server：若传入已建立并登录的 SMTP 连接，则复用（批量发送时避免反复登录被限速）。
    返回 (ok, err_msg)"""
    user = (cfg.get("user") or "").strip()
    pwd = (cfg.get("pass") or "").strip()
    if not user or not pwd:
        return False, "未配置发件邮箱或授权码"

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header(from_name or user.split("@")[0], "utf-8")), user))
    msg["To"] = to_addr

    own_conn = server is None
    try:
        if server is None:
            s = detect_smtp(user)
            host = (cfg.get("host") or "").strip() or s["host"]
            port = int(cfg.get("port") or s["port"])
            use_ssl = bool(cfg.get("ssl", s.get("ssl", False)))
            use_tls = bool(cfg.get("tls", s.get("tls", False)))
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port, timeout=40)
            else:
                server = smtplib.SMTP(host, port, timeout=40)
            server.ehlo()
            if use_tls and not use_ssl:
                server.starttls()
                server.ehlo()
            server.login(user, pwd)
        server.sendmail(user, [to_addr], msg.as_string())
        return True, ""
    except Exception as e:
        return False, str(e)
    finally:
        if own_conn and server is not None:
            try:
                server.quit()
            except Exception:
                pass


# ---------- 数据库（本地状态） ----------
def init_db():
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS followup (
        id TEXT PRIMARY KEY,          -- 公司名|国家 的归一键
        status TEXT,                  -- 跟进状态
        note TEXT,                    -- 备注
        updated TEXT                  -- 更新时间
    )""")
    con.execute("""CREATE TABLE IF NOT EXISTS sent (
        id TEXT PRIMARY KEY,
        sent_at TEXT
    )""")
    con.commit()
    return con


def norm_key(name, country):
    s = (name or "").strip().lower()
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", s)
    return f"{s}|{(country or '').strip()}"


# ---------- 数据加载 ----------
_pool_cache = None
_json_cache = None


def load_pool():
    global _pool_cache
    if _pool_cache is not None:
        return _pool_cache
    rows = []
    with open(POOL, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    _pool_cache = rows
    return rows


def load_json_index():
    """把每日 _leads_*.json 按 (公司名,国家) 建索引，供补充开发信内容"""
    global _json_cache
    if _json_cache is not None:
        return _json_cache
    idx = {}
    for f in sorted(glob.glob(os.path.join(LOGS, "_leads_*.json"))):
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for d in data:
            name = d.get("name", "")
            # 每日 JSON 无国家字段，用 name 做单键（够用，因每天单市场）
            k = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (name or "").strip().lower())
            if k:
                idx[k] = d
    _json_cache = idx
    return idx


def merge_content(row, json_idx):
    """把每日 JSON 里的开发信内容按公司名合并进来"""
    k = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (row.get("公司名", "") or "").strip().lower())
    j = json_idx.get(k)
    if not j:
        return row
    for field in ("wa_opener", "wa_opener_cn", "wa_opener_local",
                  "email_subject", "email_subject_cn", "email_body", "email_body_cn"):
        if j.get(field):
            row[field] = j[field]
    # 官网产品：JSON 里叫 products，CSV 里叫 官网产品
    if j.get("products") and not row.get("官网产品"):
        row["官网产品"] = j["products"]
    return row


# ---------- 身份信息（从 profile.json 读取，避免硬编码签名） ----------
PROFILE_PATH = os.path.join(BASE, "tools", "profile.json")

def load_profile():
    """从 tools/profile.json 读取姓名/公司/城市，供开场白签名使用。
    缺失时回退到中性占位，绝不硬编码任何真人签名。"""
    try:
        with open(PROFILE_PATH, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    name = (d.get("name") or "").strip()
    name_cn = (d.get("name_cn") or "").strip()
    city = (d.get("city") or "").strip()
    city_cn = (d.get("city_cn") or "").strip()
    company = (d.get("company") or "").strip()
    if not name:
        name = "your name"
    if not name_cn:
        name_cn = name
    if not city:
        city = "your city"
    if not city_cn:
        city_cn = city
    return name, name_cn, city, city_cn, company


# ---------- WhatsApp 开场白补齐（朋友问候式、简短、按产品） ----------
def wa_greeting(row):
    """生成简短朋友式 WhatsApp 开场白（统一风格，按行业/产品定制）。
    返回 (opener_en, opener_cn)。"""
    industry = (row.get("行业") or "").strip()
    country = (row.get("国家") or "").strip()
    company = (row.get("公司名") or "").strip()

    # 按行业关键词匹配，生成贴合其工厂产品的开场白（短、朋友口吻）
    text = industry.lower()
    if "电缆" in industry or "线缆" in industry or "cable" in text or "kabel" in text:
        product = "cable & wire colouring"
        cn = "电线电缆配色"
    elif "hdpe" in text or "管材" in industry or "pipe" in text or "管" in industry:
        product = "HDPE pipe colouring"
        cn = "HDPE管材配色"
    elif "薄膜" in industry or "film" in text or "袋" in industry:
        product = "film & packaging colouring"
        cn = "薄膜/包装配色"
    elif "吹塑" in industry or "blow" in text or "瓶" in industry or "bottle" in text:
        product = "blow moulding colouring"
        cn = "吹塑配色"
    elif "注塑" in industry or "injection" in text or "molding" in text or "moulding" in text or "压铸" in industry:
        product = "injection moulding colouring"
        cn = "注塑配色"
    elif "食品" in industry or "food" in text or "iml" in text:
        product = "food-grade packaging colouring"
        cn = "食品级包装配色"
    elif "包装" in industry or "packaging" in text:
        product = "packaging colouring"
        cn = "包装配色"
    else:
        product = "your plastic colouring"
        cn = "塑料配色"

    name, name_cn, city, city_cn, company = load_profile()
    opener_en = (f"Hi! {name} from {city} here. We make colour masterbatch "
                 f"for {product}. Happy to free-match a sample for you — just message me.")
    opener_cn = f"你好！我是{city_cn}的 {name_cn}，做{cn}用色母粒。可以免费帮你打个样配色，发我样品就行，随时聊。"
    return opener_en, opener_cn


def get_wa_list():
    """返回有真实 WhatsApp 号的客户，附带（补齐后的）开场白与备注建议"""
    import re as _re
    def is_wa(v):
        s = (v or "").strip()
        if not s:
            return False
        if s.startswith(("该市场", "待", "明确无", "无", "不")):
            return False
        return len(_re.sub(r"\D", "", s)) >= 8

    def clean_wa(v):
        # 去空格/括号等，保留 + 和数字
        return _re.sub(r"[^\d+]", "", (v or "").strip())

    out = []
    for c in get_all_customers():
        raw = c.get("WhatsApp") or ""
        if not is_wa(raw):
            continue
        opener_en, opener_cn = wa_greeting(c)
        # 备注建议：公司名 + 产品（简短）
        company = (c.get("公司名") or "").strip()
        product = (c.get("官网产品") or "").strip() or (c.get("行业") or "").strip()
        note = f"{company} | {product}" if product else company
        out.append({
            "_key": c.get("_key"),
            "公司名": company,
            "国家": c.get("国家", ""),
            "等级": c.get("等级", ""),
            "行业": c.get("行业", ""),
            "WhatsApp": clean_wa(raw),
            "联系人": c.get("联系人", ""),
            "开场白": opener_en,
            "开场白_cn": opener_cn,
            "备注": note,
            "已发送": c.get("已发送"),
            "跟进状态": c.get("跟进状态", "未联系"),
        })
    # 排序：等级 A>B>C，再按国家
    order = {"A": 0, "B": 1, "C": 2}
    out.sort(key=lambda x: (order.get(x["等级"], 3), x["国家"]))
    return out


# ---------- 当天新客户（暂存区） ----------
def _norm_name(s):
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (s or "").strip().lower())


def get_pool_names():
    """总池里所有公司名的归一化集合"""
    pool = load_pool()
    return {_norm_name(r.get("公司名", "")) for r in pool if r.get("公司名")}


def _daily_followup(key, fallback=""):
    """读当天客户在本地库里的跟进状态（key = 公司名归一|日期）。"""
    con = init_db()
    cur = con.execute("SELECT status FROM followup WHERE id=?", (key,))
    r = cur.fetchone()
    return (r[0] if r else fallback)


def get_pool_status_map():
    """总池里 (归一公司名|国家) -> 跟进状态 的映射，用于当天客户 in_pool 时回显。"""
    pool = load_pool()
    m = {}
    for r in pool:
        name = (r.get("公司名") or "").strip()
        country = (r.get("国家") or "").strip()
        if not name:
            continue
        m[norm_key(name, country)] = (r.get("跟进状态") or "未联系").strip()
    return m


def get_daily_leads_detail():
    """扫描 logs/_leads_*.json，返回按日期分组的当天客户明细，
    并标注每家在不在总池（in_pool）、以及有效跟进状态（本地库 > 总池 > JSON 初始值）。"""
    pool_names = get_pool_names()
    pool_status = get_pool_status_map()
    result = []
    for f in sorted(glob.glob(os.path.join(LOGS, "_leads_*.json")), reverse=True):
        m = re.search(r"_leads_(\d{8})\.json", f)
        if not m:
            continue
        date = m.group(1)
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for d in data:
            name = d.get("name", "")
            nm = _norm_name(name)
            if not nm:
                continue
            key = f"{nm}|{date}"
            in_pool = nm in pool_names
            # 有效跟进状态：本地库（当天 key）优先；否则若已入库取总池状态；再否则取 JSON 初始 status
            db_status = _daily_followup(key, "")
            if db_status:
                followup = db_status
            elif in_pool:
                followup = pool_status.get(norm_key(name, d.get("country") or d.get("国家") or ""), "未联系")
            else:
                followup = d.get("status", "") or "未联系"
            result.append({
                "date": date,
                "name": name,
                "country": d.get("country") or d.get("国家") or d.get("market") or "",
                "industry": d.get("industry", ""),
                "city": d.get("city", ""),
                "grade": d.get("grade", ""),
                "total": d.get("total", 0),
                "website": d.get("website", ""),
                "email": d.get("email", ""),
                "phone": d.get("phone", ""),
                "contact": d.get("contact", ""),
                "job": d.get("job", ""),
                "whatsapp": d.get("whatsapp", ""),
                "products": d.get("products", ""),
                "pitch": d.get("pitch", ""),
                "source": d.get("source", ""),
                "wa_opener": d.get("wa_opener", ""),
                "email_subject": d.get("email_subject", ""),
                "email_body": d.get("email_body", ""),
                "in_pool": in_pool,
                "followup": followup,
                "_key": key,  # 暂存区专用 key
            })
    return result


def get_daily_new():
    """当天新客户列表（含是否已入库），按日期倒序、等级排序"""
    items = get_daily_leads_detail()
    order = {"A": 0, "B": 1, "C": 2}
    items.sort(key=lambda x: (x["date"], order.get(x["grade"], 3), -safe_int(x["total"])), reverse=False)
    return items


# ---------- 并入总池（复用 import_leads 去重逻辑） ----------
FREE_MAIL = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "qq.com",
             "163.com", "126.com", "foxmail.com", "gmx.de", "web.de", "orange.fr", "libero.it",
             "naver.com", "daum.net", "hanmail.net", "yandex.ru", "mail.ru", "rediffmail.com"}
LEGAL_SUFFIX = ["incorporated", "inc", "llc", "ltd", "limited", "gmbh", "co", "corp", "corporation",
                "company", "kk", "srl", "spa", "sa", "bv", "nv", "pty", "plc", "pte", "sdnbhd",
                "tbk", "as", "ab", "oy", "spzoo", "lda"]
PLACEHOLDER = {"待验证⚠️", "该市场不使用—", "待核实", "-", "—", "n/a", "N/A"}
POOL_COLS = ["排名", "国家", "公司名", "行业", "城市", "总分", "等级", "官网", "邮箱", "电话",
             "联系人", "职位", "WhatsApp", "Zalo", "LINE", "KakaoTalk", "官网产品",
             "跟进状态", "最后联系日", "切入建议", "来源"]


def _norm_name_pool(s):
    s = (s or "").lower()
    s = re.sub(r"[\s\-_.,&'()]+", "", s)
    for suf in LEGAL_SUFFIX:
        if s.endswith(suf) and len(s) > len(suf) + 2:
            s = s[:-len(suf)]
            break
    return s


def _domain_of(url):
    d = re.sub(r"^https?://", "", (url or "").strip().lower())
    return d.split("/")[0].replace("www.", "")


def _email_domain(e):
    e = (e or "").strip().lower()
    if "@" not in e:
        return ""
    d = e.split("@")[-1]
    return "" if d in FREE_MAIL else d


def _norm_phone(p):
    d = re.sub(r"\D", "", p or "")
    return d[-9:] if len(d) >= 7 else ""


def merge_into_pool(items, commit=True):
    """把当天客户 items（dict 列表，字段同 daily_leads_detail）按四键去重合并进总池。
    返回 (stats, err)。"""
    from difflib import SequenceMatcher
    import shutil
    import datetime

    # 读总池
    with open(POOL, encoding="utf-8-sig", newline="") as f:
        header, data = _read_pool_csv(f)
    idx = {c: i for i, c in enumerate(header)}

    by_dom, by_mail, by_tel, by_name = {}, {}, {}, {}
    for i, r in enumerate(data):
        d = dict(zip(header, r))
        dm = _domain_of(d.get("官网"))
        if dm:
            by_dom.setdefault(dm, i)
        em = _email_domain(d.get("邮箱"))
        if em:
            by_mail.setdefault(em, i)
        ph = _norm_phone(d.get("电话"))
        if ph:
            by_tel.setdefault(ph, i)
        by_name.setdefault(_norm_name_pool(d.get("公司名")), i)

    added, merged, skipped = [], [], []
    names = list(by_name.keys())

    for c in items:
        nm = _norm_name_pool(c.get("name", ""))
        dm = _domain_of(c.get("website"))
        em = _email_domain(c.get("email"))
        ph = _norm_phone(c.get("phone"))

        hit_i, hit_key = None, ""
        if dm and dm in by_dom:
            hit_i, hit_key = by_dom[dm], f"官网 {dm}"
        if hit_i is None and em and em in by_mail:
            hit_i, hit_key = by_mail[em], f"邮箱 {em}"
        if hit_i is None and ph and ph in by_tel:
            hit_i, hit_key = by_tel[ph], f"电话 {ph}"
        if hit_i is None and nm in by_name:
            hit_i, hit_key = by_name[nm], "公司名相同"
        if hit_i is None and len(nm) >= 6:
            best, best_r = None, 0
            for k, j in by_name.items():
                if abs(len(k) - len(nm)) > 8:
                    continue
                r = SequenceMatcher(None, nm, k).ratio()
                if r > best_r:
                    best, best_r = j, r
            if best is not None and best_r >= 0.90:
                hit_i, hit_key = best, f"公司名近似 {best_r:.2f}"

        # 组装候选行（当天字段 → 总池列）
        cand = {
            "国家": c.get("country", ""),
            "公司名": c.get("name", ""),
            "行业": c.get("industry", ""),
            "城市": c.get("city", ""),
            "总分": str(c.get("total", 0)),
            "等级": c.get("grade", ""),
            "官网": c.get("website", ""),
            "邮箱": c.get("email", ""),
            "电话": c.get("phone", ""),
            "联系人": c.get("contact", ""),
            "职位": "",
            "WhatsApp": c.get("whatsapp", ""),
            "Zalo": "", "LINE": "", "KakaoTalk": "",
            "官网产品": c.get("products", ""),
            "跟进状态": "未联系",
            "最后联系日": "",
            "切入建议": c.get("pitch", ""),
            "来源": c.get("source", ""),
        }

        if hit_i is not None:
            row = data[hit_i]
            filled = []
            for col in POOL_COLS:
                if col in ("排名", "来源", "跟进状态", "等级", "总分"):
                    continue
                j = idx[col]
                newval = (cand.get(col) or "").strip()
                if not (row[j] or "").strip() and newval and newval not in PLACEHOLDER:
                    row[j] = newval
                    filled.append(col)
            if filled:
                merged.append((cand["公司名"], hit_key, filled))
                j = idx["来源"]
                src_new = (cand.get("来源") or "").strip()
                if src_new and src_new not in (row[j] or ""):
                    row[j] = ((row[j] or "").strip() + " | " + src_new).strip(" |")
            else:
                skipped.append((cand["公司名"], hit_key))
            continue

        new = [(cand.get(col) or "").strip() for col in POOL_COLS]
        data.append(new)
        i = len(data) - 1
        if dm:
            by_dom[dm] = i
        if em:
            by_mail[em] = i
        if ph:
            by_tel[ph] = i
        by_name[nm] = i
        names.append(nm)
        added.append(cand["公司名"])

    # 重排名
    order = {"A": 0, "B": 1, "C": 2}

    def key(r):
        d = dict(zip(header, r))
        try:
            total = int(d.get("总分") or 0)
        except ValueError:
            total = 0
        return (order.get((d.get("等级") or "C").strip(), 3), -total)

    data.sort(key=key)
    for i, r in enumerate(data, 1):
        r[idx["排名"]] = str(i)

    stats = {"added": len(added), "merged": len(merged), "skipped": len(skipped),
             "added_names": added, "merged_names": [m[0] for m in merged]}

    if not commit:
        return stats, ""

    # 备份 → 写入
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = POOL + f".bak-import-{stamp}"
    shutil.copy2(POOL, bak)
    with open(POOL, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(data)
    # 清缓存，下次重新加载
    global _pool_cache
    _pool_cache = None
    stats["backup"] = os.path.basename(bak)
    return stats, ""


def _read_pool_csv(f):
    rows = list(csv.reader(f))
    if not rows:
        return POOL_COLS, []
    header = rows[0]
    data = [r for r in rows[1:] if any((c or "").strip() for c in r)]
    data = [(r + [""] * len(header))[: len(header)] if len(r) != len(header) else r for r in data]
    return header, data


def get_all_customers():
    pool = load_pool()
    jidx = load_json_index()
    con = init_db()
    out = []
    for r in pool:
        d = dict(r)
        d = merge_content(d, jidx)
        key = norm_key(r.get("公司名", ""), r.get("国家", ""))
        # 本地状态覆盖 CSV 状态（本地是最新的点选结果）
        cur = con.execute("SELECT status, note, updated FROM followup WHERE id=?", (key,))
        fu = cur.fetchone()
        if fu:
            d["跟进状态"] = fu[0] or d.get("跟进状态", "未联系")
            d["备注"] = fu[1] or ""
            d["本地更新时间"] = fu[2] or ""
        sent = con.execute("SELECT sent_at FROM sent WHERE id=?", (key,)).fetchone()
        d["已发送"] = bool(sent)
        d["_key"] = key
        out.append(d)
    return out


def get_rejected():
    """读「无联系方式」剔除客户表（leads/剔除-无联系方式.csv），供工作台「已剔除」视图展示。
    这些客户是 purge_uncontactable.py 从总池移出的（无邮箱且无社交账号），保留供人工复核/补挖。"""
    path = os.path.join(BASE, "leads", "剔除-无联系方式.csv")
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            d = dict(r)
            d["_key"] = norm_key(r.get("公司名", ""), r.get("国家", ""))
            out.append(d)
    return out


def get_daily_groups():
    """按「入库日期」维度：总池没有日期字段，改用每日 JSON 文件名作为日期锚点"""
    groups = {}
    for f in sorted(glob.glob(os.path.join(LOGS, "_leads_*.json"))):
        m = re.search(r"_leads_(\d{8})\.json", f)
        if not m:
            continue
        date = m.group(1)
        try:
            data = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        names = set()
        for d in data:
            names.add(re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (d.get("name", "") or "").strip().lower()))
        groups[date] = names
    return groups


# ---------- 查询 ----------
def query(params):
    customers = get_all_customers()
    market = params.get("market", [""])[0].strip()
    grade = params.get("grade", [""])[0].strip()
    status = params.get("status", [""])[0].strip()
    q = params.get("q", [""])[0].strip().lower()
    date = params.get("date", [""])[0].strip()

    # 按日期筛选（用每日 JSON 的公司名集合做锚点）
    if date:
        groups = get_daily_groups()
        names = groups.get(date, set())
        customers = [c for c in customers
                     if re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", (c.get("公司名", "") or "").strip().lower()) in names]

    if market:
        customers = [c for c in customers if c.get("国家", "").strip() == market]
    if grade:
        customers = [c for c in customers if c.get("等级", "").strip() == grade]
    if status:
        if status == "未发":
            customers = [c for c in customers if not c.get("已发送")]
        else:
            customers = [c for c in customers if (c.get("跟进状态") or "").strip() == status]
    if q:
        customers = [c for c in customers
                     if q in (c.get("公司名", "") + c.get("行业", "") + c.get("国家", "") + c.get("城市", "")).lower()]

    # 排序：等级 A>B>C，再按总分降序
    order = {"A": 0, "B": 1, "C": 2}
    customers.sort(key=lambda c: (order.get(c.get("等级", "C"), 3), -safe_int(c.get("总分"))) )
    return customers


def safe_int(v):
    try:
        return int(float(v or 0))
    except Exception:
        return 0


def analytics():
    """数据分析聚合：市场/行业/等级/状态/社交渠道/官网产品覆盖/邮箱覆盖/日期趋势"""
    from collections import Counter, defaultdict
    customers = get_all_customers()
    mk = Counter(c.get("国家", "?") for c in customers)
    ind = Counter((c.get("行业") or "未分类").strip() for c in customers)
    gr = Counter(c.get("等级", "?") for c in customers)
    st = Counter((c.get("跟进状态") or "未联系").strip() for c in customers)

    # 等级×市场交叉
    cross = defaultdict(lambda: defaultdict(int))
    for c in customers:
        cross[c.get("国家", "?")][c.get("等级", "?")] += 1

    # 社交渠道覆盖
    channels = {
        "WhatsApp": sum(1 for c in customers if (c.get("WhatsApp") or "").strip() and c["WhatsApp"].strip() not in ("该市场不使用—", "待核实")),
        "Zalo": sum(1 for c in customers if (c.get("Zalo") or "").strip() and c["Zalo"].strip() not in ("该市场不使用—", "待核实")),
        "LINE": sum(1 for c in customers if (c.get("LINE") or "").strip() and c["LINE"].strip() not in ("该市场不使用—", "待核实")),
        "KakaoTalk": sum(1 for c in customers if (c.get("KakaoTalk") or "").strip() and c["KakaoTalk"].strip() not in ("该市场不使用—", "待核实")),
    }

    # 日期趋势（每日新增数 + 累计）
    groups = get_daily_groups()
    dates = sorted(groups.keys())
    trend = []
    cum = 0
    for d in dates:
        n = len(groups[d])
        cum += n
        trend.append({"date": d, "new": n, "cum": cum})

    return {
        "市场": [{"name": k, "value": v} for k, v in mk.most_common()],
        "行业": [{"name": k, "value": v} for k, v in ind.most_common(12)],
        "等级": [{"name": k, "value": gr.get(k, 0)} for k in ("A", "B", "C")],
        "状态": [{"name": k, "value": v} for k, v in st.most_common()],
        "等级市场交叉": {k: dict(v) for k, v in cross.items()},
        "社交渠道": channels,
        "趋势": trend,
        "邮箱覆盖": sum(1 for c in customers if (c.get("邮箱") or "").strip() and "@" in c["邮箱"]),
        "官网产品覆盖": sum(1 for c in customers if (c.get("官网产品") or "").strip()),
        "总客户": len(customers),
        "已发送": sum(1 for c in customers if c.get("已发送")),
        "总分均值": round(sum(safe_int(c.get("总分")) for c in customers) / max(len(customers), 1), 1),
    }


def summary(customers):
    from collections import Counter
    mk = Counter(c.get("国家", "?") for c in customers)
    gr = Counter(c.get("等级", "?") for c in customers)
    st = Counter((c.get("跟进状态") or "未联系").strip() for c in customers)
    return {
        "总数": len(customers),
        "市场": dict(mk.most_common()),
        "等级": dict(gr),
        "状态": dict(st),
        "有邮箱": sum(1 for c in customers if (c.get("邮箱") or "").strip() and "@" in c["邮箱"]),
        "有官网产品": sum(1 for c in customers if (c.get("官网产品") or "").strip()),
        "已发送": sum(1 for c in customers if c.get("已发送")),
    }


# ---------- 状态更新 ----------
def update_status(key, status, note=""):
    if status not in VALID_STATUS:
        return False, f"非法状态：{status}"
    con = init_db()
    now = _now()
    con.execute("""INSERT INTO followup (id, status, note, updated) VALUES (?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET status=excluded.status,
                   note=excluded.note, updated=excluded.updated""",
                (key, status, note, now))
    con.commit()
    return True, "ok"


def set_daily_followup(key, status, name="", country=""):
    """当天客户「一键已跟进」：写入本地库当天 key；若该客户已入库，同步写总池 key，保证客户列表一致。"""
    if status not in VALID_STATUS:
        return False, f"非法状态：{status}"
    ok, msg = update_status(key, status, "")
    if not ok:
        return False, msg
    # 若已入库，同步总池（用 公司名|国家 的 key）——当天暂存区与客户列表状态保持一致
    if name:
        pool_names = get_pool_names()
        nm = _norm_name(name)
        if nm in pool_names:
            update_status(norm_key(name, country), status, "")
    return True, "ok"


def mark_sent(key, sent):
    con = init_db()
    if sent:
        con.execute("INSERT INTO sent (id, sent_at) VALUES (?,?) ON CONFLICT(id) DO NOTHING",
                    (key, _now()))
    else:
        con.execute("DELETE FROM sent WHERE id=?", (key,))
    con.commit()
    return True, "ok"


def _now():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- 批量发送（后台线程 + 进度） ----------
_send_state = {
    "running": False,
    "lock": threading.Lock(),
    "total": 0,
    "done": 0,
    "ok": 0,
    "fail": 0,
    "interval": 10,
    "results": [],   # [{name, email, ok, msg}]
    "started": "",
}


def _send_worker(keys, interval, cfg):
    """后台批量发信。复用同一条 SMTP 连接（登录一次），避免反复登录被 Gmail 限速"""
    customers = {c["_key"]: c for c in get_all_customers()}
    with _send_state["lock"]:
        _send_state["total"] = len(keys)
        _send_state["done"] = 0
        _send_state["ok"] = 0
        _send_state["fail"] = 0
        _send_state["interval"] = interval
        _send_state["results"] = []
        _send_state["started"] = _now()
        _send_state["running"] = True

    import time
    from_name = cfg.get("from_name") or ""

    # 建立并登录一次 SMTP 连接
    server = None
    try:
        s = detect_smtp((cfg.get("user") or "").strip())
        host = (cfg.get("host") or "").strip() or s["host"]
        port = int(cfg.get("port") or s["port"])
        use_ssl = bool(cfg.get("ssl", s.get("ssl", False)))
        use_tls = bool(cfg.get("tls", s.get("tls", False)))
        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=40)
        else:
            server = smtplib.SMTP(host, port, timeout=40)
        server.ehlo()
        if use_tls and not use_ssl:
            server.starttls()
            server.ehlo()
        server.login((cfg.get("user") or "").strip(), (cfg.get("pass") or "").strip())
    except Exception as e:
        # 连接/登录失败：整批失败
        with _send_state["lock"]:
            for key in keys:
                c = customers.get(key, {})
                _send_state["done"] += 1
                _send_state["fail"] += 1
                _send_state["results"].append({"name": c.get("公司名", key), "email": c.get("邮箱", ""), "ok": False, "msg": f"SMTP 连接失败：{e}"})
            _send_state["running"] = False
        if server:
            try: server.quit()
            except Exception: pass
        return

    try:
        for key in keys:
            c = customers.get(key)
            if not c:
                with _send_state["lock"]:
                    _send_state["done"] += 1
                    _send_state["fail"] += 1
                    _send_state["results"].append({"name": key, "email": "", "ok": False, "msg": "客户不存在"})
                continue

            to_addr = (c.get("邮箱") or "").strip()
            subject = c.get("email_subject") or "Business cooperation — custom masterbatch"
            body = c.get("email_body") or c.get("email_body_cn") or ""

            # 个性化替换 {联系人} 占位符
            contact = (c.get("联系人") or "").split("(")[0].split("/")[0].strip()
            if contact and contact not in ("待拆分", "待核实"):
                body = body.replace("{联系人}", contact).replace("{联系人姓名}", contact)
                body = body.replace("{contact}", contact).replace("{Contact}", contact)

            ok, err = send_one_email(cfg, to_addr, subject, body, from_name, server=server)

            with _send_state["lock"]:
                _send_state["done"] += 1
                _send_state["results"].append({"name": c.get("公司名", ""), "email": to_addr, "ok": ok, "msg": err})
                if ok:
                    _send_state["ok"] += 1
                    mark_sent(key, True)
                    update_status(key, "已发信", "")
                else:
                    _send_state["fail"] += 1

            if _send_state["done"] < _send_state["total"]:
                time.sleep(interval)
    finally:
        if server:
            try: server.quit()
            except Exception: pass
        with _send_state["lock"]:
            _send_state["running"] = False


def start_send(keys, interval, cfg):
    with _send_state["lock"]:
        if _send_state["running"]:
            return False, "已有发送任务进行中"
    if not keys:
        return False, "未选择任何客户"
    if not cfg.get("user") or not cfg.get("pass"):
        return False, "请先保存发件邮箱与授权码"
    t = threading.Thread(target=_send_worker, args=(list(keys), int(interval or 10), cfg), daemon=True)
    t.start()
    return True, "ok"


def send_progress():
    with _send_state["lock"]:
        return {
            "running": _send_state["running"],
            "total": _send_state["total"],
            "done": _send_state["done"],
            "ok": _send_state["ok"],
            "fail": _send_state["fail"],
            "interval": _send_state["interval"],
            "started": _send_state["started"],
            "results": _send_state["results"][:],
        }


# ---------- 获客发现（多渠道 discover，后台线程 + 进度） ----------
_discover_state = {
    "running": False,
    "lock": threading.Lock(),
    "phase": "",          # 当前阶段：customs/maps/web/verify/done
    "phase_done": 0,      # 当前阶段已处理数
    "phase_total": 0,     # 当前阶段总数
    "channels": [],       # 本次启用的渠道
    "total": 0,           # 合并去重后的买家总数（verify 阶段用它当 total）
    "done": 0,            # 验证完成的买家数
    "logs": [],           # [{t, msg}] 实时日志（最多保留 200 条）
    "results": [],        # 最终完整档案（官网/邮箱/WA/联系人）
    "outfile": "",
    "started": "",
}


def _discover_log(msg):
    with _discover_state["lock"]:
        _discover_state["logs"].append({"t": _now(), "msg": msg})
        if len(_discover_state["logs"]) > 200:
            _discover_state["logs"] = _discover_state["logs"][-200:]


def _load_tool(relpath, modname):
    import importlib.util
    path = os.path.join(BASE, "tools", relpath)
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _discover_worker(queries, market, channels, do_verify, limit):
    """后台跑 discover 三渠道 + 同步验证。进度写入 _discover_state"""
    try:
        disc = _load_tool("discover.py", "discover_worker")
        # 复用 discover.py 里已实现好的渠道函数，避免重复造轮子
        with _discover_state["lock"]:
            _discover_state["running"] = True
            _discover_state["channels"] = list(channels)
            _discover_state["logs"] = []
            _discover_state["results"] = []
            _discover_state["started"] = _now()
            _discover_state["phase"] = "start"
            _discover_state["done"] = 0
            _discover_state["total"] = 0
            _discover_state["outfile"] = ""

        buyers = {}
        _discover_log(f"开始：产品词「{'，'.join(queries)}」 市场「{market or '不限'}」 渠道「{'，'.join(channels)}」")

        # 阶段 1：各渠道抓取
        for ch in channels:
            with _discover_state["lock"]:
                _discover_state["phase"] = ch
                _discover_state["phase_done"] = 0
                _discover_state["phase_total"] = 0
            _discover_log(f"→ 渠道 [{ch}] 抓取中…")
            try:
                if ch == "customs":
                    got = disc.channel_customs(queries)
                elif ch == "maps":
                    if not market:
                        _discover_log("  ⚠️ maps 需要市场，跳过")
                        continue
                    got = disc.channel_maps(market, queries)
                elif ch == "web":
                    if not market:
                        _discover_log("  ⚠️ web 需要市场，跳过")
                        continue
                    got = disc.channel_web(market, queries)
                else:
                    _discover_log(f"  未知渠道 {ch}，跳过")
                    continue
            except Exception as e:
                _discover_log(f"  渠道 [{ch}] 出错：{e}")
                got = []
            new = 0
            for b in got:
                k = disc._norm(b.get("name", ""))
                if k and k not in buyers:
                    buyers[k] = b
                    new += 1
            _discover_log(f"  渠道 [{ch}] 抓到 {len(got)} 家，新增 {new}，累计 {len(buyers)}")

        merged = list(buyers.values())
        with _discover_state["lock"]:
            _discover_state["total"] = len(merged)
        _discover_log(f"三渠道合并去重后共 {len(merged)} 家")

        if do_verify and merged:
            with _discover_state["lock"]:
                _discover_state["phase"] = "verify"
                _discover_state["phase_total"] = len(merged)
                _discover_state["phase_done"] = 0
            _discover_log(f"开始同步验证（搜官网→抓邮箱/社交→挖 WhatsApp），上限 {limit or '不限'}…")
            final = disc.verify_buyers(merged, market, limit=limit)
            # verify_buyers 内部有 print，但我们要把进度也推到 state：这里粗略按结果数推进
            with _discover_state["lock"]:
                _discover_state["results"] = final
                _discover_state["phase_done"] = len(final)
                _discover_state["done"] = len(final)
        else:
            final = merged

        # 写文件
        import datetime
        today = datetime.date.today().isoformat()
        tag = re.sub(r"[^A-Za-z0-9]", "", (market or queries[0])[:20]) or "discover"
        outdir = os.path.join(BASE, "leads")
        os.makedirs(outdir, exist_ok=True)
        outfile = os.path.join(outdir, f"{today}-discover-{tag}.json")
        try:
            with open(outfile, "w", encoding="utf-8") as f:
                json.dump(final, f, ensure_ascii=False, indent=2)
            with _discover_state["lock"]:
                _discover_state["outfile"] = outfile
            _discover_log(f"已保存到 {outfile}")
        except Exception as e:
            _discover_log(f"写文件失败：{e}")

        if do_verify:
            with_site = sum(1 for r in final if r.get("site"))
            with_email = sum(1 for r in final if r.get("emails"))
            with_wa = sum(1 for r in final if r.get("whatsapp"))
            _discover_log(f"完成：共 {len(final)} 家 | 有官网 {with_site} | 有邮箱 {with_email} | 有 WhatsApp {with_wa}")
        else:
            _discover_log(f"完成：共 {len(final)} 家（未验证）")

        with _discover_state["lock"]:
            _discover_state["phase"] = "done"
            _discover_state["running"] = False
    except Exception as e:
        _discover_log(f"任务异常：{e}")
        with _discover_state["lock"]:
            _discover_state["phase"] = "error"
            _discover_state["running"] = False


def start_discover(queries, market, channels, do_verify, limit):
    with _discover_state["lock"]:
        if _discover_state["running"]:
            return False, "已有发现任务进行中"
    if not queries:
        return False, "请填写产品关键词"
    if not channels:
        return False, "请至少选择一个渠道"
    t = threading.Thread(target=_discover_worker, args=(list(queries), market or "", list(channels), bool(do_verify), int(limit or 0)), daemon=True)
    t.start()
    return True, "ok"


def discover_progress():
    with _discover_state["lock"]:
        return {
            "running": _discover_state["running"],
            "phase": _discover_state["phase"],
            "phase_done": _discover_state["phase_done"],
            "phase_total": _discover_state["phase_total"],
            "channels": _discover_state["channels"][:],
            "total": _discover_state["total"],
            "done": _discover_state["done"],
            "logs": _discover_state["logs"][:],
            "results": _discover_state["results"][:],
            "outfile": _discover_state["outfile"],
            "started": _discover_state["started"],
        }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            self._serve_html()
            return
        if u.path == "/api/customers":
            self._send({"data": query(parse_qs(u.query))})
            return
        if u.path == "/api/summary":
            self._send({"data": summary(query(parse_qs(u.query)))})
            return
        if u.path == "/api/dates":
            groups = get_daily_groups()
            # 返回日期 + 各自客户数
            self._send({"data": [{"date": d, "count": len(n)} for d, n in sorted(groups.items(), reverse=True)]})
            return
        if u.path == "/api/analytics":
            self._send({"data": analytics()})
            return
        if u.path == "/api/statuses":
            self._send({"data": VALID_STATUS})
            return
        if u.path == "/api/wa":
            self._send({"data": get_wa_list()})
            return
        if u.path == "/api/smtp":
            cfg = load_smtp_cfg()
            # 返回时打码授权码，避免前端明文回显
            pwd = cfg.get("pass", "")
            masked = pwd[:2] + "***" + pwd[-2:] if len(pwd) > 6 else "***"
            self._send({"data": {**cfg, "pass": masked, "has_pass": bool(pwd)}})
            return
        if u.path == "/api/send-progress":
            self._send({"data": send_progress()})
            return
        if u.path == "/api/daily":
            self._send({"data": get_daily_new()})

        if u.path == "/api/rejected":
            self._send({"data": get_rejected()})
            return
        if u.path == "/api/discover-progress":
            self._send({"data": discover_progress()})
            return
        self._send({"error": "not found"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            body = {}
        if u.path == "/api/status":
            ok, msg = update_status(body.get("key", ""), body.get("status", ""), body.get("note", ""))
            self._send({"ok": ok, "msg": msg}, 200 if ok else 400)
            return
        if u.path == "/api/sent":
            ok, msg = mark_sent(body.get("key", ""), bool(body.get("sent")))
            self._send({"ok": ok, "msg": msg})
            return
        if u.path == "/api/daily-status":
            ok, msg = set_daily_followup(body.get("key", ""), body.get("status", ""),
                                         body.get("name", ""), body.get("country", ""))
            self._send({"ok": ok, "msg": msg}, 200 if ok else 400)
            return
        if u.path == "/api/smtp":
            # 保存 SMTP 配置。pass 打码时（含 ***）不覆盖已存密码
            cfg = dict(body or {})
            user = (cfg.get("user") or "").strip()
            pwd = (cfg.get("pass") or "").strip()
            old = load_smtp_cfg()
            if pwd and "***" in pwd:
                cfg["pass"] = old.get("pass", "")
            cfg["user"] = user
            cfg.setdefault("from_name", cfg.get("from_name", ""))
            save_smtp_cfg(cfg)
            self._send({"ok": True, "msg": "已保存"})
            return
        if u.path == "/api/send-test":
            # 单封试发：发到指定收件地址（默认发件邮箱自己）
            cfg = load_smtp_cfg()
            to = (body.get("to") or "").strip() or cfg.get("user", "")
            subj = body.get("subject") or "测试邮件 — 色母粒工作台"
            text = body.get("body") or "这是一封来自本地获客工作台的测试邮件。"
            ok, err = send_one_email(cfg, to, subj, text, cfg.get("from_name", ""))
            self._send({"ok": ok, "msg": err or "发送成功"})
            return
        if u.path == "/api/send":
            cfg = load_smtp_cfg()
            keys = body.get("keys") or []
            interval = body.get("interval", 10)
            ok, msg = start_send(keys, interval, cfg)
            self._send({"ok": ok, "msg": msg})
            return
        if u.path == "/api/merge-pool":
            # 把选中的当天客户并入总池
            keys = body.get("keys") or []
            commit = bool(body.get("commit", True))
            if not keys:
                self._send({"ok": False, "msg": "未选择任何客户"}, 400)
                return
            all_items = get_daily_leads_detail()
            by_key = {x["_key"]: x for x in all_items}
            items = [by_key[k] for k in keys if k in by_key]
            if not items:
                self._send({"ok": False, "msg": "所选客户不存在"}, 400)
                return
            try:
                stats, err = merge_into_pool(items, commit=commit)
                self._send({"ok": True, "stats": stats, "msg": err})
            except Exception as e:
                self._send({"ok": False, "msg": str(e)}, 500)
            return
        if u.path == "/api/discover":
            # 启动多渠道获客发现任务
            q_raw = body.get("queries") or ""
            if isinstance(q_raw, list):
                queries = [q.strip() for q in q_raw if (q or "").strip()]
            else:
                queries = [q.strip() for q in str(q_raw).split(",") if q.strip()]
            market = (body.get("market") or "").strip()
            channels = body.get("channels") or []
            do_verify = bool(body.get("verify", True))
            limit = int(body.get("limit") or 0)
            ok, msg = start_discover(queries, market, channels, do_verify, limit)
            self._send({"ok": ok, "msg": msg}, 200 if ok else 400)
            return
        self._send({"error": "not found"}, 404)

    def _serve_html(self):
        html_path = os.path.join(BASE, "tools", "workbench.html")
        try:
            body = open(html_path, encoding="utf-8").read().encode("utf-8")
        except Exception:
            body = b"workbench.html not found"
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    init_db()
    # 首次加载数据，预热缓存
    get_all_customers()
    try:
        srv = ThreadingHTTPServer((HOST, PORT), Handler)
    except OSError as e:
        if "10048" in str(e) or "Address already in use" in str(e) or "10013" in str(e):
            print(f"⚠️ 端口 {PORT} 已被占用（本机可能已有一个工作台在运行）。")
            print(f"   换一个端口再启动：MB_PORT={PORT + 1} python tools/workbench.py")
            print(f"   注意：若连到了旧实例，看到的是旧实例的数据，不是本目录的数据。")
        else:
            print(f"❌ 启动失败：{e}")
        sys.exit(1)
    print(f"✅ 本地客户工作台已启动： http://{HOST}:{PORT}")
    print(f"   数据源：{POOL}")
    print(f"   状态库：{DB}（点选状态即落盘，换浏览器不丢）")
    print(f"   按 Ctrl+C 停止")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")


if __name__ == "__main__":
    main()
