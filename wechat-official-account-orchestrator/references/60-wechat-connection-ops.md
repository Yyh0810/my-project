# 60 微信公众号接入操作手册

用于把本地 Markdown/HTML 稿件安全送入微信公众号草稿箱。本文面向内部运营、内容编辑和自动化维护人员。

默认目标是“创建草稿箱草稿”，不是正式群发。

## 通路总览

```text
本地 Markdown
-> 本地预检
-> 生成 HTML
-> 生成素材清单
-> 上传正文图片
-> 回填微信图片 URL
-> 上传封面图
-> 生成草稿 JSON
-> 创建公众号草稿箱
-> 后台人工终审
```

## 一次性准备

公众号后台准备：

- 确认账号具备开发者接口权限。
- 获取 `AppID` 和 `AppSecret`。
- 配置接口调用 IP 白名单。
- 确认素材、草稿箱相关接口可用。
- 明确当前操作账号和目标公众号，不跨账号混用。

本机环境变量：

```powershell
[Environment]::SetEnvironmentVariable("WECHAT_APPID", "你的AppID", "User")
[Environment]::SetEnvironmentVariable("WECHAT_APPSECRET", "你的AppSecret", "User")
```

重开 PowerShell 后检查：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_api_draft.py" check-config
```

要求：

- 不在聊天、文档、截图里粘贴 `AppSecret`。
- 不保存 `access_token` 到稿件目录。
- 不把 `.env`、配置截图、接口回执中的敏感字段发给外部人员。

## 日常操作流程

以下示例假设文件在当前工作目录：

```text
article.md
cover.jpg
body-01.png
body-02.png
```

### 优先方式：总控脚本

已有本地稿件时，优先使用总控脚本串联预检、HTML、素材清单、图片回填、草稿 JSON 和草稿箱动作：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\orchestration\wechat_local_to_draft.py" "article.md" --cover "cover.jpg" --preset tech
```

默认是 dry-run，不上传、不创建草稿箱。输出目录默认为：

```text
article.wechat-build\
```

关键产物：

- `article.preflight.json`：本地预检。
- `article.tech.html` 或 `article.source.html`：HTML 预览。
- `article.assets.json`：素材清单。
- `article.quality.json`：内容专业度审稿报告，需传入 `--quality-review`。
- `uploaded-images.json`：正文图片映射。
- `article.wechat.html`：回填后的微信正文 HTML。
- `article.draft.json`：草稿箱 JSON。
- `chain-report.json`：完整链路报告。

用户明确确认“上传图片并创建草稿箱”后，才允许真实执行：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\orchestration\wechat_local_to_draft.py" "article.md" --cover "cover.jpg" --preset tech --execute --confirm-draftbox
```

重要稿件建议先带内容审稿：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\orchestration\wechat_local_to_draft.py" "article.md" --cover "cover.jpg" --preset tech --quality-review
```

团队固定账号可使用非敏感 profile：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\orchestration\wechat_local_to_draft.py" "article.md" --profile tech-internal --quality-review
```

profile 存放在：

```text
C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\assets\profiles\
```

profile 只允许保存账号显示名、默认作者、默认主题、评论开关等非敏感配置；不得保存 `AppSecret`、`access_token`、API key。

需要审稿失败即停止草稿箱产物时：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\orchestration\wechat_local_to_draft.py" "article.md" --cover "cover.jpg" --preset tech --quality-review --strict-quality
```

链路失败后接续执行：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\orchestration\wechat_local_to_draft.py" "article.md" --resume-from rewrite-images --mapping "uploaded-images.json"
```

可接续阶段：

```text
preflight
quality-review
render
assets
upload-images
rewrite-images
cover
draft-json
add-draft
```

接续执行不会伪造前序产物。缺少依赖文件时，脚本会明确报错，并要求从更早阶段恢复。

生成团队交接单：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_handoff_report.py" "article.wechat-build\chain-report.json" --out "handoff.md"
```

如已有正文图片上传映射，可接续链路：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\orchestration\wechat_local_to_draft.py" "article.md" --cover "cover.jpg" --mapping "uploaded-images.json"
```

如已有封面 `thumb_media_id`，可跳过封面上传：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\orchestration\wechat_local_to_draft.py" "article.md" --thumb-media-id "MEDIA_ID" --execute --confirm-draftbox
```

总控脚本仍然只到草稿箱，不包含正式发布或群发。

### 分步方式：排错和接续

当总控脚本阻断、需要定位具体失败点，或只想接续某一步时，再使用下面的分步命令。

### 1. 预检稿件

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\review\article_preflight_check.py" "article.md" --out "article.preflight.json"
```

通过条件：

- 无占位符。
- 标题、摘要、作者等元数据明确。
- 本地图片存在。
- 创意模块不过量。
- 无危险链接协议。

### 2. 生成 HTML 预览

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\formatting\wechat_format_presets.py" "article.md" --preset tech --out "article.html"
```

如需移动端截图自测：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\qa\visual_selftest.py" "article.html" --out-dir "."
```

截图级自测不是默认必跑项。只有复杂表格、代码块、长链接、宽图、重要发布时再跑。

### 3. 生成素材清单

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\assets\image_asset_manifest.py" "article.html" --out "article.assets.json"
```

检查：

- `missing_local` 必须为 `0`。
- `blocked` 必须为 `0`。
- 本地正文图片需要上传到微信后再回填。

### 4. 上传正文图片

先 dry-run：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_api_draft.py" upload-image --image "body-01.png"
```

确认后执行：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_api_draft.py" upload-image --image "body-01.png" --execute
```

把返回的微信图片 URL 写入 `uploaded-images.json`：

```json
{
  "body-01.png": "https://mmbiz.qpic.cn/..."
}
```

### 5. 回填正文图片 URL

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\assets\rewrite_image_sources.py" "article.html" --mapping "uploaded-images.json" --out "article.wechat.html"
```

回填后再次检查：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\assets\image_asset_manifest.py" "article.wechat.html" --out "article.wechat.assets.json"
```

如果视觉自测发现微信图片 URL 坏图，暂停草稿箱步骤，重新上传或核对 URL。

### 6. 上传封面图

先 dry-run：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_api_draft.py" upload-thumb --image "cover.jpg"
```

确认后执行：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_api_draft.py" upload-thumb --image "cover.jpg" --execute
```

记录返回的 `media_id`，它就是草稿箱需要的 `thumb_media_id`。

### 7. 生成草稿 JSON

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_api_draft.py" prepare-article `
  --title "文章标题" `
  --author "作者" `
  --digest "摘要" `
  --content-html "article.wechat.html" `
  --thumb-media-id "上一步返回的media_id" `
  --out "article.draft.json"
```

检查 `article.draft.json`：

- 标题正确。
- 摘要正确。
- `thumb_media_id` 非空。
- `content` 来自 `article.wechat.html`，不是旧 HTML。

### 8. 创建草稿箱草稿

先 dry-run：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_api_draft.py" add-draft --article-json "article.draft.json"
```

确认后执行：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\wechat\wechat_api_draft.py" add-draft --article-json "article.draft.json" --execute
```

成功标准：

- 接口返回成功。
- 拿到草稿相关回执。
- 微信公众平台后台草稿箱能看到该文章。

没有后台确认时，只能说“接口创建草稿成功”，不能说“发布完成”。

## 常见故障

| 现象 | 常见原因 | 处理 |
| --- | --- | --- |
| `check-config` 显示 `secret_present: false` | 没配置 `WECHAT_APPSECRET` | 配置环境变量并重开 PowerShell |
| token 获取失败 | AppID/AppSecret 错误、IP 白名单不匹配 | 核对后台配置和出口 IP |
| 正文图片上传失败 | 图片路径错误、格式/大小不合适、接口权限问题 | 先检查本地路径和文件，再看接口错误 |
| 草稿 JSON 缺 `thumb_media_id` | 没上传封面图 | 先执行 `upload-thumb` |
| HTML 里仍是本地图片路径 | 未执行回填或映射文件不匹配 | 运行 `rewrite_image_sources.py` |
| 视觉自测坏图 | 回填 URL 不可访问或是假 URL | 重新上传图片，使用真实返回 URL |
| 草稿创建失败 | 内容字段不合规、封面素材无效、接口权限不足 | 读接口错误，不伪装成功 |

## 团队交接清单

交给下一位同事前，至少提供：

```text
文章源稿：
HTML 预览：
微信回填 HTML：
素材清单：
预检报告：
封面图：
thumb_media_id：
草稿 JSON：
草稿箱接口回执：
后台人工检查状态：
阻塞项：
```

不要交接：

- AppSecret。
- access token。
- 含密钥的截图。
- 未确认的客户数据。
- 未授权的素材来源。

## 正式发布边界

正式发布或群发不属于默认通路。必须满足：

- 草稿箱已经创建并人工终审。
- 用户明确要求正式发布或群发。
- 再次确认文章标题、目标账号、发布时间和发布边界。

没有二次确认时，停在草稿箱。

正式发布前按 `references/70-formal-release-ops.md` 生成并检查发布门禁文件：

```powershell
python "C:\Users\ASUS\.codex\skills\wechat-official-account-orchestrator\scripts\formal_release_gate.py" "article.release.json" --out "article.release.gate.json"
```

