# 22 公开资料调研与资料台账

用于解决缺新物料、复用旧材料、事实不新的问题。本文规定什么时候必须联网调研，以及如何把公开资料固化为可审稿的资料台账。

## 何时必须公开调研

满足任一条件时，先调研公开资料，再进入标题、大纲和成稿：

- 用户只给主题、受众，没有提供新材料。
- 主题涉及最新技术、安全事件、漏洞、政策、平台规则、产品版本、行业动态。
- 稿件需要引用市场数据、第三方结论、报告、公告或社区观察。
- 当前材料明显来自旧主题，和新主题不匹配。

## 调研边界

- 由 Codex 会话执行联网检索，本地脚本不直接联网。
- 只使用公开可访问资料，不使用未授权客户、内部截图、密钥或非公开数据。
- 不把网页内容直接混进正文，先形成资料台账。
- 资料不足时保留 `待核验`，不能为了成稿补造事实。

## 资料台账

生成台账模板：

```bash
python scripts/content/research_ledger_builder.py --topic "AI Agent 安全运营" --type security-analysis --out article.research-ledger.json
```

已有公开来源 JSON 时：

```bash
python scripts/content/research_ledger_builder.py --topic "AI Agent 安全运营" --type security-analysis --sources sources.json --out article.research-ledger.json
```

每条来源必须包含：

- 来源标题。
- URL。
- 发布时间。
- 访问时间。
- 来源类型。
- 可信度。
- 可引用结论。
- 不确定项。
- 不允许使用项。

## 使用规则

- `high` 可信来源优先：官方公告、标准文档、厂商安全通告、论文、权威报告。
- `medium` 来源可辅助判断：可信媒体、社区实践、公开案例。
- `low/unknown` 来源不能单独支撑关键结论。
- 来源里没有明示的客户、数据、指标、漏洞状态，不得写成确定事实。
- 调研台账进入论证链后，才允许用于写作包和初稿提示词。

