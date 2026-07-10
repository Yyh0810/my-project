#!/usr/bin/env python3
"""微信公众平台草稿箱与素材上传辅助脚本。

默认只做 dry-run。只有显式传入 --execute 才会调用微信接口。
凭证只从环境变量读取，避免出现在命令历史和聊天记录中。
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from wechat_error_utils import explain_wechat_error


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
UPLOADIMG_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
ADD_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
ADD_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"


def dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def print_json(obj: Any) -> None:
    print(dump(obj))


def mask(value: str | None) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "*" * len(value)
    return value[:4] + "*" * (len(value) - 8) + value[-4:]


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def require_execute(args: argparse.Namespace, action: str) -> None:
    if not args.execute:
        print_json(
            {
                "ok": False,
                "dry_run": True,
                "action": action,
                "message": "未传入 --execute，已阻止真实微信接口调用。",
            }
        )
        raise SystemExit(2)


def credentials(args: argparse.Namespace) -> tuple[str, str]:
    appid = os.environ.get(args.appid_env, "")
    secret = os.environ.get(args.secret_env, "")
    missing = [name for name, value in [(args.appid_env, appid), (args.secret_env, secret)] if not value]
    if missing:
        raise SystemExit(f"缺少环境变量：{', '.join(missing)}")
    return appid, secret


def request_json(url: str, data: bytes | None = None, headers: dict[str, str] | None = None) -> Any:
    req = Request(url, data=data, headers=headers or {})
    with urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit(f"接口返回不是 JSON：{raw[:500]}")
    if isinstance(result, dict) and result.get("errcode") not in (None, 0):
        raise SystemExit(dump({"ok": False, "wechat_error": result, "explanation": explain_wechat_error(result)}))
    return result


def get_access_token(args: argparse.Namespace) -> str:
    appid, secret = credentials(args)
    query = urlencode({"grant_type": "client_credential", "appid": appid, "secret": secret})
    result = request_json(f"{TOKEN_URL}?{query}")
    token = result.get("access_token")
    if not token:
        raise SystemExit(dump({"ok": False, "message": "微信未返回 access_token。", "response": result}))
    return token


def post_json(url: str, payload: Any) -> Any:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return request_json(url, body, {"Content-Type": "application/json; charset=utf-8"})


def post_multipart(url: str, file_field: str, file_path: Path) -> Any:
    if not file_path.exists():
        raise SystemExit(f"文件不存在：{file_path}")
    boundary = "----CodexWechatBoundary" + uuid.uuid4().hex
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    chunks: list[bytes] = []
    chunks.append(f"--{boundary}\r\n".encode("utf-8"))
    chunks.append(
        (
            f'Content-Disposition: form-data; name="{file_field}"; '
            f'filename="{file_path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(file_path.read_bytes())
    chunks.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(chunks)
    return request_json(url, body, {"Content-Type": f"multipart/form-data; boundary={boundary}"})


def cmd_check_config(args: argparse.Namespace) -> None:
    appid = os.environ.get(args.appid_env, "")
    secret = os.environ.get(args.secret_env, "")
    print_json(
        {
            "ok": bool(appid and secret),
            "dry_run": True,
            "appid_env": args.appid_env,
            "appid": mask(appid) if appid else "",
            "secret_env": args.secret_env,
            "secret_present": bool(secret),
            "endpoints": {
                "token": TOKEN_URL,
                "upload_article_image": UPLOADIMG_URL,
                "add_permanent_material": ADD_MATERIAL_URL,
                "add_draft": ADD_DRAFT_URL,
            },
            "note": "不会打印 AppSecret 或 access_token。",
        }
    )


def cmd_prepare_article(args: argparse.Namespace) -> None:
    content = read_text(args.content_html)
    article: dict[str, Any] = {
        "title": args.title,
        "author": args.author or "",
        "digest": args.digest or "",
        "content": content,
        "content_source_url": args.source_url or "",
        "thumb_media_id": args.thumb_media_id or "",
        "show_cover_pic": 1 if args.show_cover_pic else 0,
        "need_open_comment": 1 if args.need_open_comment else 0,
        "only_fans_can_comment": 1 if args.only_fans_can_comment else 0,
    }
    payload = {"articles": [article]}
    if args.out:
        Path(args.out).write_text(dump(payload) + "\n", encoding="utf-8")
        print_json({"ok": True, "dry_run": True, "output": str(Path(args.out)), "articles": 1})
    else:
        print_json(payload)


def cmd_upload_image(args: argparse.Namespace) -> None:
    path = Path(args.image)
    if not args.execute:
        print_json(
            {
                "ok": path.exists(),
                "dry_run": True,
                "action": "upload_article_image",
                "endpoint": UPLOADIMG_URL,
                "image": str(path),
                "exists": path.exists(),
                "note": "传入 --execute 后会上传正文图片并返回微信图片 URL。",
            }
        )
        return
    token = get_access_token(args)
    result = post_multipart(f"{UPLOADIMG_URL}?access_token={token}", "media", path)
    print_json({"ok": True, "action": "upload_article_image", "result": result})


def cmd_upload_thumb(args: argparse.Namespace) -> None:
    path = Path(args.image)
    if not args.execute:
        print_json(
            {
                "ok": path.exists(),
                "dry_run": True,
                "action": "upload_thumb_material",
                "endpoint": ADD_MATERIAL_URL,
                "image": str(path),
                "exists": path.exists(),
                "note": "传入 --execute 后会新增永久 thumb 素材并返回 thumb_media_id。",
            }
        )
        return
    token = get_access_token(args)
    query = urlencode({"access_token": token, "type": "thumb"})
    result = post_multipart(f"{ADD_MATERIAL_URL}?{query}", "media", path)
    print_json({"ok": True, "action": "upload_thumb_material", "result": result})


def cmd_add_draft(args: argparse.Namespace) -> None:
    payload = read_json(args.article_json)
    if isinstance(payload, dict) and "articles" not in payload:
        payload = {"articles": [payload]}
    articles = payload.get("articles") if isinstance(payload, dict) else None
    if not isinstance(articles, list) or not articles:
        raise SystemExit("article-json 必须是 article 对象或包含 articles 数组的对象。")
    missing_thumb = [idx for idx, item in enumerate(articles) if not item.get("thumb_media_id")]
    if missing_thumb:
        raise SystemExit(f"缺少 thumb_media_id 的文章索引：{missing_thumb}")
    if not args.execute:
        print_json(
            {
                "ok": True,
                "dry_run": True,
                "action": "add_draft",
                "endpoint": ADD_DRAFT_URL,
                "articles": len(articles),
                "titles": [item.get("title", "") for item in articles],
                "note": "传入 --execute 后会创建公众号草稿箱草稿。",
            }
        )
        return
    token = get_access_token(args)
    result = post_json(f"{ADD_DRAFT_URL}?access_token={token}", payload)
    print_json({"ok": True, "action": "add_draft", "result": result})


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--execute", action="store_true", help="允许真实调用微信接口；默认只 dry-run。")
    parser.add_argument("--appid-env", default="WECHAT_APPID", help="AppID 环境变量名。")
    parser.add_argument("--secret-env", default="WECHAT_APPSECRET", help="AppSecret 环境变量名。")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="微信草稿箱与素材上传辅助脚本，默认不产生副作用。")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("check-config", help="检查本机环境变量和接口配置。")
    add_common(p)
    p.set_defaults(func=cmd_check_config)

    p = sub.add_parser("prepare-article", help="把 HTML 和元数据组装为 draft/add JSON。")
    add_common(p)
    p.add_argument("--title", required=True)
    p.add_argument("--content-html", required=True)
    p.add_argument("--thumb-media-id", default="")
    p.add_argument("--author", default="")
    p.add_argument("--digest", default="")
    p.add_argument("--source-url", default="")
    p.add_argument("--show-cover-pic", action="store_true", default=True)
    p.add_argument("--need-open-comment", action="store_true")
    p.add_argument("--only-fans-can-comment", action="store_true")
    p.add_argument("--out", help="输出 JSON 文件。")
    p.set_defaults(func=cmd_prepare_article)

    p = sub.add_parser("upload-image", help="上传正文内图片，返回可写入正文的微信图片 URL。")
    add_common(p)
    p.add_argument("--image", required=True)
    p.set_defaults(func=cmd_upload_image)

    p = sub.add_parser("upload-thumb", help="上传封面缩略图为永久 thumb 素材，返回 media_id。")
    add_common(p)
    p.add_argument("--image", required=True)
    p.set_defaults(func=cmd_upload_thumb)

    p = sub.add_parser("add-draft", help="调用 draft/add 创建草稿箱草稿。")
    add_common(p)
    p.add_argument("--article-json", required=True)
    p.set_defaults(func=cmd_add_draft)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        raise SystemExit(130)


if __name__ == "__main__":
    main()
