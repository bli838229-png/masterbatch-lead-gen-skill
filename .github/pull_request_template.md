## 感谢你的贡献 🙏

提交 PR 前，请确认：

- [ ] 已阅读 [CONTRIBUTING.md](CONTRIBUTING.md)
- [ ] 代码/文档改动与项目风格一致
- [ ] 未包含任何真实客户数据、密钥或个人信息（邮箱、手机号、公司客户名单等）
- [ ] 如涉及 `profile.json` / `smtp_config.json`，只改动 `*.example.*` 模板，不提交真实值
- [ ] 已本地测试通过（Python 脚本 `python -c "import ast; ast.parse(open('xxx.py').read())"` 语法检查）

## 改动说明

- **类型**：bug 修复 / 新功能 / 文档 / 其他
- **改动内容**：
- **测试情况**：

## 安全检查（必填）

请确认本次改动**没有**引入真实客户数据或敏感信息：
- [ ] 确认无泄露
