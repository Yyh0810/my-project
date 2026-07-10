---
name: wechat-official-account-orchestrator
description: 微信公众号独立新版总控，面向内部科技安全号处理科技、安全、AI 智能体、产品类图文生产。用于明确要求“内部科技安全公众号总控”“科技安全号从选题到草稿箱 dry-run”“微信草稿箱链路”“公众号发布前总检”的场景；也可接续已有 Markdown、HTML、图片产物做发布前检查。默认只使用本 skill 的 references、assets 和 scripts；不依赖其他 skill、md2wechat 或其他外部能力。image-2 / 当前 Codex 图像工具属于可用的固有生图能力，但仅在用户明确要求并确认副作用时调用。默认只到本地预览和草稿箱 dry-run；正式群发、上传、远程图片生成、调用微信接口等副作用动作必须获得用户明确确认。
---

# 微信公众号总控

## 定位

把本 skill 作为独立新版微信公众号文章运营总控使用，默认服务内部科技安全号。默认只使用本 skill 自带的参考文档、资产和脚本；不调用、不转交给其他 skill，也不默认依赖 `md2wechat` 或其他外部能力。`image-2` / 当前 Codex 图像工具作为固有生图能力保留，但真实生图仍需用户明确要求并确认副作用。

默认场景：

- 使用对象：内部运营团队。
- 内容方向：内部科技安全号，覆盖科技、安全、AI 智能体、产品类文章。
- 默认边界：本地预览和微信公众号草稿箱 dry-run。
- 发布策略：正式群发永远不是默认动作，必须二次确认。

## 工作方式

先判断用户处在哪个阶段，再读取对应模块。不要一次性加载所有参考文档。

| 场景 | 读取 |
| --- | --- |
| 任何任务开始前的硬约束、质量门禁、安全边界 | `references/00-operating-contract.md` |
| 指定使用本 skill 后的会话式引导、问题顺序、副作用确认 | `references/05-guided-mode.md` |
| 链路产物地图、文件用途、交接解释 | `references/06-output-map.md` |
| 完整流程、接续已有产物、判断下一步 | `references/10-workflow.md` |
| 账号定位、栏目、选题、标题、摘要 | `references/20-planning.md` |
| 公开资料调研、资料台账、来源可信度和引用边界 | `references/22-public-research.md` |
| 安全分析、AI Agent、产品发布、行业观察、案例复盘的内容打法 | `references/25-content-playbooks.md` |
| 模型协作成稿、写作包、事实台账、分段写作任务 | `references/27-model-assisted-drafting.md` |
| 初稿写法样例、开头/分析/结尾片段、文章类型范式 | `references/28-draft-examples.md` |
| 正文写作、改写、审稿、合规、事实检查 | `references/30-writing-review.md` |
| 安全分析稿、产品说明稿、行业观察稿的审稿模板 | `references/35-review-rubrics.md` |
| 排版、预览、封面、正文配图、可用图像生成工具、公开工具经验 | `references/40-formatting-assets.md` |
| 封面、正文配图、信息图的视觉 brief 和通用生成提示词 | `references/42-visual-asset-playbooks.md` |
| 小创意组件、局部点缀、组件素材库 | `references/45-creative-block-library.md` |
| 草稿箱、上传、回执、正式发布边界 | `references/50-draftbox-delivery.md` |
| 微信公众号 API 接入、本机配置、团队交接操作 | `references/60-wechat-connection-ops.md` |
| 草稿箱之后的正式发布/群发门禁、二次确认、发布后回执 | `references/70-formal-release-ops.md` |
| 微信 API 错误码、失败原因和接续处理 | `references/80-wechat-api-errors.md` |

## 阶段路由

- 用户明确指定“使用这个 skill”“用公众号总控”“一步步引导我做公众号文章”时：先进入 `05-guided-mode.md`，每轮最多问 2-4 个关键问题；不要直接倾倒全部脚本。上下文足够后，优先用 `scripts/orchestration/wechat_article_wizard.py` 生成下一步命令。
- 用户明确要求“内部科技安全公众号总控”“科技安全号完整链路”“从选题到草稿箱”“微信草稿箱链路”：从 `10-workflow.md`、`22-public-research.md` 和 `25-content-playbooks.md` 开始，按 `资料台账 -> 论证链 -> 标题策略 -> 大纲 -> 成稿写作包 -> 初稿提示词 -> 模型初稿 -> 内容审稿 -> 表达严谨性审稿 -> 改稿计划 -> 组件编排 -> 锁定预设排版 -> 草稿箱 dry-run` 推进。
- 用户给了 Markdown：跳过选题和初稿，从审稿、排版、配图或草稿箱就绪检查开始。
- 用户给了 HTML 和图片：从终审和草稿箱就绪检查开始。
- 用户只要排版：进入 `40-formatting-assets.md`，保护源稿，输出预览或 HTML。
- 用户要封面、正文配图、信息图或“生图”：进入 `40-formatting-assets.md`，先产出设计 brief；只有用户明确要求调用图像生成工具时，才按授权执行外部生图动作。
- 用户只要草稿箱或发布：进入 `50-draftbox-delivery.md`，先做安全和质量门禁。
- 用户要图片帖、多图、九宫格：按图片消息思路处理，不当成长文图文。

不覆盖朋友圈文案、社群话术、小程序开发、企业微信客户运营、非微信渠道发布。

## 强制规则

这些规则优先级最高：

- 禁止自作主张：不能擅自决定账号、品牌定位、正式发布、群发、上传图片、跳过审稿。
- 禁止跳步骤：缺正文不能排版，缺预览不能进草稿箱，缺二次确认不能群发。
- 禁止伪完成：没有文件、预览、检查结论或接口回执，不得声称“已完成”。
- 禁止覆盖源稿：默认生成新文件或临时稿，除非用户明确要求修改源稿。
- 禁止索要密钥：不让用户在聊天里粘贴 API key、AppSecret、access token。
- 禁止混淆状态：预览成功不等于草稿箱成功，草稿箱成功不等于正式发布。
- 禁止静默降级：工具不可用或能力降低时，必须说明差异。
- 禁止编造事实：漏洞、政策、产品版本、客户案例、指标等不确定时要查证或标注待确认。

## 质量门禁

每个完整流程必须做质量检查。默认通过线：

- 进入排版：内容质量、可信度、结构完整度均不低于 4/5。
- 进入草稿箱：内容、排版、图片、元数据、发布安全均不低于 4/5。
- 正式发布：全部核心维度不低于 4/5，且没有红线问题。

出现红线问题时，暂停发布路径，先给修复建议。用户说“快速发”也不能取消质量检查，只能压缩说明。

## 外部工具边界

本 skill 默认不调用其他 skill、`md2wechat` 或其他外部能力。`image-2` / 当前 Codex 图像工具是固有生图能力，但只在用户明确要求生成视觉资产并确认副作用后调用。若用户明确要求使用 `md2wechat`，可运行：

```bash
md2wechat version --json
md2wechat capabilities --json
md2wechat inspect <article.md> --json
md2wechat preview <article.md>
```

本 skill 自带的确定性脚本：

```bash
python scripts/formatting/wechat_format_presets.py article.md --preset formal --out article.html
python scripts/formatting/wechat_creative_blocks.py --style insight --title "核心洞察" --text "一句需要强调的话"
python scripts/orchestration/wechat_article_wizard.py --mode new --topic "AI Agent 安全运营" --audience "安全运营团队" --type security-analysis
python scripts/orchestration/wechat_article_wizard.py --mode existing --article article.md --preset tech
python scripts/review/article_preflight_check.py article.md
python scripts/content/research_ledger_builder.py --topic "AI Agent 安全运营" --type security-analysis --out article.research-ledger.json
python scripts/content/article_argument_chain.py --topic "AI Agent 安全运营" --type security-analysis --ledger article.research-ledger.json --out article.argument-chain.json
python scripts/review/article_quality_review.py article.md --out article.quality.json
python scripts/review/article_style_rigor_review.py article.md --out article.rigor.json
python scripts/content/article_outline_builder.py --topic "AI Agent 安全运营" --type security-analysis --audience "安全运营团队" --out article.outline.md
python scripts/content/article_writing_pack.py --topic "AI Agent 安全运营" --type security-analysis --outline article.outline.md --argument-chain article.argument-chain.json --out article.writing-pack.json
python scripts/content/article_draft_prompt_builder.py article.writing-pack.json --out article.draft-prompt.md
python scripts/content/title_strategy.py --topic "AI Agent 安全运营" --type security-analysis --out article.titles.json
python scripts/review/article_rewrite_modes.py article.md --mode dehype --out article.dehype.md
python scripts/review/article_revision_plan.py article.md article.quality.json --rigor-json article.rigor.json --out article.revision-plan.md
python scripts/formatting/article_component_planner.py article.md --type security-analysis --preset tech --out article.components.md --plan article.components.json
python scripts/assets/visual_asset_plan.py article.md --type security-analysis --style tech --out article.visual.json
python scripts/assets/image_asset_manifest.py article.html --out article.assets.json
python scripts/assets/rewrite_image_sources.py article.html --mapping uploaded-images.json --out article.wechat.html
python scripts/wechat/wechat_api_draft.py check-config
python scripts/wechat/wechat_api_draft.py upload-image --image cover.png
python scripts/wechat/wechat_api_draft.py add-draft --article-json article.draft.json
python scripts/wechat/formal_release_gate.py article.release.json
python scripts/wechat/wechat_handoff_report.py chain-report.json --out handoff.md
python scripts/qa/run_skill_regression.py
```

已有 Markdown 或 HTML 稿件需要从本地一路检查到草稿箱时，优先使用总控脚本，避免手工漏步骤：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech
```

该脚本默认 dry-run，只生成预检、HTML、素材清单、微信回填 HTML、草稿 JSON 和链路报告。需要把内容专业度审稿纳入链路时使用：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech --quality-review
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech --quality-review --strict-quality
```

`--strict-quality` 下，审稿总分低于 4/5 或存在阻断项时，不生成草稿箱 JSON。

团队复用时可使用非敏感 profile 和阶段接续：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --profile tech-internal --quality-review
python scripts/orchestration/wechat_local_to_draft.py article.md --resume-from rewrite-images --mapping uploaded-images.json
```

profile 只能保存账号显示名、默认作者、默认主题等非敏感配置；禁止保存 AppSecret、access_token、API key。

真实上传正文图片、封面素材并创建草稿箱时，必须由用户明确确认后同时传入：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech --execute --confirm-draftbox
```

主题与组件需要横向挑选时，生成预览目录：

```bash
python scripts/formatting/build_theme_preview_gallery.py
```

截图级视觉自测不是默认步骤。只有用户明确要求“自测/截图检查/移动端检查”，或 HTML 预览包含复杂表格、代码块、长链接、宽图、流程图、疑似破版内容时，才运行：

```bash
python scripts/qa/visual_selftest.py article.html
```

微信接口脚本默认只 dry-run。只有用户明确同意上传、草稿箱动作，并且命令带 `--execute` 时，才允许真实调用微信接口。

只运行能回答下一步决策的最小命令。预览、上传、草稿箱、正式发布必须区分清楚。

## 完成标准

完整流程结束时，必须说明：

- 当前状态。
- 文章源文件。
- 预览或 HTML 路径。
- 封面和正文图片状态。
- 质量检查结果。
- 草稿箱结果或阻塞项。
- 下一步。

没有对应证据时，不要写“已完成”。

