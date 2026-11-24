# -*- coding: utf-8 -*-
"""
线索入库器（多键去重 + 增量合并 + 入库前校验）

把 classify_leads.py 产出的合格客户表，按 4 类键去重后合并进 master-lead-pool.csv：
  1) 官网域名       2) 邮箱域名（排除免费邮局）   3) 电话归一化（后 9 位）   4) 公司名（去后缀 + 模糊匹配）

规则：
  - 已存在 → **只补空字段，绝不覆盖已有值**（人工核实过的信息优先级最高），记「合并」
  - 不存在 → 追加，记「新增」
  - 写库前自动备份；写完自动跑 schema_check，不通过则回滚

用法：
    python tools/import_leads.py leads/2026-11-16-candidates-Ohio.csv            # 预演（默认，不写库）
    python tools/import_leads.py leads/2026-11-16-candidates-Ohio.csv --commit   # 实际写入
"""
import argparse
import csv
import datetime
import os
import re
import shutil
import sys
from difflib import SequenceMatcher

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(BASE, "master-lead-pool.csv")

BASE_COLS = [
    "排名", "国家", "公司名", "行业", "城市", "总分", "等级", "官网", "邮箱", "电话",
    "联系人", "职位", "WhatsApp", "Zalo", "LINE", "KakaoTalk", "官网产品",
    "跟进状态", "最后联系日", "切入建议", "来源",
]
DIM_COLS = ["产品匹配度", "需求强度", "规模匹配度", "决策人可触达性",
            "联系渠道质量", "地域适配", "采购周期/频率"]

PLACEHOLDER = {"待验证⚠️", "该市场不使用—", "待核实", "-", "—", "n/a", "N/A"}

FREE_MAIL = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "qq.com",
             "163.com", "126.com", "foxmail.com", "gmx.de", "web.de", "orange.fr", "libero.it",
             "naver.com", "daum.net", "hanmail.net", "yandex.ru", "mail.ru", "rediffmail.com"}

LEGAL_SUFFIX = ["incorporated", "inc", "llc", "ltd", "limited", "gmbh", "co", "corp", "corporation",
                "company", "kk", "srl", "spa", "sa", "bv", "nv", "pty", "plc", "pte", "sdnbhd",
                "tbk", "as", "ab", "oy", "spzoo", "lda"]


def norm_name(s):
    s = (s or "").lower()
    s = re.sub(r"[\s\-_.,&'()]+", "", s)
    for suf in LEGAL_SUFFIX:
        if s.endswith(suf) and len(s) > len(suf) + 2:
            s = s[: -len(suf)]
            break
    return s


def domain_of(url):
    d = re.sub(r"^https?://", "", (url or "").strip().lower())
    return d.split("/")[0].replace("www.", "")


def email_domain(e):
    e = (e or "").strip().lower()
    if "@" not in e:
        return ""
    d = e.split("@")[-1]
    return "" if d in FREE_MAIL else d


def norm_phone(p):
    d = re.sub(r"\D", "", p or "")
    return d[-9:] if len(d) >= 7 else ""


def read_pool():
    with open(POOL, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return BASE_COLS, []
    header = rows[0]
    data = [r for r in rows[1:] if any((c or "").strip() for c in r)]
    # 历史坏行补齐/截断
    data = [(r + [""] * len(header))[: len(header)] if len(r) != len(header) else r for r in data]
    return header, data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidates")
    ap.add_argument("--commit", action="store_true", help="实际写入（默认只预演）")
    ap.add_argument("--fuzzy", type=float, default=0.90, help="公司名模糊阈值（默认 0.90）")
    args = ap.parse_args()

    with open(args.candidates, encoding="utf-8-sig", newline="") as f:
        cand = [r for r in csv.DictReader(f) if (r.get("公司名") or "").strip()]
    if not cand:
        sys.exit("候选表为空")

    header, data = read_pool()
    idx = {c: i for i, c in enumerate(header)}

    # 建索引
    by_dom, by_mail, by_tel, by_name = {}, {}, {}, {}
    for i, r in enumerate(data):
        d = dict(zip(header, r))
        dm = domain_of(d.get("官网"))
        if dm:
            by_dom.setdefault(dm, i)
        em = email_domain(d.get("邮箱"))
        if em:
            by_mail.setdefault(em, i)
        ph = norm_phone(d.get("电话"))
        if ph:
            by_tel.setdefault(ph, i)
        by_name.setdefault(norm_name(d.get("公司名")), i)

    names = list(by_name.keys())
    added, merged, skipped = [], [], []
    touched = {}   # 行号 -> 补了哪些字段

    for c in cand:
        nm = norm_name(c["公司名"])
        dm = domain_of(c.get("官网"))
        em = email_domain(c.get("邮箱"))
        ph = norm_phone(c.get("电话"))

        hit_i, hit_key = None, ""
        if dm and dm in by_dom:
            hit_i, hit_key = by_dom[dm], f"官网域名 {dm}"
        if hit_i is None and em and em in by_mail:
            hit_i, hit_key = by_mail[em], f"邮箱域名 {em}"
        if hit_i is None and ph and ph in by_tel:
            hit_i, hit_key = by_tel[ph], f"电话尾号 {ph}"
        if hit_i is None and nm in by_name:
            hit_i, hit_key = by_name[nm], "公司名完全相同"
        if hit_i is None and len(nm) >= 6:
            best, best_r = None, 0
            for k, j in by_name.items():
                if abs(len(k) - len(nm)) > 8:
                    continue
                r = SequenceMatcher(None, nm, k).ratio()
                if r > best_r:
                    best, best_r = j, r
            if best is not None and best_r >= args.fuzzy:
                hit_i, hit_key = best, f"公司名近似 {best_r:.2f}"

        if hit_i is not None:
            row = data[hit_i]
            filled = []
            for col in BASE_COLS:
                if col in ("排名", "来源", "跟进状态", "等级", "总分"):
                    continue
                j = idx[col]
                newval = (c.get(col) or "").strip()
                if not (row[j] or "").strip() and newval and newval not in PLACEHOLDER:
                    row[j] = newval
                    filled.append(col)
            if filled:
                merged.append((c["公司名"], hit_key, filled))
                touched[hit_i] = filled
                # 来源追加
                j = idx["来源"]
                src_new = (c.get("来源") or "").strip()
                if src_new and src_new not in (row[j] or ""):
                    row[j] = ((row[j] or "").strip() + " | " + src_new).strip(" |")
            else:
                skipped.append((c["公司名"], hit_key))
            continue

        new = [(c.get(col) or "").strip() for col in BASE_COLS]
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
        added.append(c["公司名"])

    # 重排名：A→B→C，同级别按分降序
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

    print(f"候选 {len(cand)} 家 → 新增 {len(added)} · 合并 {len(merged)} · 跳过(信息无增益) {len(skipped)}")
    if merged:
        print("\n[合并明细]（只补空字段，不覆盖已有值）")
        for n, k, f in merged[:10]:
            print(f"  ~ {n[:36]:<36} ← {k} | 补: {', '.join(f)}")
    if skipped:
        print("\n[跳过]")
        for n, k in skipped[:8]:
            print(f"  = {n[:36]:<36} ← {k}（库内已有，且无新信息）")

    if not args.commit:
        print(f"\n这是预演，未写入。确认无误后加 --commit 执行。当前库 {len(data) - len(added)} 条 → 将变为 {len(data)} 条")
        return

    # 备份 → 写入 → 校验 → 失败回滚
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = POOL + f".bak-import-{stamp}"
    shutil.copy2(POOL, bak)
    with open(POOL, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(data)

    rc = os.system(f'cd "{BASE}" && python tools/schema_check.py > "{BASE}\\logs\\_import_check.log" 2>&1')
    with open(os.path.join(BASE, "logs", "_import_check.log"), encoding="utf-8", errors="replace") as f:
        log = f.read()
    if rc != 0:
        shutil.copy2(bak, POOL)
        print("\n❌ 入库后校验未通过，已回滚到备份：" + os.path.basename(bak))
        print(log)
        sys.exit(1)

    print(f"\n✅ 已写入 {POOL}（共 {len(data)} 条）")
    print(f"   备份: {os.path.basename(bak)}")


if __name__ == "__main__":
    main()
