# -*- coding: utf-8 -*-
"""生成《客户跟进台》单文件 HTML —— 逐家跟进工作台

数据源：master-lead-pool.csv（198 家）
产出：reports/customer-followup-desk.html
用法：python tools/build_followup_html.py
"""
import csv
import datetime
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outreach_copy import pick as pick_copy  # noqa: E402

BASE = os.environ.get("MB_HOME") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # MB_HOME 可指定工作目录，默认脚本上一级
SRC = os.path.join(BASE, "master-lead-pool.csv")
OUT = os.path.join(BASE, "reports", "customer-followup-desk.html")


def build_rows():
    with open(SRC, encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if (r.get("公司名") or "").strip()]
    rows.sort(key=lambda r: int(float(r.get("排名") or 9999)))

    out = []
    for r in rows:
        rank = int(float(r.get("排名") or 0))
        name = r["公司名"].strip()
        industry = (r.get("行业") or "").strip()
        contact = (r.get("联系人") or "").strip()
        city = (r.get("城市") or "").strip()
        copy = pick_copy(rank=rank, name=name, industry=industry, city=city,
                         country=r["国家"].strip(), contact=contact,
                         grade=r["等级"].strip(), prod=(r.get("官网产品") or "").strip())

        out.append({
            "r": rank,
            "n": name,
            "c": r["国家"].strip(),
            "ci": city,
            "g": r["等级"].strip(),
            "s": int(float(r.get("总分") or 0)),
            "ind": industry,
            "site": (r.get("官网") or "").strip(),
            "prod": (r.get("官网产品") or "").strip(),
            "ct": contact,
            "ti": (r.get("职位") or "").strip(),
            "em": (r.get("邮箱") or "").strip(),
            "ph": (r.get("电话") or "").strip(),
            "wa": (r.get("WhatsApp") or "").strip(),
            "zl": (r.get("Zalo") or "").strip(),
            "ln": (r.get("LINE") or "").strip(),
            "kk": (r.get("KakaoTalk") or "").strip(),
            "pitch": (r.get("切入建议") or "").strip(),
            "wa_en": copy["wa_en"],
            "wa_zh": copy["wa_zh"],
            "sj_en": copy["sj_en"],
            "sj_zh": copy["sj_zh"],
            "m_en": copy["m_en"],
            "m_zh": copy["m_zh"],
            "pers": copy["pers"],
        })
    return out


HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>客户跟进台 · 色母粒海外获客</title>
<style>
:root{
  --bg:#f6f5f2; --card:#fff; --ink:#1c1f24; --sub:#6b7280; --line:#e5e3dd;
  --brand:#1f4e79; --brand2:#2f6fa8; --accent:#c2410c;
  --ok:#15803d; --warn:#b45309; --bad:#b91c1c;
  --chip:#eef2f7;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:940px;margin:0 auto;padding:16px 14px 90px}
header{display:flex;flex-wrap:wrap;align-items:center;gap:10px;margin-bottom:14px}
h1{font-size:19px;margin:0;letter-spacing:.5px}
h1 small{display:block;font-size:12px;color:var(--sub);font-weight:400;letter-spacing:0}
.grow{flex:1}
.btn{border:1px solid var(--line);background:#fff;border-radius:9px;padding:8px 13px;font-size:13px;
  cursor:pointer;color:var(--ink);transition:.15s}
.btn:hover{border-color:var(--brand2);color:var(--brand)}
.btn.primary{background:var(--brand);border-color:var(--brand);color:#fff}
.btn.primary:hover{background:var(--brand2);color:#fff}
.btn.ghost{background:transparent}
.btn.gmail{background:#137a4b;border-color:#137a4b;color:#fff;text-decoration:none;display:inline-block}
.btn.gmail:hover{background:#0f6440;color:#fff;border-color:#0f6440}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.stat{background:#fff;border:1px solid var(--line);border-radius:9px;padding:7px 12px;font-size:12.5px;color:var(--sub)}
.stat b{color:var(--ink);font-size:15px;margin-left:5px}
.stat.alert b{color:var(--bad)}
.bar{height:5px;background:#e7e5df;border-radius:3px;overflow:hidden;margin:2px 0 16px}
.bar i{display:block;height:100%;background:linear-gradient(90deg,var(--brand2),var(--brand));width:0;transition:width .3s}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 18px 16px;
  box-shadow:0 1px 2px rgba(20,25,40,.04)}
.card-top{display:flex;gap:12px;align-items:flex-start;margin-bottom:4px}
.name{font-size:19px;font-weight:700;line-height:1.3;word-break:break-word}
.meta{color:var(--sub);font-size:12.5px;margin-top:3px}
.badge{flex:none;width:40px;height:40px;border-radius:11px;display:grid;place-items:center;
  font-weight:700;font-size:17px;color:#fff;background:var(--brand)}
.badge.b{background:#8aa0b8}.badge.c{background:#b9b4a8}
.score{font-size:11px;color:var(--sub);text-align:center;margin-top:3px}
.idx{font-size:12px;color:var(--sub);margin-left:auto;flex:none}
.sect{margin-top:14px;border-top:1px dashed var(--line);padding-top:12px}
.sect:first-of-type{border-top:0;padding-top:0}
.lbl{font-size:11px;letter-spacing:1px;color:var(--sub);text-transform:uppercase;margin-bottom:6px}
.rows{display:grid;gap:6px}
.row{display:flex;gap:8px;font-size:13.5px;align-items:baseline}
.row .k{flex:none;width:62px;color:var(--sub);font-size:12.5px}
.row .v{flex:1;word-break:break-all}
.contacts{display:flex;flex-wrap:wrap;gap:7px;margin-top:8px}
.chip{display:inline-flex;align-items:center;gap:6px;background:var(--chip);border:1px solid transparent;
  border-radius:8px;padding:6px 10px;font-size:12.5px;color:var(--brand);text-decoration:none;cursor:pointer}
.chip:hover{background:#e3ebf4;border-color:#cfdcea}
.chip.na{color:#a8a29e;background:#f4f2ee;cursor:default}
.pitch{background:#fbfaf7;border-left:3px solid #d9cfbe;padding:10px 12px;border-radius:0 8px 8px 0;
  font-size:13px;color:#3f3a33;line-height:1.65}
.msg{background:#fbfcfe;border:1px solid #e3eaf3;border-radius:10px;padding:12px;font-size:13.5px;
  white-space:pre-wrap;line-height:1.7}
.msg.zh{background:#fcfbf8;border-color:#efe9dd;color:#4a4438}
/* —— WhatsApp 两句区（绿系，轻） —— */
.wa{background:#f4fbf6;border:1px solid #cfeadd;border-radius:10px;padding:12px 13px;font-size:13.5px;
  white-space:pre-wrap;line-height:1.72;color:#1f3d31}
.wa.zh{background:#fcfbf8;border-color:#efe9dd;color:#4a4438}
/* —— 邮件区（纸感，重） —— */
.mailwrap{border:1px solid #d8e0ea;border-radius:12px;overflow:hidden;background:#fff;
  box-shadow:0 1px 2px rgba(16,32,52,.04)}
.subjbar{display:flex;align-items:center;gap:8px;padding:9px 12px;background:#eef3f9;
  border-bottom:1px solid #dde6f0;font-size:13px;color:#20364f}
.subjbar .k{font-size:10.5px;letter-spacing:.8px;color:#6b7f96;text-transform:uppercase;flex:none}
.subjbar .s{flex:1;font-weight:600;line-height:1.4}
.mailbody{padding:15px 16px;font-size:13.6px;line-height:1.82;white-space:pre-wrap;color:#1c2632;
  font-family:-apple-system,"Segoe UI","Helvetica Neue",Arial,sans-serif}
.mailbody .sig{color:#5a6b7f}
.mailbody.zh{background:#fcfbf8;color:#4a4438;font-family:inherit}
.mailhead{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px 0}
.maillen{font-size:11px;color:var(--sub)}

.tag{display:inline-block;font-size:11px;padding:2px 7px;border-radius:5px;margin-left:7px;
  vertical-align:middle;font-weight:400}
.tag.ok{background:#e7f5ec;color:var(--ok)}
.tag.warn{background:#fdf3e3;color:var(--warn)}
.msg-actions{display:flex;gap:8px;margin-top:9px;flex-wrap:wrap}
.status{display:flex;flex-wrap:wrap;gap:7px;margin-top:4px}
.st{border:1px solid var(--line);background:#fff;border-radius:20px;padding:7px 14px;font-size:13px;cursor:pointer;color:var(--sub)}
.st:hover{border-color:var(--brand2)}
.st.on{background:var(--brand);border-color:var(--brand);color:#fff;font-weight:600}
.st.on[data-v="成交"]{background:var(--ok);border-color:var(--ok)}
.st.on[data-v="无效"]{background:var(--bad);border-color:var(--bad)}
textarea{width:100%;border:1px solid var(--line);border-radius:9px;padding:9px 11px;font-size:13.5px;
  font-family:inherit;resize:vertical;min-height:62px;background:#fff;color:var(--ink)}
textarea:focus{outline:2px solid #dbe6f2;border-color:var(--brand2)}
.nav{position:fixed;left:0;right:0;bottom:0;background:rgba(255,255,255,.96);backdrop-filter:blur(8px);
  border-top:1px solid var(--line);padding:10px 14px;display:flex;gap:10px;align-items:center;z-index:20}
.nav .wrap2{max-width:940px;margin:0 auto;width:100%;display:flex;gap:10px;align-items:center}
.nav .btn{flex:1;padding:12px;font-size:14px}
.nav .pos{flex:none;font-size:12.5px;color:var(--sub);min-width:78px;text-align:center}
.empty{text-align:center;color:var(--sub);padding:50px 20px;font-size:14px}
table{width:100%;border-collapse:collapse;background:#fff;border-radius:12px;overflow:hidden;font-size:13px}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line);white-space:nowrap}
th{background:#f1efe9;font-size:12px;color:#4b5563;font-weight:600;position:sticky;top:0;cursor:pointer}
tr:hover td{background:#faf9f6}
td.mono{font-variant-numeric:tabular-nums}
.pill{display:inline-block;font-size:11px;padding:1px 7px;border-radius:5px}
.pill.A{background:#e7f5ec;color:var(--ok)}.pill.B{background:#eef2f7;color:var(--brand)}
.pill.C{background:#f2f0eb;color:#8a8577}
.pill.s1{background:#fdf3e3;color:var(--warn)}
.pill.s2{background:#e7f5ec;color:var(--ok)}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
select,input[type=search]{border:1px solid var(--line);border-radius:9px;padding:8px 11px;font-size:13px;
  background:#fff;color:var(--ink);font-family:inherit}
input[type=search]{flex:1;min-width:150px}
.toast{position:fixed;left:50%;bottom:92px;transform:translate(-50%,10px);background:#1c1f24;color:#fff;
  padding:9px 16px;border-radius:8px;font-size:13px;opacity:0;pointer-events:none;transition:.2s;z-index:50}
.toast.on{opacity:1;transform:translate(-50%,0)}
.hide{display:none!important}
@media (max-width:560px){
  .wrap{padding:12px 10px 96px}.card{padding:15px 14px}
  .row .k{width:54px}.name{font-size:17px}
  th,td{padding:8px}
}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="grow">
      <h1>客户跟进台<small>色母粒 · 定制配色 / 阻燃母粒 &nbsp;|&nbsp; __GEN_DATE__ 生成 · __TOTAL__ 家</small></h1>
    </div>
    <button class="btn" id="viewBtn">列表视图</button>
    <button class="btn ghost" id="exportBtn">导出进度</button>
  </header>

  <div class="stats" id="stats"></div>
  <div class="bar"><i id="barFill"></i></div>

  <!-- 跟进模式 -->
  <div id="followWrap">
    <div class="toolbar">
      <select id="fCountry"><option value="">全部国家</option></select>
      <select id="fGrade">
        <option value="A">仅 A 级（34）</option>
        <option value="AB">A + B 级</option>
        <option value="">全部等级</option>
      </select>
      <select id="fStatus">
        <option value="todo">仅未跟进</option>
        <option value="">全部状态</option>
        <option value="已发信">已发信</option>
        <option value="已回复">已回复</option>
      </select>
      <input type="search" id="q" placeholder="搜公司/城市/行业…">
    </div>
    <div id="cardHost"></div>
  </div>

  <!-- 列表视图 -->
  <div id="listWrap" class="hide">
    <div class="toolbar"><input type="search" id="q2" placeholder="搜公司名 / 城市 / 行业"></div>
    <div style="overflow:auto;max-height:calc(100vh - 210px);border:1px solid var(--line);border-radius:12px">
      <table id="tbl"><thead><tr>
        <th data-k="r">#</th><th data-k="n">公司</th><th data-k="c">国家</th><th data-k="ci">城市</th>
        <th data-k="g">级</th><th data-k="s">分</th><th data-k="st">状态</th><th>行业</th>
      </tr></thead><tbody></tbody></table>
    </div>
  </div>
</div>

<div class="nav" id="nav">
  <div class="wrap2">
    <button class="btn" id="prevBtn">← 上一位</button>
    <div class="pos" id="pos"></div>
    <button class="btn primary" id="nextBtn">下一位 →</button>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
const DATA = __DATA__;
const KEY = "mb_followup_v1";
const STATUSES = ["未联系","已发信","已回复","已报价","已寄样","成交","无效"];

let store = {};
try { store = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e){ store = {}; }
const save = () => localStorage.setItem(KEY, JSON.stringify(store));
const rec = r => store[r] || {st:"未联系", note:"", ts:""};

let queue = [], at = 0;
const $ = s => document.querySelector(s);
const host = $("#cardHost");

function countries(){
  const m = new Map();
  DATA.forEach(d => m.set(d.c, (m.get(d.c)||0)+1));
  return [...m.entries()].sort((a,b)=>b[1]-a[1]);
}

function initFilters(){
  const sel = $("#fCountry");
  countries().forEach(([c,n])=>{
    const o=document.createElement("option"); o.value=c; o.textContent=`${c}（${n}）`; sel.appendChild(o);
  });
}

function buildQueue(){
  const c = $("#fCountry").value, g = $("#fGrade").value,
        st = $("#fStatus").value, q = $("#q").value.trim().toLowerCase();
  queue = DATA.filter(d=>{
    if (c && d.c !== c) return false;
    if (g === "A" && d.g !== "A") return false;
    if (g === "AB" && d.g === "C") return false;
    if (st === "todo" && rec(d.r).st !== "未联系") return false;
    if (st && st !== "todo" && rec(d.r).st !== st) return false;
    if (q && !(d.n+d.ci+d.ind+d.c).toLowerCase().includes(q)) return false;
    return true;
  });
  // A 级优先，其次按分数
  queue.sort((a,b)=> (a.g===b.g ? b.s-a.s : (a.g==="A"?-1:(b.g==="A"?1:0))));
  at = 0;
  render();
}

function chip(label, val, href){
  if (!val || /^(该市场不使用|待验证|待核实|明确无)/.test(val)) {
    return `<span class="chip na">${label} —</span>`;
  }
  const t = `<span class="chip" data-copy="${attr(val)}">${label} ${esc(val.length>26?val.slice(0,26)+"…":val)} ⧉</span>`;
  return href ? `<a class="chip" href="${href}" target="_blank" rel="noopener">${label} ↗</a>` + t : t;
}

function esc(s){ return String(s||"").replace(/[&<>]/g, m=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[m])); }
function attr(s){ return esc(s).replace(/"/g,"&quot;").replace(/'/g,"&#39;"); }
function waLink(v){ const d=(v||"").replace(/\D/g,""); return d.length>7 ? "https://wa.me/"+d : ""; }

function render(){
  const total = DATA.length;
  const done = DATA.filter(d=>rec(d.r).st!=="未联系").length;
  const aLeft = DATA.filter(d=>d.g==="A" && rec(d.r).st==="未联系").length;
  const replied = DATA.filter(d=>["已回复","已报价","已寄样","成交"].includes(rec(d.r).st)).length;
  const sent = DATA.filter(d=>rec(d.r).st!=="未联系").length;
  $("#stats").innerHTML = `
    <div class="stat">总客户 <b>${total}</b></div>
    <div class="stat">A 级未跟 <b class="${aLeft?'alert':''}">${aLeft}</b></div>
    <div class="stat">已跟进 <b>${done}</b></div>
    <div class="stat">有回复 <b>${replied}</b></div>
    <div class="stat">回复率 <b>${sent?Math.round(replied/sent*100)+"%":"—"}</b></div>`;
  $("#barFill").style.width = (done/total*100).toFixed(1)+"%";
  $("#pos").textContent = queue.length ? `${at+1} / ${queue.length}` : "0 / 0";
  $("#prevBtn").disabled = at<=0;
  $("#nextBtn").disabled = at>=queue.length-1;

  if (!queue.length){ host.innerHTML = `<div class="empty">这个筛选下没有客户了。换个条件，或去列表视图看看。</div>`; return; }
  const d = queue[at], s = rec(d.r);
  host.innerHTML = `
  <div class="card">
    <div class="card-top">
      <div class="badge ${d.g.toLowerCase()}">${d.g}</div>
      <div style="flex:1">
        <div class="name">${esc(d.n)}</div>
        <div class="meta">${esc(d.c)}${d.ci?" · "+esc(d.ci):""} · ${d.s} 分 · #${d.r}</div>
      </div>
      <div class="score">${d.ct?esc(d.ct.split("/")[0].trim()):""}</div>
    </div>

    <div class="sect">
      <div class="rows">
        <div class="row"><span class="k">行业</span><span class="v">${esc(d.ind)||"—"}</span></div>
        ${d.ti?`<div class="row"><span class="k">职位</span><span class="v">${esc(d.ti)}</span></div>`:""}
        ${d.prod?`<div class="row"><span class="k">官网产品</span><span class="v">${esc(d.prod)}</span></div>`:""}
      </div>
      <div class="contacts">
        ${d.em?`<span class="chip" data-copy="${attr(d.em)}">邮箱 ${esc(d.em.length>26?d.em.slice(0,26)+"…":d.em)} ⧉</span>`:""}
        ${d.ph?`<span class="chip" data-copy="${attr(d.ph)}">电话 ${esc(d.ph)} ⧉</span>`:""}
        ${d.wa?chip("WhatsApp", d.wa, waLink(d.wa)):""}
        ${d.zl?chip("Zalo", d.zl, ""):""}
        ${d.ln?chip("LINE", d.ln, ""):""}
        ${d.kk?chip("KakaoTalk", d.kk, ""):""}
        ${d.site?`<a class="chip" href="${esc(d.site)}" target="_blank" rel="noopener">官网 ↗</a>`:""}
        ${d.site?`<span class="chip" data-copy="${attr(d.site)}">复制网址 ⧉</span>`:""}
      </div>
    </div>

    ${d.pitch?`<div class="sect"><div class="lbl">为什么值得跟</div><div class="pitch">${esc(d.pitch)}</div></div>`:""}

    <!-- ① WhatsApp：两句，负责让对方回一句 -->
    <div class="sect">
      <div class="lbl">① WhatsApp 开场白 · 两句${d.pers?'<span class="tag ok">逐家定制</span>':'<span class="tag warn">⚠️ 行业级模板</span>'}</div>
      <div class="wa">${esc(d.wa_en)}</div>
      <div class="msg-actions">
        <button class="btn" data-copy="${attr(d.wa_en)}">复制 WhatsApp 英文</button>
        ${d.wa && waLink(d.wa)?`<a class="btn primary" href="${waLink(d.wa)}" target="_blank" rel="noopener">打开 WhatsApp 聊天 ↗</a>`:""}
        <button class="btn ghost" data-toggle="waZh">看中文参照</button>
      </div>
      <div class="wa zh hide" id="waZh" style="margin-top:9px">${esc(d.wa_zh)}</div>
      <div class="msg-actions hide" id="waZhAct" style="margin-top:9px">
        <button class="btn" data-copy="${attr(d.wa_zh)}">复制中文（仅参照，不外发）</button>
      </div>
    </div>

    <!-- ② 开发信：完整邮件，负责让对方认真评估 -->
    <div class="sect">
      <div class="lbl">② 开发信 · 完整邮件${d.pers?'<span class="tag ok">逐家定制</span>':'<span class="tag warn">⚠️ 行业级模板</span>'}</div>
      <div class="mailwrap">
        <div class="subjbar">
          <span class="k">Subject</span>
          <span class="s">${esc(d.sj_en)}</span>
          <button class="btn ghost" style="padding:3px 9px;font-size:11.5px;flex:none" data-copy="${attr(d.sj_en)}">复制主题</button>
        </div>
        <div class="mailbody">${esc(d.m_en)}</div>
      </div>
      <div class="msg-actions">
        <button class="btn primary" data-copy="${attr(d.m_en)}">复制整封邮件（主题另复制）</button>
        ${d.em && /@/.test(d.em)?`<a class="btn gmail" href="https://mail.google.com/mail/?view=cm&fs=1&to=${encodeURIComponent(d.em)}&su=${encodeURIComponent(d.sj_en)}&body=${encodeURIComponent(d.m_en)}" target="_blank" rel="noopener">用 Gmail 打开发送</a>`:""}
        ${d.em && /@/.test(d.em)?`<a class="btn" href="mailto:${esc(d.em)}?subject=${encodeURIComponent(d.sj_en)}&body=${encodeURIComponent(d.m_en)}">其他邮件客户端</a>`:""}
        <button class="btn ghost" data-toggle="mailZh">看中文参照</button>
      </div>
      <div class="mailwrap hide" id="mailZh" style="margin-top:10px">
        <div class="subjbar">
          <span class="k">主题</span>
          <span class="s">${esc(d.sj_zh)}</span>
          <button class="btn ghost" style="padding:3px 9px;font-size:11.5px;flex:none" data-copy="${attr(d.sj_zh)}">复制主题</button>
        </div>
        <div class="mailbody zh">${esc(d.m_zh)}</div>
      </div>
      <div class="msg-actions hide" id="mailZhAct" style="margin-top:9px">
        <button class="btn" data-copy="${attr(d.m_zh)}">复制中文参照邮件</button>
      </div>
    </div>

    <div class="sect">
      <div class="lbl">跟进状态</div>
      <div class="status">${STATUSES.map(v=>`<button class="st ${s.st===v?'on':''}" data-v="${v}" data-r="${d.r}">${v}</button>`).join("")}</div>
      <textarea id="note" placeholder="备注：发的是邮件还是 WhatsApp、对方的回复、报价要求、打样进度…（自动保存）">${esc(s.note)}</textarea>
    </div>
  </div>`;
}

function toast(t){ const el=$("#toast"); el.textContent=t; el.classList.add("on");
  clearTimeout(el._t); el._t=setTimeout(()=>el.classList.remove("on"),1400); }

function copy(text){
  const done = ()=>{ toast("已复制"); };
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(done).catch(()=>fallback(text,done));
  } else fallback(text,done);
}
function fallback(text, done){
  const ta=document.createElement("textarea"); ta.value=text;
  ta.style.position="fixed"; ta.style.opacity="0"; document.body.appendChild(ta);
  ta.select(); try{ document.execCommand("copy"); done(); }catch(e){ toast("复制失败，请手动选中"); }
  document.body.removeChild(ta);
}

/* 事件委托 */
document.addEventListener("click", e=>{
  const c = e.target.closest("[data-copy]");
  if (c){ copy(c.getAttribute("data-copy")); return; }
  const st = e.target.closest(".st");
  if (st){
    const r = +st.dataset.r, v = st.dataset.v;
    const cur = rec(r);
    store[r] = {st:v, note:cur.note, ts:new Date().toISOString().slice(0,16).replace("T"," ")};
    save();
    st.parentNode.querySelectorAll(".st").forEach(b=>b.classList.toggle("on", b===st));
    renderStatsOnly();
    // 标完若已不符合当前筛选（如"仅未跟进"），自动跳到下一位
    const d = queue[at];
    if (d && d.r === r && !matches()){
      queue.splice(at,1);
      if (at >= queue.length) at = Math.max(0, queue.length-1);
      render();
    }
    return;
  }
  const tg = e.target.closest("[data-toggle]");
  if (tg){
    const id = tg.dataset.toggle;
    const box = $("#" + id), act = $("#" + id + "Act");
    const on = box.classList.toggle("hide");
    if (act) act.classList.toggle("hide", on);
    tg.textContent = on ? (id === "waZh" ? "看中文参照" : "看中文参照") : "收起中文";
    return;
  }
});

function matches(){
  const d = queue[at]; if (!d) return false;
  const c = $("#fCountry").value, g = $("#fGrade").value,
        st = $("#fStatus").value, q = $("#q").value.trim().toLowerCase();
  if (c && d.c !== c) return false;
  if (g === "A" && d.g !== "A") return false;
  if (g === "AB" && d.g === "C") return false;
  if (st === "todo" && rec(d.r).st !== "未联系") return false;
  if (st && st !== "todo" && rec(d.r).st !== st) return false;
  if (q && !(d.n+d.ci+d.ind+d.c).toLowerCase().includes(q)) return false;
  return true;
}

function renderStatsOnly(){
  const total = DATA.length;
  const done = DATA.filter(d=>rec(d.r).st!=="未联系").length;
  const aLeft = DATA.filter(d=>d.g==="A" && rec(d.r).st==="未联系").length;
  const replied = DATA.filter(d=>["已回复","已报价","已寄样","成交"].includes(rec(d.r).st)).length;
  const sent = done;
  $("#stats").innerHTML = `
    <div class="stat">总客户 <b>${total}</b></div>
    <div class="stat">A 级未跟 <b class="${aLeft?'alert':''}">${aLeft}</b></div>
    <div class="stat">已跟进 <b>${done}</b></div>
    <div class="stat">有回复 <b>${replied}</b></div>
    <div class="stat">回复率 <b>${sent?Math.round(replied/sent*100)+"%":"—"}</b></div>`;
  $("#barFill").style.width = (done/total*100).toFixed(1)+"%";
}

document.addEventListener("input", e=>{
  if (e.target.id === "note"){
    const d = queue[at], cur = rec(d.r);
    store[d.r] = {...cur, note:e.target.value};
    save();
  }
});

$("#prevBtn").onclick = ()=>{ if(at>0){at--; render(); window.scrollTo({top:0,behavior:"smooth"});} };
$("#nextBtn").onclick = ()=>{ if(at<queue.length-1){at++; render(); window.scrollTo({top:0,behavior:"smooth"});} };
["#fCountry","#fGrade","#fStatus","#q"].forEach(s=>{
  const el=$(s); el.addEventListener(el.tagName==="INPUT"?"input":"change", buildQueue);
});

$("#viewBtn").onclick = ()=>{
  const l = $("#listWrap").classList.toggle("hide");
  $("#followWrap").classList.toggle("hide", !l);
  $("#nav").classList.toggle("hide", !l);
  $("#viewBtn").textContent = l ? "列表视图" : "跟进模式";
  if (l) drawTable();
};

let sortK="r", sortAsc=true;
document.querySelectorAll("th[data-k]").forEach(th=>{
  th.onclick = ()=>{ const k=th.dataset.k; sortAsc = (k===sortK)? !sortAsc : true; sortK=k; drawTable(); };
});
$("#q2").addEventListener("input", drawTable);

function drawTable(){
  const q = ($("#q2").value||"").toLowerCase();
  let rows = DATA.filter(d=> !q || (d.n+d.ci+d.ind+d.c).toLowerCase().includes(q));
  rows.sort((a,b)=>{
    let x=a[sortK], y=b[sortK];
    if (sortK==="r"||sortK==="s"){ x=+x; y=+y; }
    else if (sortK==="st"){ x=rec(a.r).st; y=rec(b.r).st; }
    return (x>y?1:x<y?-1:0) * (sortAsc?1:-1);
  });
  $("#tbl tbody").innerHTML = rows.map(d=>{
    const s = rec(d.r).st;
    const cls = s==="未联系"?"s1":"s2";
    return `<tr data-r="${d.r}" style="cursor:pointer">
      <td class="mono">${d.r}</td><td><b>${esc(d.n)}</b></td><td>${esc(d.c)}</td>
      <td>${esc(d.ci)}</td><td><span class="pill ${d.g}">${d.g}</span></td>
      <td class="mono">${d.s}</td><td><span class="pill ${cls}">${s}</span></td>
      <td style="white-space:normal;max-width:260px">${esc(d.ind)}</td></tr>`;
  }).join("");
  $("#tbl tbody").querySelectorAll("tr").forEach(tr=>{
    tr.onclick = ()=>{
      const r = +tr.dataset.r;
      $("#listWrap").classList.add("hide"); $("#followWrap").classList.remove("hide");
      $("#nav").classList.remove("hide"); $("#viewBtn").textContent="列表视图";
      $("#fCountry").value=""; $("#fGrade").value=""; $("#fStatus").value=""; $("#q").value="";
      queue = DATA.slice().sort((a,b)=>a.r-b.r);
      at = queue.findIndex(x=>x.r===r); render();
      window.scrollTo({top:0,behavior:"smooth"});
    };
  });
}

$("#exportBtn").onclick = ()=>{
  const head = ["排名","公司名","国家","城市","等级","跟进状态","备注","更新时间"];
  const lines = [head.join(",")];
  DATA.forEach(d=>{
    const s = rec(d.r);
    const cells = [d.r,d.n,d.c,d.ci,d.g,s.st,s.note||"",s.ts||""]
      .map(v=>`"${String(v).replace(/"/g,'""')}"`);
    lines.push(cells.join(","));
  });
  const blob = new Blob(["\ufeff"+lines.join("\r\n")], {type:"text/csv;charset=utf-8"});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "跟进进度-" + new Date().toISOString().slice(0,10) + ".csv";
  a.click(); URL.revokeObjectURL(a.href);
  toast("已导出 CSV");
};

document.addEventListener("keydown", e=>{
  if (e.target.tagName==="TEXTAREA"||e.target.tagName==="INPUT") return;
  if (e.key==="ArrowRight") $("#nextBtn").click();
  if (e.key==="ArrowLeft") $("#prevBtn").click();
});

initFilters();
buildQueue();
</script>
</body>
</html>
"""


def main():
    rows = build_rows()
    total = len(rows)
    html = (HTML
            .replace("__DATA__", json.dumps(rows, ensure_ascii=False))
            .replace("__GEN_DATE__", datetime.date.today().isoformat())
            .replace("__TOTAL__", str(total)))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    per = sum(1 for r in rows if r["pers"])
    print(f"已生成: {OUT}")
    print(f"客户 {total} 家 | 个性化锚点 {per} 家 | 降级 {total-per} 家 | {os.path.getsize(OUT)//1024} KB")


if __name__ == "__main__":
    main()
