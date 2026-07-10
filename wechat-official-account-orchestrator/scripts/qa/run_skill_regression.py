#!/usr/bin/env python3
"""微信公众号总控 skill 回归测试入口。"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_ROOT = SCRIPT_DIR.parent
SKILL_DIR = SCRIPT_ROOT.parent
SAMPLE_MD = SKILL_DIR / "assets" / "theme-previews" / "sample.md"
SCRIPT_PATHS = {
    "article_argument_chain.py": SCRIPT_ROOT / "content" / "article_argument_chain.py",
    "article_component_planner.py": SCRIPT_ROOT / "formatting" / "article_component_planner.py",
    "article_draft_prompt_builder.py": SCRIPT_ROOT / "content" / "article_draft_prompt_builder.py",
    "article_outline_builder.py": SCRIPT_ROOT / "content" / "article_outline_builder.py",
    "article_quality_review.py": SCRIPT_ROOT / "review" / "article_quality_review.py",
    "article_revision_plan.py": SCRIPT_ROOT / "review" / "article_revision_plan.py",
    "article_rewrite_modes.py": SCRIPT_ROOT / "review" / "article_rewrite_modes.py",
    "article_style_rigor_review.py": SCRIPT_ROOT / "review" / "article_style_rigor_review.py",
    "article_writing_pack.py": SCRIPT_ROOT / "content" / "article_writing_pack.py",
    "research_ledger_builder.py": SCRIPT_ROOT / "content" / "research_ledger_builder.py",
    "title_strategy.py": SCRIPT_ROOT / "content" / "title_strategy.py",
    "visual_asset_plan.py": SCRIPT_ROOT / "assets" / "visual_asset_plan.py",
    "wechat_api_draft.py": SCRIPT_ROOT / "wechat" / "wechat_api_draft.py",
    "wechat_article_wizard.py": SCRIPT_ROOT / "orchestration" / "wechat_article_wizard.py",
    "wechat_creative_blocks.py": SCRIPT_ROOT / "formatting" / "wechat_creative_blocks.py",
    "wechat_format_presets.py": SCRIPT_ROOT / "formatting" / "wechat_format_presets.py",
    "wechat_handoff_report.py": SCRIPT_ROOT / "wechat" / "wechat_handoff_report.py",
    "wechat_local_to_draft.py": SCRIPT_ROOT / "orchestration" / "wechat_local_to_draft.py",
}


def script(name: str) -> str:
    return str(SCRIPT_PATHS[name])
ARTICLE_TYPES = [
    "security-analysis",
    "agent-observation",
    "product-launch",
    "industry-observation",
    "case-review",
]


def run(cmd: list[str], expect: int = 0) -> dict[str, Any]:
    proc = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", capture_output=True)
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "ok": proc.returncode == expect,
        "stdout": stdout[-2000:],
        "stderr": stderr[-2000:],
        "expected": expect,
    }


def check(condition: bool, name: str, detail: str = "") -> dict[str, Any]:
    return {
        "cmd": ["internal-check", name],
        "returncode": 0 if condition else 1,
        "ok": condition,
        "stdout": detail,
        "stderr": "" if condition else detail,
        "expected": 0,
    }


def write_problem(path: Path) -> None:
    path.write_text(
        """---
title: AI 安全平台彻底解决所有漏洞风险
---

# AI 安全平台彻底解决所有漏洞风险

正文与标题不一致。我们声称 100% 解决所有风险，是行业第一。

这里出现 CVE-2026-12345、90% 效率提升和 payload 复现步骤。

测试用伪造字段：access_token=abcdefghijklmnopqrstuvwxyz123456
""",
        encoding="utf-8",
    )


def write_sources(path: Path) -> None:
    path.write_text(
        json.dumps(
            [
                {
                    "source_title": "OpenAI Agent 安全实践公开说明",
                    "url": "https://example.com/openai-agent-security",
                    "published_at": "2026-07-01",
                    "accessed_at": "2026-07-10",
                    "source_type": "official",
                    "credibility": "high",
                    "usable_claims": ["AI Agent 落地需要权限、上下文和人工复核边界。"],
                    "uncertainties": ["具体效率数据需要另行核验。"],
                    "do_not_use": ["不得写成完全替代人工。"],
                }
            ],
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def write_rigor_problem(path: Path) -> None:
    path.write_text(
        """---
title: AI Agent 平台产品介绍
author: 内容运营组
digest: 这是一篇测试稿。
---

# AI Agent 平台产品介绍

随着 AI 技术的快速发展，AI Agent 正在改变所有行业。首先，我们的平台能力非常全面。其次，我们的平台功能非常强大。最后，我们的平台可以帮助团队完成很多事情。

因此，这是一个非常重要的产品能力升级。产品、平台、方案、能力都已经准备好了。
""",
        encoding="utf-8",
    )


def write_plain_article(path: Path) -> None:
    path.write_text(
        """---
title: AI Agent 安全运营的判断链路
author: 内容运营组
digest: 围绕 AI Agent 安全运营，说明风险、边界和下一步检查动作。
---

# AI Agent 安全运营的判断链路

AI Agent 进入安全运营之后，团队需要关注的不只是工具能完成多少任务，而是权限、上下文和人工复核边界是否清楚。

## 风险为什么值得关注

如果 Agent 能读取日志、调用工具、生成处置建议，它就会进入原本由多人协作完成的判断链路。这个变化会影响风险识别、证据复核和处置责任。

## 判断边界

涉及客户数据、权限变更和生产系统操作时，不能只依赖自动化结论。相关数据、效率指标和外部案例仍需待核验。

## 下一步建议

建议先选择低风险场景试点，检查权限范围、日志来源、人工确认点和复盘指标。
""",
        encoding="utf-8",
    )


def main() -> None:
    if not SAMPLE_MD.exists():
        raise SystemExit(f"样稿不存在：{SAMPLE_MD}")

    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="wechat-skill-regression-") as tmp:
        tmpdir = Path(tmp)
        good_out = tmpdir / "good-build"
        bad_md = tmpdir / "problem.md"
        bad_out = tmpdir / "problem-build"
        handoff = tmpdir / "handoff.md"
        outline = tmpdir / "outline.md"
        titles = tmpdir / "titles.json"
        rewrite = tmpdir / "rewrite.md"
        writing_pack_md = tmpdir / "writing-pack.md"
        draft_prompt_md = tmpdir / "draft-prompt.md"
        bad_quality = tmpdir / "problem.quality.json"
        bad_rigor = tmpdir / "problem.rigor.json"
        revision_plan_md = tmpdir / "revision-plan.md"
        sources_json = tmpdir / "sources.json"
        research_empty = tmpdir / "empty.research-ledger.json"
        research_ledger = tmpdir / "research-ledger.json"
        argument_chain = tmpdir / "argument-chain.json"
        rigor_problem = tmpdir / "rigor-problem.md"
        rigor_report = tmpdir / "rigor-problem.rigor.json"
        components_md = tmpdir / "sample.components.md"
        components_plan = tmpdir / "sample.components.json"
        components_html = tmpdir / "sample.components.html"
        plain_article = tmpdir / "plain.md"
        cover_brief = tmpdir / "cover.brief.md"
        body_images = tmpdir / "body-images.md"
        infographic = tmpdir / "infographic.md"
        wizard_new = tmpdir / "wizard-new.md"
        wizard_existing = tmpdir / "wizard-existing.md"
        wizard_preview = tmpdir / "wizard-preview.md"
        wizard_draft = tmpdir / "wizard-draft.md"
        write_problem(bad_md)
        write_sources(sources_json)
        write_rigor_problem(rigor_problem)
        write_plain_article(plain_article)

        results.append(run([sys.executable, script("wechat_format_presets.py"), "--list"]))
        results.append(run([sys.executable, script("wechat_creative_blocks.py"), "--list"]))
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_article_wizard.py"),
                    "--mode",
                    "new",
                    "--topic",
                    "AI Agent 安全运营",
                    "--audience",
                    "安全运营团队",
                    "--type",
                    "security-analysis",
                    "--out",
                    str(wizard_new),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_article_wizard.py"),
                    "--mode",
                    "existing",
                    "--article",
                    str(plain_article),
                    "--preset",
                    "tech",
                    "--out",
                    str(wizard_existing),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_article_wizard.py"),
                    "--mode",
                    "preview",
                    "--article",
                    str(plain_article),
                    "--preset",
                    "tech",
                    "--out",
                    str(wizard_preview),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_article_wizard.py"),
                    "--mode",
                    "draft-dry-run",
                    "--article",
                    str(plain_article),
                    "--preset",
                    "tech",
                    "--out",
                    str(wizard_draft),
                ]
            )
        )
        wizard_texts = {
            "new": wizard_new.read_text(encoding="utf-8") if wizard_new.exists() else "",
            "existing": wizard_existing.read_text(encoding="utf-8") if wizard_existing.exists() else "",
            "preview": wizard_preview.read_text(encoding="utf-8") if wizard_preview.exists() else "",
            "draft": wizard_draft.read_text(encoding="utf-8") if wizard_draft.exists() else "",
        }
        results.append(
            check(
                all(token in wizard_texts["new"] for token in ["research_ledger_builder.py", "article_argument_chain.py", "title_strategy.py", "article_outline_builder.py", "article_writing_pack.py", "article_draft_prompt_builder.py"]),
                "wizard-new-commands",
                "新建模式必须输出资料台账、论证链、标题、大纲、写作包和初稿提示词命令。",
            )
        )
        results.append(
            check(
                all(token in wizard_texts["existing"] for token in ["article_quality_review.py", "article_style_rigor_review.py", "article_revision_plan.py", "article_component_planner.py", "wechat_format_presets.py"]),
                "wizard-existing-commands",
                "接续模式必须输出审稿、表达严谨性审稿、改稿计划、组件编排和排版命令。",
            )
        )
        results.append(
            check(
                all(token in wizard_texts["preview"] for token in ["article_component_planner.py", "wechat_format_presets.py", "visual_selftest.py"]),
                "wizard-preview-commands",
                "预览模式必须输出组件编排、锁定 preset 排版和可选视觉自测命令。",
            )
        )
        results.append(
            check(
                "wechat_local_to_draft.py" in wizard_texts["draft"] and "--quality-review" in wizard_texts["draft"] and "--execute" not in wizard_texts["draft"],
                "wizard-draft-dry-run-safe",
                "草稿箱 dry-run 模式必须输出本地总控命令，且默认不得包含 --execute。",
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("research_ledger_builder.py"),
                    "--topic",
                    "AI Agent 安全运营",
                    "--type",
                    "security-analysis",
                    "--out",
                    str(research_empty),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("research_ledger_builder.py"),
                    "--topic",
                    "AI Agent 安全运营",
                    "--type",
                    "security-analysis",
                    "--sources",
                    str(sources_json),
                    "--out",
                    str(research_ledger),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_argument_chain.py"),
                    "--topic",
                    "AI Agent 安全运营",
                    "--type",
                    "security-analysis",
                    "--ledger",
                    str(research_ledger),
                    "--out",
                    str(argument_chain),
                ]
            )
        )
        for article_type in ARTICLE_TYPES:
            results.append(
                run(
                    [
                        sys.executable,
                        script("article_outline_builder.py"),
                        "--topic",
                        "AI Agent 安全运营",
                        "--type",
                        article_type,
                        "--audience",
                        "安全运营团队",
                        "--out",
                        str(tmpdir / f"{article_type}.md"),
                    ]
                )
            )
        for article_type in ARTICLE_TYPES:
            results.append(
                run(
                    [
                        sys.executable,
                        script("article_writing_pack.py"),
                        "--topic",
                        "AI Agent 安全运营",
                        "--type",
                        article_type,
                        "--audience",
                        "安全运营团队",
                        "--outline",
                        str(tmpdir / f"{article_type}.md"),
                        "--argument-chain",
                        str(argument_chain),
                        "--out",
                        str(tmpdir / f"{article_type}.writing-pack.json"),
                    ]
                )
            )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_writing_pack.py"),
                    "--topic",
                    "AI Agent 安全运营",
                    "--type",
                    "security-analysis",
                    "--audience",
                    "安全运营团队",
                    "--outline",
                    str(tmpdir / "security-analysis.md"),
                    "--argument-chain",
                    str(argument_chain),
                    "--out",
                    str(writing_pack_md),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_draft_prompt_builder.py"),
                    str(tmpdir / "security-analysis.writing-pack.json"),
                    "--out",
                    str(draft_prompt_md),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_style_rigor_review.py"),
                    str(rigor_problem),
                    "--out",
                    str(rigor_report),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_component_planner.py"),
                    str(plain_article),
                    "--type",
                    "security-analysis",
                    "--preset",
                    "tech",
                    "--out",
                    str(components_md),
                    "--plan",
                    str(components_plan),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_format_presets.py"),
                    str(components_md),
                    "--preset",
                    "tech",
                    "--out",
                    str(components_html),
                ]
            )
        )
        for article_type in ARTICLE_TYPES:
            results.append(
                run(
                    [
                        sys.executable,
                        script("visual_asset_plan.py"),
                        str(SAMPLE_MD),
                        "--type",
                        article_type,
                        "--style",
                        "tech",
                        "--out",
                        str(tmpdir / f"{article_type}.visual.json"),
                    ]
                )
            )
        results.append(
            run(
                [
                    sys.executable,
                    script("visual_asset_plan.py"),
                    str(SAMPLE_MD),
                    "--type",
                    "security-analysis",
                    "--asset",
                    "cover",
                    "--out",
                    str(cover_brief),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("visual_asset_plan.py"),
                    str(SAMPLE_MD),
                    "--type",
                    "product-launch",
                    "--asset",
                    "body",
                    "--out",
                    str(body_images),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("visual_asset_plan.py"),
                    str(SAMPLE_MD),
                    "--type",
                    "agent-observation",
                    "--asset",
                    "infographic",
                    "--out",
                    str(infographic),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("title_strategy.py"),
                    "--topic",
                    "AI Agent 安全运营",
                    "--type",
                    "security-analysis",
                    "--out",
                    str(titles),
                ]
            )
        )
        sample_outline = (tmpdir / "security-analysis.md").read_text(encoding="utf-8")
        results.append(
            check(
                all(token in sample_outline for token in ["---", "fact_status", "待核验", "## 待核验事实"]),
                "outline-structure",
                "大纲必须包含 frontmatter、fact_status 和待核验事实区。",
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_rewrite_modes.py"),
                    str(bad_md),
                    "--mode",
                    "dehype",
                    "--out",
                    str(rewrite),
                ]
            )
        )
        title_payload = json.loads(titles.read_text(encoding="utf-8"))
        title_ok = (
            len(title_payload.get("titles", [])) == 4
            and all({"risk_level", "reason", "recommended"} <= set(item) for item in title_payload.get("titles", []))
        )
        results.append(check(title_ok, "title-json-shape", "标题策略必须输出 4 类标题和风险字段。"))
        empty_research_payload = json.loads(research_empty.read_text(encoding="utf-8"))
        research_payload = json.loads(research_ledger.read_text(encoding="utf-8"))
        research_ok = (
            empty_research_payload.get("requires_web_research") is True
            and research_payload.get("ok") is True
            and all(field in research_payload["sources"][0] for field in ["source_title", "url", "published_at", "accessed_at", "credibility", "usable_claims", "uncertainties", "do_not_use"])
        )
        results.append(check(research_ok, "research-ledger-shape", "资料台账必须包含来源、时间、可信度、可引用结论和不允许使用项。"))
        argument_payload = json.loads(argument_chain.read_text(encoding="utf-8"))
        argument_ok = (
            argument_payload.get("ok") is True
            and all(key in argument_payload.get("dimensions", {}) for key in ["core_claim", "supporting_evidence", "reasoning", "scope_boundary", "reader_action", "product_connection_boundary"])
        )
        results.append(check(argument_ok, "argument-chain-shape", "论证链必须包含核心判断、证据、推理、边界、读者动作和产品边界。"))
        writing_pack_payload = json.loads((tmpdir / "security-analysis.writing-pack.json").read_text(encoding="utf-8"))
        writing_pack_ok = (
            writing_pack_payload.get("ok") is True
            and all(
                key in writing_pack_payload
                for key in ["writing_strategy", "fact_ledger", "section_tasks", "model_collaboration", "human_decisions_required"]
            )
            and len(writing_pack_payload.get("section_tasks", [])) >= 3
            and "待核验" in json.dumps(writing_pack_payload.get("fact_ledger", []), ensure_ascii=False)
            and writing_pack_payload.get("argument_chain", {}).get("provided") is True
        )
        results.append(check(writing_pack_ok, "writing-pack-json-shape", "成稿写作包必须包含策略、事实台账、分段任务、模型协作和人工决策点。"))
        writing_pack_md_text = writing_pack_md.read_text(encoding="utf-8")
        results.append(
            check(
                all(token in writing_pack_md_text for token in ["模型写作提示", "人工复核", "事实台账", "不得编造事实"])
                or all(token in writing_pack_md_text for token in ["模型写作提示", "人工复核", "事实台账", "待核验"]),
                "writing-pack-markdown-output",
                "成稿写作包 Markdown 必须便于交给模型和人工复核。",
            )
        )
        draft_prompt_text = draft_prompt_md.read_text(encoding="utf-8")
        results.append(
            check(
                all(token in draft_prompt_text for token in ["System Prompt", "User Prompt", "章节任务", "只输出 Markdown 初稿", "待核验", "论证链核心判断"]),
                "draft-prompt-output",
                "初稿提示词必须包含 system/user prompt、章节任务、输出约束和待核验规则。",
            )
        )
        rigor_payload = json.loads(rigor_report.read_text(encoding="utf-8"))
        results.append(
            check(
                rigor_payload.get("ok") is False and rigor_payload.get("model_review_prompt") and len(rigor_payload.get("issues", [])) >= 2,
                "style-rigor-review",
                "表达严谨性审稿必须检出 AI 味、结构单一或产品硬插问题，并输出模型复审提示。",
            )
        )
        component_plan = json.loads(components_plan.read_text(encoding="utf-8"))
        component_md_text = components_md.read_text(encoding="utf-8")
        component_html_text = components_html.read_text(encoding="utf-8")
        component_ok = (
            components_md.exists()
            and 2 <= component_plan.get("component_count", 0) <= 4
            and re.search(r"^:::\s*(quote|insight|warning|checklist|summary|source|question|definition|steps)", component_md_text, flags=re.M)
            and 'data-creative-block="' in component_html_text
            and 'data-preset="tech"' in component_html_text
        )
        results.append(check(component_ok, "component-planner-render", "组件编排必须输出新稿、2-4 个组件，并能用 tech 预设渲染。"))
        visual_payload = json.loads((tmpdir / "security-analysis.visual.json").read_text(encoding="utf-8"))
        visual_ok = (
            all(key in visual_payload for key in ["cover", "body_images", "infographic", "review_checklist"])
            and visual_payload["cover"].get("aspect_ratio") == "16:9"
            and "generation_prompt" in visual_payload["cover"]
            and "image_2_prompt" in visual_payload["cover"]
            and "generation_policy" in visual_payload["cover"]
            and "固有生图能力" in visual_payload["cover"].get("generation_policy", "")
            and len(visual_payload.get("body_images", [])) >= 2
        )
        results.append(check(visual_ok, "visual-plan-json-shape", "视觉计划必须包含封面、正文配图、信息图和审核清单。"))
        body_ok = all(
            item.get("position") and item.get("related_section") and item.get("prompt")
            for item in visual_payload.get("body_images", [])
        )
        results.append(check(body_ok, "visual-body-section-binding", "正文配图必须绑定插入位置和对应章节。"))
        info_ok = "待核验" in visual_payload["infographic"].get("data_policy", "")
        results.append(check(info_ok, "visual-infographic-fact-policy", "信息图必须保留待核验数据策略。"))
        md_ok = (
            "16:9" in cover_brief.read_text(encoding="utf-8")
            and "生成提示词" in cover_brief.read_text(encoding="utf-8")
            and "对应章节" in body_images.read_text(encoding="utf-8")
            and "待核验" in infographic.read_text(encoding="utf-8")
        )
        results.append(check(md_ok, "visual-markdown-outputs", "视觉计划 Markdown 必须覆盖封面、正文配图和信息图核心字段。"))
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_local_to_draft.py"),
                    str(SAMPLE_MD),
                    "--profile",
                    "tech-internal",
                    "--quality-review",
                    "--out-dir",
                    str(good_out),
                ]
            )
        )
        rewrite_text = rewrite.read_text(encoding="utf-8")
        results.append(
            check(
                "100%" not in rewrite_text and "彻底解决" not in rewrite_text and "行业第一" not in rewrite_text,
                "dehype-rewrite",
                "dehype 应降低 100%、彻底解决、行业第一等表达。",
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_local_to_draft.py"),
                    str(SAMPLE_MD),
                    "--profile",
                    "tech-internal",
                    "--quality-review",
                    "--resume-from",
                    "rewrite-images",
                    "--out-dir",
                    str(good_out),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_local_to_draft.py"),
                    str(bad_md),
                    "--quality-review",
                    "--strict-quality",
                    "--out-dir",
                    str(bad_out),
                ],
                expect=1,
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_quality_review.py"),
                    str(bad_md),
                    "--out",
                    str(bad_quality),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_style_rigor_review.py"),
                    str(bad_md),
                    "--out",
                    str(bad_rigor),
                ]
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("article_revision_plan.py"),
                    str(bad_md),
                    str(bad_quality),
                    "--rigor-json",
                    str(bad_rigor),
                    "--out",
                    str(revision_plan_md),
                ]
            )
        )
        revision_text = revision_plan_md.read_text(encoding="utf-8")
        results.append(
            check(
                all(token in revision_text for token in ["改稿任务", "P0", "阻断", "复验命令", "表达严谨性"]),
                "revision-plan-output",
                "问题稿必须生成包含 P0、阻断项和复验命令的改稿计划。",
            )
        )
        results.append(
            run(
                [
                    sys.executable,
                    script("wechat_handoff_report.py"),
                    str(good_out / "chain-report.json"),
                    "--out",
                    str(handoff),
                ]
            )
        )
        results.append(run([sys.executable, script("wechat_api_draft.py"), "check-config"]))
        results.append(run([sys.executable, script("wechat_local_to_draft.py"), str(SAMPLE_MD), "--execute"], expect=1))

        ok = all(item["ok"] for item in results)
        payload = {
            "ok": ok,
            "total": len(results),
            "passed": sum(1 for item in results if item["ok"]),
            "failed": [item for item in results if not item["ok"]],
            "note": "测试目录使用临时目录，命令结束后自动删除。",
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if not ok:
            raise SystemExit(1)


if __name__ == "__main__":
    main()

