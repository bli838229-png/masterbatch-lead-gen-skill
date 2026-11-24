#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pick_market.py — 决定今天打哪个市场（唯一裁判，别凭记忆挑）

规则（全部可计算）：
  · 周一~周四 → main 轨道：status=active 中 priority 最小者
  · 周五      → wa   轨道：WhatsApp 专项日，印尼/印度/土耳其轮换（last_run 最久远的先跑）
  · 存量积压：某 main 市场 累计 ≥60 家 且 未联系 A 级 ≥10 家 → 判 stocked，自动跳到下一个
  · status=pending / stocked 一律不参与

用法：
  python tools/pick_market.py                  # 只看今天选谁（不动文件）
  python tools/pick_market.py --date 2026-11-20 # 指定日期（预演周五）
  python tools/pick_market.py --apply          # 把判定的 stocked 落盘（其它不改）

输出最后一行固定为 `MARKET=<市场>`，方便自动化直接取。
"""
from __future__ import annotations

import argparse
import csv
import datetime
import os
import sys

BASE = os.environ.get("MB_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # MB_HOME 可指定工作目录，默认脚本上一级
PLAN = os.path.join(BASE, "market-plan.csv")
POOL = os.path.join(BASE, "master-lead-pool.csv")

STOCK_LEADS = 60   # 存量家数阈值
STOCK_A_LEFT = 10  # 未联系 A 级阈值
WEEK_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save(path, rows, fields):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def match_leads(pool, market: str) -> list[dict]:
    """市场名与池内 国家 字段做包含匹配（越南 vs 越南-中北部 这类子市场也算）"""
    out = []
    for r in pool:
        c = (r.get("国家") or "").strip()
        if not c:
            continue
        if c == market or c in market or market in c:
            out.append(r)
    return out


def stock_stat(leads: list[dict]) -> dict:
    a = [x for x in leads if x.get("等级") == "A"]
    b = [x for x in leads if x.get("等级") == "B"]
    a_todo = [x for x in a if (x.get("跟进状态") or "未联系") == "未联系"]
    b_todo = [x for x in b if (x.get("跟进状态") or "未联系") == "未联系"]
    return {"total": len(leads), "a": len(a), "a_todo": len(a_todo), "b": len(b), "b_todo": len(b_todo)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default="", help="YYYY-MM-DD，默认今天")
    ap.add_argument("--apply", action="store_true", help="把判定的 stocked 写回 market-plan.csv")
    args = ap.parse_args()

    d = datetime.date.fromisoformat(args.date) if args.date else datetime.date.today()
    weekday = d.weekday()            # 0=周一
    is_wa_day = weekday == 4         # 周五
    track = "wa" if is_wa_day else "main"

    plan = load(PLAN)
    fields = list(plan[0].keys())
    pool = load(POOL)

    print(f"=== {d} {WEEK_CN[weekday]} → 轨道 {track}"
          f"{'（WhatsApp 专项日）' if is_wa_day else '（主线获客）'} ===")

    # 候选
    if track == "main":
        cands = [r for r in plan if r.get("track", "main") == "main" and r["status"] == "active"]
        cands.sort(key=lambda r: int(r["priority"]))
    else:
        cands = [r for r in plan if r.get("track") == "wa" and r["status"] == "active"]
        # 没跑过的(last_run 空)优先，其次最久没跑的，再按 priority
        cands.sort(key=lambda r: (r.get("last_run") or "", int(r["priority"])))

    if not cands:
        print("❌ 该轨道没有 active 市场，请检查 market-plan.csv")
        sys.exit(1)

    chosen = None
    skipped = []
    for r in cands:
        st = stock_stat(match_leads(pool, r["market"].strip()))
        line = (f"  {r['market']:8} pri={r['priority']:>2} last_run={r.get('last_run') or '从未':10} "
                f"存量{st['total']:>3} 家 / A级{st['a']:>2}(未联系{st['a_todo']:>2}) / 未联系B {st['b_todo']:>2}")
        # 存量积压只对主线生效：wa 轨道的目标就是攒聊天号，不该因为"存量够了"被跳过
        if track == "main" and st["total"] >= STOCK_LEADS and st["a_todo"] >= STOCK_A_LEFT:
            print(line + "  ⛔ 存量已够开发 → stocked，跳过")
            skipped.append(r)
            continue
        print(line + "  ✅ 选中")
        chosen = r
        break

    if skipped and args.apply:
        for r in skipped:
            r["status"] = "stocked"
        save(PLAN, plan, fields)
        print(f"\n已把 {len(skipped)} 个市场标为 stocked（{'、'.join(x['market'] for x in skipped)}）")

    if not chosen:
        print("❌ 所有候选都已存量饱和，需要人工加新市场")
        sys.exit(1)

    st = stock_stat(match_leads(pool, chosen["market"].strip()))
    print()
    print(f"市场      : {chosen['market']}")
    print(f"语言      : {chosen['language']}")
    print(f"优先级    : {chosen['priority']}  轨道: {chosen.get('track')}")
    print(f"存量      : {st['total']} 家（A {st['a']} / 未联系A {st['a_todo']} / 未联系B {st['b_todo']}）")
    if is_wa_day:
        print("今日重点  : 抓聊天号 —— 深挖后必须跑 find_whatsapp.py --crawl，日报额外给 WhatsApp 覆盖数")
        print("轮换顺序  : 印尼 → 印度 → 土耳其（按 last_run 最久远自动轮）")
    if not st["total"]:
        print("提示      : 该市场是全新市场，本轮从 0 开始抓 30 家")
    print()
    print(f"MARKET={chosen['market']}")


if __name__ == "__main__":
    main()
