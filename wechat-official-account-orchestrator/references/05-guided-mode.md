# 05 引导式总控模式

用于用户明确指定使用本 skill，或说“用公众号总控带我做一篇”“一步步来”“从选题到草稿箱”的场景。

## 核心原则

- 默认先引导，不直接把所有脚本和流程一次性丢给用户。
- 每轮最多问 2-4 个关键问题，问题必须服务于下一步产物。
- 先判断任务类型，再判断已有物料，再决定是否联网调研、是否生成大纲、是否进入审稿或排版。
- 用户给出足够上下文后，执行最小必要命令，不额外扩展流程。
- 不覆盖源稿，所有生成、改写、组件插入、预览默认输出新文件。
- 上传、草稿箱、远程图片生成、调用微信接口、正式发布都属于副作用，必须用户明确确认。

## 第一轮识别

第一轮只确认当前入口，不问无关细节。

必须判断：

- 是从 0 做一篇，还是接续已有 Markdown/HTML/图片？
- 目标是选题、大纲、成稿、审稿、排版预览、草稿箱 dry-run，还是正式发布前检查？
- 面向读者是谁？
- 文章类型属于哪一类：`security-analysis`、`agent-observation`、`product-launch`、`industry-observation`、`case-review`。

示例提问：

```text
我先按总控向导推进。需要确认 4 点：
1. 这是从 0 新做，还是基于已有稿件接续？
2. 目标读者是谁？
3. 文章类型更接近安全分析、AI Agent 观察、产品发布、行业观察、案例复盘中的哪一类？
4. 你是否已有新材料或参考链接？
```

## 资料与联网边界

当用户没有提供新物料，且主题涉及最新技术、安全、AI Agent、产品趋势、政策、漏洞、行业动态时，应主动建议公开资料调研。

调研必须先形成资料台账，不允许直接把网上内容混入正文。

资料台账必须包含：

- 来源标题
- URL
- 发布时间
- 访问时间
- 来源类型
- 可信度
- 可引用结论
- 不确定项
- 不允许使用项

如果当前环境不能联网，应说明限制，并生成空台账模板或要求用户提供参考材料。

## 风格与模板锁定

排版前必须确认或使用 profile 默认 preset。未指定时默认 `tech`。

可选风格包括：

- `tech`：简约科技风，适合技术、安全、AI Agent 观察。
- `formal`：正式克制风，适合发布说明、客户向内容。
- `security`：安全分析风，适合风险、漏洞、处置建议。
- `product`：产品说明风，适合版本发布、能力介绍。

一旦进入排版阶段，必须把实际使用的 preset 写入链路报告，避免 HTML 与预设不一致。

## 小组件使用规则

小组件不会凭空出现在 HTML 中，必须先生成组件版 Markdown，再排版。

默认流程：

```bash
python scripts/formatting/article_component_planner.py article.md --type security-analysis --preset tech --out article.components.md --plan article.components.json
python scripts/formatting/wechat_format_presets.py article.components.md --preset tech --out article.html
```

组件选择规则：

- 核心判断：`quote` / `insight`
- 风险提示：`warning`
- 术语解释：`definition`
- 行动建议：`checklist` / `steps`
- 章节小结：`summary`
- 来源边界：`source`

默认插入 2-4 个组件。不要为了装饰堆组件。

## 视觉资产与图像生成

封面、正文配图、信息图先生成 brief 和提示词。

```bash
python scripts/assets/visual_asset_plan.py article.md --type security-analysis --style tech --out article.visual.json
```

真实调用 image-2 / 当前 Codex 图像工具属于副作用。只有用户明确要求生成图片并授权时，才执行生图动作；否则只输出 brief、提示词和审核清单。

禁止生成：

- 客户标识
- 密钥、token、凭证
- 真实漏洞利用细节
- 未授权品牌标识
- 长中文画面文字

## 推荐交互顺序

从 0 做一篇：

```text
任务类型确认 -> 受众/文章类型 -> 新物料检查 -> 公开资料调研建议 -> 资料台账 -> 论证链 -> 标题策略 -> 大纲 -> 写作包 -> 初稿提示词 -> 模型初稿 -> 审稿 -> 表达严谨性审稿 -> 改稿计划 -> 组件编排 -> 视觉计划 -> 锁定预设排版 -> 草稿箱 dry-run
```

接续已有 Markdown：

```text
稿件识别 -> 文章类型/preset 确认 -> 内容审稿 -> 表达严谨性审稿 -> 改稿计划 -> 组件编排 -> 视觉计划 -> HTML 预览 -> 草稿箱 dry-run
```

已有 HTML 和图片：

```text
来源确认 -> 元数据检查 -> 图片与链接检查 -> 发布安全检查 -> 草稿箱 dry-run
```

## 向导脚本

向导脚本只生成下一步建议和命令，不执行整条链路。

```bash
python scripts/orchestration/wechat_article_wizard.py --mode new --topic "AI Agent 安全运营" --audience "安全运营团队" --type security-analysis
python scripts/orchestration/wechat_article_wizard.py --mode existing --article article.md --preset tech
python scripts/orchestration/wechat_article_wizard.py --mode preview --article article.md --preset tech
python scripts/orchestration/wechat_article_wizard.py --mode draft-dry-run --article article.md --preset tech
```

## 禁止行为

- 不要在第一轮就要求用户提供所有信息。
- 不要因为用户说“发一下”就默认正式发布；默认解释为进入草稿箱或草稿箱 dry-run。
- 不要跳过资料台账直接编事实。
- 不要跳过组件版 Markdown 直接承诺小组件会出现在 HTML 中。
- 不要未确认 preset 就生成最终 HTML。
- 不要索要密钥、token、AppSecret。
- 不要在未获得确认时调用上传、草稿箱、远程生图或正式发布动作。

