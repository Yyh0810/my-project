# 06 产物地图

用于解释总控链路会生成哪些文件、这些文件解决什么问题、什么时候需要交给用户确认。

## 内容生产产物

| 产物 | 生成阶段 | 用途 | 是否可直接发布 |
| --- | --- | --- | --- |
| `article.research-ledger.json` | 公开资料调研后 | 固化来源、时间、可信度、可引用结论、不确定项和禁用项 | 否 |
| `article.argument-chain.json` | 资料台账后 | 约束核心判断、支撑证据、推理过程、适用边界、读者动作、产品连接边界 | 否 |
| `article.titles.json` | 标题策略 | 输出专业标题、传播标题、客户向标题、正式标题及风险提示 | 否 |
| `article.outline.md` | 大纲生成 | 生成可写稿 Markdown 骨架，保留待核验事实区 | 否 |
| `article.writing-pack.json` | 成稿写作包 | 汇总写作策略、事实台账、分段写作任务、模型协作要求、人工复核点 | 否 |
| `article.draft-prompt.md` | 初稿提示词 | 给模型生成初稿使用，要求保留事实边界和待核验标记 | 否 |

## 审稿与改稿产物

| 产物 | 生成阶段 | 用途 | 是否阻断后续 |
| --- | --- | --- | --- |
| `article.quality.json` | 内容审稿 | 检查标题兑现度、结构完整度、事实可信度、专业表达、风险合规、产品表达、读者收益、发布就绪度 | 总分低于 4/5 或有阻断项时阻断草稿箱 |
| `article.rigor.json` | 表达严谨性审稿 | 检查 AI 味、机械结构、泛泛开头、证据不足、产品硬插等问题 | 有阻断项时先改稿 |
| `article.revision-plan.md` | 改稿计划 | 合并内容审稿与表达严谨性审稿，形成按优先级排序的修改任务 | 是改稿依据 |
| `article.dehype.md` | 降营销味改稿 | 降低夸大、绝对化、过度营销表达 | 否 |

## 组件、视觉与排版产物

| 产物 | 生成阶段 | 用途 | 注意事项 |
| --- | --- | --- | --- |
| `article.components.json` | 组件编排 | 记录插入哪些组件、插入原因、位置和使用 preset | 不直接发布 |
| `article.components.md` | 组件编排 | 带 `:::` 小组件语法的新 Markdown | 后续排版应使用该文件 |
| `article.visual.json` | 视觉计划 | 记录封面 brief、正文配图建议、信息图结构、生成提示词、图片审核清单 | 不生成图片 |
| `article.html` | 锁定预设排版 | 本地 HTML 预览，可用于人工检查和后续草稿箱链路 | 预览成功不等于草稿箱成功 |
| `article.assets.json` | 素材清单 | 记录 HTML 中的图片、封面、远程/本地路径状态 | 上传前检查依据 |
| `article.wechat.html` | 图片回填后 HTML | 将本地图片替换为微信素材 URL 后的 HTML | 需要上传确认 |

## 草稿箱链路产物

| 产物 | 生成阶段 | 用途 | 安全边界 |
| --- | --- | --- | --- |
| `article.draft.json` | 草稿箱 dry-run | 生成可用于微信草稿箱接口的结构化 JSON | dry-run 不调用微信接口 |
| `chain-report.json` | 总控链路报告 | 记录输入、preset、质量审稿、素材状态、草稿箱 JSON、阻断项、下一步 | 团队交接依据 |
| `handoff.md` | 交接报告 | 给运营/审核/发布人员阅读的 Markdown 报告 | 不含密钥 |

## 判断规则

- 如果只有 `article.html`，说明完成了本地预览，不代表能进入草稿箱。
- 如果有 `chain-report.json` 且无阻断项，说明 dry-run 链路完整。
- 如果要真实创建草稿箱，必须额外确认并使用 `--execute --confirm-draftbox`。
- 如果要正式发布或群发，必须在草稿箱后进入人工终审和二次确认。
- 如果要使用小组件，最终排版输入必须是 `article.components.md`，不是原始 `article.md`。
- 如果要使用图片，先检查 `article.visual.json` 和 `article.assets.json`，再决定是否生成、上传或替换图片。
