# 40 排版、预览与配图

用于 Markdown 转 HTML、微信阅读体验、主题、模块、本地预览、封面、正文配图和信息图规划。默认只使用本 skill 自带脚本；只有用户明确要求时，才调用 image-2 / 当前 Codex 图像工具生图。

## 排版原则

本 skill 的排版脚本独立运行，不依赖外部编辑器或其他 skill。排版遵循：

- 写作与排版解耦：保护源稿，排版写入临时稿或输出稿。
- 所见即所得：结构性排版后给出预览或说明无法预览的原因。
- 微信兼容优先：样式内联，避免依赖外部 CSS、脚本和复杂布局。
- 手机宽度检查：重点看标题、代码、表格、图片。
- 图片状态显式化：本地、图床、微信素材、Base64、待上传必须区分。
- 副作用隔离：预览不上传，上传不等于草稿箱，草稿箱不等于群发。

## 排版目标

- 手机端易读。
- 标题层级清楚。
- 重点信息醒目但不过度。
- 图片位置自然。
- 复杂元素可降级。
- 适合复制到微信后台或进入草稿箱。

## 前端 UI 设计借鉴

可以参考前端 UI 设计技巧，但必须转译成公众号阅读版式，不能照搬网页组件。

可吸收的 UI 原则：

- 信息层级：标题、导读、正文、重点块、行动引导要有清楚主次。
- 留白节奏：段落、模块、图片之间要有稳定间距，避免密集堆叠。
- 视觉焦点：每屏只突出一个重点，不同时强调多个结论。
- 色彩系统：每个预设使用 1 个主色、1 个浅色背景、1 个正文色、1 个弱化色，避免杂色。
- 卡片克制：只把关键判断、清单、引用、CTA 做成块，不把每段话都做成卡片。
- 移动优先：按手机宽度检查标题、表格、代码、图片和长词换行。
- 稳定尺寸：图片、代码块、表格、提示块要有明确边界，避免复制到微信后挤压。
- 可扫读：长段落拆短，列表用于步骤/清单，不滥用装饰。

不能照搬的网页能力：

- 不依赖 JavaScript、交互组件、悬浮层、动效。
- 不依赖外部 CSS、CSS Grid、复杂响应式布局。
- 不使用嵌套卡片、复杂阴影和过度圆角。
- 不把公众号正文做成 landing page 或 dashboard。
- 不在正文里写“点击这里”“悬停查看”等网页交互语言。

落地到预设时：

- `minimal` 保持低装饰和高可读性。
- `formal` 保持严肃、低饱和、少模块。
- `tech` 使用结构化标题、代码友好、冷色强调。
- `alert` 只在风险提示、应急通知中使用，避免整篇高压。
- `product` 强调场景、能力、证据和行动引导。
- `news` 强调报道节奏和评论感。
- `elegant` 用于品牌和温和观点，避免过甜或过装饰。

## 样式预设脚本

需要快速生成微信友好的内联样式 HTML 时，优先使用：

```bash
python scripts/review/article_preflight_check.py article.md
python scripts/formatting/wechat_format_presets.py article.md --preset formal --out article.formal.html
```

可用预设：

| 预设 | 中文名 | 适用场景 |
| --- | --- | --- |
| `minimal` | 简约风 | 通用文章、轻量说明、内部复盘 |
| `formal` | 正式风 | 政务、客户汇报、严肃通知、正式观点 |
| `tech` | 科技风 | 技术解读、安全分析、AI 智能体文章 |
| `alert` | 警示风 | 漏洞应急、风险提示、紧急通知 |
| `product` | 产品说明风 | 产品能力、解决方案、功能介绍 |
| `news` | 新闻评论风 | 行业观察、深度评论、事件分析 |
| `elegant` | 雅致风 | 品牌稿、访谈、温和观点文章 |
| `government` | 政务正式风 | 政企客户、正式汇报、监管/合规主题 |
| `case` | 案例复盘风 | 项目复盘、安全事件复盘、客户案例 |
| `tutorial` | 教程清单风 | 操作指南、检查清单、最佳实践 |
| `deepread` | 深度长文风 | 深度分析、白皮书摘要、长篇观点 |
| `warm` | 温和品牌风 | 品牌沟通、客户故事、轻产品叙事 |
| `security` | 安全分析风 | 威胁分析、漏洞解读、防御策略 |
| `research` | 研究报告风 | 调研报告、白皮书摘要、行业研判 |
| `launch` | 新品发布风 | 产品发布、能力升级、版本公告 |
| `ops` | 运营复盘风 | 活动复盘、项目总结、增长/运营分析 |

脚本只覆盖常用 Markdown 子集，适合做草稿预设和快速预览。复杂表格、Mermaid、数学公式等内容仍需单独检查或转图片。

需要使用小组件时，先生成组件版 Markdown，再锁定预设排版：

```bash
python scripts/formatting/article_component_planner.py article.md --type security-analysis --preset tech --out article.components.md --plan article.components.json
python scripts/formatting/wechat_format_presets.py article.components.md --preset tech --out article.html
```

不要期望排版脚本自动发明组件。组件必须先以 `:::` Markdown 块写入稿件，HTML 才会渲染出对应模块。

已固化的公开工具技巧：

- 跳过 YAML frontmatter，避免标题、作者等元数据进入正文。
- 使用 URL 白名单，阻断 `javascript:`、`vbscript:` 等危险链接和图片源。
- 基础表格渲染为内联样式表格，手机端仍需预览检查。
- 任务列表转为“已完成/待处理”普通列表，避免微信后台样式丢失。
- 代码块、引用、列表、图片都使用内联样式，降低微信后台复制丢样式的概率。

## 主题预览目录

需要横向比较主题时，生成本地预览目录：

```bash
python scripts/formatting/build_theme_preview_gallery.py
```

默认输出到：

```text
assets/theme-previews/index.html
```

目录会为每个主题生成一份样稿 HTML，并保留 `sample.md` 作为主题测试源。挑选主题时优先看：

- 标题层级是否符合账号气质。
- 正文密度是否适合目标读者。
- 创意组件是否过重或过轻。
- 代码、表格、引用在手机宽度下是否清楚。
- 是否适合当前文章类型，而不是只看颜色喜好。

## 视觉资产计划

审稿通过后、排版预览前，先把封面、正文配图和信息图拆成可审核的视觉计划：

```bash
python scripts/assets/visual_asset_plan.py article.md --type security-analysis --style tech --out article.visual.json
```

只生成某一类资产时：

```bash
python scripts/assets/visual_asset_plan.py article.md --type security-analysis --asset cover --out cover.brief.md
python scripts/assets/visual_asset_plan.py article.md --type product-launch --asset body --out body-images.md
python scripts/assets/visual_asset_plan.py article.md --type agent-observation --asset infographic --out infographic.md
```

该脚本只输出 brief、通用生成提示词、正文插图位置、信息图结构和审核清单，不生成图片、不上传素材、不写入草稿箱。需要真实生图时，必须由用户明确要求并确认 image-2 / 当前 Codex 图像工具调用。

视觉打法详见 `references/42-visual-asset-playbooks.md`。默认文章类型沿用：

```text
security-analysis
agent-observation
product-launch
industry-observation
case-review
```

## 小创意模块

可以少量复用小创意模块，提升稿件节奏，但不要把整篇文章堆满装饰。默认一篇 1500-2500 字文章最多使用 2-4 个创意模块。

完整组件库见 `references/45-creative-block-library.md`。

可用模块：

| 模块 | 用途 | 适合位置 |
| --- | --- | --- |
| `divider` | 短分割线 / 转场标签 | 大段落切换、章节缓冲 |
| `question` | 分割线 + 小标签 + 提问条 | 章节转场、引出核心疑问 |
| `quote` | 左侧色条 + 浅色高亮底 | 关键判断、引用、观点强调 |
| `insight` | 核心洞察卡 | 小结、判断、策略建议 |
| `agentbox` | 标签信息卡 + 浅蓝内容框 | 产品视角、Agent 视角、案例旁白 |
| `checklist` | 检查清单 | 发布前检查、应急步骤、能力要点 |
| `steps` | 步骤/时间线 | 流程、路径、处置顺序 |
| `stat` | 关键数字 | 数据点、风险规模、效率指标 |
| `compare` | 左右对比 | 旧做法 vs 新做法、误区 vs 建议 |
| `cta` | 行动提示 | 文末、下载/咨询/下一步 |
| `warning` | 风险提示 | 漏洞风险、发布阻断、注意事项 |
| `definition` | 概念解释 | 术语定义、产品概念、技术背景 |
| `summary` | 本节小结 | 章节收束、关键结论复盘 |
| `source` | 依据与说明 | 数据来源、口径说明、事实边界 |

在 Markdown 中直接写：

```markdown
:::question
传统防御的“致盲点”：为什么 82 个漏洞能长驱直入？
:::

:::quote
你真正需要关注的，不只是漏洞本身，而是**行为背后的核心驱动力**。
:::

:::agentbox AgentBox
最近有个现象很有意思。

而你，还在纠结：**本地跑工具总是丢上下文，不同项目要重新配一遍环境**。
:::
```

生成 HTML 时，`wechat_format_presets.py` 会自动把这些块渲染成微信友好的内联样式。

自动编排组件时使用：

```bash
python scripts/formatting/article_component_planner.py article.md --type security-analysis --preset tech --out article.components.md --plan article.components.json
```

该脚本默认输出新稿，不覆盖源稿。生成后应对 `article.components.md` 执行锁定预设排版。

也可以单独生成 HTML 片段：

```bash
python scripts/formatting/wechat_creative_blocks.py --style question --title "传统防御的致盲点是什么？"
python scripts/formatting/wechat_creative_blocks.py --style quote --text "关键不是工具更多，而是**判断链路更完整**。"
python scripts/formatting/wechat_creative_blocks.py --style agentbox --title AgentBox --text "这里写 Agent 视角的补充说明。"
python scripts/formatting/wechat_creative_blocks.py --style checklist --title "发布前确认" --file checklist.txt
python scripts/formatting/wechat_creative_blocks.py --style warning --title "风险提示" --text "这里写阻断项或注意事项。"
python scripts/formatting/wechat_creative_blocks.py --style definition --title "什么是判断链路" --text "这里写概念解释。"
```

使用约束：

- `question` 只放短句，避免超过两行。
- `quote` 用于强调，不承载长篇正文。
- `agentbox` 用于旁白或案例，不替代正文主叙事。
- 不连续堆叠两个以上创意模块。
- 正式、政务类稿件减少装饰，优先用 `quote`，慎用 `agentbox`。
- 安全应急类稿件保持克制，避免让风险信息显得娱乐化。

## 可选视觉自测

HTML 预览是默认产物，浏览器截图级自测不是默认步骤。仅在以下情况运行：

- 用户明确要求“自测”“截图检查”“移动端检查”“看一下会不会破版”。
- HTML 里有复杂表格、代码块、长链接、宽图、流程图或大尺寸信息图。
- 预览后怀疑存在横向溢出、图片不显示、文字挤压。
- 客户交付、重要发布或正式活动前需要更高强度质检。

运行命令：

```bash
python scripts/qa/visual_selftest.py article.html
```

脚本默认使用系统 Microsoft Edge，不强制下载 Playwright 自带 Chromium。需要切换时可使用：

```bash
python scripts/qa/visual_selftest.py article.html --browser chrome
python scripts/qa/visual_selftest.py article.html --browser chromium
```

脚本会默认检查 `375x812`、`414x896`、`768x1024` 三个视口，并输出截图和 JSON 结论。若本机未安装 Playwright 或指定浏览器不可用，要说明“视觉自测未执行”，不能把未执行说成通过。

默认草稿箱前检查只要求 HTML 预览和素材清单；不要因为未运行截图级自测就阻断普通稿件。

## 排版检查

排版前：

- 标题层级合理。
- 段落不过长。
- 列表不过密。
- 代码、命令、编号可读。
- 图片路径存在。
- 无占位符。
- 标题、摘要、作者等元数据明确。

可运行轻量预检：

```bash
python scripts/review/article_preflight_check.py article.md
```

预览后：

- 标题不重复。
- 图片能显示。
- 文字不挤压、不溢出。
- 代码和表格在手机宽度下不破版。
- 公式、流程图、复杂图表必要时转图片。
- 模块不影响正文阅读。

## 配图策略

封面要求：

- 一个明确视觉中心。
- 不堆大量文字。
- 专业、可信、克制。
- 标题安全区明确。
- 不使用误导性或无关氛围图。

正文图优先放在：

- 复杂机制后。
- 流程说明处。
- 检查清单处。
- 产品能力或价值总结处。
- 结尾行动引导前。

图片检查：

- 文件存在。
- 分辨率和画幅适合微信。
- 不含敏感信息。
- 与正文段落对应。
- 无明显版权风险。
- 体积不过大。
- 状态明确：本地、图床、微信素材或待上传。

远程生图属于副作用。用户未明确同意时，只输出方案和提示词。

## 图像生成流程

用户明确要求封面、正文配图、信息图、概念图或“生图”，并授权调用 image-2 / 当前 Codex 图像工具时，才执行真实生图。若用户未授权或工具不可用，只交付 brief 和提示词，不能把提示词方案说成已经生成图片。

调用前先形成设计 brief：

- 用途：封面 / 正文配图 / 信息图 / 九宫格 / 贴图。
- 画幅：公众号封面默认 16:9，正文图按内容选择横版、竖版或方图。
- 主题：文章标题、核心观点、关键词。
- 风格：科技、安全、产品类默认专业、可信、克制。
- 文字：默认不在图中塞长文；需要文字时只放短标题或标签。
- 禁用：客户敏感信息、密钥、真实攻击步骤、误导性品牌或未经授权标识。

提示词要求：

- 明确主体、场景、构图、色彩、材质、信息层级。
- 避免泛泛的“科技感背景图”。
- 封面要留出标题安全区。
- 信息图要先设计内容结构，再生成图像。
- 不确定事实不写入画面文字。

生成后检查：

- 是否符合用途和画幅。
- 是否与文章标题和正文匹配。
- 是否含敏感信息或错误文字。
- 是否清晰、专业、可用于微信。
- 是否需要二次生成或局部调整。

## 阶段输出

```text
源文件：
输出预览/HTML：
排版策略：
排版质量：x/5
封面状态：
正文配图：
图像生成状态：
图片质量：x/5
问题和风险：
是否进入终审/草稿箱：
```

