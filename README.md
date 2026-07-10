# WeChat Official Account Orchestrator

`wechat-official-account-orchestrator` 是一个面向微信公众号图文生产的 Codex skill。它把选题、资料整理、写作、审稿、视觉计划、排版预览和草稿箱 dry-run 串成一条可检查、可回退、可交接的工作流。

默认使用场景是内部科技安全公众号，适合科技、安全、AI Agent、产品解读、行业观察、案例复盘等内容。它不是单纯的写作提示词，而是一个带质量门禁、副作用边界和本地脚本链路的公众号运营总控。

## 一键安装

安装到 Codex skills 目录：

```powershell
git clone https://github.com/Yyh0810/my-project.git "$env:USERPROFILE\.codex\skills\wechat-official-account-orchestrator"
```

如果已经安装过，更新本地版本：

```powershell
git -C "$env:USERPROFILE\.codex\skills\wechat-official-account-orchestrator" pull
```

Linux / macOS 可以使用：

```bash
git clone https://github.com/Yyh0810/my-project.git "${CODEX_HOME:-$HOME/.codex}/skills/wechat-official-account-orchestrator"
```

安装完成后，重启 Codex，让新的 skill 生效。

## 快速开始

安装并重启后，在 Codex 对话里直接使用 skill 名称。

### 从 0 做一篇公众号文章

```text
使用 $wechat-official-account-orchestrator 帮我为内部科技安全公众号准备一篇文章，从选题、成稿、审稿、视觉计划、排版预览到草稿箱 dry-run。
```

### 接续已有 Markdown 稿件

```text
使用 $wechat-official-account-orchestrator 检查这篇 Markdown 稿件，做审稿、排版预览和草稿箱 dry-run。
```

### 做发布前总检

```text
使用 $wechat-official-account-orchestrator 对这份 HTML 和图片做公众号发布前总检。
```

默认只生成本地产物和 dry-run 报告，不上传图片、不创建真实草稿箱、不正式发布。

## 能力地图

| 你要做什么                    | 默认产出                                                 | 直接这样说                               |
| ----------------------------- | -------------------------------------------------------- | ---------------------------------------- |
| 从 0 生产一篇内部科技安全文章 | 资料台账、论证链、标题策略、大纲、写作包、初稿、审稿报告 | `从选题开始做一篇 AI Agent 安全运营文章` |
| 接续已有 Markdown             | 审稿结论、改稿建议、组件版 Markdown、HTML 预览           | `检查并排版这篇 Markdown`                |
| 跑草稿箱 dry-run              | 预检报告、HTML、素材清单、草稿 JSON、链路报告            | `把这篇稿件跑到草稿箱 dry-run`           |
| 做封面和正文配图规划          | 视觉 brief、image-2 提示词、图片审核清单                 | `给这篇文章做封面和正文配图方案`         |
| 做正式发布前检查              | 终审结论、阻塞项、发布门禁建议                           | `做公众号发布前总检`                     |

## 工作流

完整链路默认按下面顺序推进：

```text
选题 -> 资料台账 -> 论证链 -> 标题策略 -> 大纲 -> 写作包 -> 初稿
  -> 内容审稿 -> 严谨性审稿 -> 改稿计划 -> 组件编排
  -> 排版预览 -> 素材检查 -> 草稿箱 dry-run -> 发布前总检
```

如果用户已经提供 Markdown、HTML、图片或草稿箱产物，skill 会从对应阶段接续，不会强制从选题重新开始。

## 核心边界

- 默认只使用本 skill 自带的 `references/`、`assets/` 和 `scripts/`。
- 不默认调用其他 skill、`md2wechat` 或其他外部能力。
- `image-2` / 当前 Codex 图像工具可用于生图，但必须由用户明确要求并确认副作用。
- 微信接口默认只做 dry-run。
- 真实上传图片、创建草稿箱或调用微信接口前，必须显式确认。
- 正式发布或群发永远不是默认动作，必须二次确认。

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

启用严格质量门禁：

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

进入排版前，内容质量、可信度和结构完整度都应不低于 4/5。

进入草稿箱前，内容、排版、图片、元数据和发布安全都应不低于 4/5。

出现以下问题时应暂停推进：

- 标题承诺正文无法兑现。
- 关键事实未经确认却写成确定结论。
- 存在未处理的敏感信息。
- 预览不可用或图片不显示。
- 封面缺失却要进草稿箱。
- 草稿箱没有回执却声称成功。

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

## 维护规则

- `SKILL.md` 只放触发条件、主流程和强制边界。
- 长规则、打法、模板说明放在 `references/`。
- 可重复执行、容易出错的步骤放在 `scripts/`。
- 新脚本不要直接放到 `scripts/` 根目录，应按能力放入子目录。
- 新文章模板、prompt pack、审稿模板、视觉模板优先放入 `scripts/templates/` 或 `assets/`。
- 修改脚本路径或链路规则后，运行 `python scripts/qa/run_skill_regression.py`。

## 常见问题

### 安装后没有生效

1. 确认仓库目录在 `~/.codex/skills/wechat-official-account-orchestrator`。
2. 确认 `SKILL.md` 位于该目录根部。
3. 重启 Codex。
4. 在对话中使用完整名称 `$wechat-official-account-orchestrator`。

### 只想做排版，不想从选题开始

直接提供 Markdown，并说明：

```text
使用 $wechat-official-account-orchestrator 只做这篇稿件的审稿、排版预览和草稿箱 dry-run，不重新选题。
```

### 可以直接正式发布吗

不默认正式发布。正式发布、群发、上传图片、创建真实草稿箱都属于副作用动作，必须先完成质量检查，并由用户明确确认。
