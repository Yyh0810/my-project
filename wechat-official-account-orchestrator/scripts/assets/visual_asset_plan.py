#!/usr/bin/env python3
"""生成公众号视觉资产 brief、通用生成提示词和审核清单。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ARTICLE_TYPES = {
    "security-analysis": {
        "label": "安全分析",
        "cover_subject": "抽象风险路径、资产拓扑和防护边界",
        "body_images": [
            ("风险链路分析后", "风险路径图", "展示资产、暴露面、权限和处置动作的关系，不包含攻击复现步骤。"),
            ("检查与处置建议前", "检查清单图", "将关键检查动作整理为移动端可读清单。"),
        ],
        "infographic": "风险路径图",
        "forbidden": ["攻击 payload", "真实利用步骤", "客户系统截图", "泄露 IP/域名"],
    },
    "agent-observation": {
        "label": "AI Agent 观察",
        "cover_subject": "Agent 协作、上下文流转和任务编排",
        "body_images": [
            ("现象说明后", "工作流对比图", "对比人工流程和 Agent 辅助流程。"),
            ("落地边界处", "能力边界图", "标明 Agent 适合、不适合和必须人工审核的环节。"),
        ],
        "infographic": "人机协作流程图",
        "forbidden": ["完全替代人工", "无人审核", "自动决策无边界"],
    },
    "product-launch": {
        "label": "产品发布",
        "cover_subject": "场景问题和产品能力结构",
        "body_images": [
            ("能力介绍后", "能力架构图", "展示能力模块和使用路径，不写未经核验指标。"),
            ("使用路径处", "流程图", "展示从问题到使用再到结果的步骤。"),
        ],
        "infographic": "能力矩阵图",
        "forbidden": ["未经证实的客户收益", "竞品贬损", "夸大效果数字"],
    },
    "industry-observation": {
        "label": "行业观察",
        "cover_subject": "行业变化、趋势节点和观察视角",
        "body_images": [
            ("趋势判断后", "影响矩阵", "展示现象、影响对象和行动建议。"),
            ("结论前", "决策框架图", "帮助读者判断是否需要跟进。"),
        ],
        "infographic": "现象-证据-判断-行动结构图",
        "forbidden": ["无来源市场规模", "无来源排名", "无来源增长率"],
    },
    "case-review": {
        "label": "案例复盘",
        "cover_subject": "复盘路径、关键节点和经验沉淀",
        "body_images": [
            ("过程回顾后", "时间线图", "展示关键节点和决策点，隐藏敏感信息。"),
            ("经验沉淀处", "改进清单图", "整理可复用经验和后续动作。"),
        ],
        "infographic": "复盘闭环图",
        "forbidden": ["客户名称", "合同", "报价", "内部策略", "未脱敏截图"],
    },
}

ASSETS = ["all", "cover", "body", "infographic"]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def strip_html(text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_title(text: str, path: Path) -> str:
    meta = re.search(r"^title:\s*[\"']?(.+?)[\"']?\s*$", text, flags=re.M)
    if meta:
        return meta.group(1).strip()
    h1 = re.search(r"^#\s+(.+)$", text, flags=re.M)
    if h1:
        return h1.group(1).strip()
    html_title = re.search(r"<title>(.*?)</title>", text, flags=re.I | re.S)
    if html_title:
        return strip_html(html_title.group(1))
    return path.stem


def extract_headings(text: str) -> list[str]:
    headings = [m.group(2).strip() for m in re.finditer(r"^(#{2,3})\s+(.+)$", text, flags=re.M)]
    if headings:
        return headings[:8]
    html_headings = re.findall(r"<h[2-3]\b[^>]*>(.*?)</h[2-3]>", text, flags=re.I | re.S)
    return [strip_html(item) for item in html_headings if strip_html(item)][:8]


def cover_prompt(title: str, article_type: str, style: str, audience: str) -> str:
    spec = ARTICLE_TYPES[article_type]
    return (
        f"为微信公众号文章《{title}》设计 16:9 封面图。"
        f"文章类型：{spec['label']}；目标读者：{audience}；视觉风格：{style}。"
        f"主体：{spec['cover_subject']}。构图专业、克制、可信，移动端清晰，留出标题安全区。"
        "不要放长中文，不使用客户标识、密钥、真实攻击步骤、未经授权品牌标识。"
    )


def build_plan(path: Path, article_type: str, style: str, audience: str) -> dict[str, Any]:
    text = read_text(path)
    title = extract_title(text, path)
    headings = extract_headings(text)
    spec = ARTICLE_TYPES[article_type]
    body = []
    for idx, (position, image_type, note) in enumerate(spec["body_images"], start=1):
        section = headings[min(idx - 1, len(headings) - 1)] if headings else position
        body.append(
            {
                "name": f"正文配图 {idx}",
                "position": position,
                "related_section": section,
                "type": image_type,
                "brief": note,
                "prompt": f"生成公众号正文配图：{image_type}。主题《{title}》。对应章节：{section}。风格：{style}。画面清晰、信息层级明确、移动端可读；不写待核验数据，不包含禁用元素。",
            }
        )
    return {
        "article": {
            "file": str(path),
            "title": title,
            "article_type": article_type,
            "article_type_label": spec["label"],
            "audience": audience,
            "style": style,
            "headings": headings,
        },
        "cover": {
            "aspect_ratio": "16:9",
            "subject": spec["cover_subject"],
            "composition": "一个明确视觉中心，背景克制，留出标题安全区。",
            "color": "与主题预设一致，避免过度炫光和杂色。",
            "text_policy": "默认不放长中文；如必须放文字，只放短标题或短标签。",
            "forbidden": spec["forbidden"],
            "preferred_tools": ["image-2", "当前 Codex 图像工具"],
            "generation_policy": "image-2 / 当前 Codex 图像工具作为固有生图能力保留；仅在用户明确要求并授权后执行。",
            "generation_prompt": cover_prompt(title, article_type, style, audience),
            "image_2_prompt": cover_prompt(title, article_type, style, audience),
        },
        "body_images": body,
        "infographic": {
            "type": spec["infographic"],
            "structure": ["现象/问题", "关键证据（待核验）", "判断链路", "行动建议"],
            "data_policy": "只保留待核验数据位，不编造具体数字。",
            "prompt": f"生成公众号信息图结构：{spec['infographic']}。主题《{title}》。使用占位数据位并标记待核验，信息层级清楚，适合移动端阅读。",
        },
        "review_checklist": [
            "视觉是否符合文章类型和目标读者。",
            "封面是否为 16:9，并留出标题安全区。",
            "是否避免长中文、小字和复杂图例。",
            "是否包含客户标识、密钥、攻击步骤或未经授权品牌。",
            "正文配图是否绑定具体章节。",
            "信息图是否只使用待核验数据位，不编造数字。",
            "是否需要用户明确授权后再调用 image-2 / 当前 Codex 图像工具。",
        ],
        "safety_note": "本脚本只生成视觉计划和通用生成提示词，不生成图片、不上传素材、不写入草稿箱。",
    }


def render_markdown(plan: dict[str, Any], asset: str) -> str:
    lines = ["# 公众号视觉资产计划", ""]
    article = plan["article"]
    lines.extend(
        [
            f"- 文章：{article['title']}",
            f"- 类型：{article['article_type']} / {article['article_type_label']}",
            f"- 读者：{article['audience']}",
            f"- 风格：{article['style']}",
            "",
        ]
    )
    if asset in ("all", "cover"):
        cover = plan["cover"]
        lines.extend(["## 封面 brief", ""])
        for key in ["aspect_ratio", "subject", "composition", "color", "text_policy"]:
            lines.append(f"- {key}：{cover[key]}")
        lines.append(f"- 禁用项：{'、'.join(cover['forbidden'])}")
        lines.extend(["", "### 生成提示词", "", cover["generation_prompt"], ""])
    if asset in ("all", "body"):
        lines.extend(["## 正文配图计划", ""])
        for item in plan["body_images"]:
            lines.append(f"### {item['name']}")
            lines.append(f"- 插入位置：{item['position']}")
            lines.append(f"- 对应章节：{item['related_section']}")
            lines.append(f"- 类型：{item['type']}")
            lines.append(f"- brief：{item['brief']}")
            lines.append(f"- prompt：{item['prompt']}")
            lines.append("")
    if asset in ("all", "infographic"):
        info = plan["infographic"]
        lines.extend(["## 信息图结构", ""])
        lines.append(f"- 类型：{info['type']}")
        lines.append(f"- 结构：{' -> '.join(info['structure'])}")
        lines.append(f"- 数据策略：{info['data_policy']}")
        lines.append(f"- prompt：{info['prompt']}")
        lines.append("")
    lines.extend(["## 审核清单", ""])
    for item in plan["review_checklist"]:
        lines.append(f"- {item}")
    lines.extend(["", f"> {plan['safety_note']}"])
    return "\n".join(lines) + "\n"


def filter_plan(plan: dict[str, Any], asset: str) -> dict[str, Any]:
    if asset == "all":
        return plan
    base = {"article": plan["article"], "review_checklist": plan["review_checklist"], "safety_note": plan["safety_note"]}
    if asset == "cover":
        base["cover"] = plan["cover"]
    elif asset == "body":
        base["body_images"] = plan["body_images"]
    elif asset == "infographic":
        base["infographic"] = plan["infographic"]
    return base


def main() -> None:
    parser = argparse.ArgumentParser(description="生成公众号视觉资产 brief、通用生成提示词和审核清单。")
    parser.add_argument("input", help="Markdown 或 HTML 稿件。")
    parser.add_argument("--type", required=True, choices=sorted(ARTICLE_TYPES), help="文章类型。")
    parser.add_argument("--style", default="tech", help="视觉风格或排版主题。")
    parser.add_argument("--audience", default="内部运营团队", help="目标读者。")
    parser.add_argument("--asset", choices=ASSETS, default="all", help="输出资产类型。")
    parser.add_argument("--format", choices=["json", "markdown"], default=None, help="输出格式；默认按扩展名推断。")
    parser.add_argument("--out", help="输出文件。")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        raise SystemExit(f"输入文件不存在：{src}")
    plan = filter_plan(build_plan(src, args.type, args.style, args.audience), args.asset)
    out_format = args.format
    if out_format is None:
        out_format = "markdown" if args.out and Path(args.out).suffix.lower() in {".md", ".markdown"} else "json"
    content = render_markdown(plan if args.asset == "all" else build_plan(src, args.type, args.style, args.audience), args.asset) if out_format == "markdown" else json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"视觉资产计划已生成：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
