# Contributing

感谢你有兴趣为 Masterbatch Lead Gen 做贡献！🎨

这是一个「方法论 + 提示词 + 脚本工具链」的获客 Skill，欢迎各种形式的贡献，尤其是：

- **新的本地语言**：新增目标市场的获客关键词、开发信模板（越南语、土耳其语、西班牙语、阿拉伯语等）
- **新的开发信模板**：分行业、分场景的差异化文案
- **脚本改进**：`tools/` 下流水线脚本的 bug 修复与功能增强
- **文档**：references/ 深度指南的补充与勘误

## 贡献前必读

1. **绝不提交任何客户真实数据**。企业名单、邮箱、电话、跟进记录等一律不能出现在 PR 里——用占位符或示例数据代替。
2. **绝不提交密钥**。`smtp_config.json`、`tools/profile.json` 含个人身份/授权码，已在 `.gitignore` 中排除，请勿强制添加。
3. **遵守红线**（见 `SKILL.md`「重要规则」与 `references/safety-compliance.md`）：
   - 绝不编造企业信息，来源可追溯
   - 开发信只生成草稿，不自动化发送
   - 尊重 GDPR / CASL 等法规

## 如何贡献

1. Fork 本仓库，克隆到本地。
2. 创建特性分支：`git checkout -b feat/your-feature`。
3. 修改后本地自测：`python init_workspace.py D:\test-workspace` 初始化一个干净工作目录跑通流程。
4. 提交 PR，说明改动动机与测试情况。

## 代码风格

- Python 3.8+，标准库优先（脚本尽量零第三方依赖）。
- 中文注释与文档统一 UTF-8。
- CSV 以 `utf-8-sig` 读写（兼容 Excel）。

## 目录约定

- `tools/` 是流水线脚本的唯一权威副本，修改后请同步更新 `README.md` 的「Repository layout」。
- 关键词数据在 `tools/data/map_keywords.json`。
- 新模板放进 `templates/` 或 `references/`。

欢迎提交 Issue 讨论新市场的获客打法。一起把外贸获客这件事做得更漂亮！
