# 27 模型协作成稿

用于把标题、大纲和材料转成可控初稿。目标不是让模型自由发挥，而是让模型在事实台账、段落任务和人工复核点约束下完成初稿。

## 适用场景

- 从 0 做一篇公众号文章，已经有主题、文章类型和目标读者。
- 已有大纲，但缺少可执行的分段写作任务。
- 已有采访纪要、产品资料或事实材料，需要转成公众号初稿。
- 需要让模型写初稿，但不能编造客户、数字、漏洞编号、产品指标。

## 默认链路

```text
资料台账 -> 论证链 -> playbook -> 标题策略 -> 大纲 -> 成稿写作包 -> 初稿提示词 -> 模型初稿 -> 审稿质检 -> 改稿计划 -> 二次改稿 -> 组件编排 -> 视觉计划 -> 排版预览
```

生成写作包：

```bash
python scripts/content/article_writing_pack.py --topic "AI Agent 安全运营" --type security-analysis --audience "安全运营团队" --out article.writing-pack.json
```

已有大纲时：

```bash
python scripts/content/article_writing_pack.py --topic "AI Agent 安全运营" --type security-analysis --outline article.outline.md --argument-chain article.argument-chain.json --out article.writing-pack.json
```

有事实材料时：

```bash
python scripts/content/article_writing_pack.py --topic "AI Agent 安全运营" --type security-analysis --source-notes notes.md --out article.writing-pack.json
```

生成可直接交给模型的初稿提示词：

```bash
python scripts/content/article_draft_prompt_builder.py article.writing-pack.json --out article.draft-prompt.md
```

审稿后生成改稿计划：

```bash
python scripts/review/article_quality_review.py article.md --out article.quality.json
python scripts/review/article_revision_plan.py article.md article.quality.json --out article.revision-plan.md
```

## 写作包必须包含

- 核心角度：文章要证明或解释的主判断。
- 读者任务：读者看完后应能判断什么、行动什么。
- 事实台账：必须核验的事实、来源、使用章节。
- 论证链：核心判断、支撑证据、推理过程、适用边界、读者动作、产品连接边界。
- 分段写作任务：每节写作目标、必须包含、避免事项、模型提示词。
- 模型协作提示：system 和 user 两级提示词。
- 人工决策点：标题、事实、产品连接、授权素材、是否进入审稿。
- 通过标准：判断初稿是否能进入审稿质检。

## 模型使用边界

模型可以做：

- 把大纲扩成可读初稿。
- 调整段落顺序和表达节奏。
- 把复杂概念写得更清楚。
- 生成不同口吻的表达版本。
- 根据审稿报告修复结构和措辞问题。

模型不能做：

- 补造客户名称、案例、合同、报价、部署效果。
- 补造漏洞编号、政策条款、市场规模、排名、百分比。
- 暗示产品能力已经覆盖未提供的场景。
- 删除 `待核验` 标记后直接写成确定事实。
- 自行决定进入草稿箱或正式发布。

## 初稿提示词要求

`article_draft_prompt_builder.py` 输出的提示词必须包含：

- system prompt：角色、语气、事实边界。
- user prompt：主题、标题、文章类型、目标读者、目标字数、核心角度。
- 章节任务：每节字数建议、写作目标、必须包含、避免事项。
- 事实规则：缺少来源时保留 `待核验`。
- 输出约束：只输出 Markdown 初稿，不输出 HTML、图片、上传或草稿箱状态。

模型初稿生成后，不能直接排版。先做人工事实补齐和审稿质检。

## 人工判断点

模型初稿生成后，必须人工确认：

- 标题承诺是否被正文兑现。
- 开头是否具体，不是模板化套话。
- 每节是否有结论、依据和边界。
- 事实台账里的 `待核验` 是否补齐来源或保留标记。
- 产品连接是否过重，是否有销售腔。
- 是否存在绝对化、恐吓式、竞品贬损或未经授权表达。

## 质量目标

高质量初稿应满足：

- 有一个明确的核心判断，而不是信息堆叠。
- 每个小节承担不同任务，不重复同一句价值判断。
- 读者能获得具体判断标准、检查动作或决策问题。
- 专业但不堆术语，克制但不空泛。
- 所有不确定事实都有 `待核验` 标记。

## 与审稿质检的关系

写作包和模型初稿不等于可发布稿。进入排版前必须运行：

```bash
python scripts/review/article_quality_review.py article.md --out article.quality.json
```

审稿未通过时，先生成改稿计划：

```bash
python scripts/review/article_revision_plan.py article.md article.quality.json --out article.revision-plan.md
```

改稿计划要把问题转成优先级、修订动作和通过标准。总分低于 4/5 或存在阻断项时，不进入视觉计划、排版或草稿箱链路。

## 写法样例

模型写作时可参考 `references/28-draft-examples.md`。样例只用于学习结构和语气，不得照抄其中事实，也不得用样例替代来源。

