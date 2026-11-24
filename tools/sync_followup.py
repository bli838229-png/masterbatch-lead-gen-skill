# -*- coding: utf-8 -*-
"""把《客户跟进表.xlsx》的跟进结果回写到 master-lead-pool.csv

只回写两列：跟进状态、最后联系日（下次跟进日只留在表里，池子 schema 不变）。
匹配键：公司名（去空格/小写/去标点）+ 国家，双键确认，匹配不到就报出来不硬塞。

用法：
    python tools/sync_followup.py            # 预演，只打印差异
    python tools/sync_followup.py --commit   # 实际写入（写前自动备份 + 写完跑 schema_check）
"""
import argparse
import csv
import datetime
import os
import re
import shutil
import subprocess
import sys

try:
    import openpyxl
except ImportError:
    print("缺少 openpyxl，请先运行：pip install openpyxl")
    sys.exit(1)

BASE = os.environ.get("MB_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # MB_HOME 可指定工作目录，默认脚本上一级
XLSX = os.path.join(BASE, "客户跟进表.xlsx")
POOL = os.path.join(BASE, "master-lead-pool.csv")
SHEET = "客户总表"

VALID_STATUS = {"未联系", "已发信", "已回复", "已报价", "已寄样", "成交", "无效"}


def norm(name: str) -> str:
    s = (name or "").strip().lower()
    s = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", s)
    for suf in ("inc", "llc", "ltd", "co", "corp", "gmbh", "bv", "sa", "plc", "jsc", "pteltd"):
        if s.endswith(suf) and len(s) > len(suf) + 2:
            s = s[: -len(suf)]
    return s


def to_date(v):
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", action="store_true", help="实际写入（默认只预演）")
    ap.add_argument("--from-csv", dest="from_csv", default="",
                    help="从《客户跟进台》导出的进度 CSV 读取（不填则读 客户跟进表.xlsx）")
    args = ap.parse_args()

    if not os.path.exists(XLSX):
        print(f"找不到跟进表：{XLSX}")
        sys.exit(1)

    xrows = []
    if args.from_csv:
        # 从《客户跟进台》HTML 导出的进度 CSV 读取
        with open(args.from_csv, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                name = (row.get("公司名") or "").strip()
                if not name:
                    continue
                ts = (row.get("更新时间") or "").strip()
                d = None
                if ts:
                    try:
                        d = datetime.date.fromisoformat(ts.split(" ")[0])
                    except ValueError:
                        d = None
                xrows.append({
                    "编号": row.get("排名"),
                    "公司名": name,
                    "国家": (row.get("国家") or "").strip(),
                    "跟进状态": (row.get("跟进状态") or "").strip(),
                    "最后跟进日": d,
                })
        print(f"（来源：跟进台导出 CSV {os.path.basename(args.from_csv)}）")
    else:
        wb = openpyxl.load_workbook(XLSX, data_only=True)
        if SHEET not in wb.sheetnames:
            print(f"跟进表里没有「{SHEET}」工作表")
            sys.exit(1)
        ws = wb[SHEET]

        # 定位表头（第 1 行）
        head = {str(ws.cell(row=1, column=c).value or "").strip(): c for c in range(1, ws.max_column + 1)}
        need = ["编号", "公司名", "国家", "跟进状态", "最后跟进日"]
        miss = [n for n in need if n not in head]
        if miss:
            print("跟进表缺少列：" + "、".join(miss))
            sys.exit(1)

        for r in range(2, ws.max_row + 1):
            name = ws.cell(row=r, column=head["公司名"]).value
            if not name:
                continue
            xrows.append({
                "编号": ws.cell(row=r, column=head["编号"]).value,
                "公司名": str(name).strip(),
                "国家": str(ws.cell(row=r, column=head["国家"]).value or "").strip(),
                "跟进状态": str(ws.cell(row=r, column=head["跟进状态"]).value or "").strip(),
                "最后跟进日": to_date(ws.cell(row=r, column=head["最后跟进日"]).value),
            })

    with open(POOL, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        pool = list(reader)

    key = {}
    for i, p in enumerate(pool):
        key[(norm(p.get("公司名")), (p.get("国家") or "").strip())] = i

    changes, unmatched, bad_status = [], [], []
    for x in xrows:
        st = x["跟进状态"] or "未联系"
        if st not in VALID_STATUS:
            bad_status.append((x["编号"], x["公司名"], st))
            continue
        idx = key.get((norm(x["公司名"]), x["国家"]))
        if idx is None:
            unmatched.append((x["编号"], x["公司名"], x["国家"]))
            continue
        p = pool[idx]
        old_st = (p.get("跟进状态") or "未联系").strip()
        old_dt = (p.get("最后联系日") or "").strip()
        new_dt = x["最后跟进日"].isoformat() if x["最后跟进日"] else old_dt
        if old_st == st and old_dt == new_dt:
            continue
        changes.append({
            "行号": idx + 2,
            "公司名": p.get("公司名"),
            "国家": p.get("国家"),
            "跟进状态": (old_st, st),
            "最后联系日": (old_dt or "(空)", new_dt or "(空)"),
        })
        p["跟进状态"] = st
        p["最后联系日"] = new_dt

    # 一致性告警：表里有跟进记录但状态还是未联系
    warn = [x for x in xrows if (x["跟进状态"] or "未联系") == "未联系" and x["最后跟进日"]]

    print(f"=== 跟进记录 {len(xrows)} 家 / 线索池 {len(pool)} 条 ===")
    if not changes:
        print("✅ 两边一致，没有需要同步的改动")
    else:
        print(f"{'将' if not args.commit else '已'}更新 {len(changes)} 条：")
        for c in changes:
            a, b = c["跟进状态"]
            d1, d2 = c["最后联系日"]
            print(f"  行{c['行号']:<5} {c['公司名'][:28]:<30} {c['国家']:<5} 状态 {a}→{b} | 最后联系 {d1}→{d2}")
    if bad_status:
        print(f"⚠️ 非法状态 {len(bad_status)} 条（跳过，请改回下拉选项）：")
        for c in bad_status[:10]:
            print("   ", c)
    if unmatched:
        print(f"⚠️ 线索池里找不到 {len(unmatched)} 家（不会硬写）：")
        for c in unmatched[:10]:
            print("   ", c)
    if warn:
        print(f"⚠️ {len(warn)} 家有跟进日期但状态仍为「未联系」，记得在总表把状态改成已发信/已回复：")
        for c in warn[:5]:
            print("   ", c["编号"], c["公司名"])

    if not args.commit:
        print("\n（预演模式，未写入。确认无误后加 --commit）")
        return
    if not changes:
        return

    bak = os.path.join(BASE, "logs", "_pool_before_sync_%s.csv" %
                       datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(os.path.dirname(bak), exist_ok=True)
    shutil.copy2(POOL, bak)
    print(f"\n已备份 → {bak}")

    with open(POOL, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(pool)
    print("✅ 已写回线索池")

    chk = os.path.join(BASE, "tools", "schema_check.py")
    if os.path.exists(chk):
        r = subprocess.run([sys.executable, chk, POOL], capture_output=True, text=True)
        print(r.stdout.strip() or r.stderr.strip())
        if r.returncode != 0:
            shutil.copy2(bak, POOL)
            print("❌ 校验未通过，已回滚到备份")


if __name__ == "__main__":
    main()
