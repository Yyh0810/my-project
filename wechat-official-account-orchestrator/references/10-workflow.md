# 10 工作流程

用于完整流程、接续已有产物、判断下一步。

## 阶段总览

`引导式入口 -> 意图确认 -> 账号/风格 -> 新物料检查 -> 公开资料调研 -> 资料台账 -> 论证链 -> playbook -> 标题策略 -> 大纲 -> 成稿写作包 -> 初稿提示词 -> 模型初稿 -> 内容审稿 -> 表达严谨性审稿 -> 改稿计划 -> 二次改稿 -> 组件编排 -> 视觉计划 -> 锁定预设排版/预览 -> 配图/素材 -> 终审 -> 草稿箱 -> 后台人工终审 -> 正式发布门禁 -> 正式发布/群发`

| 阶段 | 最低输入 | 最低交付 |
| --- | --- | --- |
| 引导式入口 | 用户目标或显式指定本 skill | 当前模式、关键问题、下一步命令 |
| 意图确认 | 用户目标或已有路径 | 当前阶段、目标边界 |
| 账号/风格 | 账号定位或默认内部科技号 | 目标读者、语气、禁用项 |
| 新物料检查 | 主题、受众、用户材料 | 是否需要公开资料调研 |
| 公开资料调研 | 无新材料或涉及最新事实 | 可公开来源候选 |
| 资料台账 | 公开来源 | 来源、发布时间、可信度、可引用结论、不确定项 |
| 论证链 | 资料台账、主题、文章类型 | 核心判断、证据、推理、边界、读者动作 |
| playbook | 主题方向或素材 | 文章类型、结构打法、证据要求 |
| 标题策略 | 主题、文章类型 | 专业/传播/客户向/正式标题候选 |
| 大纲 | 主题、文章类型、读者 | 可写稿 Markdown 骨架 |
| 成稿写作包 | 大纲、主题、材料 | 核心角度、事实台账、分段写作任务、模型提示词、人工复核点 |
| 初稿提示词 | 成稿写作包 | 可直接交给模型的 system/user prompt、章节字数、输出约束 |
| 模型初稿 | 初稿提示词、材料 | 可审稿 Markdown，保留待核验事实 |
| 内容审稿 | 正文 | 质量报告、问题清单、修改建议 |
| 表达严谨性审稿 | 正文 | AI 味、叙事单一、严谨性报告 |
| 改稿计划 | 正文、审稿 JSON | 按优先级排列的改稿任务、通过标准、复验命令 |
| 二次改稿 | 改稿计划、源稿 | 可重新审稿的修订稿 |
| 组件编排 | 定稿 Markdown、文章类型、预设 | 组件计划、组件版 Markdown |
| 视觉计划 | 审稿后正文、文章类型 | 封面 brief、正文配图计划、信息图结构、审核清单 |
| 锁定预设排版/预览 | 组件版 Markdown、preset | HTML 或预览路径、排版问题 |
| 配图/素材 | 标题、正文、视觉计划 | 封面状态、正文图清单、风险 |
| 终审 | HTML、图片、元数据 | 质量结论、阻塞项 |
| 草稿箱 | 终审通过、用户明确意图 | 草稿结果或明确阻塞 |
| 后台人工终审 | 草稿箱后台可见 | 人工检查结论、问题或通过 |
| 正式发布门禁 | 草稿箱、人工终审、用户二次确认 | 门禁结果、发布边界 |
| 正式发布/群发 | 门禁通过、目标账号明确 | 发布回执或明确阻塞 |

## 路由规则

- 用户明确要求“用这个 skill”“公众号总控一步步来”时，先读 `05-guided-mode.md`，用少量问题确认入口；需要输出命令时优先运行 `scripts/orchestration/wechat_article_wizard.py`。
- 用户给 Markdown：从审稿开始，不重写选题和正文，除非用户要求。
- 用户给 HTML：从终审开始，确认它来自当前定稿。
- 用户只要排版：进入 `40-formatting-assets.md`，保护源稿。
- 用户只要草稿箱：进入 `50-draftbox-delivery.md`，先做质量和安全门禁。
- 用户明确要求正式发布/群发：先完成 `50-draftbox-delivery.md`，再进入 `70-formal-release-ops.md` 做二次确认和门禁检查。
- 存在多个候选目录：先按文件名和修改时间判断，仍不确定再问用户。
- 从 0 做一篇：先读 `22-public-research.md` 和 `25-content-playbooks.md`；无新材料或涉及最新事实时，先形成资料台账和论证链。

## 阶段门禁

- 当前阶段没有最低交付，不进入下一阶段。
- 发现阻塞项，先报告阻塞项和修复路径。
- 所有“完成”必须对应文件、文本产物、预览路径、检查结论或接口回执。
- 用户要求快速完成，也不能跳过审稿、图片状态检查、质量门禁、草稿箱后台人工终审和正式发布二次确认。
- 内容审稿总分低于 4/5 或存在阻断项时，不进入草稿箱。
- 大纲和标题阶段不得编造客户、数字、漏洞编号、产品指标；缺失事实写 `待核验`。
- 缺新材料且主题涉及最新事实时，必须先做公开资料调研并生成资料台账。
- 没有支撑证据或论证链阻断项时，不进入成稿写作包。
- 成稿写作包必须保留事实台账和人工复核点；模型初稿不得删除未核验事实标记。
- 内容审稿或表达严谨性审稿失败时先生成改稿计划并二次改稿，不能直接进入视觉计划、排版或草稿箱。
- 使用小组件时必须先生成组件版 Markdown，再对组件版 Markdown 锁定 preset 排版。
- 视觉计划只生成 brief、prompt 和审核清单；调用 image-2 / 当前 Codex 图像工具必须用户明确要求并授权。

## 内容生产链路

从 0 生产稿件时，先生成结构化产物，再进入审稿和排版：

```bash
python scripts/orchestration/wechat_article_wizard.py --mode new --topic "AI Agent 安全运营" --audience "安全运营团队" --type security-analysis
python scripts/content/title_strategy.py --topic "AI Agent 安全运营" --type security-analysis --out article.titles.json
python scripts/content/research_ledger_builder.py --topic "AI Agent 安全运营" --type security-analysis --out article.research-ledger.json
python scripts/content/article_argument_chain.py --topic "AI Agent 安全运营" --type security-analysis --ledger article.research-ledger.json --out article.argument-chain.json
python scripts/content/article_outline_builder.py --topic "AI Agent 安全运营" --type security-analysis --audience "安全运营团队" --out article.outline.md
python scripts/content/article_writing_pack.py --topic "AI Agent 安全运营" --type security-analysis --outline article.outline.md --argument-chain article.argument-chain.json --out article.writing-pack.json
python scripts/content/article_draft_prompt_builder.py article.writing-pack.json --out article.draft-prompt.md
python scripts/review/article_rewrite_modes.py article.md --mode dehype --out article.dehype.md
python scripts/review/article_style_rigor_review.py article.md --out article.rigor.json
python scripts/review/article_revision_plan.py article.md article.quality.json --rigor-json article.rigor.json --out article.revision-plan.md
python scripts/formatting/article_component_planner.py article.md --type security-analysis --preset tech --out article.components.md --plan article.components.json
```

接续已有稿件时，先让向导输出最小必要步骤：

```bash
python scripts/orchestration/wechat_article_wizard.py --mode existing --article article.md --preset tech
python scripts/orchestration/wechat_article_wizard.py --mode preview --article article.md --preset tech
python scripts/orchestration/wechat_article_wizard.py --mode draft-dry-run --article article.md --preset tech
```

文章类型固定为：

```text
security-analysis
agent-observation
product-launch
industry-observation
case-review
```

改稿模式固定为：

```text
formal
technical
product
customer
dehype
```

## 本地到草稿箱总控链路

审稿通过后，可先生成视觉计划：

```bash
python scripts/assets/visual_asset_plan.py article.md --type security-analysis --style tech --out article.visual.json
```

视觉计划不生成图片、不上传素材。需要生成封面或配图时，先让用户确认 brief；只有用户明确要求调用 image-2 / 当前 Codex 图像工具时，才执行生图动作。

已有 Markdown 或 HTML 后，优先用总控脚本把确定性步骤串起来：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech
```

默认只生成本地产物和链路报告，不调用微信接口。需要把内容专业度审稿纳入链路时加 `--quality-review`，需要审稿失败即阻断时再加 `--strict-quality`。它覆盖：

```text
预检 -> 内容审稿 -> HTML 预览 -> 素材清单 -> 正文图片映射/回填 -> 草稿 JSON -> 草稿箱 dry-run 报告
```

真实创建草稿箱必须额外满足：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech --execute --confirm-draftbox
```

团队接续失败链路时，使用：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --resume-from rewrite-images --mapping uploaded-images.json
```

固定账号风格时，使用非敏感 profile：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --profile tech-internal --quality-review
```

该脚本不包含正式发布。草稿箱之后继续按 `70-formal-release-ops.md` 做后台人工终审和正式发布门禁。

## 可选命令

默认使用本 skill 自带脚本检查和预览。只有用户明确要求使用 `md2wechat` 时，才运行：

```bash
md2wechat version --json
md2wechat capabilities --json
md2wechat inspect <article.md> --json
md2wechat preview <article.md>
```

没有工具时，输出等价人工检查：标题、摘要、作者、图片、占位符、封面、正文结构、草稿箱阻塞项。

