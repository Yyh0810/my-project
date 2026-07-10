#!/usr/bin/env python3
"""根据 chain-report.json 生成团队交接报告。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        raise SystemExit("chain-report 必须是 JSON 对象。")
    return data


def status_label(report: dict[str, Any]) -> str:
    if report.get("ok"):
        return str(report.get("status") or "ok")
    return str(report.get("status") or "blocked")


def bullet(label: str, value: Any) -> str:
    if value in (None, "", [], {}):
        value = "无"
    return f"- {label}：{value}"


def render(report: dict[str, Any], source: Path) -> str:
    metadata = report.get("metadata") if isinstance(report.get("metadata"), dict) else {}
    outputs = report.get("outputs") if isinstance(report.get("outputs"), dict) else {}
    quality = report.get("quality_review") if isinstance(report.get("quality_review"), dict) else {}
    profile = report.get("profile") if isinstance(report.get("profile"), dict) else {}
    stages = report.get("stages") if isinstance(report.get("stages"), list) else []
    blockers = report.get("blocking") or report.get("issues") or []
    if quality.get("blocking"):
        blockers = list(blockers) + list(quality.get("blocking", []))

    lines: list[str] = []
    lines.append("# 微信公众号稿件交接单")
    lines.append("")
    lines.append("## 当前状态")
    lines.append("")
    lines.append(bullet("链路报告", source))
    lines.append(bullet("状态", status_label(report)))
    lines.append(bullet("是否真实调用微信接口", "否，dry-run" if report.get("dry_run", True) else "是"))
    lines.append(bullet("接续阶段", report.get("resume_from", "preflight")))
    lines.append(bullet("安全边界", report.get("safety_note", "正式发布必须另行确认")))
    lines.append("")

    lines.append("## 稿件信息")
    lines.append("")
    lines.append(bullet("标题", metadata.get("title")))
    lines.append(bullet("作者", metadata.get("author")))
    lines.append(bullet("摘要", metadata.get("digest")))
    if profile:
        lines.append(bullet("Profile", profile.get("profile_name") or profile.get("path")))
        lines.append(bullet("账号显示名", profile.get("account_name")))
    lines.append("")

    lines.append("## 关键产物")
    lines.append("")
    for key in ["preflight", "quality_review", "html", "assets", "uploaded_images", "wechat_html", "wechat_assets", "draft_json"]:
        if key in outputs:
            lines.append(bullet(key, outputs[key]))
    lines.append("")

    lines.append("## 审稿与阻塞")
    lines.append("")
    if quality:
        lines.append(bullet("审稿通过", quality.get("ok")))
        lines.append(bullet("审稿分数", quality.get("score")))
        lines.append(bullet("审稿报告", quality.get("path")))
    if blockers:
        lines.append("阻塞项：")
        for item in blockers:
            lines.append(f"- {item}")
    else:
        lines.append("- 阻塞项：无")
    lines.append("")

    lines.append("## 阶段记录")
    lines.append("")
    for stage in stages:
        if not isinstance(stage, dict):
            continue
        if stage.get("skipped"):
            state = "跳过"
        elif stage.get("dry_run"):
            state = "dry-run"
        else:
            state = "通过" if stage.get("ok") else "未通过"
        reused = "，复用既有产物" if stage.get("reused") else ""
        output = f"，产物：{stage.get('output')}" if stage.get("output") else ""
        lines.append(f"- {stage.get('name', '未命名阶段')}：{state}{reused}{output}")
    lines.append("")

    lines.append("## 下一步")
    lines.append("")
    if report.get("ok"):
        lines.append("- 如目标是草稿箱，检查 `draft_json` 与微信后台状态。")
        lines.append("- 如需要真实创建草稿箱，必须由负责人确认后执行 `--execute --confirm-draftbox`。")
        lines.append("- 正式发布不属于本交接单默认动作，必须另做发布门禁。")
    else:
        lines.append("- 先修复阻塞项。")
        lines.append("- 修复后使用 `--resume-from` 从失败阶段或其前一阶段接续。")
    lines.append("")
    lines.append("## 禁止交接内容")
    lines.append("")
    lines.append("- AppSecret、access_token、API key。")
    lines.append("- 含密钥的截图、接口 URL 或日志。")
    lines.append("- 未授权客户信息、合同、报价、内部策略。")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="根据 chain-report.json 生成微信公众号稿件交接单。")
    parser.add_argument("chain_report", help="wechat_local_to_draft.py 输出的 chain-report.json。")
    parser.add_argument("--out", help="输出 Markdown；默认打印到 stdout。")
    args = parser.parse_args()

    source = Path(args.chain_report)
    if not source.exists():
        raise SystemExit(f"chain-report 不存在：{source}")
    content = render(read_json(source), source)
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"交接单已生成：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
