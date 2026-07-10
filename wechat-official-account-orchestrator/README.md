# WeChat Official Account Orchestrator

`wechat-official-account-orchestrator` 是一个独立的微信公众号总控 skill，默认面向内部科技安全公众号，用于把科技、安全、AI Agent、产品类内容从选题、资料台账、成稿、审稿、排版预览推进到草稿箱 dry-run。

它不是普通写作助手，而是带质量门禁、副作用边界和本地脚本链路的公众号生产流程控制器。

## 快速开始

在 Codex 中直接这样说：

```text
使用 $wechat-official-account-orchestrator 做一篇内部科技安全公众号文章，从选题到草稿箱 dry-run。
```

如果已有稿件：

```text
使用 $wechat-official-account-orchestrator 检查这篇 Markdown 稿件，做审稿、排版预览和草稿箱 dry-run。
```

如果只做发布前检查：

```text
使用 $wechat-official-account-orchestrator 对这份 HTML 和图片做公众号发布前总检。
```

默认只生成本地产物和 dry-run 报告，不上传图片、不创建真实草稿箱、不正式发布。

## 适合做什么

| 你要做什么 | 默认产出 | 直接这样说 |
| --- | --- | --- |
| 从 0 做一篇内部科技安全文章 | 资料台账、论证链、标题、大纲、写作包、初稿、审稿报告 | `从选题开始做一篇 AI Agent 安全运营文章` |
| 接续已有 Markdown | 审稿、改稿建议、组件版 Markdown、HTML 预览 | `检查并排版这篇 Markdown` |
| 做草稿箱 dry-run | 预检、HTML、素材清单、草稿 JSON、链路报告 | `把这篇稿件跑到草稿箱 dry-run` |
| 做封面/配图规划 | 视觉 brief、image-2 提示词、审核清单 | `给这篇文章做封面和正文配图方案` |
| 做正式发布前检查 | 终审结论、阻塞项、发布门禁建议 | `做公众号发布前总检` |

## 核心边界

- 默认只使用本 skill 自带的 `references/`、`assets/` 和 `scripts/`。
- 不默认调用其他 skill、`md2wechat` 或其他外部能力。
- `image-2` / 当前 Codex 图像工具作为固有生图能力保留，但真实生图必须由用户明确要求并确认副作用。
- 微信接口默认 dry-run。真实上传图片或创建草稿箱必须显式确认，并使用 `--execute --confirm-draftbox`。
- 正式发布或群发永远不是默认动作，必须二次确认。

## 阅读顺序

如果你只是使用这个 skill，优先读：

1. [SKILL.md](./SKILL.md)：触发条件、主流程、强制规则和完成标准。
2. [references/00-operating-contract.md](./references/00-operating-contract.md)：质量门禁、副作用边界、禁止事项。
3. [references/05-guided-mode.md](./references/05-guided-mode.md)：从 0 开始或向导式使用时的提问顺序。
4. [references/10-workflow.md](./references/10-workflow.md)：完整链路和接续已有稿件的路由。
5. [references/06-output-map.md](./references/06-output-map.md)：每个产物文件的用途和交接含义。

如果你要维护或扩展这个 skill，再读：

- [scripts/README.md](./scripts/README.md)：脚本目录分层和新增规则。
- [references/40-formatting-assets.md](./references/40-formatting-assets.md)：排版、组件、视觉计划。
- [references/50-draftbox-delivery.md](./references/50-draftbox-delivery.md)：草稿箱 dry-run、上传和交付。
- [references/60-wechat-connection-ops.md](./references/60-wechat-connection-ops.md)：微信 API 配置、命令和排错。
- [references/70-formal-release-ops.md](./references/70-formal-release-ops.md)：正式发布门禁。

## 目录结构

```text
wechat-official-account-orchestrator/
  SKILL.md
  README.md
  agents/
    openai.yaml
  assets/
    profiles/
    theme-previews/
  references/
    00-operating-contract.md
    05-guided-mode.md
    06-output-map.md
    10-workflow.md
    ...
  scripts/
    orchestration/
    content/
    review/
    formatting/
    assets/
    wechat/
    qa/
    templates/
```

## 常用命令

生成下一步向导：

```bash
python scripts/orchestration/wechat_article_wizard.py --mode new --topic "AI Agent 安全运营" --audience "安全运营团队" --type security-analysis
```

本地到草稿箱 dry-run：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech --quality-review
```

严格质量门禁：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech --quality-review --strict-quality
```

真实创建草稿箱前必须由用户确认：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech --execute --confirm-draftbox
```

运行回归测试：

```bash
python scripts/qa/run_skill_regression.py
```

## 质量门禁

进入排版前，内容质量、可信度、结构完整度都应不低于 4/5。

进入草稿箱前，内容、排版、图片、元数据、发布安全都应不低于 4/5。

出现以下问题时应暂停推进：

- 标题承诺正文无法兑现。
- 关键事实未经确认却写成确定结论。
- 存在未处理的敏感信息。
- 预览不可用或图片不显示。
- 封面缺失却要进草稿箱。
- 草稿箱没有回执却声称成功。

## 维护规则

- `SKILL.md` 只放触发条件、主流程和强制边界。
- 长规则、打法、模板说明放在 `references/`。
- 可重复执行、容易出错的步骤放在 `scripts/`。
- 新脚本不要直接放到 `scripts/` 根目录，应按能力放入子目录。
- 新文章模板、prompt pack、审稿模板、视觉模板优先放入 `scripts/templates/` 或 `assets/`。
- 修改脚本路径或链路规则后，运行：

```bash
python scripts/qa/run_skill_regression.py
```

