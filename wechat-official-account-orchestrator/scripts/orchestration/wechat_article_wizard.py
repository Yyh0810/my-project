#!/usr/bin/env python3
"""生成微信公众号总控的下一步引导，不执行实际链路。"""

from __future__ import annotations

import argparse
from pathlib import Path


ARTICLE_TYPES = {
    "security-analysis": "安全分析",
    "agent-observation": "AI Agent 观察",
    "product-launch": "产品发布",
    "industry-observation": "行业观察",
    "case-review": "案例复盘",
}

MODES = {
    "new": "从 0 新做一篇",
    "existing": "接续已有稿件",
    "preview": "生成组件版与 HTML 预览",
    "draft-dry-run": "草稿箱 dry-run 链路",
}


def quote(value: str | Path) -> str:
    text = str(value).replace('"', '\\"')
    return f'"{text}"'


def command(parts: list[str | Path]) -> str:
    rendered: list[str] = []
    for part in parts:
        text = str(part)
        if text.startswith("--") or text == "python":
            rendered.append(text)
        elif text.startswith("scripts/"):
            rendered.append(text)
        else:
            rendered.append(quote(text))
    return " ".join(rendered)


def build_new(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    topic = args.topic or "待补充主题"
    audience = args.audience or "待补充目标读者"
    article_type = args.article_type
    next_steps = [
        "确认主题、目标读者、文章类型和是否已有新物料。",
        "如果没有新物料，先由 Codex 会话联网检索公开资料，再把来源写入资料台账；脚本本身不联网、不伪造来源。",
        "基于资料台账生成论证链，再进入标题、大纲和写作包。",
        "把写作包转换为初稿提示词后，再交给模型生成可审稿 Markdown。",
    ]
    commands = [
        command(["python", "scripts/content/research_ledger_builder.py", "--topic", topic, "--type", article_type, "--out", "article.research-ledger.json"]),
        command(["python", "scripts/content/article_argument_chain.py", "--topic", topic, "--type", article_type, "--ledger", "article.research-ledger.json", "--out", "article.argument-chain.json"]),
        command(["python", "scripts/content/title_strategy.py", "--topic", topic, "--type", article_type, "--out", "article.titles.json"]),
        command(["python", "scripts/content/article_outline_builder.py", "--topic", topic, "--type", article_type, "--audience", audience, "--out", "article.outline.md"]),
        command(["python", "scripts/content/article_writing_pack.py", "--topic", topic, "--type", article_type, "--audience", audience, "--outline", "article.outline.md", "--argument-chain", "article.argument-chain.json", "--out", "article.writing-pack.json"]),
        command(["python", "scripts/content/article_draft_prompt_builder.py", "article.writing-pack.json", "--out", "article.draft-prompt.md"]),
    ]
    return next_steps, commands


def build_existing(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    article = args.article
    article_type = args.article_type
    preset = args.preset
    next_steps = [
        "先做内容审稿和表达严谨性审稿，不直接排版。",
        "如果审稿发现阻断项，先生成改稿计划并修订。",
        "定稿后生成组件版 Markdown，再用锁定 preset 输出 HTML。",
        "HTML 预览通过后，才进入素材检查或草稿箱 dry-run。",
    ]
    commands = [
        command(["python", "scripts/review/article_quality_review.py", article, "--out", "article.quality.json"]),
        command(["python", "scripts/review/article_style_rigor_review.py", article, "--out", "article.rigor.json"]),
        command(["python", "scripts/review/article_revision_plan.py", article, "article.quality.json", "--rigor-json", "article.rigor.json", "--out", "article.revision-plan.md"]),
        command(["python", "scripts/formatting/article_component_planner.py", article, "--type", article_type, "--preset", preset, "--out", "article.components.md", "--plan", "article.components.json"]),
        command(["python", "scripts/formatting/wechat_format_presets.py", "article.components.md", "--preset", preset, "--out", "article.html"]),
    ]
    return next_steps, commands


def build_preview(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    article = args.article
    article_type = args.article_type
    preset = args.preset
    next_steps = [
        "锁定 preset，先生成组件版 Markdown。",
        "用组件版 Markdown 生成 HTML 预览，确保小组件被渲染。",
        "只有预览包含复杂表格、宽图、长链接或代码块时，才额外运行浏览器视觉自测。",
    ]
    commands = [
        command(["python", "scripts/formatting/article_component_planner.py", article, "--type", article_type, "--preset", preset, "--out", "article.components.md", "--plan", "article.components.json"]),
        command(["python", "scripts/formatting/wechat_format_presets.py", "article.components.md", "--preset", preset, "--out", "article.html"]),
        command(["python", "scripts/qa/visual_selftest.py", "article.html"]),
    ]
    return next_steps, commands


def build_draft_dry_run(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    article = args.article
    article_type = args.article_type
    preset = args.preset
    next_steps = [
        "先做质量审稿和表达严谨性审稿，确认没有阻断项。",
        "生成组件版 Markdown 和 HTML 预览。",
        "执行草稿箱 dry-run，只生成本地产物和 chain-report.json，不调用微信接口。",
        "真实创建草稿箱必须另行确认，并额外添加执行确认参数。",
    ]
    commands = [
        command(["python", "scripts/review/article_quality_review.py", article, "--out", "article.quality.json"]),
        command(["python", "scripts/review/article_style_rigor_review.py", article, "--out", "article.rigor.json"]),
        command(["python", "scripts/formatting/article_component_planner.py", article, "--type", article_type, "--preset", preset, "--out", "article.components.md", "--plan", "article.components.json"]),
        command(["python", "scripts/formatting/wechat_format_presets.py", "article.components.md", "--preset", preset, "--out", "article.html"]),
        command(["python", "scripts/orchestration/wechat_local_to_draft.py", "article.components.md", "--preset", preset, "--quality-review"]),
    ]
    return next_steps, commands


def render(args: argparse.Namespace) -> str:
    builders = {
        "new": build_new,
        "existing": build_existing,
        "preview": build_preview,
        "draft-dry-run": build_draft_dry_run,
    }
    next_steps, commands = builders[args.mode](args)
    known = [
        f"- 当前模式：{MODES[args.mode]}",
        f"- 文章类型：{args.article_type}（{ARTICLE_TYPES[args.article_type]}）",
        f"- 锁定 preset：{args.preset}",
    ]
    if args.topic:
        known.append(f"- 主题：{args.topic}")
    if args.audience:
        known.append(f"- 目标读者：{args.audience}")
    if args.article:
        known.append(f"- 稿件：{args.article}")

    lines = ["# 微信公众号总控向导", "", "## 已知信息", *known, "", "## 建议下一步"]
    lines.extend(f"{idx}. {step}" for idx, step in enumerate(next_steps, 1))
    lines.extend(["", "## 推荐命令", "```powershell", *commands, "```", "", "## 安全边界"])
    lines.extend(
        [
            "- 本向导只生成下一步建议和命令，不执行完整链路。",
            "- 默认只给 dry-run 命令，不会上传、创建草稿箱或正式发布。",
            "- 真实草稿箱动作必须由用户明确确认后再添加执行确认参数。",
            "- 正式发布或群发必须在草稿箱之后二次确认。",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="生成微信公众号总控下一步引导。")
    parser.add_argument("--mode", required=True, choices=sorted(MODES), help="向导模式。")
    parser.add_argument("--topic", help="文章主题。")
    parser.add_argument("--audience", help="目标读者。")
    parser.add_argument("--type", dest="article_type", default="security-analysis", choices=sorted(ARTICLE_TYPES), help="文章类型。")
    parser.add_argument("--article", help="已有 Markdown/HTML 稿件路径。")
    parser.add_argument("--preset", default="tech", help="排版预设，默认 tech。")
    parser.add_argument("--out", help="把向导输出写入 Markdown 文件。")
    args = parser.parse_args()

    if args.mode == "new" and not args.topic:
        parser.error("--mode new 需要提供 --topic。")
    if args.mode in {"existing", "preview", "draft-dry-run"} and not args.article:
        parser.error(f"--mode {args.mode} 需要提供 --article。")
    if args.article and not Path(args.article).exists():
        parser.error(f"稿件不存在：{args.article}")
    return args


def main() -> None:
    args = parse_args()
    text = render(args)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()

