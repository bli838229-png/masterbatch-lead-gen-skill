# -*- coding: utf-8 -*-
"""
线索数据入库校验器（防字段错位 / 防评分不自洽 / 防重复入池）

用法：
    python tools/schema_check.py                          # 校验总池
    python tools/schema_check.py leads/2026-11-16-US-leads.csv   # 校验当日CSV（含7维）

退出码 0=通过，1=有错误（自动化流程应中止入库并修复）
"""
import csv
import sys
import os
import re
from collections import Counter

BASE_COLS = [
    "排名", "国家", "公司名", "行业", "城市", "总分", "等级", "官网", "邮箱", "电话",
    "联系人", "职位", "WhatsApp", "Zalo", "LINE", "KakaoTalk", "官网产品",
    "跟进状态", "最后联系日", "切入建议", "来源",
]
DIM_COLS = ["产品匹配度", "需求强度", "规模匹配度", "决策人可触达性",
            "联系渠道质量", "地域适配", "采购周期/频率"]
STATUS_SET = {"未联系", "已发信", "已回复", "已报价", "已寄样", "成交", "无效"}
GRADE_SET = {"A", "B", "C"}

# 「官网」列禁止出现的域名：目录站 / 数据商 / 社交平台（填了这些等于没有官网）
BAD_DOMAINS = [
    "thomasnet.com", "contactout.com", "growjo.com", "rocketreach.co", "zoominfo.com",
    "dnb.com", "manta.com", "yellowpages", "kompass", "europages", "alibaba.com",
    "indiamart.com", "made-in-china.com", "globalsources.com", "amazon.com",
    "linkedin.com", "facebook.com", "crunchbase.com", "bloomberg.com", "owler.com",
]


def norm(s):
    return (s or "").strip().lower()


def domain_of(url):
    d = re.sub(r"^https?://", "", (url or "").strip().lower())
    return d.split("/")[0].replace("www.", "")


def check(path):
    errs, warns = [], []
    if not os.path.exists(path):
        return [f"文件不存在: {path}"], []

    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return [f"空文件: {path}"], []

    header, data = rows[0], [r for r in rows[1:] if any((c or "").strip() for c in r)]

    has_dims = all(c in header for c in DIM_COLS)
    expected = BASE_COLS + DIM_COLS if has_dims else BASE_COLS

    # 1) 表头必须与规范完全一致（顺序也一致）
    if header != expected:
        missing = [c for c in expected if c not in header]
        extra = [c for c in header if c not in expected]
        errs.append(f"表头不符规范。缺列={missing} 多列={extra}")
        if [c for c in header if c in expected] and header[:len(expected)] != [c for c in expected if c in header]:
            errs.append("列顺序与规范不一致（会导致字段错位）")
        return errs, warns  # 表头不对就不再往下逐行校验，避免误报

    # 2) 每行列数一致
    bad_len = [(i + 2, len(r)) for i, r in enumerate(data) if len(r) != len(expected)]
    if bad_len:
        errs.append(f"列数不一致的行 {len(bad_len)} 行（疑未转义逗号）: {bad_len[:5]}")

    # 3) 逐行字段校验
    for i, r in enumerate(data, start=2):
        if len(r) != len(expected):
            continue
        d = dict(zip(expected, r))

        grade = (d.get("等级") or "").strip()
        if grade not in GRADE_SET:
            errs.append(f"第{i}行 等级非法={grade!r} ({d.get('公司名')})")

        total = (d.get("总分") or "").strip()
        if not total.isdigit():
            errs.append(f"第{i}行 总分非数字={total!r} ({d.get('公司名')})")
        elif has_dims:
            dims = []
            ok = True
            for c in DIM_COLS:
                v = (d.get(c) or "").strip()
                if not v.isdigit():
                    errs.append(f"第{i}行 {c} 非数字={v!r} ({d.get('公司名')})")
                    ok = False
                else:
                    dims.append(int(v))
            if ok and sum(dims) != int(total):
                errs.append(f"第{i}行 7维之和={sum(dims)} ≠ 总分={total} ({d.get('公司名')})")
            if ok and any(x < 0 or x > 5 for x in dims):
                errs.append(f"第{i}行 存在维度分超出 0-5 ({d.get('公司名')})")

        st = (d.get("跟进状态") or "").strip()
        if st not in STATUS_SET:
            errs.append(f"第{i}行 跟进状态非法={st!r}（应为 {sorted(STATUS_SET)}）")

        # 官网必须是公司自有域名，不能是目录站/数据商/社交平台
        dm = domain_of(d.get("官网", ""))
        if dm and any(b in dm for b in BAD_DOMAINS):
            errs.append(f"第{i}行 官网是目录站/数据商而非客户官网: {dm} ({d.get('公司名')})")

    # 4) 重复检测（公司名 / 官网域名）
    names = Counter(norm(d.get("公司名", "")) for d in (dict(zip(expected, r)) for r in data if len(r) == len(expected)))
    dup_n = [k for k, v in names.items() if v > 1 and k]
    if dup_n:
        errs.append(f"公司名重复 {len(dup_n)} 组: {dup_n[:5]}")

    doms = Counter(domain_of(d.get("官网", "")) for d in (dict(zip(expected, r)) for r in data if len(r) == len(expected)))
    dup_d = [k for k, v in doms.items() if v > 1 and k]
    if dup_d:
        warns.append(f"官网域名重复 {len(dup_d)} 组（需确认是否分公司）: {dup_d[:5]}")

    # 5) 质量提示（非阻断）
    blank_prod = sum(1 for d in (dict(zip(expected, r)) for r in data if len(r) == len(expected))
                     if not (d.get("官网产品") or "").strip())
    if blank_prod:
        warns.append(f"官网产品为空 {blank_prod} 行（A/B 级应补齐，用于开发信锚点）")

    return errs, warns


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "master-lead-pool.csv"
    errs, warns = check(path)
    print(f"=== 校验 {path} ===")
    if warns:
        print("\n[警告] 不阻断，但影响质量：")
        for w in warns:
            print("  ⚠️ ", w)
    if errs:
        print(f"\n[错误] {len(errs)} 项，必须修复后才能入库：")
        for e in errs[:30]:
            print("  ❌", e)
        if len(errs) > 30:
            print(f"  ... 另有 {len(errs)-30} 项")
        sys.exit(1)
    print("\n✅ 校验通过")


if __name__ == "__main__":
    main()
