# 80 微信 API 错误处理

用于微信素材上传、封面素材、草稿箱创建失败后的排查。脚本会尽量输出 `reason`、`likely_causes`、`next_steps`，但接口错误仍以微信回执为准。

## 处理原则

- 不重复盲目执行 `--execute`。
- 保留 `chain-report.json` 和接口错误回执。
- 先区分配置问题、权限问题、素材问题、内容问题。
- 修复后优先使用 `--resume-from` 从失败阶段接续。
- 不把 AppSecret、access_token 或含密钥截图发给他人。

## 常见错误

| errcode | 含义 | 常见原因 | 处理 |
| --- | --- | --- | --- |
| `-1` | 系统繁忙 | 微信平台短暂不可用、网络抖动 | 稍后重试，从失败阶段接续 |
| `40001` | access_token 无效 | AppID/AppSecret 不匹配、凭证变更 | 检查环境变量和后台配置 |
| `40013` | AppID 不合法 | AppID 配错、账号类型不对 | 从公众号后台重新复制 AppID |
| `40014` | access_token 不合法 | token 过期或旧 token | 重新执行接口步骤 |
| `40037` | media_id 不合法 | thumb_media_id 不属于当前账号或已失效 | 重新上传封面素材 |
| `40064` | IP 不在白名单 | 出口 IP 未配置或变更 | 在公众号后台配置当前出口 IP |
| `41001` | 缺少 access_token | token 获取失败、AppSecret 缺失 | 先运行 `check-config` |
| `41005` | 缺少 media 数据 | 图片路径错误、文件为空 | 检查素材清单和本地文件 |
| `45009` | 接口调用频率超过限制 | 短时间重复上传或创建草稿 | 降低重试频率，稍后接续 |
| `45029` | 调用频率过高 | 自动重试过快 | 停止重复执行 |
| `48001` | 接口权限不足 | 账号未开通接口或类型不支持 | 检查公众号后台接口权限 |

## 推荐接续方式

图片上传失败：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --resume-from upload-images --execute --confirm-draftbox
```

已有正文图片映射，只需回填：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --mapping uploaded-images.json --resume-from rewrite-images
```

封面素材失败：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --resume-from cover --cover cover.png --execute --confirm-draftbox
```

草稿箱创建失败：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --resume-from add-draft --thumb-media-id MEDIA_ID --execute --confirm-draftbox
```

正式发布失败不在本链路内处理。正式发布必须走 `70-formal-release-ops.md` 的门禁。

