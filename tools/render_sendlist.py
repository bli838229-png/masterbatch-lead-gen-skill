# -*- coding: utf-8 -*-
"""生成「Gmail 发信队列」页：一封一点，点开就是填好的撰写窗口

为什么不做成全自动发送：
  1. skill 红线——对外发送必须人工确认（AI 只备料）
  2. 一次性群发 27 封冷邮件，Gmail 会判定异常行为，轻则进垃圾箱、重则限权
  3. 欧盟 GDPR / 加拿大 CASL 对未经同意的商业邮件有法律要求，需人工判断对象是否适用

产出：reports/gmail-sendlist.html（勾选进度存 localStorage，可导出 CSV 回写线索池）
用法：python tools/render_sendlist.py
"""
import csv
import json
import os
import re
import urllib.parse

BASE = os.environ.get("MB_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(BASE, "master-lead-pool.csv")
OUT = os.path.join(BASE, "reports", "gmail-sendlist.html")

import sys
sys.path.insert(0, os.path.join(BASE, "tools"))
from outreach_copy import pick  # noqa: E402


def ok_email(v):
    v = (v or "").strip()
    if not v or "@" not in v:
        return False
    if re.match(r"^(待核实|待验证|明确无|该市场不使用|⚠️)", v):
        return False
    if re.search(r"(example|xxx|your|abc)@", v, re.I):
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[a-z]{2,}$", v))


def gmail_url(email, subject, body):
    q = lambda s: urllib.parse.quote(s, safe="")  # noqa: E731
    return ("https://mail.google.com/mail/?view=cm&fs=1&to=" + q(email)
            + "&su=" + q(subject) + "&body=" + q(body))


def load():
    rows = [r for r in csv.DictReader(open(POOL, encoding="utf-8-sig"))
            if (r.get("等级") or "").strip() in ("A", "B")]
    out = []
    for r in rows:
        name = (r.get("公司名") or "").strip()
        if not name:
            continue
        try:
            rank = int(float(r.get("排名") or 0))
        except Exception:
            rank = 0
        c = pick(rank=rank, name=name, industry=(r.get("行业") or "").strip(),
                 city=(r.get("城市") or "").strip(), country=(r.get("国家") or "").strip(),
                 contact=(r.get("联系人") or "").strip(), grade=(r.get("等级") or "").strip(),
                 prod=(r.get("官网产品") or "").strip())
        em = (r.get("邮箱") or "").strip()
        out.append({
            "r": rank, "n": name, "c": (r.get("国家") or "").strip(),
            "ci": (r.get("城市") or "").strip(), "g": (r.get("等级") or "").strip(),
            "s": int(float(r.get("总分") or 0)), "em": em if ok_email(em) else "",
            "emraw": em, "site": (r.get("官网") or "").strip(),
            "ind": (r.get("行业") or "").strip(), "prod": (r.get("官网产品") or "").strip(),
            "sj": c["sj_en"], "bd": c["m_en"], "sjzh": c["sj_zh"], "bdzh": c["m_zh"],
        })
    out.sort(key=lambda x: (0 if x["g"] == "A" else 1, -x["s"]))
    return out


def esc(s):
    return (str(s or "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build(data):
    for d in data:
        d["gurl"] = gmail_url(d["em"], d["sj"], d["bd"]) if d["em"] else ""
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    sendable = [d for d in data if d["em"]]
    n_a = sum(1 for d in sendable if d["g"] == "A")
    no_mail = [d for d in data if not d["em"]]

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gmail 发信队列 · 色母粒获客</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f4f6f9;color:#1c2632;
 font:14px/1.6 -apple-system,"Segoe UI","Microsoft YaHei",Arial,sans-serif}}
.wrap{{max-width:1080px;margin:0 auto;padding:22px 18px 60px}}
h1{{font-size:19px;margin:0 0 4px}}
.sub{{color:#6b7787;font-size:12.5px;margin-bottom:16px}}
.bar{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:14px}}
.stat{{background:#fff;border:1px solid #e3e8ef;border-radius:9px;padding:9px 14px;font-size:12.5px}}
.stat b{{font-size:17px;color:#0f172a;margin-right:3px}}
.stat.red b{{color:#c8302c}}
.filters{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px}}
.filters input{{flex:1;min-width:180px;padding:7px 11px;border:1px solid #d8dee7;border-radius:8px;font-size:13px}}
.filters button{{padding:7px 13px;border:1px solid #d8dee7;background:#fff;border-radius:8px;
 font-size:12.5px;cursor:pointer;color:#3c4a5a}}
.filters button.on{{background:#0f172a;color:#fff;border-color:#0f172a}}
.row{{background:#fff;border:1px solid #e3e8ef;border-radius:11px;padding:13px 15px;margin-bottom:9px;
 display:flex;gap:14px;align-items:flex-start}}
.row.done{{opacity:.5;background:#f8fafc}}
.idx{{width:26px;height:26px;border-radius:7px;background:#eef2f7;color:#5a6a7d;
 font-size:12px;display:flex;align-items:center;justify-content:center;flex:none;font-weight:600}}
.idx.a{{background:#fdeceb;color:#c8302c}}
.main{{flex:1;min-width:0}}
.nm{{font-weight:600;font-size:14.5px;margin-bottom:2px}}
.meta{{color:#7a8595;font-size:12px;margin-bottom:6px}}
.mail{{font:12.5px/1.5 ui-monospace,Consolas,monospace;color:#2b6cb0;word-break:break-all}}
.sj{{font-size:12.5px;color:#42506a;margin-top:5px;background:#f6f8fb;padding:6px 9px;border-radius:6px}}
.acts{{display:flex;flex-direction:column;gap:6px;flex:none;width:142px}}
a.gm{{display:block;text-align:center;background:#137a4b;color:#fff;text-decoration:none;
 padding:8px 10px;border-radius:8px;font-size:12.5px;font-weight:600}}
a.gm:hover{{background:#0f6440}}
.chk{{display:flex;align-items:center;gap:6px;font-size:12px;color:#5a6a7d;justify-content:center;cursor:pointer}}
.nomail{{background:#fffbe9;border:1px solid #f3e2b4;border-radius:11px;padding:12px 15px;margin-bottom:9px;
 font-size:12.5px;color:#7a6414}}
.nomail a{{color:#8a6d12}}
.empty{{text-align:center;color:#8a94a3;padding:40px}}
.tip{{background:#eef5ff;border:1px solid #cfe0f7;border-radius:10px;padding:11px 14px;
 font-size:12.5px;color:#2a4a72;margin-bottom:16px}}
</style></head><body><div class="wrap">
<h1>Gmail 发信队列</h1>
<div class="sub">点「用 Gmail 打开发送」→ Gmail 撰写窗口已填好收件人、主题、正文 → 你扫一眼按发送</div>

<div class="tip">为什么不是一键全发：27 封冷邮件一次性群发，Gmail 会判为异常行为（先进垃圾箱，再限权）。
这里保留「逐封确认」这一下，速度却比复制粘贴快十倍——收件人、主题、正文都不用你填。</div>

<div class="bar">
  <div class="stat red"><b>{n_a}</b>A 级可发</div>
  <div class="stat"><b>{len(sendable)}</b>家邮箱可用</div>
  <div class="stat"><b id="sentN">0</b>已发</div>
  <div class="stat"><b>{len(no_mail)}</b>家邮箱待补</div>
  <div style="flex:1"></div>
  <button class="filters" style="padding:7px 14px;border:1px solid #d8dee7;background:#fff;border-radius:8px;font-size:12.5px;cursor:pointer" id="exp">导出已发清单</button>
</div>

<div class="filters">
  <input id="q" placeholder="搜公司名 / 国家 / 行业…">
  <button class="on" data-f="all">全部</button>
  <button data-f="A">A 级</button>
  <button data-f="todo">未发</button>
</div>

<div id="host"></div>
</div>
<script>
const DATA = {payload};
const KEY = "mb_gmail_sent_v1";
const store = JSON.parse(localStorage.getItem(KEY) || "{{}}");
const $ = s => document.querySelector(s);
let filter = "all";

function render(){{
  const q = ($("#q").value || "").trim().toLowerCase();
  let list = DATA.filter(d => d.em);
  if (filter === "A") list = list.filter(d => d.g === "A");
  if (filter === "todo") list = list.filter(d => !store[d.n]);
  if (q) list = list.filter(d => (d.n + d.c + d.ind).toLowerCase().includes(q));
  const host = $("#host");
  if (!list.length) {{
    const nm = DATA.filter(d => !d.em);
    host.innerHTML = '<div class="empty">当前筛选下没有可发客户</div>'
      + (filter === "all" ? nomailHtml(nm) : "");
    bind(); return;
  }}
  host.innerHTML = list.map((d, i) => `
    <div class="row ${{store[d.n] ? "done" : ""}}" data-n="${{encodeURIComponent(d.n)}}">
      <div class="idx ${{d.g === "A" ? "a" : ""}}">${{i + 1}}</div>
      <div class="main">
        <div class="nm">${{d.n}}</div>
        <div class="meta">${{d.c}}${{d.ci ? " · " + d.ci : ""}} · ${{d.g}} 级 · ${{d.s}} 分 · ${{d.ind}}</div>
        <div class="mail">${{d.em}}</div>
        <div class="sj">${{d.sj}}</div>
      </div>
      <div class="acts">
        <a class="gm" href="${{d.gurl}}" target="_blank" rel="noopener">用 Gmail 打开发送</a>
        <label class="chk"><input type="checkbox" data-done="${{encodeURIComponent(d.n)}}" ${{store[d.n] ? "checked" : ""}}> 已发送</label>
      </div>
    </div>`).join("") + (filter === "all" ? nomailHtml(DATA.filter(d => !d.em)) : "");
  bind();
  $("#sentN").textContent = Object.keys(store).length;
}}

function nomailHtml(nm){{
  if (!nm.length) return "";
  return `<div style="margin:22px 0 9px;font-size:13px;font-weight:600;color:#7a6414">邮箱待补（走官网表单或再挖一次）</div>`
    + nm.map(d => `<div class="nomail"><b>${{d.n}}</b> · ${{d.c}} · ${{d.g}} 级 · 原值「${{d.emraw || "空"}}」`
      + (d.site ? ` · <a href="${{d.site.startsWith("http") ? d.site : "https://" + d.site}}" target="_blank" rel="noopener">去官网找联系表单</a>` : "")
      + `</div>`).join("");
}}

function bind(){{
  document.querySelectorAll("[data-done]").forEach(cb => {{
    cb.onchange = e => {{
      const n = decodeURIComponent(cb.dataset.done);
      if (cb.checked) store[n] = new Date().toISOString().slice(0, 16).replace("T", " ");
      else delete store[n];
      localStorage.setItem(KEY, JSON.stringify(store));
      const row = cb.closest(".row");
      if (row) row.classList.toggle("done", cb.checked);
      $("#sentN").textContent = Object.keys(store).length;
    }};
  }});
}}

document.querySelectorAll(".filters button[data-f]").forEach(b => {{
  b.onclick = () => {{
    document.querySelectorAll(".filters button[data-f]").forEach(x => x.classList.toggle("on", x === b));
    filter = b.dataset.f; render();
  }};
}});
$("#q").oninput = render;
$("#exp").onclick = () => {{
  const rows = [["公司名", "国家", "等级", "邮箱", "发送时间"]];
  DATA.filter(d => store[d.n]).forEach(d => rows.push([d.n, d.c, d.g, d.em, store[d.n]]));
  const csv = "\\uFEFF" + rows.map(r => r.map(v => '"' + String(v).replace(/"/g, '""') + '"').join(",")).join("\\r\\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], {{type: "text/csv"}}));
  a.download = "已发清单-" + new Date().toISOString().slice(0, 10) + ".csv";
  a.click();
}};
render();
</script>
</body></html>"""


def main():
    data = load()
    html = build(data)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    sendable = [d for d in data if d["em"]]
    print(f"已生成 {OUT}")
    print(f"可发 {len(sendable)} 家（A 级 {sum(1 for d in sendable if d['g'] == 'A')} 家）"
          f"| 邮箱待补 {len(data) - len(sendable)} 家")
    print(f"最长 Gmail 链接：{max(len(d['gurl']) for d in sendable)} 字符")


if __name__ == "__main__":
    main()
