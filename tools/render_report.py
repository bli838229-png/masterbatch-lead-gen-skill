# -*- coding: utf-8 -*-
"""
可复用 HTML 日报生成器（每天用同一个，不再手写一次性脚本）

用法：
    python tools/render_report.py <输入json> [输出html] [市场名] [日期]

示例：
    python tools/render_report.py logs/_leads_20261116.json reports/2026-11-16-daily-report.html 美国 2026-11-16

输入 JSON：数组，每家一个对象。必填 name/industry/city/total/grade/dims/reasons；
可选 website/email/phone/contact/job/whatsapp/zalo/line/kakaotalk/products/status/
     pitch/source/email_subject/email_body/email_body_cn/wa_opener/wa_opener_cn/wa_opener_local
缺字段会优雅降级（显示"—"），不会报错。
"""
import json
import sys
import html
import os
import datetime

DIM_NAMES = ["产品匹配度", "需求强度", "规模匹配度", "决策人可触达性",
             "联系渠道质量", "地域适配", "采购周期/频率"]


def esc(s):
    return html.escape(str(s if s is not None else ""), quote=True)


def g(v, default="—"):
    """取值并降级"""
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


def grade_badge(grade):
    color = {"A": "#d94a3d", "B": "#e08e2b", "C": "#8e9aa6"}.get(grade, "#8e9aa6")
    return (f'<span style="background:{color};color:#fff;padding:2px 10px;'
            f'border-radius:11px;font-weight:700;font-size:12px;">{esc(grade)}</span>')


def status_badge(st):
    colors = {"未联系": "#8e9aa6", "已发信": "#1a73c9", "已回复": "#2f9e5e",
              "已报价": "#c9861a", "已寄样": "#7d4fc4", "成交": "#1f8a4c", "无效": "#b0b6bd"}
    c = "#8e9aa6"
    for k, v in colors.items():
        if st.startswith(k):
            c = v
            break
    return (f'<span style="background:{c};color:#fff;padding:1px 8px;border-radius:9px;'
            f'font-size:11px;font-weight:600;">{esc(st)}</span>')


def dim_bar(score):
    try:
        sc = float(score)
    except Exception:
        sc = 0
    pct = max(0, min(100, sc / 5 * 100))
    color = "#2f9e5e" if sc >= 4 else ("#e08e2b" if sc >= 2 else "#c8ced4")
    return (f'<div style="background:#eceff2;border-radius:4px;height:7px;">'
            f'<div style="background:{color};height:7px;border-radius:4px;width:{pct}%;"></div></div>')


def copy_block(idx, label, text, color="#1a5c9e"):
    if not text or not str(text).strip():
        return ""
    return f'''
    <div style="margin-top:8px;">
      <div style="font-size:11px;font-weight:700;color:{color};margin-bottom:3px;">{esc(label)}</div>
      <div style="background:#fff;border:1px solid #e3e8ee;border-radius:5px;padding:8px;
                  font-size:12px;line-height:1.55;color:#2c3e50;white-space:pre-wrap;"
           id="t{idx}_{esc(label)}">{esc(text)}</div>
      <button onclick="cp('t{idx}_{esc(label)}',this)"
              style="margin-top:4px;background:{color};color:#fff;border:none;padding:4px 10px;
                     border-radius:5px;cursor:pointer;font-size:11px;">📋 复制</button>
    </div>'''


def build(data, market, date):
    total = len(data)
    cnt = {k: sum(1 for d in data if d.get("grade") == k) for k in ("A", "B", "C")}
    a_uncontact = sum(1 for d in data if d.get("grade") == "A"
                      and str(d.get("status", "未联系")).startswith("未联系"))
    with_prod = sum(1 for d in data if g(d.get("products"), "") != "")
    with_person = sum(1 for d in data if g(d.get("contact"), "") not in ("", "待核实")
                      and "待核实" not in str(d.get("contact")))
    ab = cnt["A"] + cnt["B"]

    cards = []
    for i, d in enumerate(data, 1):
        dims = d.get("dims") or [0] * 7
        reasons = d.get("reasons") or [""] * 7
        dims_html = ""
        for j, dim in enumerate(DIM_NAMES):
            sc = dims[j] if j < len(dims) else 0
            rs = reasons[j] if j < len(reasons) else ""
            dims_html += f'''
            <div style="margin:6px 0;">
              <div style="display:flex;justify-content:space-between;font-size:12px;color:#55606b;">
                <span>{j+1}. {dim}</span><span style="font-weight:700;">{esc(sc)}/5</span>
              </div>
              {dim_bar(sc)}
              <div style="font-size:11px;color:#8b959f;margin-top:2px;">{esc(rs)}</div>
            </div>'''

        # 社交渠道按市场拆行（该市场不用的显示"—"）
        ch_rows = ""
        for label, key in (("WhatsApp", "whatsapp"), ("Zalo", "zalo"),
                           ("LINE", "line"), ("KakaoTalk", "kakaotalk")):
            val = g(d.get(key), "")
            if val:
                ch_rows += f'<div>💬 {label}：{esc(val)}</div>'

        prod = g(d.get("products"), "")
        prod_html = (f'<div style="background:#fff8e6;border-left:3px solid #e08e2b;padding:6px 8px;'
                     f'border-radius:4px;margin:6px 0;font-size:12px;">'
                     f'<b>🏷️ 官网产品（开发信锚点）：</b>{esc(prod)}</div>')

        openers = (copy_block(i, "英语 · 发送版", d.get("wa_opener"), "#1a5c9e")
                   + copy_block(i, "中文 · 参照版", d.get("wa_opener_cn"), "#6b7280")
                   + copy_block(i, "当地语言 · 示例版", d.get("wa_opener_local"), "#2f9e5e"))

        cards.append(f'''
    <div class="card" data-grade="{esc(d.get('grade'))}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <span style="font-size:13px;color:#a7b0b9;font-weight:700;">#{i}</span>
          <span style="font-size:17px;font-weight:800;color:#1e2a35;">{esc(g(d.get('name')))}</span>
        </div>
        <div style="text-align:right;white-space:nowrap;">
          <span style="font-size:21px;font-weight:800;color:#1e2a35;">{esc(g(d.get('total'),'0'))}</span>
          <span style="color:#a7b0b9;font-size:12px;">/35</span> {grade_badge(d.get('grade'))}
        </div>
      </div>
      <div style="font-size:12.5px;color:#55606b;margin:6px 0;">
        <div>🏭 {esc(g(d.get('industry')))}</div>
        <div>📍 {esc(g(d.get('city')))}</div>
        <div>🌐 {('<a href="%s" target="_blank">%s</a>' % (esc(d.get('website')), esc(d.get('website')))) if g(d.get('website'), '') else '—'}</div>
      </div>
      {prod_html}
      <div style="background:#f7f9fb;border-radius:6px;padding:8px;font-size:12px;color:#33404d;margin:8px 0;">
        <div>👤 决策人：{esc(g(d.get('contact')))}</div>
        <div>🏷️ 职位：{esc(g(d.get('job')))}</div>
        <div>✉️ 邮箱：{esc(g(d.get('email')))}</div>
        <div>📞 电话：{esc(g(d.get('phone')))}</div>
        {ch_rows if ch_rows else '<div>💬 社交：—</div>'}
        <div style="margin-top:4px;">🔁 跟进状态：{status_badge(str(d.get('status') or '未联系'))}</div>
      </div>
      <div style="border-top:1px solid #eef1f4;padding-top:8px;">
        <div style="font-weight:700;font-size:12.5px;color:#1e2a35;margin-bottom:4px;">7 维评分明细</div>
        {dims_html}
      </div>
      <div style="background:#fdf6ec;border-radius:6px;padding:8px;margin:8px 0;font-size:12px;">
        <b>🎯 切入建议：</b>{esc(g(d.get('pitch')))}
      </div>
      <div style="background:#eef5fd;border-radius:6px;padding:10px;">
        <div style="font-weight:700;font-size:12.5px;color:#1a5c9e;">💬 开场白（英语必发 · 中文参照 · 当地语言示例）</div>
        {openers if openers else '<div style="font-size:12px;color:#8b959f;margin-top:6px;">—</div>'}
      </div>
      <div style="font-size:11px;color:#aab2ba;margin-top:6px;">来源：{esc(g(d.get('source')))}</div>
    </div>''')

    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>色母粒海外获客日报 · {esc(date)} {esc(market)}</title>
<style>
  *{{box-sizing:border-box;}}
  body{{font-family:-apple-system,"Segoe UI","Microsoft YaHei",sans-serif;margin:0;
        background:#f4f6f8;color:#1e2a35;line-height:1.5;}}
  .header{{background:linear-gradient(135deg,#22303d,#1a5c9e);color:#fff;padding:26px 22px;}}
  .header h1{{margin:0;font-size:22px;}}
  .header p{{margin:6px 0 0;font-size:12.5px;opacity:.85;}}
  .stats{{display:flex;flex-wrap:wrap;gap:10px;padding:18px 22px;}}
  .stat{{background:#fff;border-radius:9px;padding:12px 16px;min-width:104px;
         box-shadow:0 1px 3px rgba(0,0,0,.06);}}
  .stat .num{{font-size:21px;font-weight:800;}}
  .stat .label{{font-size:11.5px;color:#8b959f;margin-top:2px;}}
  .wrap{{padding:0 22px 40px;}}
  .card{{background:#fff;border-radius:10px;padding:14px 16px;margin-bottom:14px;
         box-shadow:0 1px 3px rgba(0,0,0,.06);border-left:4px solid #cfd6dd;}}
  .card[data-grade="A"]{{border-left-color:#d94a3d;}}
  .card[data-grade="B"]{{border-left-color:#e08e2b;}}
  .card[data-grade="C"]{{border-left-color:#8e9aa6;}}
  .bar{{position:sticky;top:0;background:#f4f6f8;padding:10px 22px;z-index:9;}}
  .bar button{{background:#fff;border:1px solid #d6dce2;border-radius:16px;padding:5px 14px;
               margin-right:6px;cursor:pointer;font-size:12.5px;}}
  .bar button.on{{background:#1a5c9e;color:#fff;border-color:#1a5c9e;}}
</style></head><body>
<div class="header">
  <h1>色母粒海外获客日报 · {esc(market)}</h1>
  <p>{esc(date)} · 定制色母粒 + 阻燃母粒 · 全量 A/B/C 排名（含 7 维评分与三语开场白）</p>
</div>
<div class="stats">
  <div class="stat"><div class="num">{total}</div><div class="label">客户总数</div></div>
  <div class="stat"><div class="num" style="color:#d94a3d;">{cnt['A']}</div><div class="label">A 级</div></div>
  <div class="stat"><div class="num" style="color:#e08e2b;">{cnt['B']}</div><div class="label">B 级</div></div>
  <div class="stat"><div class="num" style="color:#8e9aa6;">{cnt['C']}</div><div class="label">C 级</div></div>
  <div class="stat"><div class="num" style="color:#d94a3d;">{a_uncontact}</div><div class="label">未联系 A 级 ⚠️</div></div>
  <div class="stat"><div class="num">{with_prod}/{ab}</div><div class="label">官网产品已补</div></div>
  <div class="stat"><div class="num">{with_person}</div><div class="label">已挖实名决策人</div></div>
</div>
<div class="bar">
  <button class="on" onclick="flt(this,'')">全部</button>
  <button onclick="flt(this,'A')">只看 A</button>
  <button onclick="flt(this,'B')">只看 B</button>
  <button onclick="flt(this,'C')">只看 C</button>
</div>
<div class="wrap">{''.join(cards)}</div>
<script>
function cp(id, btn){{
  var t=document.getElementById(id).innerText;
  navigator.clipboard.writeText(t).then(function(){{
    var o=btn.innerText; btn.innerText='✅ 已复制'; setTimeout(function(){{btn.innerText=o;}},1200);
  }});
}}
function flt(btn, g){{
  document.querySelectorAll('.bar button').forEach(function(b){{b.classList.remove('on');}});
  btn.classList.add('on');
  document.querySelectorAll('.card').forEach(function(c){{
    c.style.display = (!g || c.dataset.grade===g) ? '' : 'none';
  }});
}}
</script></body></html>'''


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    infile = sys.argv[1]
    date = sys.argv[4] if len(sys.argv) > 4 else datetime.date.today().isoformat()
    outfile = sys.argv[2] if len(sys.argv) > 2 else f"reports/{date}-daily-report.html"
    market = sys.argv[3] if len(sys.argv) > 3 else ""

    with open(infile, encoding="utf-8") as f:
        data = json.load(f)
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(build(data, market, date))

    print(f"✅ 日报已生成: {outfile}")
    print(f"   {len(data)} 家 | A{sum(1 for d in data if d.get('grade')=='A')}"
          f" B{sum(1 for d in data if d.get('grade')=='B')}"
          f" C{sum(1 for d in data if d.get('grade')=='C')}")


if __name__ == "__main__":
    main()
