#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""render_wa_worklist.py — 把 WhatsApp 候选表渲染成「点开即验」的工作清单"""
import csv
import datetime
import html
import os

BASE = os.environ.get("MB_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # MB_HOME 可指定工作目录，默认脚本上一级
SRC = os.path.join(BASE, "leads", "_whatsapp_candidates.csv")
OUT = os.path.join(BASE, "reports", "whatsapp-candidates.html")


def main():
    if not os.path.exists(SRC):
        print("没有候选表，先跑 tools/find_whatsapp.py")
        return
    with open(SRC, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    hi = [r for r in rows if r["置信度"] == "高"]
    mid = [r for r in rows if r["置信度"] == "中"]
    today = datetime.date.today().strftime("%Y-%m-%d")

    def card(r, cls):
        name = html.escape(r["公司名"] or "")
        num = html.escape(r["号码"] or "")
        link = html.escape(r["wa链接"] or "")
        src = html.escape(r.get("匹配来源") or "")
        ev = html.escape(r.get("证据") or "")
        note = html.escape(r.get("备注") or "")
        site = html.escape(r.get("官网") or "")
        return f'''<div class="row {cls}">
  <div class="main">
    <div class="nm">{name} <span class="tag">{html.escape(r["国家"])} · {html.escape(r["等级"])}</span></div>
    <div class="meta"><span class="num">{num}</span><span class="src">{src}</span></div>
    <div class="ev">{ev}{(" · " + note) if note else ""}</div>
  </div>
  <div class="acts">
    <a class="btn primary" href="{link}" target="_blank" rel="noopener">打开 WhatsApp 验号</a>
    <button class="btn" data-copy="{num}">复制号码</button>
    {f'<a class="btn ghost" href="{site}" target="_blank" rel="noopener">官网</a>' if site else ''}
  </div>
</div>'''

    body_hi = "".join(card(r, "hi") for r in hi) or '<div class="empty">暂无高置信号码</div>'
    body_mid = "".join(card(r, "mid") for r in mid) or '<div class="empty">暂无待验号码</div>'

    doc = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WhatsApp 挖号清单 · {today}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f4f6f8;color:#1c2632;
  font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}}
header{{background:#0f2a3f;color:#fff;padding:22px 28px}}
h1{{margin:0 0 6px;font-size:19px;font-weight:650;letter-spacing:.3px}}
.sub{{font-size:12.5px;color:#a9c0d0;line-height:1.7}}
.sub b{{color:#5fe0a8}}
.wrap{{max-width:900px;margin:0 auto;padding:20px 16px 60px}}
h2{{font-size:13px;color:#5b6b7a;margin:26px 0 10px;letter-spacing:.6px;font-weight:650}}
h2 span{{color:#98a6b3;font-weight:400;margin-left:6px}}
.row{{background:#fff;border:1px solid #e3e8ee;border-radius:10px;padding:13px 15px;margin-bottom:9px;
  display:flex;gap:14px;align-items:center;justify-content:space-between}}
.row.hi{{border-left:4px solid #16a34a}}
.row.mid{{border-left:4px solid #e0a800}}
.main{{min-width:0;flex:1}}
.nm{{font-size:14.5px;font-weight:620;margin-bottom:5px}}
.tag{{font-size:11px;font-weight:500;color:#6b7a88;background:#eef2f6;padding:2px 7px;border-radius:5px;margin-left:6px}}
.meta{{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap;margin-bottom:4px}}
.num{{font-family:ui-monospace,Consolas,monospace;font-size:15px;font-weight:650;color:#0f2a3f;letter-spacing:.5px}}
.src{{font-size:11.5px;color:#7c8b99}}
.ev{{font-size:11.5px;color:#93a1ae;line-height:1.55;word-break:break-all}}
.acts{{display:flex;gap:7px;flex-shrink:0;flex-wrap:wrap;justify-content:flex-end}}
.btn{{font:inherit;font-size:12.5px;padding:7px 11px;border-radius:7px;border:1px solid #d3dbe3;
  background:#fff;color:#2b3a48;cursor:pointer;text-decoration:none;white-space:nowrap}}
.btn:hover{{background:#f6f8fa}}
.btn.primary{{background:#128c4a;border-color:#128c4a;color:#fff;font-weight:600}}
.btn.primary:hover{{background:#0f7a40}}
.btn.ghost{{color:#7c8b99}}
.empty{{color:#98a6b3;font-size:13px;padding:14px;background:#fff;border-radius:9px;border:1px dashed #dde3ea}}
.tip{{background:#fff8e6;border:1px solid #f0dfae;color:#6a5417;border-radius:9px;
  padding:12px 15px;font-size:12.5px;line-height:1.8;margin-top:14px}}
.tip b{{color:#4a3a0c}}
@media(max-width:640px){{.row{{flex-direction:column;align-items:stretch}}.acts{{justify-content:flex-start}}}}
</style></head><body>
<header>
  <h1>WhatsApp 挖号清单</h1>
  <div class="sub">生成于 {today} · 高置信 <b>{len(hi)}</b> 家（官网自挂，可直接发）· 待验 <b>{len(mid)}</b> 家（点开链接 3 秒确认）<br>
  验号方法：点「打开 WhatsApp 验号」→ 出现头像/公司名＝有效；提示 invalid＝号码不存在，别写库。</div>
</header>
<div class="wrap">
  <h2>可直接发<span>官网自己挂了 WhatsApp 按钮，等于官方公开</span></h2>
  {body_hi}
  <h2>待验<span>手机号段命中，但不确定是否开通 WhatsApp</span></h2>
  {body_mid}
  <div class="tip">
    <b>三条纪律</b><br>
    1. 只发已验证的号码；invalid 的一律不写库、不发。<br>
    2. 一次只发一条，2-3 天后再追；同一号码 3 条无回应即停（防举报封号）。<br>
    3. 号码归属与公司对不上（头像/名称不符）就不要发——发错人比不发更伤。
  </div>
</div>
<script>
document.addEventListener("click", async (e)=>{{
  const b = e.target.closest("[data-copy]");
  if (!b) return;
  const v = b.dataset.copy, old = b.textContent;
  try {{ await navigator.clipboard.writeText(v); }} catch(_) {{
    const t = document.createElement("textarea"); t.value = v; document.body.appendChild(t);
    t.select(); document.execCommand("copy"); t.remove();
  }}
  b.textContent = "已复制"; setTimeout(()=>b.textContent = old, 1100);
}});
</script>
</body></html>'''
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"已生成 {OUT}（高置信 {len(hi)} / 待验 {len(mid)}）")


if __name__ == "__main__":
    main()
