# 浏览器深挖实战手册（Chrome 实时抓取官网/地图/决策人）

本文档把「客户深挖」从"搜索关键词静态补信息"升级为**开真实 Chrome 实时抓谷歌地图、点官网、抓联系页、挖决策人**。

> 🔴 **核心原则**：浏览器深挖是**第一优先**手段（信息最硬、最新、可溯源），地图负责"发现客户"，官网深挖负责"拿到联系方式"，搜索只作兜底。
> 🔴 **红线**：官网打不开/未确认的一律标「待核实⚠️」，**宁留白不编造**。

---

## 〇、三层漏斗（每日获客的标准打法）

```
① 谷歌地图（发现客户）
   → tools/maps_scrape.py 多关键词分片搜索
   → 拿到：公司名 + 电话 + 地址（每个查询 10-20 家，4-6 组凑满 30+）
        ↓
② 搜索补官网（定位门户）
   → 内置在 site_deepdive.py：搜「公司名 + official website」
   → 品牌名匹配打分挑官网（防张冠李戴）
        ↓
③ 浏览器深挖官网（拿联系方式）
   → tools/site_deepdive.py 逐个打开官网
   → 拿到：真实官网 URL + 邮箱 + 电话 + footer 社交链接 + 决策人
```

---

## 一、主通道：用户自己的 Chrome（唯一正确姿势）

**主通道 = 用户本机正在运行的 Chrome**，通过 `browser-use` **自动发现**，**不需要也不要用 9222/9223 固定端口**，更不要自建 headless 浏览器。

```bash
BU_NAME=mainchk browser-use <<'PY'
print(page_info().get("url"))
PY
```

**关键点**：
- **不要设 `BU_CDP_URL`**。设了反而连不上（那是指向特定调试端口的）。
- 用固定会话名 `BU_NAME=mainchk`，让 daemon 复用同一条连接、保持标签状态。
- 首次连接 Chrome 可能弹「是否允许远程调试（Allow remote debugging）」，**让用户点一次 Allow** 即可，之后自动复用。
- 历史教训（2026-11-16）：自建的 9222 启动时带 `--no-proxy-server`，导致 Google 全域 `ERR_CONNECTION_TIMED_OUT`；而用户自己的 Chrome 走系统代理，Google 搜索/地图全通。**所以必须用用户的 Chrome。**

### 连接自检（每次跑前一行）

```bash
BU_NAME=mainchk browser-use <<'PY'
print("OK:", page_info().get("url")[:80])
PY
```

看到 `OK: ...` 即通道正常；若报 `remote-debugging-setup`，让用户在弹出的 Chrome 提示里点 **Allow**，或手动打开 `chrome://inspect/#remote-debugging` 勾选允许。

---

## 二、第 ① 层：谷歌地图抓客户

```bash
cd D:\masterbatch-leadgen
python tools/maps_scrape.py "Ohio" "injection molding Cleveland,plastic extrusion Columbus,blow molding Cincinnati,custom compound Toledo"
```

- **参数**：`地区` + `逗号分隔的关键词列表`（建议 4-6 组，含城市名，结果差异更大）。
- **原理**：Maps 的 feed 是虚拟列表、滚动不灵，所以用「多关键词分片搜索」替代滚动——每个查询抓 10-20 家，合并去重。
- **输出**：`leads/<日期>-map-<地区>.json`（name / tel / addr / raw）。
- **实测（2026-11-16）**：3 组关键词 → 26 家真实企业，电话地址齐全。

> ⚠️ 地图列表页**不给官网链接**（"网站"是 JS 按钮），所以官网必须靠第 ② 层搜索补。

---

## 三、第 ② + ③ 层：官网深挖

```bash
python tools/site_deepdive.py "leads/2026-11-16-map-Ohio.json" 40
```

- **每家流程**：Google 搜「公司名 + official website」→ 品牌名匹配挑官网 → 打开官网 → 抓正文/邮箱/电话/footer 社交链接。
- **品牌匹配打分**（防张冠李戴）：公司名压缩串 vs 域名主体，`前缀5字命中=2分 / 前缀4字=1分 / 0分=不采用`。全不命中就返回空、标「待核实」，**绝不硬凑**。
- **输出**：`leads/<日期>-deepdive-<地区>.json`（site / emails / tels / socials / snippet / site_candidates / status）。
- **实测（2026-11-16）**：6/6 全部命中正确官网，4 家挖到邮箱，2 家挖到社交链接。

**status 含义**：
| status | 含义 | 处理 |
|---|---|---|
| `ok` | 官网打开成功并抓到信息 | 直接入库 |
| `site-unverified` | 有候选但品牌不匹配 | 标「待核实⚠️」+ 保留 candidates 供人工点开确认 |
| `no-site` | 搜不到任何候选 | 标「暂无官网」，靠电话/地图页 |
| `page-fail` | 官网打不开（反爬/证书） | 降级搜索补 |

---

## 四、深挖执行序列（每家 A/B 级客户）

```
① 打开官网首页 → 抓 title + body（业务/产品线/认证/规模）
② 解析 footer 社交链接：facebook.com / zalo.me / wa.me / linkedin.com
③ 打开联系页（/contact、/contact-us、/about、/team；越南加 /lien-he）→ 抓邮箱/电话
④ 提取决策人：body 里搜 procurement / purchasing / sales / general manager / CEO / owner
⑤ 官网无决策人 → 搜索兜底：site:linkedin.com/company/ "公司名"
⑥ 每条信息标来源，抓不到写「待核实⚠️」
```

**硬性验收（写进日报和日志）**：A/B 级客户**官网打开率 ≥80%**；达不到要继续补抓，不达标不算完成。

---

## 五、降级兜底

以下情况**立即降级 WebSearch**，不要死磕浏览器：

1. 官网打不开 / SSL 报错 / Cloudflare 验证页
2. 联系页需登录（LinkedIn 决策人、部分 B2B 目录）
3. 连续 2 次页面读取超时
4. `js()` 返回空（纯 JS 空壳页）

降级关键词：
- 决策人：`"公司名" "procurement"` / `"公司名" "general manager"`
- 社交主页：`site:facebook.com "公司本地语言名"` / `site:linkedin.com/company/ "公司名"`
- 联系邮箱：`"公司名" contact email`

---

## 六、合规红线

1. **只用公开信息**：官网、联系页、公开目录、公开新闻稿；不爬非公开数据、不绕过登录墙。
2. **LinkedIn 只手动搜**：AI 只整理"该联系谁 + 开场白"，绝不自动化加好友/私信。
3. **个人隐私克制**：只收集商务相关的公开决策人信息。
4. **事实可溯源**：每条信息标来源，无法核实的写「待核实」，**宁留白不编造**。
5. **发送永远人工**：深挖只做"备料"，绝不通过浏览器自动发信/加好友。
6. **地图合规**：用 Google Maps 正常搜索页（等同人工浏览），不做高频轰炸式抓取，避免触发验证码。

---

## 七、排错速查

| 现象 | 原因 | 解决 |
|---|---|---|
| `remote-debugging-setup: none of your browsers...` | 带了错误的 `BU_CDP_URL`，或 Chrome 未授权 | 去掉 `BU_CDP_URL`，只用 `BU_NAME=mainchk`；让用户在 Chrome 提示里点 Allow |
| `Chrome is asking "Allow remote debugging?"` | 首次连接需授权 | 用户点 Allow 一次即可，后续复用 |
| Google 页面 `ERR_CONNECTION_TIMED_OUT` | 用了带 `--no-proxy-server` 的自建 Chrome | 改用用户自己的 Chrome（走系统代理） |
| `Runtime.evaluate timed out` | 页面太重/后台标签不渲染 | 加长等待，或 `activate_tab(current_tab())` |
| 地图只出 10 家就没了 | feed 虚拟列表不滚动 | 换更多关键词/城市分片，别死磕滚动 |
| 官网张冠李戴（A公司指到B网站） | 品牌匹配缺失 | 已内置打分；`site-unverified` 的必须人工确认 |
| `open`/`state`/`close` 报 "removed" | 用了 1.0 之前的旧语法 | 改用 heredoc 原生 Python（见第一节） |
