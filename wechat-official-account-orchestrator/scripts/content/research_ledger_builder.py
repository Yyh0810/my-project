#!/usr/bin/env python3
"""生成和校验公众号公开资料台账。

本脚本不联网、不抓取网页。真实使用时由 Codex 会话先检索公开资料，
再把来源固化为 JSON，交给本脚本校验和格式化。
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


ARTICLE_TYPES = {
    "security-analysis": "安全分析",
    "agent-observation": "AI Agent 观察",
    "product-launch": "产品发布",
    "industry-observation": "行业观察",
    "case-review": "案例复盘",
}

REQUIRED_SOURCE_FIELDS = [
    "source_title",
    "url",
    "published_at",
    "accessed_at",
    "source_type",
    "credibility",
    "usable_claims",
    "uncertainties",
    "do_not_use",
]

SOURCE_TYPES = ["official", "research", "media", "vendor", "community", "internal-note", "unknown"]
CREDIBILITY = ["high", "medium", "low", "unknown"]


def empty_source(topic: str) -> dict[str, Any]:
    return {
        "source_title": f"{topic}：待补充公开来源",
        "url": "待补充",
        "published_at": "待补充",
        "accessed_at": date.today().isoformat(),
        "source_type": "unknown",
        "credibility": "unknown",
        "usable_claims": ["待补充"],
        "uncertainties": ["待核验"],
        "do_not_use": ["未确认前不得写成确定事实"],
    }


def read_sources(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    src = Path(path)
    if not src.exists():
        raise SystemExit(f"来源文件不存在：{src}")
    data = json.loads(src.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict) and "sources" in data:
        data = data["sources"]
    if not isinstance(data, list):
        raise SystemExit("来源文件必须是 JSON 数组，或包含 sources 数组的对象。")
    return [item for item in data if isinstance(item, dict)]


def normalize_source(source: dict[str, Any], topic: str) -> dict[str, Any]:
    normalized = empty_source(topic)
    normalized.update(source)
    for key in ["usable_claims", "uncertainties", "do_not_use"]:
        value = normalized.get(key)
        if isinstance(value, str):
            normalized[key] = [value]
        elif not isinstance(value, list):
            normalized[key] = ["待补充"]
        else:
            normalized[key] = [str(item) for item in value if str(item).strip()] or ["待补充"]
    return normalized


def validate_source(source: dict[str, Any]) -> tuple[list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    for field in REQUIRED_SOURCE_FIELDS:
        value = source.get(field)
        if value in (None, "", [], "待补充"):
            issues.append(f"缺少字段或未补充：{field}")
    url = str(source.get("url", ""))
    if url != "待补充" and not re.match(r"^https?://", url, flags=re.I):
        issues.append("url 必须是 http/https 公开链接。")
    if source.get("source_type") not in SOURCE_TYPES:
        warnings.append("source_type 不在建议枚举内。")
    if source.get("credibility") not in CREDIBILITY:
        warnings.append("credibility 不在建议枚举内。")
    if any("待补充" in str(item) for item in source.get("usable_claims", [])):
        warnings.append("可引用结论仍有待补充项。")
    return issues, warnings


def build_ledger(args: argparse.Namespace) -> dict[str, Any]:
    raw_sources = read_sources(args.sources)
    sources = [normalize_source(item, args.topic) for item in raw_sources] or [empty_source(args.topic)]
    source_results = []
    all_issues: list[str] = []
    all_warnings: list[str] = []
    for idx, source in enumerate(sources, start=1):
        issues, warnings = validate_source(source)
        all_issues.extend([f"来源 {idx}：{item}" for item in issues])
        all_warnings.extend([f"来源 {idx}：{item}" for item in warnings])
        source_results.append({"index": idx, "ok": not issues, "issues": issues, "warnings": warnings, **source})
    has_real_source = bool(raw_sources)
    return {
        "ok": has_real_source and not all_issues,
        "topic": args.topic,
        "article_type": args.type,
        "article_type_label": ARTICLE_TYPES[args.type],
        "research_mode": "conversation-web-research",
        "note": "本脚本不联网；缺新材料时，应由 Codex 会话先检索公开资料，再把结果写入本台账。",
        "requires_web_research": not has_real_source,
        "required_fields": REQUIRED_SOURCE_FIELDS,
        "sources": source_results,
        "issues": all_issues,
        "warnings": all_warnings,
    }


def render_markdown(ledger: dict[str, Any]) -> str:
    lines = [
        "# 公开资料台账",
        "",
        f"- 主题：{ledger['topic']}",
        f"- 文章类型：{ledger['article_type']} / {ledger['article_type_label']}",
        f"- 是否需要公开调研：{'是' if ledger['requires_web_research'] else '否'}",
        "",
        "## 来源清单",
        "",
    ]
    for source in ledger["sources"]:
        lines.extend(
            [
                f"### {source['index']}. {source['source_title']}",
                "",
                f"- URL：{source['url']}",
                f"- 发布时间：{source['published_at']}",
                f"- 访问时间：{source['accessed_at']}",
                f"- 来源类型：{source['source_type']}",
                f"- 可信度：{source['credibility']}",
                "- 可引用结论：",
            ]
        )
        for item in source["usable_claims"]:
            lines.append(f"  - {item}")
        lines.append("- 不确定项：")
        for item in source["uncertainties"]:
            lines.append(f"  - {item}")
        lines.append("- 不允许使用项：")
        for item in source["do_not_use"]:
            lines.append(f"  - {item}")
        if source["issues"]:
            lines.append("- 问题：")
            for item in source["issues"]:
                lines.append(f"  - {item}")
        lines.append("")
    lines.extend(["## 使用边界", "", f"> {ledger['note']}"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成和校验公众号公开资料台账；脚本本身不联网。")
    parser.add_argument("--topic", required=True, help="文章主题。")
    parser.add_argument("--type", required=True, choices=sorted(ARTICLE_TYPES), help="文章类型。")
    parser.add_argument("--sources", help="公开来源 JSON 数组或包含 sources 数组的 JSON 文件。")
    parser.add_argument("--format", choices=["json", "markdown"], default=None, help="输出格式；默认按扩展名推断。")
    parser.add_argument("--out", help="输出文件。")
    args = parser.parse_args()

    ledger = build_ledger(args)
    out_format = args.format
    if out_format is None:
        out_format = "markdown" if args.out and Path(args.out).suffix.lower() in {".md", ".markdown"} else "json"
    content = render_markdown(ledger) if out_format == "markdown" else json.dumps(ledger, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"公开资料台账已生成：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
