# 06 · 提交状态与操作

## 当前状态

- 题号：**3 · 企业知识问答 Agent**。
- 已完成：本地代码、环境示例、45 项测试、11 条离线与 11 条真实 DeepSeek 运行记录、五份必需文档、离线 CI 配置。真实记录首轮 10/11，修正过窄断言后原样重评 11/11。
- 已推送：`main` 分支；本地 `origin` 指向下列仓库。
- GitHub URL：[https://github.com/gehengxuan/xiaoyinbishi](https://github.com/gehengxuan/xiaoyinbishi)。
- 贡献与用时：见 [AI 协作记录](04-ai-usage.md)和[开发时段记录](work-log.json)，明确具体 AI 使用范围与统计口径。
- 最终 SHA：读取 `git rev-parse HEAD` 并与远端 main 对照；不要使用旧 SHA 代替最终提交。

## 复核运行与贡献记录

本次真实验收已经完成，见 [review.md](../examples/live/review.md)。如需重新运行，请使用新目录保留已提交记录；当前 macOS Python 使用系统 CA：

```bash
SSL_CERT_FILE=/etc/ssl/cert.pem PYTHONPATH=src python3 scripts/evaluate.py \
  --provider deepseek --env-file .env --output-dir examples/live-new
```

真实运行结果、失败和限制已记录于 `03-evaluation.md`；项目贡献、AI 参与范围与关键取舍见 `04-ai-usage.md`、`05-retrospective.md`。后续新增修改、验证或学习时间可继续追加，保持陈述与实际记录一致。源码和 Trace 的讲解入口见 [07-interview-walkthrough.md](07-interview-walkthrough.md)。

## GitHub 提交

已按用户指定命令配置远端、将分支重命名为 main 并完成推送。后续如有更改，应先提交，再推送并核对 SHA：

```bash
git status --short
git check-ignore .env
git remote -v
git push origin main
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

本地 `.env` 必须继续被忽略，不得为了提交而强制添加。私有仓库需要按试卷要求给指定评审账号读取权限；评审账号尚未提供，当前没有修改任何账号权限。

最终提交文本：题号 3、真实 GitHub URL、上述命令得到的完整 SHA。代码、资料与所有运行记录应在同一仓库内。
