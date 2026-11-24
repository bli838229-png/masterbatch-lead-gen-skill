# Google Maps 自动获客体系（关键词库 → 工厂甄别 → 入库）

> 这不是一张关键词表，而是一条**可日复一日运行的流水线**：
> `关键词引擎` 按国家自动出本地语言词 → `地图抓取` 拿公司名/电话/地址 → `甄别器` 剔除贸易商/模具厂/回收厂并判断母粒需求 → `入库器` 多键去重合并进客户库。
>
> 四个环节各有独立命令，可单跑、可串跑。**加新市场只改数据文件，不改代码。**

---

## 一、体系总览

| 环节 | 工具 | 输入 | 输出 |
|---|---|---|---|
| ① 关键词 | `tools/kwgen.py` + `tools/data/map_keywords.json` | 国家 / 行业 / 层级 | 本地语言查询 + 可直接执行的命令 |
| ② 抓取 | `tools/maps_scrape.py` | region + 查询串 | `leads/<日期>-map-<地区>.json` |
| ③ 甄别 | `tools/classify_leads.py` | ①的 json（+深挖 json） | `-candidates.csv` / `.evidence.json` / `-rejected.csv` / `-unsure.csv` |
| ④ 入库 | `tools/import_leads.py` | candidates.csv | 合并进 `master-lead-pool.csv`（21 列） |

深挖（官网/决策人/社交）仍按 `browser-deep-dive.md` 与 `deep-dive-intelligence.md` 走，**甄别器不替代深挖，只决定「谁值得深挖」**。

---

## 二、关键词引擎：按国家自动生成

### 2.1 数据层结构（`tools/data/map_keywords.json`）

- `markets`：市场 → `{country, lang[], cities[]}`。中国别名（美国/德国/日本…）与英文国名都可传参。
- `languages`：语种 → `{label, terms{行业键: 本地语言词}}`。目前覆盖 **18 语种**。
- `industries`：行业 → `{label, tier, color_need, fr_need, note}`。`tier=A` 表示高价值刚需（汽车/电缆/家电/医疗）。
- `negative_terms`：排除词总表（供甄别器使用，见第四节）。

### 2.2 命令

```bash
# 看支持哪些市场
python tools/kwgen.py --list

# A 级行业（汽车/电缆/家电/医疗）× 自动挑 4 个没跑过的城市
python tools/kwgen.py --country 美国 --tier A --cities 4 --max-queries 6

# 指定城市 + 指定行业
python tools/kwgen.py --country 德国 --city "Stuttgart" --industry inj,auto

# 只输出可直接执行的命令
python tools/kwgen.py --country 日本 --tier A --cities 2 --cmd
```

### 2.3 三条内置规则（都是踩过坑加的）

1. **城市轮换**：记账在 `logs/_kw_rotation.json`。同一市场连续跑会自动换城，一轮跑完才重置——避免天天搜同一批厂（美国 15 城、德国 10 城、日本 8 城…）。
2. **均衡分配**：2 城 × 4 行业 + 上限 6 条 → 每城 3 条，不会只覆盖首城。
3. **行业轮转**：按已用城市数偏移行业顺序——否则 `medical` 这种排在末位的行业永远排不进前 6 条。

> 每条查询都**自带城市名**（`injection molding Cleveland OH`），避免全国泛搜出一堆无关结果。

---

## 三、抓取：多关键词分片

```bash
python tools/maps_scrape.py "United States" "automotive plastic parts Cleveland OH,wire and cable manufacturer Cleveland OH"
```

- 一次浏览器会话跑完所有关键词，只付一次连接开销
- 输出 `name / tel / addr / raw / src_query`，按公司名归一化去重
- `raw` 里含 Google 品类词（`注塑成型服务`/`塑料制品供应商`/`模具制造商`）和评论数 `4.7(128)`——**这是甄别器最重要的输入**

---

## 四、工厂甄别：把「卖料的」和「用料的」分开

地图列表里混着大量非目标：色母粒同行、模具厂、设备商、回收厂、贸易商。甄别器按三级处理：

### 4.1 强排除（命中即剔除）

| 类别 | 命中词示例 |
|---|---|
| 同行（色母粒/色粉/助剂） | masterbatch、色母、母粒、pigment、颜料、compounding |
| 回收/再生料 | recycling、回收、再生料、リサイクル、재활용 |
| 设备/模具制造 | machine、注塑机、模具、mold maker、tool & die、금형 |
| 非塑料（金属/玻璃/纸） | metal stamping、steel fabrication、glass manufacturer |

### 4.2 弱排除（只在**没有任何工艺证据**时才剔除）

`distributor / wholesale / supplier / 供应商 / 经销商 / 贸易` ——
真工厂的描述里也会出现 supplier，所以**有工艺词就放行**。

### 4.3 待确认（不硬判，交人工/深挖）

品类只写「制造商 / manufacturer」，既无工艺词也无材质词 → 进 `-unsure.csv`，不直接扔掉，也不混进合格池。

### 4.4 品类误判纠正（实测踩到的坑）

Google 的品类会错标，**公司名本身是工艺证据时可以推翻品类**：

- `Rotocast Technologies` 品类写作「模具制造商」，但 Rotocast=滚塑 → 判定为**滚塑厂**，保留
- `Ohio Precision Molding` 名称只有 `Molding`（不是 `injection molding`）→ 必须把 `molding/moulding/molder` 全部收进词典，否则整类公司被误杀

> 这条规则的价值：**宁可用名字救回来，也不用品类错杀**。误杀是静默损失，比多留一家脏数据贵得多。

---

## 五、母粒需求判断（AI 判「要不要色母/阻燃」）

按行业映射，每个判断都有可追溯依据，不猜：

| 行业 | 配色需求 | 阻燃需求 | 判断理由 |
|---|---|---|---|
| 电线电缆 | 3 | 3 | 芯线分色 + 护套 UL94/VW-1，**双刚需** |
| 家电/电子外壳 | 3 | 3 | UL94 V-0 外壳 + 高光配色 |
| 汽车塑料件 | 3 | 2 | 内饰低 ΔE + EV 件阻燃 |
| 医疗塑料件 | 2 | 3 | 医用级色母 + 阻燃 |
| 型材/异型材 | 3 | 2 | 户外耐候配色 |
| 注塑/挤出 | 3 | 2 | 通用换色频繁 |
| 吹膜/薄膜 | 3 | 1 | 薄膜着色 + 功能母粒 |
| 管材管件 | 2 | 2 | 色相稳定 + 部分阻燃 |
| 吹塑中空 | 2 | 1 | HDPE 着色 |
| 滚塑 | 3 | 1 | 油箱水箱配色 |
| 塑料包装 | 2 | 1 | 食品接触级配色 |

**需求强度分** = `(配色+阻燃)/6×5`，双刚需（6/6）自动得 5 分。

---

## 六、7 维预评分与分级（缺数据就承认缺数据）

| 维度 | 地图阶段怎么来 | 缺数据时 |
|---|---|---|
| 产品匹配度 | 行业 tier：A=5 / B=4 / 未确认=2 | 标「行业未确认」 |
| 需求强度 | 配色+阻燃映射 | 标「需求未确认」 |
| 规模匹配度 | **评论数代理**：≥50→5、≥10→4、≥3→3、<3→2；有 2 个以上官网产品再 +1 | 无评论数→3，标「规模待核实」 |
| 决策人可触达性 | 电话+1、官网+1（地图无实名，上限 3） | 标「无联系方式」 |
| 联系渠道质量 | 电话/官网/邮箱/社交组合 1-5 | 标「社交号未验证」 |
| 地域适配 | 城市命中市场清单=4，否则 3 | — |
| 采购周期 | 双刚需→4，单需求→3 | 标「采购周期未知」 |

**分级**（预评分，深挖后可升级）：

- **A**：总分 ≥26 且 匹配=5 且 需求≥4 且 渠道≥3 且 缺口≤3
- **B**：总分 ≥17
- **C**：其余

> ⚠️ 这是**预评分**。地图阶段拿不到员工数/决策人实名，所以 A 级也必须在当天走完深挖才算真 A。**绝不允许把「评论数多」当成「规模大」写进跟进记录**——它只是活跃度代理。

---

## 七、每日 SOP（约 20 分钟出一条 30 家合格线索）

```bash
cd D:\masterbatch-leadgen

# 1) 出词（自动换城）
python tools/kwgen.py --country 美国 --tier all --cities 3 --max-queries 6 --cmd
#    → 复制输出的命令执行

# 2) 抓取（浏览器必须先连上用户 Chrome）
python tools/maps_scrape.py "United States" "<上一步的查询串>"

# 3) 深挖（A/B 级官网 + 产品页 + 社交链接）
python tools/site_deepdive.py "leads/2026-11-16-map-Ohio.json" 40

# 4) 甄别（合入深挖数据，剔除同行/贸易/设备，判母粒需求）
python tools/classify_leads.py leads/2026-11-16-map-Ohio.json --country 美国 \
    --deepdive leads/2026-11-16-deepdive-Ohio.json

# 5) 入库（先预演，再 commit）
python tools/import_leads.py leads/2026-11-16-candidates-Ohio.csv
python tools/import_leads.py leads/2026-11-16-candidates-Ohio.csv --commit
```

**凑不满 30 家怎么办**：`classify` 会明确提示「合格仅 N 家」。此时按顺序做三件事——
① 加城市（`--cities 6`）② 降层级补 B 级行业（`--tier all`）③ 换邻近城市群。
**不允许为了让数字好看而放宽甄别标准**，也不允许把 `-unsure.csv` 里的公司直接当合格客户入池。

---

## 八、红线

1. **每天 30 家真实数据**是下限，不是上限；但**凑数不能靠放水**，只能靠扩城市/扩行业。
2. **不编造**：地图没有的字段留空；判不出行业就标「待确认」；社交号只标三态（✅/⚠️/—），不编号码。
3. **社交渠道按市场**：越南 Zalo、韩国 KakaoTalk、日本/泰国 LINE、其余 WhatsApp——不用的渠道填「该市场不使用—」。
4. **只存本地**：客户数据只在工作目录 + 桌面当天文件夹，不进任何公开渠道。
5. **AI 只备料不发送**：所有邮件/WhatsApp 由人工发送。
6. **官网必须是客户自有域名**：目录站/数据商（thomasnet、rocketreach、zoominfo…）会被 `schema_check.py` 拦截。

---

## 九、扩充指南

| 要加什么 | 改哪里 | 怎么改 |
|---|---|---|
| 新国家 | `map_keywords.json` → `markets` | 加 `{country, lang, cities[]}`，城市填 5-8 个工业城市 |
| 新语种 | `map_keywords.json` → `languages` | 加 11 个行业词（缺的行业键会自动跳过） |
| 新行业 | `map_keywords.json` → `industries` + 各语种 `terms` | 定 tier 与配色/阻燃需求，再加本地语言词 |
| 新排除词 | `classify_leads.py` → `STRONG_NEG` / `WEAK_NEG` | 强排除=一定不是客户；弱排除=没工艺证据时才剔 |

> 加完跑一遍 `python tools/kwgen.py --country <新国家> --cities 2` 验证不报错即可。

---

## 十、已知局限（如实记录，不粉饰）

1. **地图不给员工数**：规模只能用评论数代理，真正的规模要在深挖时从官网「About/工厂面积/员工数」补。
2. **地图不给官网**：官网靠 `site_deepdive.py` 补，补不到的 `官网` 留空，**绝不填目录站凑数**。
3. **评论数会误伤**：老厂可能只有 2 条评论（客户不来点评），所以评论数只影响规模分，**不参与剔除决策**。
4. **品类词依赖界面语言**：Google 地图界面是中文时品类返回中文（`注塑成型服务`），英文界面返回英文——词典已双语覆盖，换语言界面不影响。
5. **滚塑/热成型等小众工艺**词典仍在扩充，遇到未覆盖工艺会进「待确认」而不是被误杀。
