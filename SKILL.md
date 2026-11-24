---
name: masterbatch-lead-gen
slug: masterbatch-lead-gen
displayName: Masterbatch Lead Gen
display_name: Masterbatch Lead Gen
display_name_en: Masterbatch Lead Gen
description: 色母粒工厂海外自动获客工作流。面向定制色母粒 / 配色打样 / 阻燃母粒制造商的全球线索发现、企业评估、多语言开发信草稿与 CRM 线索池管理。Use when user asks to find overseas customers, discover prospects, generate outreach emails, evaluate leads, research target markets, or manage a masterbatch export pipeline.
description_zh: 色母粒工厂海外自动获客工作流，覆盖目标市场研究、海外企业发现、线索评分、多语言开发信草稿与线索池管理。
description_en: Overseas lead-generation workflow for masterbatch manufacturers — target-market research, prospect discovery, lead scoring, multilingual outreach drafting, and a local lead pool.
tags: [色母粒, masterbatch, 外贸, 获客, lead-generation, 开发信, 线索, export, B2B]
version: 0.1.0
license: MIT
author: AI Global Masterbatch Agent
user-invocable: true
metadata: {"openclaw":{"emoji":"🎨","category":"business","tags":["masterbatch","lead-generation","export","B2B","色母粒","外贸获客"]}}
---

# Masterbatch Lead Gen（色母粒海外获客工作流）

面向色母粒工厂的**海外自动获客** Skill。它把「找客户 → 评客户 → 写开发信 → 存线索」这条外贸获客闭环，做成一整套可复用的方法论与提示词，让 AI 成为你的 24 小时外贸团队。

> 本 Skill 是**纯方法论 + 提示词 + 知识库**，不依赖任何 APP / 后端 / 数据库。它直接复用 WorkBuddy 自带的联网搜索、文件读写、定时任务能力，即可跑通完整闭环。

> 🌐 **浏览器自动化（可选增强）**：本 Skill 支持调用 WorkBuddy 的浏览器自动化能力（browser-use，CDP 直连本机谷歌 Chrome），复用你的登录态去深挖官网联系方式、抓取 JS 渲染页面。何时用浏览器、何时用搜索，见 [`references/lead-gen-workflow.md`](references/lead-gen-workflow.md)「浏览器自动化接入」章节。

## 谁需要它

- 生产**定制色母粒**、**配色打样**（实物色板 / Pantone / RAL）、**阻燃母粒**的制造商。
- 想用 AI 低成本开发海外市场的外贸主管 / 老板 / SOHO。
- 目标市场：**欧美、日韩等发达国家优先**（美国、德国、日本、韩国、英国、法国、意大利等），东南亚（越南、泰国、印尼）、中东、拉美作为跑量基本盘。

## 核心业务边界（务必遵守）

1. **产品范围**：只做定制色母粒、配色打样、阻燃母粒。**不生产、不推广填充母粒。**
2. **事实与推断分离**：搜索到的企业信息必须标注来源；不确定的信息写"待核实"，**绝不编造**联系方式或资质。
3. **开发信必须人工审批**：本 Skill 只生成开发信**草稿**，不发送任何邮件。发送前必须由人工确认。
4. **客户隐私**：客户资料是敏感数据，永不写入公开文档、永不提交到 GitHub 或任何公开渠道。
5. **本地语言**：面向目标国家时，开发信与关键词必须使用当地语言（越南语、土耳其语、西班牙语等），而非只写英文。

## 六个 Agent 岗位（一整套外贸团队）

本 Skill 用「六个岗位」模拟一支完整的外贸团队。每当你执行任务时，先切换到对应岗位的角色视角：

| 岗位 | 职责 | 何时用 |
|---|---|---|
| 🎯 **市场研究 Agent** | 目标国家市场研判、进入策略、本地语言关键词 | 选定目标市场 / 做国家调研 |
| 🗺️ **地图抓取 Agent** | 用浏览器脚本 `tools/maps_scrape.py` 按国家/地区批量抓取企业 | 从谷歌地图抓客户 |
| 🔍 **客户开发 Agent** | 从联网搜索发现海外企业、按行业/国家/关键词挖掘 | 找潜在客户 |
| 📄 **官网研究 Agent** | 提取企业官网公开信息、公开邮箱、决策人线索 | 深挖某家企业的真实业务 |
| ✍️ **商务沟通 Agent** | 生成个性化多语言开发信 / WhatsApp / LinkedIn 文案 | 写触达内容 |
| 🧮 **客户评估 Agent** | 对线索评分分级、核验事实 | 筛选高价值线索 |
| 👔 **总经理 Agent** | 运营汇总、风险提示、合规审核 | 复盘 / 决策 |

## 获客闭环（核心工作流）

```text
① 市场研究    → 确定国家 + 产品 + 本地语言关键词
② 地图抓取    → `kwgen.py` 出本地语言词+换城 → `maps_scrape.py` 分片抓 → `classify_leads.py` 甄别真工厂 → `import_leads.py` 去重入库（见 `references/maps-keyword-system.md`）
   挖聊天号    → `find_whatsapp.py --crawl` 抓官网 wa.me + 号段推断手机 → `render_wa_worklist.py` 点验清单（见 `references/whatsapp-sourcing.md`）
③ 企业发现    → 联网搜索海外企业（官网、目录、展会名录）
④ 官网深挖    → 提取业务、公开邮箱、决策人线索
⑤ 线索评分    → 按 7 维打分分级（A/B/C，含负分项）
⑥ 开发信草稿  → 多语言个性化开发信（仅草稿）
⑦ 多渠道触达  → 邮件/WhatsApp/LinkedIn 文案备好，人工发送
⑧ 整理+审核   → 汇总成线索表 + 合规审核清单
```

> **务实版自动化**：AI 负责全部「抓取、筛选、写作、整理、审核」的重活，但**对外发送（邮件/WhatsApp/LinkedIn）一律人工手动**，避免平台封号。详见 `references/lead-gen-workflow.md`。

每一步的具体操作、提示词模板、评分维度和开发信模板，见下方 references 文档。

## 零、部署（换机器 / 给别人用）

```bash
# 1) 装 skill（拿到 SKILL.md + references/ + tools/ + templates/）
cp -r masterbatch-lead-gen ~/.workbuddy/skills/masterbatch-lead-gen

# 2) 初始化工作目录（生成脚本、空线索池、50 国市场表）
python ~/.workbuddy/skills/masterbatch-lead-gen/init_workspace.py "D:////my-leadgen"

# 3) 必改两处，否则会带着别人的公司与签名发出去
#    <工作目录>\tools\profile.json          姓名/公司/邮箱/WhatsApp
#    references/company-profile.md           产能/认证/年限等真实数据
```

**目录约定**：`tools/` 必须与 `master-lead-pool.csv` 同级（脚本默认用「脚本所在目录的上一级」定位数据，也可用环境变量 `MB_HOME` 指定）。所有命令都在工作目录下以 `python tools/xxx.py` 执行。

## 快速开始

### 1. 选定目标市场

```
请用市场研究 Agent 视角，调研越南市场：
- 目标产品：定制色母粒、阻燃母粒
- 需要：市场规模、主要应用行业、本地语言关键词、进入建议
```

### 2. 发现海外企业

```
请用客户开发 Agent 视角，帮我找越南的注塑厂 / 塑料加工厂，
这些企业可能需要定制色母粒。用越南语关键词搜索，列出 20 家，
并标注每家官网和业务范围。
```

### 3. 写开发信

```
请用商务沟通 Agent 视角，给这家越南企业写一封越南语开发信：
- 公司名：xxx
- 业务：xxx
- 我们优势：定制色母粒 + 配色打样 + 阻燃母粒
生成草稿（不要发送），语气专业、克制、不夸大。
```

## 📚 深度指南（references/）

| 文档 | 内容 |
|---|---|
| [`references/industry-knowledge.md`](references/industry-knowledge.md) | 色母粒行业知识、产品线、认证、术语中英对照 |
| [`references/lead-gen-workflow.md`](references/lead-gen-workflow.md) | 六步获客闭环的详细操作与提示词模板 |
| [`references/multilingual-keywords.md`](references/multilingual-keywords.md) | 越南语 / 土耳其语 / 西班牙语 / 英语 / 德语 / 法语 / 意大利语 / 韩语 / 日语获客关键词库 |
| [`references/tiered-keywords.md`](references/tiered-keywords.md) | **按 A/B/C 分层关键词库 + 双渠道**：A 级精准狙击词 / B 级广撒网词 / C 级排雷词，打通谷歌地图、谷歌浏览器两条获客渠道的搜索规则 |
| [`references/outreach-templates.md`](references/outreach-templates.md) | 多语言开发信模板（英/越/土/西/德/法/意/韩/日）+ 分行业差异化 + 撰写规范 + 红线 |
| [`references/lead-scoring.md`](references/lead-scoring.md) | 线索评分（7 维 + 负分项 + 行业加权）、分级标准、评分提示词 |
| [`references/safety-compliance.md`](references/safety-compliance.md) | 数据安全、隐私、合规红线（重要！） |
| [`references/automation-guide.md`](references/automation-guide.md) | 每天自动获客：工作目录、市场轮换、多键去重、定时任务、每日产出（含 HTML 日报）、人工审核节点 |
| [`references/deep-dive-intelligence.md`](references/deep-dive-intelligence.md) | A/B 级客户深挖（同等深挖）：决策人挖掘、目录站补抓、社交双渠道必查（按市场 WhatsApp/Zalo/KakaoTalk/LINE）、HTML 情报看板产出 |
| [`references/maps-keyword-system.md`](references/maps-keyword-system.md) | **Google Maps 自动获客体系（4 段流水线）**：`kwgen.py` 按国家自动出本地语言关键词+城市轮换 → `maps_scrape.py` 抓取 → `classify_leads.py` 甄别真工厂+判配色/阻燃需求+7维预评分 → `import_leads.py` 多键去重入库 |
| [`references/browser-deep-dive.md`](references/browser-deep-dive.md) | **浏览器深挖实战手册（三层漏斗）**：用户 Chrome 自动连接、谷歌地图分片抓客户脚本 `tools/maps_scrape.py`、官网深挖脚本 `tools/site_deepdive.py`、品牌匹配防错配、官网打开率 ≥80% 验收、降级兜底 |
| [`references/market-priority-ranking.md`](references/market-priority-ranking.md) | 目标市场优先级排序（50 国，欧美日韩优先）：四档 Tier 分级、各国打法差异、切换规则 |
| [`references/company-profile.md`](references/company-profile.md) | **公司简介库（写开发信/开场白必用）**：真实公司信息、硬实力数据、实力点落位规则、多语言对照、签名模板 |
| [`references/whatsapp-sourcing.md`](references/whatsapp-sourcing.md) | **WhatsApp 号码获取 SOP**：六条找号渠道、置信度分级（高=官网自挂/中=手机号段）、各国渗透率与实测数据、`tools/find_whatsapp.py` 用法、验号与封号红线 |

## ⚠️ 重要规则

1. **绝不编造**：企业名称、网址、邮箱、电话、资质必须来自真实搜索来源；搜不到就写「待核实」，不要杜撰。
2. **开发信不发送**：所有开发信都是草稿，需人工审批后由你自行发送。本 Skill 不接任何邮箱授权、不调用发信 API、不做批量群发——**一键全发会触发 Gmail/企业邮风控（先垃圾箱、后限权），且欧盟 GDPR、加拿大 CASL 对未经同意的商业邮件有法律要求**。最省力的合规做法：`python tools/render_sendlist.py` 生成 Gmail 发信队列，点「用 Gmail 打开发送」→ 撰写窗口已填好收件人/主题/正文 → 人工确认后按发送。
3. **客户数据不出本机**：客户资料只保存在本地文件，不提交公开仓库。
4. **双通道 · 两种写法不能混**：**WhatsApp/Zalo/LINE/KakaoTalk 严格两句**（① 我是谁+做什么 ② 痛点判断+零成本提问），**邮件是一整封**（独立 `Subject:` 行 + 4 段正文 + 真实签名块）。英语发送版必写、中文参照版必配、当地语言为示例加分项（没把握就"英语 + 一句当地问候"，**绝不机翻长句**）。见 `references/outreach-templates.md` 2.4。
5. **来源可追溯**：每条企业信息都标注来源 URL，方便人工复核。
6. **A/B 级同等深挖**：A 级和 B 级客户享受完全同等的深挖待遇（官网深挖 + 决策人实名 + 社交双渠道必查〔按市场：WhatsApp/Zalo/KakaoTalk/LINE〕+ 完整联系方式），都全字段展示在 HTML 看板里；只有 C 级才降级为仅归档。见 `references/deep-dive-intelligence.md`。
7. **每天生成 HTML 日报**：每天跑完后，必须生成一份独立的 HTML 日报文件（`reports/YYYY-MM-DD-daily-report.html`），全量展示 A/B/C 排名、7 维分数条、逐维理由、A/B 级决策人与 WhatsApp/Zalo（分两行）、开场白一键复制。见 `references/automation-guide.md`。
8. **市场切换规则（不默认越南）**：欧美日韩等发达国家优先开发；当前市场「A 级客户已开发完 + B 级剩余 <10 个」就切换到下一个市场，从 50 国按优先级依次切换。**社交渠道按市场切换**：越南→Zalo、韩国→KakaoTalk、日本→LINE、泰国→LINE、欧美→WhatsApp/LinkedIn、中东·拉美→WhatsApp（29 市场逐条对照见 `outreach-templates.md` 第七章「全球触达矩阵」）。见 `references/automation-guide.md` 与 `references/market-priority-ranking.md`。
8.1 **双轨道轮换（2026-11-16 新增）**：`python tools/pick_market.py` 是唯一裁判——**周一~周四走 `main` 轨道**（按 priority 轮换，存量积压 ≥60 家且未联系 A 级 ≥10 就自动 `stocked` 跳过）；**周五走 `wa` 轨道＝WhatsApp 专项日**（印尼 → 印度 → 土耳其，按 `last_run` 最久远轮换）。周五核心 KPI 是「官网自挂 wa.me 的数量」，抓完必须跑 `find_whatsapp.py --crawl` 并把 WhatsApp 覆盖数写进日报。**别凭记忆挑市场，跑脚本取 `MARKET=` 那行。**
9. **社交媒体深挖（Facebook/LinkedIn）**：挖社交号先解析官网 `facebook.com`/`zalo.me`/`wa.me` 链接（最准）；缺官网链接时用 `site:facebook.com "本地语言公司名"`、`site:linkedin.com/company/ "公司名"` 定位官方主页；找采购决策人用 `"公司名" "procurement/supply chain/general manager"`（LinkedIn 只手动、不自动化）。完整关键词见 `references/multilingual-keywords.md` 第五章。
10. **开发信/开场白必须锚定官网产品（禁止群发腔）**：一律从 `references/company-profile.md` 取你自己的真实公司信息（公司名、署名、成立年份等硬实力数据，签名自动读 `tools/profile.json`）。**禁止出现 "ABC Masterbatch"、"David"、"david@abc.com"、"+86 138..." 之类占位符发给客户**。**更关键：A/B 级开发信与开场白必须出现对方官网上的真实产品/材质**（如 "saw you mold PC/ABS bezels for appliance OEMs"），只写 "plastic industry"、"engineering plastics" 这类通用词视为不合格、退回重写；拿不到官网信息则标注 `⚠️ 个性化降级`。写信前的官网 6 要素提取法与「官网发现→信里那句」映射表见 `references/outreach-templates.md` 第二章。**首次发信六条禁令（2026-11-16 新增，发信前必跑 `python tools/audit_outreach.py`，退出码 1＝有违规）**：① 不写一大段公司历史（身份段 1 句、≤2 行；第一段必须讲客户不讲自己）；② 不一上来强调便宜（前两段不出现 price/cheap/discount）；③ 不罗列十几个品类（只写他要的那 1 个）；④ 不追问每月采购多少吨（换成"给我树脂牌号和目标色"）；⑤ 不用群发腔（**判定标准：这句话换到任何一家公司名下都成立，就是群发腔**）；⑥ 无证据不声称 IATF 16949 / UL / RoHS / cable-grade（描述客户方的认证要求不算声称自己合规）。正反例对照见 `references/outreach-templates.md` 第 2.7 节。
11. **按 A/B/C 分层配关键词 + 双渠道搜索**：搜索不再"一把关键词扫天下"，而是**先预判客户价值层级，再用对应关键词精准捞取**——A 级用「高价值行业词 + 认证词 + 决策人词」精准狙击（工程塑料注塑/家电电子外壳/汽车内饰/线缆料）；B 级用「通用行业词 + 规模词 + 联系方式词」广撒网补候选；C 级用「排除词 + 负向信号词」快速排雷（剔除同行/设备商/回收商/贸易商/一次性打样）。两条渠道各配一套搜索规则：**谷歌地图**（多关键词 × 多城市分片抓本地实体厂）、**谷歌浏览器**（A/B 级官网深挖决策人 + `site:linkedin/company/` 社交定位）。完整关键词库见 `references/tiered-keywords.md`。
12. **地图获客走流水线，不手工拼关键词**：`kwgen.py`（按国家自动出本地语言词 + 城市轮换 + A/B 行业轮转）→ `maps_scrape.py` → `classify_leads.py`（强排除同行/回收/设备、弱排除贸易、品类误判可用公司名工艺词推翻、判配色/阻燃需求、7维预评分）→ `import_leads.py`（官网域名/邮箱域名/电话尾号/公司名模糊 四键去重，只补空不覆盖）。**绝不手工放宽甄别标准凑 30 家**，凑不满就扩城市/扩行业。完整说明见 `references/maps-keyword-system.md`。
13. **线索池 21 列字段是硬规范，`跟进状态` 必须维护**：总池与当日 CSV 的基础字段必须完全一致（21 列，见 `automation-guide.md`「入库前必做」），入库前必跑 `python tools/schema_check.py`。**`跟进状态`（未联系/已发信/已回复/已报价/已寄样/成交/无效）不是可选项**——它决定了市场切换能否判定：如果所有线索都是`未联系`，那"这个市场开发完了吗"这个问题永远无解，市场会永久卡在同一个国家。**每天开跑先算「该市场未联系 A 级 N 家」并写进日报头部**：池子只进不出等于零。
14. **人工跟进记录是触达的唯一入口，两条路径任选其一（别同时用）**：
    - **A｜跟进台页面（推荐，2026-11-16 起以云端为准）**：资料库页面 `customer-followup-desk`（https://www.workbuddy.cn/space/d/BAvojLbnXjIehf8rvQ3qdE）——一次一家、一键复制 WhatsApp 两句/整封邮件、标状态、`导出进度` 得 `跟进进度-YYYY-MM-DD.csv`；回写用 `python tools/sync_followup.py --from-csv <该csv>`。**本地 `reports/customer-followup-desk.html` 只是 `tools/build_followup_html.py` 的中间产物，不是交付物**：任何改版一律直接改云端页面（编辑事务：下载云端产物 → 改 → 提交新版本），改完不再回传本地文件给用户。两条禁忌：① 不要重排 `r`（行号）字段——页面进度存 `localStorage` 的键是 `r`，重排会让 198 家的勾选状态错位；② 不要换页面链接（`/space/d/` 与发布链接 `workbuddy.link` 不同源，进度不互通）。
    - **B｜Excel 台账**：`客户跟进表.xlsx`（`跟进台账` 一条触达一行，`客户总表` 198 家 + 公式）；回写用 `python tools/sync_followup.py`
    AI **只读不写**这两份人工文件；开跑第一步先预演同步、必要时 `--commit`（自动备份 → schema_check → 失败回滚），**再算市场切换条件**——否则算的是旧状态。见 `references/automation-guide.md`「人工跟进表」。
15. **WhatsApp 号只从客户公开处取，且必须分置信度**：`python tools/find_whatsapp.py --infer`（号段推断）/ `--crawl`（抓官网 wa.me）→ `python tools/render_wa_worklist.py` 出点验清单。**官网自挂 wa.me＝高置信可直接发；号段像手机＝中置信必须点链接验；没证据就不写库、不编号码**。禁止买号、群加、批量导通讯录（封号主因）。**先看市场再决定投不投**：越南主通道是 Zalo（实测 24 个官网：Zalo 50% / WhatsApp 17%），美国 B2B 几乎不用 WhatsApp；WhatsApp 富矿是印尼/印度/巴西/土耳其/中东。见 `references/whatsapp-sourcing.md`。
