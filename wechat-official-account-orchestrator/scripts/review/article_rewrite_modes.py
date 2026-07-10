#!/usr/bin/env python3
"""公众号稿件规则化改稿模式。"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


MODES = {
    "formal": "正式化",
    "technical": "技术化",
    "product": "产品化",
    "customer": "客户向",
    "dehype": "降营销味",
}

DEHYPE_REPLACEMENTS = {
    "最强": "较强",
    "唯一": "一种",
    "第一": "具备竞争力",
    "100%": "在明确条件下",
    "彻底解决": "缓解",
    "永久解决": "持续降低",
    "零风险": "降低风险",
    "颠覆": "改变",
    "秒杀": "优于部分传统做法",
    "吊打": "在特定场景下更适合",
}


def rewrite(text: str, mode: str) -> str:
    result = text
    if mode == "dehype":
        for src, dst in DEHYPE_REPLACEMENTS.items():
            result = result.replace(src, dst)
    elif mode == "formal":
        result = result.replace("我们觉得", "从当前材料看")
        result = result.replace("很厉害", "具备一定应用价值")
        result = result.replace("马上", "建议优先")
    elif mode == "technical":
        result = result.replace("好用", "在流程、边界和可观测性上具备可评估价值")
        result = result.replace("问题", "约束条件")
    elif mode == "product":
        result = result.replace("功能", "能力")
        result = result.replace("用户", "目标用户")
    elif mode == "customer":
        result = result.replace("我们", "团队")
        result = result.replace("产品", "方案")
    result = re.sub(r"\n{3,}", "\n\n", result)
    return append_note(result, mode)


def append_note(text: str, mode: str) -> str:
    note = (
        "\n\n---\n\n"
        f"改稿模式：{mode} / {MODES[mode]}\n\n"
        "说明：本脚本只做规则化表达调整，不新增客户、数字、漏洞编号、产品指标或外部事实。\n"
    )
    return text.rstrip() + note


def main() -> None:
    parser = argparse.ArgumentParser(description="公众号稿件规则化改稿模式。")
    parser.add_argument("input", help="输入 Markdown。")
    parser.add_argument("--mode", required=True, choices=sorted(MODES), help="改稿模式。")
    parser.add_argument("--out", required=True, help="输出 Markdown 文件；不会覆盖源稿，除非显式传同一路径。")
    args = parser.parse_args()

    src = Path(args.input)
    out = Path(args.out)
    if not src.exists():
        raise SystemExit(f"输入文件不存在：{src}")
    if src.resolve() == out.resolve():
        raise SystemExit("为避免覆盖源稿，--out 不能与输入文件相同。")
    out.write_text(rewrite(src.read_text(encoding="utf-8-sig"), args.mode) + "\n", encoding="utf-8")
    print(f"改稿已生成：{out}")


if __name__ == "__main__":
    main()
