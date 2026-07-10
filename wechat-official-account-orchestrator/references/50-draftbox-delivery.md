# 50 草稿箱与交付

用于草稿箱准备、上传、回执、失败处理、正式发布边界。

首次接入公众号、本机配置环境变量、团队交接时，先阅读 `references/60-wechat-connection-ops.md`。

## 草稿箱前置条件

进入草稿箱前确认：

- 用户明确接受草稿箱作为目标。
- 正文已经定稿。
- HTML 或预览已经生成，且来自当前定稿。
- 封面图和正文图片状态明确。
- 标题、作者、摘要等元数据完整。
- 内容、排版、图片、发布安全质量门禁通过。
- 预览和草稿箱动作已区分：预览不上传，草稿箱可能上传。
- 使用接口时，确认图片上传、封面素材、账号凭证、IP 白名单等阻塞项。

用户没有明确要求草稿箱时，只给就绪报告。用户明确要求正式发布时，也必须先完成草稿箱/终审确认，不能直接跳到群发。

## 就绪检查

- 标题、作者、摘要、正文来源完整。
- 封面图存在，或已有可用封面素材 ID。
- 正文图片存在、可上传、路径正确。
- 正文无 `TODO`、`placeholder`、`待补充` 等占位内容。
- 目标公众号账号明确。
- 本地凭证或环境变量满足草稿箱动作要求。
- 如果接口上传，access token、图片上传、草稿创建是分开的步骤。

默认使用本 skill 自带脚本做就绪检查。只有用户明确要求使用 `md2wechat` 时，才运行：

```bash
md2wechat inspect <article.md> --json
md2wechat doctor --json
md2wechat config show --format json
md2wechat config wechat-accounts --json
```

从命令输出读取阻塞项，不编造字段。

## 微信 API 草稿箱脚本

已有 Markdown 或 HTML 稿件时，优先使用总控脚本完成可信链路：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech
```

它默认只 dry-run。真实上传并创建草稿箱时，必须由用户明确确认后使用：

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --cover cover.png --preset tech --execute --confirm-draftbox
```

分步脚本用于排错、接续已有素材或验证单个环节。

接口失败时先查 `references/80-wechat-api-errors.md`。修复后优先使用 `--resume-from` 接续，不要反复从头执行真实上传。

使用内置脚本处理微信接口时，始终先 dry-run：

```bash
python scripts/wechat/wechat_api_draft.py check-config
python scripts/wechat/wechat_api_draft.py upload-image --image body.png
python scripts/wechat/wechat_api_draft.py upload-thumb --image cover.png
python scripts/wechat/wechat_api_draft.py prepare-article --title "标题" --content-html article.html --thumb-media-id MEDIA_ID --out article.draft.json
python scripts/wechat/wechat_api_draft.py add-draft --article-json article.draft.json
```

真实上传或创建草稿时，必须在用户确认后加 `--execute`。不要在聊天里索要或打印 AppSecret、access token；脚本只从环境变量读取：

- `WECHAT_APPID`
- `WECHAT_APPSECRET`

接口阶段要分清：

- `upload-image`：上传正文图片，返回可写入正文的微信图片 URL。
- `upload-thumb`：上传封面缩略图永久素材，返回 `thumb_media_id`。
- `prepare-article`：组装草稿箱 JSON，不调用接口。
- `add-draft`：创建草稿箱草稿，成功后以接口回执为准。

## 图片上传与素材管理

进入草稿箱前先生成素材清单：

```bash
python scripts/assets/image_asset_manifest.py article.html --out article.assets.json
```

按清单逐项处理：

- 本地图片：检查存在、尺寸、版权、敏感信息，再决定上传为正文图片或封面素材。
- 远程图片：确认版权和可访问性；不稳定时下载后上传到微信。
- 微信图片 URL：仍需预览确认显示。
- Base64 图片：导出为文件后再上传。
- 危险协议或缺失文件：阻断草稿箱。

正文图片上传成功后，要把本地图片路径替换成微信返回的 URL，再进入草稿箱 JSON：

```bash
python scripts/assets/rewrite_image_sources.py article.html --mapping uploaded-images.json --out article.wechat.html
```

映射文件示例：

```json
{
  "bad-epoll-01-overview.png": "https://mmbiz.qpic.cn/..."
}
```

替换后重新运行素材清单或预检，确认正文不再依赖本地图片路径。

## 失败处理

- 草稿失败，不说“已创建草稿”。
- 图片上传成功但草稿创建失败，要明确停在图片上传后。
- 预览成功不能推断草稿箱成功。
- 草稿箱成功不能推断正式群发完成。
- 给出用户可修复的下一步，不只说“配置有问题”。

## 正式发布

正式发布不是默认流程。需要继续时，转入 `references/70-formal-release-ops.md`。继续前必须同时满足：

- 用户明确要求正式发布或群发。
- 最终产物通过终审。
- 账号明确。
- 用户看到最终标题、账号和发布边界后，给出第二次明确确认。

缺任一项，停在草稿箱或就绪报告。

## 交付格式

```text
当前状态：
文章：
预览：
封面：
正文图片：
质量检查：
草稿箱：
阻塞项：
下一步：
```

