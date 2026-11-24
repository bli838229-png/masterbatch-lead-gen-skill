# -*- coding: utf-8 -*-
"""
Google Maps 获客关键词引擎（按国家自动出本地语言关键词 + 城市轮换 + 直接给可跑命令）

用法：
    # 看支持哪些市场
    python tools/kwgen.py --list

    # 美国 · A 级行业（汽车/电缆/家电/医疗），自动挑 4 个没跑过的城市
    python tools/kwgen.py --country 美国 --tier A --cities 4

    # 指定城市 + 指定行业
    python tools/kwgen.py --country 德国 --city "Stuttgart" --industry inj,auto

    # 直接输出可执行命令（复制即跑）
    python tools/kwgen.py --country 美国 --tier all --cities 3 --cmd

    # 给流水线用的 JSON
    python tools/kwgen.py --country 日本 --tier A --cities 2 --json

设计要点：
  1) 关键词来自 tools/data/map_keywords.json —— 加市场只改数据，不改代码；
  2) 城市轮换记账在 logs/_kw_rotation.json —— 同一市场连续跑不会反复搜同一批厂；
  3) 输出 region + queries，正好是 maps_scrape.py 的两个入参，无需手工拼。
"""
import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "tools", "data", "map_keywords.json")
ROTATION = os.path.join(BASE, "logs", "_kw_rotation.json")


def load_data():
    with open(DATA, encoding="utf-8") as f:
        return json.load(f)


def load_rotation():
    if os.path.exists(ROTATION):
        try:
            with open(ROTATION, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_rotation(rot):
    os.makedirs(os.path.dirname(ROTATION), exist_ok=True)
    with open(ROTATION, "w", encoding="utf-8") as f:
        json.dump(rot, f, ensure_ascii=False, indent=2)


def resolve_market(data, name):
    markets = data["markets"]
    if name in markets:
        return name
    low = name.strip().lower()
    for k, v in markets.items():
        if k.lower() == low or v["country"].lower() == low:
            return k
    # 模糊包含
    hits = [k for k in markets if low in k.lower() or low in markets[k]["country"].lower()]
    if len(hits) == 1:
        return hits[0]
    return None


def pick_industries(data, spec, tier):
    inds = data["industries"]
    if spec:
        keys = [s.strip() for s in spec.split(",") if s.strip()]
        bad = [k for k in keys if k not in inds]
        if bad:
            sys.exit(f"未知行业: {bad}. 可选: {list(inds)}")
        return keys
    if tier == "A":
        return [k for k, v in inds.items() if v["tier"] == "A"]
    if tier == "B":
        return [k for k, v in inds.items() if v["tier"] == "B"]
    # all：A 级优先，B 级补量（保持顺序）
    a = [k for k, v in inds.items() if v["tier"] == "A"]
    b = [k for k, v in inds.items() if v["tier"] == "B"]
    return a + b


def pick_cities(market_key, market, city_arg, n_cities, rot, no_rotation):
    cities = market["cities"]
    if city_arg:
        return [city_arg], []
    if no_rotation:
        return cities[:n_cities], []
    used = set(rot.get(market_key, {}).get("used_cities", []))
    fresh = [c for c in cities if c not in used]
    reused = []
    if len(fresh) < n_cities:
        # 城市用完了 -> 全部重置，从头再轮一遍（并提示）
        reused = [c for c in cities if c in used]
        fresh = cities[:]
        rot.setdefault(market_key, {})["reset_at"] = "auto"
    picked = fresh[:n_cities]
    return picked, reused


def build_queries(data, market, industries, cities, max_queries=6):
    """城市 × 行业词 -> 查询串（均衡分配，保证每个城市都有份）。
    例：2 城 + 4 行业 + 上限 6 → 每城 3 条，第 2 城换用后两个行业，避免只覆盖首城。"""
    langs = market["lang"]
    if not cities:
        return []
    per_city = max(1, max_queries // len(cities))
    out, seen = [], set()
    for city in cities:
        picked = 0
        for ind in industries:
            if picked >= per_city:
                break
            term = None
            for lg in langs:
                t = data["languages"].get(lg, {}).get("terms", {}).get(ind)
                if t:
                    term = t
                    break
            if not term:
                continue
            q = f"{term} {city}"
            if q.lower() in seen:
                continue
            seen.add(q.lower())
            out.append(q)
            picked += 1
    return out[:max_queries]


def cities_in_queries(queries, cities):
    """只把真正出现在查询里的城市记为已用，避免空耗轮换名额。"""
    hit = []
    for c in cities:
        if any(c in q for q in queries):
            hit.append(c)
    return hit or cities[:1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--country", help="市场名，如 美国 / Germany")
    ap.add_argument("--city", help="指定单个城市（覆盖轮换）")
    ap.add_argument("--cities", type=int, default=3, help="本轮挑几个城市（默认 3）")
    ap.add_argument("--industry", help="行业，逗号分隔：inj,auto,cable…")
    ap.add_argument("--tier", default="A", choices=["A", "B", "all"], help="按层级选行业（默认 A）")
    ap.add_argument("--max-queries", type=int, default=6, help="输出查询条数上限（maps_scrape 建议 4-6）")
    ap.add_argument("--cmd", action="store_true", help="只打印可直接执行的 maps_scrape 命令")
    ap.add_argument("--json", action="store_true", help="输出 JSON（供流水线消费）")
    ap.add_argument("--no-rotation", action="store_true", help="不读/不写城市轮换记录")
    ap.add_argument("--list", action="store_true", help="列出所有支持的市场")
    args = ap.parse_args()

    data = load_data()

    if args.list:
        print(f"{'市场':<12}{'国家':<20}{'语言':<12}{'城市数':<6}")
        print("-" * 56)
        for k, v in data["markets"].items():
            langs = "/".join(data["languages"].get(l, {}).get("label", l) for l in v["lang"])
            print(f"{k:<12}{v['country']:<20}{langs:<12}{len(v['cities']):<6}")
        print(f"\n共 {len(data['markets'])} 个市场 / {len(data['languages'])} 个语种 / {len(data['industries'])} 个行业")
        return

    if not args.country:
        ap.error("需要 --country（或用 --list 查看支持的市场）")

    mkey = resolve_market(data, args.country)
    if not mkey:
        sys.exit(f"未收录市场: {args.country}（先加到 map_keywords.json 的 markets）")
    market = data["markets"][mkey]

    industries = pick_industries(data, args.industry, args.tier)
    rot = load_rotation()

    # 行业轮转：同一市场多轮跑时，把没排上的行业挪到前面（否则 medical 永远排不到）
    if not args.industry and not args.no_rotation:
        off = len(rot.get(mkey, {}).get("used_cities", []))
        if off and industries:
            k = off % len(industries)
            industries = industries[k:] + industries[:k]

    cities, reset_hint = pick_cities(mkey, market, args.city, args.cities, rot, args.no_rotation)

    queries = build_queries(data, market, industries, cities, args.max_queries)
    used_cities = cities_in_queries(queries, cities)

    if args.json:
        print(json.dumps({
            "market": mkey,
            "country": market["country"],
            "lang": market["lang"],
            "cities": cities,
            "industries": industries,
            "region": market["country"],
            "queries": queries,
        }, ensure_ascii=False, indent=2))
        # JSON 模式也记账，但仅在确认要跑时才记；这里按调用即记账（流水线会调）
        if not args.no_rotation:
            node = rot.setdefault(mkey, {"used_cities": []})
            node["used_cities"] = sorted(set(node.get("used_cities", []) + used_cities))
            node["last_run"] = __import__("datetime").date.today().isoformat()
            save_rotation(rot)
        return

    if args.cmd:
        print(f'python tools/maps_scrape.py "{market["country"]}" "{",".join(queries)}"')
        # --cmd 也记账：SOP 是「复制即跑」，不记账会导致天天搜同一批城市
        if not args.no_rotation:
            node = rot.setdefault(mkey, {"used_cities": []})
            node["used_cities"] = sorted(set(node.get("used_cities", []) + used_cities))
            node["last_run"] = __import__("datetime").date.today().isoformat()
            save_rotation(rot)
        return

    langs = "/".join(data["languages"].get(l, {}).get("label", l) for l in market["lang"])
    print(f"市场: {mkey}（{market['country']}） | 语言: {langs} | 行业: {', '.join(industries)}")
    print(f"城市: {', '.join(cities)}" + ("（⚠️ 城市已轮完一轮，本次重置）" if reset_hint else ""))
    print(f"查询 {len(queries)} 条：")
    for q in queries:
        print("  -", q)
    print("\n直接执行：")
    print(f'python tools/maps_scrape.py "{market["country"]}" "{",".join(queries)}"')

    if not args.no_rotation:
        node = rot.setdefault(mkey, {"used_cities": []})
        node["used_cities"] = sorted(set(node.get("used_cities", []) + used_cities))
        node["last_run"] = __import__("datetime").date.today().isoformat()
        save_rotation(rot)
        print(f"\n已记账：{mkey} 已用城市 {len(node['used_cities'])}/{len(market['cities'])}（下次自动换城）")


if __name__ == "__main__":
    main()
