#!/usr/bin/env python3
"""把本地公众号稿件串成“预检 -> 预览 -> 素材 -> 草稿箱”的总控链路。

默认 dry-run：只生成本地产物和执行计划，不调用微信接口。
真实上传正文图片、封面素材、创建草稿箱，必须同时传入：

  --execute --confirm-draftbox

凭证只从环境变量读取，不打印 AppSecret 或 access_token。
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_ROOT = SCRIPT_DIR.parent
SKILL_DIR = SCRIPT_ROOT.parent
PROFILE_DIR = SKILL_DIR / "assets" / "profiles"
for path in [
    SCRIPT_ROOT / "review",
    SCRIPT_ROOT / "assets",
    SCRIPT_ROOT / "formatting",
    SCRIPT_ROOT / "wechat",
]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from article_preflight_check import check_file, strip_frontmatter  # noqa: E402
from article_quality_review import evaluate as review_article  # noqa: E402
from image_asset_manifest import scan as scan_images  # noqa: E402
from rewrite_image_sources import load_mapping, rewrite  # noqa: E402
from wechat_format_presets import render, resolve_preset, wrap_page  # noqa: E402

import wechat_api_draft as api  # noqa: E402


PHASES = [
    "preflight",
    "quality-review",
    "render",
    "assets",
    "upload-images",
    "rewrite-images",
    "cover",
    "draft-json",
    "add-draft",
]
PHASE_INDEX = {name: idx for idx, name in enumerate(PHASES)}


def dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def write_json(path: Path, obj: Any) -> None:
    path.write_text(dump(obj) + "\n", encoding="utf-8")


def read_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def slug(name: str) -> str:
    clean = re.sub(r"[^\w\u4e00-\u9fff.-]+", "-", name, flags=re.U).strip("-")
    return clean or "article"


def parse_markdown_meta(path: Path) -> dict[str, str]:
    text = read_text(path)
    body, meta = strip_frontmatter(text)
    if not meta.get("title"):
        h1 = re.search(r"^#\s+(.+)$", body, flags=re.M)
        if h1:
            meta["title"] = re.sub(r"`|\*|_", "", h1.group(1)).strip()
    return meta


def derive_metadata(args: argparse.Namespace, src: Path, preflight: dict[str, Any]) -> dict[str, str]:
    meta = parse_markdown_meta(src) if src.suffix.lower() not in {".html", ".htm"} else {}
    return {
        "title": args.title or meta.get("title") or str(preflight.get("title") or "") or src.stem,
        "author": args.author or meta.get("author") or "",
        "digest": args.digest or meta.get("digest") or "",
        "source_url": args.source_url or meta.get("source_url") or "",
    }


def render_or_copy_html(src: Path, out_dir: Path, preset_name: str) -> tuple[Path, str]:
    if src.suffix.lower() in {".html", ".htm"}:
        out = out_dir / f"{slug(src.stem)}.source.html"
        if src.resolve() != out.resolve():
            shutil.copyfile(src, out)
        return out, "输入为 HTML，已复制为链路源 HTML。"

    preset = resolve_preset(preset_name)
    body, title = render(read_text(src), preset)
    out = out_dir / f"{slug(src.stem)}.{preset.name}.html"
    out.write_text(wrap_page(body, preset, title), encoding="utf-8")
    return out, f"Markdown 已按 {preset.name}（{preset.label}）生成 HTML。"


def expected_html_path(src: Path, out_dir: Path, preset_name: str) -> Path:
    if src.suffix.lower() in {".html", ".htm"}:
        return out_dir / f"{slug(src.stem)}.source.html"
    return out_dir / f"{slug(src.stem)}.{resolve_preset(preset_name).name}.html"


def should_run(args: argparse.Namespace, phase: str) -> bool:
    return PHASE_INDEX[phase] >= PHASE_INDEX[args.resume_from]


def require_existing(path: Path, phase: str) -> None:
    if not path.exists():
        raise SystemExit(
            dump(
                {
                    "ok": False,
                    "status": "resume_missing_dependency",
                    "phase": phase,
                    "missing": str(path),
                    "message": "接续执行所需产物不存在。请从更早阶段恢复，或先补齐该文件。",
                }
            )
        )


def load_profile(profile_name: str | None) -> dict[str, Any]:
    if not profile_name:
        return {}
    path = Path(profile_name)
    if not path.suffix:
        path = PROFILE_DIR / f"{profile_name}.json"
    if not path.exists():
        raise SystemExit(f"profile 不存在：{path}")
    profile = read_json_file(path)
    if not isinstance(profile, dict):
        raise SystemExit(f"profile 必须是 JSON 对象：{path}")
    forbidden = {"appsecret", "app_secret", "access_token", "token", "secret", "apikey", "api_key"}
    found = [key for key in profile if key.lower() in forbidden]
    if found:
        raise SystemExit(f"profile 不能包含敏感字段：{', '.join(found)}")
    profile["_path"] = str(path)
    return profile


def apply_profile(args: argparse.Namespace, profile: dict[str, Any]) -> None:
    if not args.author and profile.get("default_author"):
        args.author = str(profile["default_author"])
    if not args.preset and profile.get("default_preset"):
        args.preset = str(profile["default_preset"])
    if args.need_open_comment is None:
        args.need_open_comment = bool(profile.get("need_open_comment", False))
    if args.only_fans_can_comment is None:
        args.only_fans_can_comment = bool(profile.get("only_fans_can_comment", False))
    if args.show_cover_pic is None:
        args.show_cover_pic = bool(profile.get("show_cover_pic", True))
    if not args.preset:
        args.preset = "tech"
    if args.need_open_comment is None:
        args.need_open_comment = False
    if args.only_fans_can_comment is None:
        args.only_fans_can_comment = False
    if args.show_cover_pic is None:
        args.show_cover_pic = True


def summarize_assets(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total": len(records),
        "blocked": sum(1 for r in records if r.get("kind") == "blocked-scheme"),
        "missing_local": sum(1 for r in records if r.get("kind") == "local" and r.get("exists") is False),
        "local": sum(1 for r in records if r.get("kind") == "local"),
        "wechat_url": sum(1 for r in records if r.get("kind") == "wechat-url"),
        "remote_url": sum(1 for r in records if r.get("kind") == "remote-url"),
        "data_image": sum(1 for r in records if r.get("kind") == "data-image"),
    }


def write_asset_manifest(path: Path, html_path: Path, base_dir: Path) -> dict[str, Any]:
    records = scan_images(read_text(html_path), base_dir)
    payload = {
        "file": str(html_path),
        "base_dir": str(base_dir),
        **summarize_assets(records),
        "records": records,
    }
    write_json(path, payload)
    return payload


def local_image_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in manifest.get("records", []) if r.get("kind") == "local"]


def upload_body_images(records: list[dict[str, Any]], token: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    seen: set[str] = set()
    for record in records:
        src = str(record.get("src") or "")
        path_text = str(record.get("path") or "")
        if not src or not path_text or path_text in seen:
            continue
        seen.add(path_text)
        path = Path(path_text)
        result = api.post_multipart(f"{api.UPLOADIMG_URL}?access_token={token}", "media", path)
        url = result.get("url") if isinstance(result, dict) else ""
        if not url:
            raise SystemExit(dump({"ok": False, "message": "正文图片上传未返回 url。", "image": str(path), "response": result}))
        mapping[src] = url
        mapping[path.name] = url
    return mapping


def upload_cover(path: Path, token: str) -> str:
    query = urlencode({"access_token": token, "type": "thumb"})
    result = api.post_multipart(f"{api.ADD_MATERIAL_URL}?{query}", "media", path)
    media_id = result.get("media_id") if isinstance(result, dict) else ""
    if not media_id:
        raise SystemExit(dump({"ok": False, "message": "封面素材上传未返回 media_id。", "image": str(path), "response": result}))
    return media_id


def prepare_draft_payload(metadata: dict[str, str], html_path: Path, thumb_media_id: str, args: argparse.Namespace) -> dict[str, Any]:
    article = {
        "title": metadata["title"],
        "author": metadata["author"],
        "digest": metadata["digest"],
        "content": read_text(html_path),
        "content_source_url": metadata["source_url"],
        "thumb_media_id": thumb_media_id,
        "show_cover_pic": 1 if args.show_cover_pic else 0,
        "need_open_comment": 1 if args.need_open_comment else 0,
        "only_fans_can_comment": 1 if args.only_fans_can_comment else 0,
    }
    return {"articles": [article]}


def load_optional_mapping(path_text: str | None) -> dict[str, str]:
    if not path_text:
        return {}
    path = Path(path_text)
    if not path.exists():
        raise SystemExit(f"图片映射文件不存在：{path}")
    return load_mapping(path)


def load_mapping_from_existing(uploaded_mapping_path: Path) -> dict[str, str]:
    if not uploaded_mapping_path.exists():
        return {}
    return load_mapping(uploaded_mapping_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本地公众号稿件到草稿箱的总控命令链路。默认 dry-run。")
    parser.add_argument("article", help="Markdown 或 HTML 稿件。")
    parser.add_argument("--profile", help="非敏感账号配置名或 JSON 路径，例如 tech-internal。")
    parser.add_argument("--resume-from", choices=PHASES, default="preflight", help="从指定阶段接续执行；会复用此前产物。")
    parser.add_argument("--cover", help="封面图。本地图片会在 execute 时上传为 thumb 素材。")
    parser.add_argument("--thumb-media-id", default="", help="已上传封面素材 media_id；提供后可跳过封面上传。")
    parser.add_argument("--preset", default="", help="Markdown 转 HTML 主题预设。HTML 输入会忽略。")
    parser.add_argument("--out-dir", help="链路产物目录；默认 <稿件名>.wechat-build。")
    parser.add_argument("--title", default="", help="覆盖标题。默认从 frontmatter 或 H1 读取。")
    parser.add_argument("--author", default="", help="覆盖作者。默认从 frontmatter 读取。")
    parser.add_argument("--digest", default="", help="覆盖摘要。默认从 frontmatter 读取。")
    parser.add_argument("--source-url", default="", help="原文链接。")
    parser.add_argument("--mapping", help="已上传正文图片映射 JSON，用于 dry-run 或接续链路。")
    parser.add_argument("--quality-review", action="store_true", help="生成内容专业度审稿报告。")
    parser.add_argument("--strict-quality", action="store_true", help="审稿未通过时阻断草稿箱 JSON 生成。")
    parser.add_argument("--execute", action="store_true", help="允许真实上传正文图片、封面素材并创建草稿箱。")
    parser.add_argument("--confirm-draftbox", action="store_true", help="二次确认：本次真实动作目标只到草稿箱。")
    parser.add_argument("--no-upload-body-images", action="store_true", help="execute 时不自动上传正文本地图片，要求通过 --mapping 提供 URL。")
    parser.add_argument("--skip-add-draft", action="store_true", help="只生成草稿 JSON，不创建草稿箱。")
    parser.add_argument("--show-cover-pic", action=argparse.BooleanOptionalAction, default=None, help="草稿是否显示封面。")
    parser.add_argument("--need-open-comment", action=argparse.BooleanOptionalAction, default=None, help="开启评论。")
    parser.add_argument("--only-fans-can-comment", action=argparse.BooleanOptionalAction, default=None, help="仅粉丝可评论。")
    parser.add_argument("--appid-env", default="WECHAT_APPID", help="AppID 环境变量名。")
    parser.add_argument("--secret-env", default="WECHAT_APPSECRET", help="AppSecret 环境变量名。")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    src = Path(args.article)
    if not src.exists():
        raise SystemExit(f"稿件不存在：{src}")
    src = src.resolve()
    out_dir = Path(args.out_dir) if args.out_dir else src.with_name(f"{slug(src.stem)}.wechat-build")
    out_dir.mkdir(parents=True, exist_ok=True)
    profile = load_profile(args.profile)
    apply_profile(args, profile)

    if args.execute and not args.confirm_draftbox:
        raise SystemExit("真实链路必须同时传入 --execute --confirm-draftbox，确认本次只创建草稿箱，不正式发布。")

    stage: list[dict[str, Any]] = []
    stem = slug(src.stem)

    preflight_path = out_dir / f"{stem}.preflight.json"
    if should_run(args, "preflight"):
        preflight = check_file(src)
        write_json(preflight_path, preflight)
        stage.append({"name": "本地预检", "ok": bool(preflight.get("ok")), "output": str(preflight_path)})
    else:
        require_existing(preflight_path, "preflight")
        preflight = read_json_file(preflight_path)
        stage.append({"name": "本地预检", "ok": bool(preflight.get("ok")), "output": str(preflight_path), "reused": True})
    if preflight.get("issues"):
        report = {
            "ok": False,
            "dry_run": not args.execute,
            "status": "blocked_before_formatting",
            "message": "预检存在阻断问题，已停止草稿箱链路。",
            "issues": preflight.get("issues"),
            "outputs": {"preflight": str(preflight_path)},
            "stages": stage,
        }
        write_json(out_dir / "chain-report.json", report)
        print(dump(report))
        raise SystemExit(1)

    quality_review: dict[str, Any] | None = None
    quality_path: Path | None = None
    if args.quality_review or args.strict_quality:
        quality_path = out_dir / f"{stem}.quality.json"
        if should_run(args, "quality-review"):
            quality_review = review_article(src)
            write_json(quality_path, quality_review)
            reused_quality = False
        else:
            require_existing(quality_path, "quality-review")
            quality_review = read_json_file(quality_path)
            reused_quality = True
        stage.append(
            {
                "name": "内容审稿质检",
                "ok": bool(quality_review.get("ok")),
                "output": str(quality_path),
                "score": quality_review.get("score"),
                "blocking": quality_review.get("blocking", []),
                **({"reused": True} if reused_quality else {}),
            }
        )
        if args.strict_quality and not quality_review.get("ok"):
            report = {
                "ok": False,
                "dry_run": not args.execute,
                "status": "blocked_by_quality_review",
                "message": "内容审稿质检未通过，已停止草稿箱链路。",
                "outputs": {"preflight": str(preflight_path), "quality_review": str(quality_path)},
                "quality_review": {
                    "path": str(quality_path),
                    "ok": bool(quality_review.get("ok")),
                    "score": quality_review.get("score"),
                    "blocking": quality_review.get("blocking", []),
                },
                "stages": stage,
            }
            write_json(out_dir / "chain-report.json", report)
            print(dump(report))
            raise SystemExit(1)

    html_path = expected_html_path(src, out_dir, args.preset)
    if should_run(args, "render"):
        html_path, render_note = render_or_copy_html(src, out_dir, args.preset)
        stage.append({"name": "生成 HTML 预览", "ok": True, "output": str(html_path), "note": render_note})
    else:
        require_existing(html_path, "render")
        stage.append({"name": "生成 HTML 预览", "ok": True, "output": str(html_path), "reused": True})

    base_dir = src.parent
    assets_path = out_dir / f"{stem}.assets.json"
    if should_run(args, "assets"):
        assets = write_asset_manifest(assets_path, html_path, base_dir)
        stage.append({"name": "生成素材清单", "ok": assets["blocked"] == 0 and assets["missing_local"] == 0, "output": str(assets_path), "summary": summarize_assets(assets.get("records", []))})
    else:
        require_existing(assets_path, "assets")
        assets = read_json_file(assets_path)
        stage.append({"name": "生成素材清单", "ok": assets["blocked"] == 0 and assets["missing_local"] == 0, "output": str(assets_path), "summary": summarize_assets(assets.get("records", [])), "reused": True})
    if assets["blocked"] or assets["missing_local"]:
        report = {
            "ok": False,
            "dry_run": not args.execute,
            "status": "blocked_by_assets",
            "message": "素材清单存在阻断问题，已停止草稿箱链路。",
            "outputs": {"html": str(html_path), "assets": str(assets_path), "preflight": str(preflight_path)},
            "stages": stage,
        }
        write_json(out_dir / "chain-report.json", report)
        print(dump(report))
        raise SystemExit(1)

    mapping = load_optional_mapping(args.mapping)
    token = ""
    uploaded_mapping_path = out_dir / "uploaded-images.json"
    if not should_run(args, "upload-images"):
        if not mapping:
            mapping = load_mapping_from_existing(uploaded_mapping_path)
        if not args.mapping:
            require_existing(uploaded_mapping_path, "upload-images")
        stage.append({"name": "正文图片上传", "ok": True, "output": str(uploaded_mapping_path), "reused": True, "count": len(mapping)})
    elif args.execute:
        namespace = argparse.Namespace(appid_env=args.appid_env, secret_env=args.secret_env)
        token = api.get_access_token(namespace)
        if not args.no_upload_body_images:
            mapping.update(upload_body_images(local_image_records(assets), token))
            write_json(uploaded_mapping_path, {"mapping": mapping})
            stage.append({"name": "上传正文图片", "ok": True, "output": str(uploaded_mapping_path), "count": len(mapping)})
        elif local_image_records(assets) and not mapping:
            raise SystemExit("存在本地正文图片，但已设置 --no-upload-body-images 且未提供 --mapping。")
    else:
        write_json(uploaded_mapping_path, {"mapping": mapping})
        stage.append({"name": "正文图片上传", "ok": True, "dry_run": True, "output": str(uploaded_mapping_path), "note": "dry-run 未上传；如提供 --mapping，会用于回填预览。"})

    if args.execute and not token and (should_run(args, "cover") or should_run(args, "add-draft")):
        namespace = argparse.Namespace(appid_env=args.appid_env, secret_env=args.secret_env)
        token = api.get_access_token(namespace)

    wechat_html_path = out_dir / f"{stem}.wechat.html"
    if should_run(args, "rewrite-images"):
        html_text = read_text(html_path)
        rewritten, replaced = rewrite(html_text, mapping) if mapping else (html_text, [])
        wechat_html_path.write_text(rewritten, encoding="utf-8")
        stage.append({"name": "回填微信图片 URL", "ok": True, "output": str(wechat_html_path), "replaced": len(replaced)})
    else:
        require_existing(wechat_html_path, "rewrite-images")
        stage.append({"name": "回填微信图片 URL", "ok": True, "output": str(wechat_html_path), "reused": True})

    wechat_assets_path = out_dir / f"{stem}.wechat.assets.json"
    if should_run(args, "rewrite-images"):
        wechat_assets = write_asset_manifest(wechat_assets_path, wechat_html_path, base_dir)
        stage.append({"name": "回填后素材复查", "ok": wechat_assets["blocked"] == 0 and wechat_assets["missing_local"] == 0, "output": str(wechat_assets_path), "summary": summarize_assets(wechat_assets.get("records", []))})
    else:
        require_existing(wechat_assets_path, "rewrite-images")
        wechat_assets = read_json_file(wechat_assets_path)
        stage.append({"name": "回填后素材复查", "ok": wechat_assets["blocked"] == 0 and wechat_assets["missing_local"] == 0, "output": str(wechat_assets_path), "summary": summarize_assets(wechat_assets.get("records", [])), "reused": True})

    metadata = derive_metadata(args, src, preflight)
    thumb_media_id = args.thumb_media_id
    cover_path = Path(args.cover).resolve() if args.cover else None
    if not should_run(args, "cover"):
        stage.append({"name": "封面素材", "ok": True, "thumb_media_id": thumb_media_id or "REUSED_OR_NOT_REQUIRED", "reused": True})
        if not thumb_media_id:
            thumb_media_id = "REUSED_THUMB_MEDIA_ID_REQUIRED_BEFORE_EXECUTE"
    elif args.execute and not thumb_media_id:
        if not cover_path:
            raise SystemExit("真实创建草稿箱前必须提供 --cover 或 --thumb-media-id。")
        if not cover_path.exists():
            raise SystemExit(f"封面图不存在：{cover_path}")
        thumb_media_id = upload_cover(cover_path, token)
        stage.append({"name": "上传封面素材", "ok": True, "cover": str(cover_path), "thumb_media_id": thumb_media_id})
    elif not thumb_media_id:
        thumb_media_id = "DRY_RUN_THUMB_MEDIA_ID_REQUIRED_BEFORE_EXECUTE"
        stage.append({"name": "封面素材", "ok": True, "dry_run": True, "cover": str(cover_path) if cover_path else "", "note": "dry-run 使用占位 thumb_media_id；真实执行前必须上传封面或提供 media_id。"})
    else:
        stage.append({"name": "封面素材", "ok": True, "thumb_media_id": thumb_media_id, "note": "使用已提供 thumb_media_id。"})

    draft_path = out_dir / f"{stem}.draft.json"
    if should_run(args, "draft-json"):
        draft_payload = prepare_draft_payload(metadata, wechat_html_path, thumb_media_id, args)
        write_json(draft_path, draft_payload)
        stage.append({"name": "生成草稿 JSON", "ok": True, "output": str(draft_path), "title": metadata["title"]})
    else:
        require_existing(draft_path, "draft-json")
        draft_payload = read_json_file(draft_path)
        stage.append({"name": "生成草稿 JSON", "ok": True, "output": str(draft_path), "title": metadata["title"], "reused": True})

    draft_result: dict[str, Any] = {"skipped": True, "reason": "dry-run 或 --skip-add-draft"}
    if not should_run(args, "add-draft"):
        stage.append({"name": "创建公众号草稿箱", "ok": True, "skipped": True, "reused": True})
    elif args.execute and not args.skip_add_draft:
        result = api.post_json(f"{api.ADD_DRAFT_URL}?access_token={token}", draft_payload)
        draft_result = {"ok": True, "result": result}
        stage.append({"name": "创建公众号草稿箱", "ok": True, "result": result})
    else:
        stage.append({"name": "创建公众号草稿箱", "ok": True, "dry_run": not args.execute, "skipped": True})

    report = {
        "ok": True,
        "dry_run": not args.execute,
        "status": "draftbox_created" if args.execute and not args.skip_add_draft else "draftbox_ready_dry_run",
        "message": "链路已完成到草稿箱创建。" if args.execute and not args.skip_add_draft else "链路已完成本地演练，未调用微信草稿箱接口。",
        "metadata": {k: v for k, v in metadata.items() if k != "source_url" or v},
        "formatting": {
            "preset": args.preset,
            "html_input": src.suffix.lower() in {".html", ".htm"},
        },
        "profile": (
            {
                "path": profile.get("_path", ""),
                "profile_name": profile.get("profile_name", ""),
                "account_name": profile.get("account_name", ""),
                "content_direction": profile.get("content_direction", ""),
            }
            if profile
            else None
        ),
        "resume_from": args.resume_from,
        "outputs": {
            "preflight": str(preflight_path),
            **({"quality_review": str(quality_path)} if quality_path else {}),
            "html": str(html_path),
            "assets": str(assets_path),
            "uploaded_images": str(uploaded_mapping_path),
            "wechat_html": str(wechat_html_path),
            "wechat_assets": str(wechat_assets_path),
            "draft_json": str(draft_path),
            "report": str(out_dir / "chain-report.json"),
        },
        "quality_review": (
            {
                "path": str(quality_path),
                "ok": bool(quality_review.get("ok")),
                "score": quality_review.get("score"),
                "blocking": quality_review.get("blocking", []),
            }
            if quality_review and quality_path
            else None
        ),
        "draft_result": draft_result,
        "stages": stage,
        "safety_note": "正式发布/群发不在本脚本范围内；草稿箱之后必须后台人工终审和二次确认。",
    }
    write_json(out_dir / "chain-report.json", report)
    print(dump(report))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
