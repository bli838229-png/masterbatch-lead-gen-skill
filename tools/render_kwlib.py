# -*- coding: utf-8 -*-
"""
关键词库可视化（把 map_keywords.json 渲染成可搜索的 HTML 索引）

用法：
    python tools/render_kwlib.py                 # -> reports/maps-keyword-library.html
    python tools/render_kwlib.py --open          # 生成后打印路径
"""
import argparse
import datetime
import html
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KW = os.path.join(BASE, "tools", "data", "map_keywords.json")


def esc(s):
    return html.escape(str(s or ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(BASE, "reports", "maps-keyword-library.html"))
    args = ap.parse_args()

    d = json.load(open(KW, encoding="utf-8"))
    markets, langs, inds = d["markets"], d["languages"], d["industries"]

    # 市场行
    rows = []
    for mk, m in markets.items():
        lg_codes = m["lang"]
        lg_label = " / ".join(langs.get(c, {}).get("label", c) for c in lg_codes)
        # 取 A 级行业的前 3 条示例查询
        a_inds = [k for k, v in inds.items() if v["tier"] == "A"]
        samples = []
        for ind in a_inds[:3]:
            term = None
            for c in lg_codes:
                term = langs.get(c, {}).get("terms", {}).get(ind)
                if term:
                    break
            if term:
                samples.append(f"{term} {m['cities'][0]}")
        cmd = f'python tools/kwgen.py --country {mk} --tier all --cities 3 --cmd'
        rows.append({
            "mk": mk, "country": m["country"], "lang": lg_label,
            "cities": len(m["cities"]), "city1": m["cities"][0],
            "samples": samples, "cmd": cmd,
            "a_cnt": len(a_inds),
        })

    # 语种覆盖矩阵：每个语种能出几个行业词
    lang_rows = []
    for code, l in langs.items():
        have = len([k for k in inds if k in l.get("terms", {})])
        lang_rows.append((l.get("label", code), code, have, len(inds)))
    lang_rows.sort(key=lambda x: -x[2])

    ind_rows = sorted(inds.items(), key=lambda kv: (kv[1]["tier"] != "A", kv[0]))

    tr_market = "\n".join(f"""<tr>
      <td class="mk">{esc(r['mk'])}</td>
      <td>{esc(r['country'])}</td>
      <td class="dim">{esc(r['lang'])}</td>
      <td class="num">{r['cities']}</td>
      <td class="dim">{esc(' · '.join(r['samples'][:2]))}</td>
      <td><button class="copy" data-c="{esc(r['cmd'])}">复制命令</button></td>
    </tr>""" for r in rows)

    tr_ind = "\n".join(f"""<tr>
      <td class="mk">{esc(v['label'])}</td>
      <td><span class="tag {'a' if v['tier']=='A' else 'b'}">{v['tier']}</span></td>
      <td class="num">{v['color_need']}</td>
      <td class="num">{v['fr_need']}</td>
      <td class="dim">{esc(v['note'])}</td>
    </tr>""" for k, v in ind_rows)

    tr_lang = "\n".join(f"""<tr>
      <td class="mk">{esc(a)}</td><td class="dim">{esc(b)}</td>
      <td class="num">{c}/{ttype}</td>
      <td><div class="bar"><i style="width:{int(c/ttype*100)}%"></i></div></td>
    </tr>""" for a, b, c, ttype in lang_rows)

    total_cities = sum(r["cities"] for r in rows)

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Google Maps 获客关键词库</title>
<style>
:root{{--bg:#f6f7f9;--card:#fff;--ink:#1b1f24;--dim:#6b7280;--line:#e5e7eb;--acc:#0f766e;--a:#b42318;--b:#1d4ed8}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.65 -apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 20px 60px}}
h1{{font-size:26px;margin:0 0 6px}}
.sub{{color:var(--dim);font-size:13px;margin-bottom:22px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:26px}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.stat b{{display:block;font-size:24px;line-height:1.2}}
.stat span{{color:var(--dim);font-size:12px}}
h2{{font-size:16px;margin:30px 0 10px;padding-left:9px;border-left:3px solid var(--acc)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}}
table{{width:100%;border-collapse:collapse}}
th,td{{text-align:left;padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{background:#fafbfc;font-size:12px;color:var(--dim);font-weight:600;white-space:nowrap}}
tr:last-child td{{border-bottom:none}}
.mk{{font-weight:600;white-space:nowrap}}
.dim{{color:var(--dim);font-size:12.5px}}
.num{{text-align:center;font-variant-numeric:tabular-nums;width:60px}}
.tag{{font-size:11px;padding:1px 7px;border-radius:99px;color:#fff;font-weight:600}}
.tag.a{{background:var(--a)}} .tag.b{{background:var(--b)}}
.bar{{background:#eef1f4;border-radius:99px;height:7px;width:110px;overflow:hidden}}
.bar i{{display:block;height:100%;background:var(--acc)}}
.copy{{font:12px inherit;padding:3px 9px;border:1px solid var(--line);background:#fff;border-radius:6px;cursor:pointer;color:var(--dim);white-space:nowrap}}
.copy:hover{{border-color:var(--acc);color:var(--acc)}}
.search{{width:100%;padding:10px 13px;border:1px solid var(--line);border-radius:8px;font:14px inherit;margin-bottom:10px;background:#fff}}
.note{{font-size:12.5px;color:var(--dim);margin:8px 0 0}}
.foot{{margin-top:34px;font-size:12px;color:var(--dim);border-top:1px solid var(--line);padding-top:14px}}
</style></head><body><div class="wrap">
<h1>Google Maps 获客关键词库</h1>
<div class="sub">按国家自动生成本地语言关键词 · 城市轮换 · 行业分层 · 生成于 {datetime.date.today().isoformat()}</div>
<div class="stats">
  <div class="stat"><b>{len(markets)}</b><span>市场</span></div>
  <div class="stat"><b>{len(langs)}</b><span>语种</span></div>
  <div class="stat"><b>{len(inds)}</b><span>行业</span></div>
  <div class="stat"><b>{total_cities}</b><span>可轮换城市</span></div>
</div>

<h2>市场 × 语言 × 城市</h2>
<input class="search" id="q" placeholder="搜索市场 / 国家 / 语言…（如 德国、Japan、韩语）">
<div class="card"><table id="tm">
<thead><tr><th>市场</th><th>国家</th><th>语言</th><th>城市</th><th>A 级示例查询</th><th>操作</th></tr></thead>
<tbody>{tr_market}</tbody></table></div>
<p class="note">命令已含城市轮换：同一市场反复调用会自动换城（记账在 <code>logs/_kw_rotation.json</code>）。</p>

<h2>行业字典（决定「值不值得深挖」）</h2>
<div class="card"><table>
<thead><tr><th>行业</th><th>层级</th><th>配色需求</th><th>阻燃需求</th><th>判断依据</th></tr></thead>
<tbody>{tr_ind}</tbody></table></div>

<h2>语种覆盖度（每个语种能出几个行业词）</h2>
<div class="card"><table>
<thead><tr><th>语种</th><th>代码</th><th>覆盖</th><th>进度</th></tr></thead>
<tbody>{tr_lang}</tbody></table></div>

<div class="foot">
数据源 <code>tools/data/map_keywords.json</code> · 加市场只需改数据文件，无需改代码 · 生成器 <code>tools/render_kwlib.py</code><br>
流水线：kwgen 出词 → maps_scrape 抓取 → classify_leads 甄别 → import_leads 入库（见 <code>references/maps-keyword-system.md</code>）
</div>
</div>
<script>
document.getElementById('q').addEventListener('input', function(e){{
  var v = e.target.value.toLowerCase();
  document.querySelectorAll('#tm tbody tr').forEach(function(tr){{
    tr.style.display = tr.innerText.toLowerCase().indexOf(v) > -1 ? '' : 'none';
  }});
}});
document.querySelectorAll('.copy').forEach(function(b){{
  b.addEventListener('click', function(){{
    navigator.clipboard.writeText(b.dataset.c).then(function(){{
      var t = b.textContent; b.textContent = '已复制'; b.style.color = '#0f766e';
      setTimeout(function(){{ b.textContent = t; }} , 1200);
    }});
  }});
}});
</script></body></html>"""

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    open(args.out, "w", encoding="utf-8").write(doc)
    print(f"已生成: {args.out}  ({len(doc)//1024} KB)")


if __name__ == "__main__":
    main()
