# 海关数据搜客户（免费资源实战）

> 目标：通过海关进出口数据，找到**正在实际进口色母粒 / 母粒 / 颜料的下游买家**。这类客户的采购意向最真实，比盲搜地图/目录命中率高得多。

## 一、免费资源清单（按用途分两类）

### 第一类：能查到「具体买家名字」的（捞名单用）

| 资源 | 覆盖范围 | 能查什么 | 关键局限 |
|---|---|---|---|
| **ImportYeti** ⭐首选 | 美国海运提单（7000万+条，免费免注册，每日更新） | 按**产品词**搜供应商 → 点进供应商看**美国客户** + 柜量 | 仅美国、仅海运、30-60天延迟、免费版只显示前几条 |
| **Volza** | 全球 200+ 国家贸易数据 | 按 **HS 编码**看分国买家分布 + 顶部买家摘要 | 免费仅摘要（具体买家名+联系方式付费）；有 Cloudflare 风控，自动化访问不稳定 |

### 第二类：只能查「市场大盘」的（定方向用，无具体公司）

| 资源 | 能查什么 | 用途 |
|---|---|---|
| **UN Comtrade** | 全球进出口统计（按国家/HS编码/时间） | 判断某市场色母粒进口规模、贸易流向 |
| **USITC DataWeb** | 美国进口商品统计（更细的编码+贸易伙伴） | 判断美国从哪些国家进口、量级 |

> 🔑 **核心结论（其他国家怎么搜）**：
> - **美国**：ImportYeti 免费全量，能拿到具体买家名单（唯一稳定免费的国家）。
> - **其他国家**（越南/印尼/土耳其等）：**免费只能靠 Volza 看「买家摘要 + 国家分布」**（具体名单+联系方式付费），且 Volza 有 Cloudflare 验证墙，自动化抓取不稳定，建议**人工登录 Volza 查**。
> - UN Comtrade / USITC 只用于「判断这个市场值不值得投入」，不能拿到具体公司。

### 色母粒/着色剂相关 HS 编码（Volza / UN Comtrade 用）

```
3206   色母粒/着色剂总类
320611 钛白粉（二氧化钛）
320619 其他着色剂/色母粒
320649 其他色母粒/无机着色
```

**用法**：`python tools/customs_scrape.py 3206 --source volza` 抓 Volza 免费摘要；UN Comtrade 用同样的 HS 编码查国家进出口量。

---

## 二、ImportYeti 实战（主战场）

**网址**：https://www.importyeti.com

### 三种搜索路径（按命中率从高到低）

> ⚠️ **重要（实测结论）**：ImportYeti 按产品词搜索返回的是「**供应商（出口方）**」，不是美国进口商。搜 `color masterbatch` 得到的是中福/智合/东莞智和等**中国色母粒厂**，而不是美国买家。要找美国买家，必须「**点进供应商页 → 抓『客户』栏**」。

**路径 1 · 产品词 → 供应商 → 反查客户（首选，脚本已自动化）**
1. 搜产品词 `color masterbatch` / `colorant` / `color concentrate` 等
2. 结果列出**该产品的供应商**（中国/全球色母粒厂）
3. 点进每家供应商 → 看「客户」栏 → 得到**从它进货的美国进口商名单**
- 例：搜 `color masterbatch` → 点「中福塑料色母粒」→ 客户栏有 `Verdeco Plastics LLC`（真实美国买家）
- 脚本 `tools/customs_scrape.py` 已把这两步自动化

**路径 2 · 供应商反查（挖竞品的客户，最高效）**
- 直接输入已知竞品中国工厂名（如 `zhihe masterbatch`），跳进公司页反查它的**美国客户**
- 命中率最高，直接拿到「已经在用中国色母粒」的买家

**路径 3 · 客户验证（已有目标名单时）**
- 拿到展会名片/领英线索后，输入公司名，查验它**是否真进口 + 供应商是谁**

### 搜色母粒客户的产品词库

```
color masterbatch          # 彩色母粒
colorant                   # 着色剂（宽泛）
color concentrate          # 色浓缩物（美国常用叫法）
white masterbatch          # 白母粒
black masterbatch          # 黑母粒
flame retardant masterbatch # 阻燃母粒
additive masterbatch       # 功能母粒
pigment dispersion         # 颜料分散体
plastic colorant           # 塑料着色剂
```

### 抓到后的核验流程（重要，别直接当客户发）

0. **还原英文名**：ImportYeti 页面会把公司名机翻成中文（如「科技金融前沿」= `Techfin Frontier LLC`）。点进 `/company/<slug>` 页看**提单原文**，或直接看页面下方「近期海运货物」里的英文公司名，用英文名做后续核验。
1. **官网核验**：提单上的名字常是贸易公司/物流抬头/集团子公司，打开官网确认「产品 + 渠道匹配」
2. **LinkedIn 找人**：搜「公司名 + purchasing / sourcing / supply chain」，找采购负责人
3. **补邮箱**：官网 Contact 页 / Hunter / Apollo 补邮箱，验证后再写开发信
4. **排除**：货代、报关行、纯贸易中间商、同名公司

> ⚠️ **开发信不要提海关数据**：直接写「我注意到贵司有 XX 产品线」，不要把提单/供应商/数量摆进邮件，会让客户觉得被监视。海关数据只用来**帮你判断**，不写进开发信。

---

## 三、自动化脚本

```bash
cd D:\masterbatch-leadgen
# 按产品词搜：①搜供应商 ②进供应商页抓美国客户（走你自己的 Chrome，首次需点 Allow）
python tools/customs_scrape.py "color masterbatch,colorant,color concentrate"
# 控制反查的供应商数量（默认 8 家，免费版够用，避免超时）
CUSTOMS_MAX_SUPPLIERS=5 python tools/customs_scrape.py "color masterbatch"
```

- 输出：`leads/<日期>-customs-<词>.json`，结构 `[{supplier, buyers:[{name, shipments}]}]`
- 原理：browser-use 走用户 Chrome 打开 ImportYeti，`new_tab` 搜索供应商 → 逐家进公司页抓「客户」栏
- ⚠️ 已实测打通（2026-11-23）：`color masterbatch` → 10 家供应商 → 抓到 `Verdeco Plastics LLC`、`Alpla Caribe Inc`、`Sajiplast SA` 等真实买家
- ⚠️ ImportYeti 是 JS 渲染 SPA，若抓不到，说明页面结构变了或 Chrome 未授权 Allow，需人工登录后重试

**抓到进口商后的下一步**：对重点进口商跑 `site_deepdive.py` 补官网/邮箱/联系人 → 走线索评分（第 6 步）→ 开发信（第 7 步）。

---

## 三·五、多渠道发现 + 同步验证（一键编排器）

把「海关 / 谷歌地图 / 浏览器搜索」三个免费渠道合并，抓到的买家名统一送去补全**官网 + 邮箱 + WhatsApp + 联系人**。

```bash
cd D:\masterbatch-leadgen
# 三渠道合并 + 同步验证补四要素（走你自己的 Chrome）
python tools/discover.py "injection molding,color masterbatch" --market 美国 --channels customs,maps,web --verify

# 只看单一渠道 / 不验证（先抓名单）
python tools/discover.py "color masterbatch" --market 美国 --channels customs
python tools/discover.py "injection molding" --market 德国 --channels maps,web --limit 20 --verify
```

- **渠道**：`customs`（ImportYeti 美国）、`maps`（Google Maps 多关键词）、`web`（Google 搜企业目录/黄页/展会名录）
- **同步验证（--verify）**：对合并去重后的买家逐个 ①搜官网 ②抓官网正文→邮箱+社交链接（含 wa.me）③挖 WhatsApp（find_whatsapp 号段规则）
- **输出**：`leads/<日期>-discover-<市场>.json`，每家含 `site/emails/socials/whatsapp/contact`
- ⚠️ maps / web 渠道需要 `--market`（地区）；customs 只覆盖美国

**补全四要素的落点**：
| 要素 | 工具 | 方式 |
|---|---|---|
| 官网 | `site_deepdive.find_site + pick_site` | Google 搜「公司名+官网」，按品牌名打分选真官网 |
| 邮箱 | `site_deepdive.dig` | 抓官网正文正则提取邮箱 |
| WhatsApp | `find_whatsapp.sniff` | 抓官网 wa.me 链接 + 各国手机号段规则 |
| 联系人 | `site_deepdive.dig` 的 socials | 抓 LinkedIn 链接作为「找采购负责人」入口 |

---

## 四、与其他数据源的关系（避免重复）

| 数据源 | 给什么 | 定位 |
|---|---|---|
| 谷歌地图 | 本地塑料加工厂（名称/电话/地址） | 生产型客户，按地区找 |
| 联网搜索/目录 | B2B 目录、展会名录 | 补充渠道 |
| **海关数据（本环节）** | **真实进口商 + 采购量证据** | **高意向买家，采购真实性最强** |

三个来源**互补去重**：地图/搜索找「生产的」，海关数据找「在进口的」，同一家公司可能同时命中，入库时按四键去重（官网/邮箱/电话/公司名）合并。

---

## 五、边界与合规

1. ImportYeti 数据**仅美国海运**，空运/陆运/其他国家覆盖不到；没有记录≠没有业务。
2. 海关数据**不能当信用评分**，也不替代制裁名单筛查。
3. 提单上的收货人可能是中间商，务必官网/LinkedIn 核验主体。
4. 不批量抓取/自动化群发（沿用 skill 的「AI 备料 + 人点发送」原则）。
