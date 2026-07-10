#!/usr/bin/env python3
"""微信公众号正式发布前的门禁检查。

本脚本不调用发布接口，只检查正式发布所需证据是否齐全。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REQUIRED = [
    "account_name",
    "article_title",
    "draft_status",
    "backend_review",
    "quality_result",
    "second_confirmation",
    "release_boundary",
]


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "y", "1", "通过", "已确认", "confirmed"}
    return bool(value)


def check(data: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    for key in REQUIRED:
        if key not in data or data[key] in ("", None):
            issues.append(f"缺少字段：{key}")

    if str(data.get("draft_status", "")).strip() not in {"草稿箱已创建", "后台可见", "draft_created"}:
        issues.append("草稿箱状态不是已创建/后台可见。")
    if not truthy(data.get("backend_review")):
        issues.append("后台人工终审未确认。")
    if str(data.get("quality_result", "")).strip() not in {"通过", "pass", "passed"}:
        issues.append("质量结论未通过。")
    if not truthy(data.get("second_confirmation")):
        issues.append("缺少正式发布二次确认。")

    boundary = str(data.get("release_boundary", ""))
    if not any(word in boundary for word in ["正式发布", "群发", "发布到公众号"]):
        warnings.append("发布边界描述不够明确，应写清是否正式发布/群发。")

    if data.get("scheduled_time") and not data.get("timezone"):
        warnings.append("设置了发布时间但未写明时区。")

    return {
        "ok": not issues,
        "issues": issues,
        "warnings": warnings,
        "evidence": {
            "account_name": data.get("account_name", ""),
            "article_title": data.get("article_title", ""),
            "draft_status": data.get("draft_status", ""),
            "release_boundary": data.get("release_boundary", ""),
            "scheduled_time": data.get("scheduled_time", ""),
        },
        "note": "本脚本只做正式发布门禁检查，不调用微信发布接口。",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="正式发布前门禁检查，不产生发布副作用。")
    parser.add_argument("release_json", help="正式发布确认 JSON。")
    parser.add_argument("--out", help="输出检查结果 JSON。")
    args = parser.parse_args()

    src = Path(args.release_json)
    if not src.exists():
        raise SystemExit(f"文件不存在：{src}")
    data = json.loads(src.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise SystemExit("release_json 必须是 JSON 对象。")
    result = check(data)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"正式发布门禁结果已生成：{args.out}")
    else:
        print(text)


if __name__ == "__main__":
    main()
