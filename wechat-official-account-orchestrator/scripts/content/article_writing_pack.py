#!/usr/bin/env python3
"""生成面向模型协作和人工审稿的公众号成稿写作包。"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ARTICLE_TYPES: dict[str, dict[str, Any]] = {
    "security-analysis": {
        "label": "安全分析",
        "reader_job": "判断风险是否与自己有关，并知道下一步该检查什么。",
        "thesis_pattern": "围绕风险链路、影响边界和可执行处置建议展开，不做攻击复现。",
        "sections": [
            ("开头", "用一个具体风险或运营盲区进入，说明为什么现在值得关注。"),
            ("风险边界", "说明影响对象、前提条件、已知和未知边界。"),
            ("链路分析", "解释资产、暴露面、权限、监测和处置之间的关系。"),
            ("行动建议", "给出检查清单、优先级和团队分工。"),
            ("产品连接", "只在有材料支撑时说明产品能帮助哪一个环节。"),
        ],
        "must_evidence": ["漏洞编号/风险对象", "影响范围", "利用状态", "日期", "来源链接或内部依据"],
        "forbidden": ["攻击 payload", "真实利用步骤", "全网沦陷", "零风险", "彻底解决"],
    },
    "agent-observation": {
        "label": "AI Agent 观察",
        "reader_job": "理解 Agent 对工作流的实际影响，并判断能否在低风险场景试点。",
        "thesis_pattern": "围绕工作方式变化、协作边界和试点条件展开，不夸大替代人工。",
        "sections": [
            ("开头", "从一个真实工作流变化或协作问题进入。"),
            ("现象", "描述变化是什么，哪些环节被影响。"),
            ("原因", "解释模型、工具、上下文、权限或流程为什么导致变化。"),
            ("边界", "说明适合、不适合和必须人工审核的环节。"),
            ("试点建议", "给出低风险试点场景、评估指标和复盘方式。"),
        ],
        "must_evidence": ["工具名称/能力范围", "实践案例", "效率或质量指标", "失败边界", "来源或待核验说明"],
        "forbidden": ["完全替代人工", "无需审核", "自动决策无边界", "颠覆一切"],
    },
    "product-launch": {
        "label": "产品发布",
        "reader_job": "理解新能力解决什么问题、如何使用、边界在哪里。",
        "thesis_pattern": "从场景问题进入，再讲能力、路径、边界和下一步，不把文章写成参数堆砌。",
        "sections": [
            ("开头", "用目标用户场景和已有痛点进入。"),
            ("场景问题", "说明为什么旧方式成本高、风险大或效率低。"),
            ("能力说明", "按用户任务解释能力，而不是按功能菜单罗列。"),
            ("使用路径", "给出从进入、配置、查看结果到复盘的路径。"),
            ("边界与 CTA", "说明适用条件、暂不覆盖范围和试用/咨询入口。"),
        ],
        "must_evidence": ["版本号", "能力范围", "上线状态", "客户效果或示例", "指标来源"],
        "forbidden": ["行业第一", "唯一", "秒杀", "100% 提升", "永久解决"],
    },
    "industry-observation": {
        "label": "行业观察",
        "reader_job": "判断一个行业现象是否值得跟进，以及跟进时看哪些证据。",
        "thesis_pattern": "用现象、证据、判断、边界和行动建议构成完整判断链。",
        "sections": [
            ("开头", "从一个可观察现象进入，避免空泛趋势词。"),
            ("现象", "说明发生了什么，影响哪些角色。"),
            ("证据", "列出报告、公告、产品动作或市场信号。"),
            ("判断", "解释变化背后的原因和可能影响。"),
            ("行动建议", "给出跟进标准、讨论问题或内部决策清单。"),
        ],
        "must_evidence": ["报告/公告", "调研口径", "市场数据", "时间范围", "来源链接"],
        "forbidden": ["所有公司都在做", "颠覆一切", "时代彻底变了", "无来源排名"],
    },
    "case-review": {
        "label": "案例复盘",
        "reader_job": "复用一次项目或事件中的经验，避免重复犯错。",
        "thesis_pattern": "围绕目标、过程、关键问题、经验沉淀和后续动作展开，先脱敏再表达。",
        "sections": [
            ("开头", "说明复盘目标、范围和可公开边界。"),
            ("背景与目标", "交代项目/事件背景，不暴露敏感身份。"),
            ("过程回顾", "按关键节点复盘，不写无关流水账。"),
            ("关键问题", "提炼决策点、约束和偏差。"),
            ("经验与动作", "输出可复用清单和下一步改进。"),
        ],
        "must_evidence": ["授权状态", "脱敏口径", "过程记录", "结果数据", "责任边界"],
        "forbidden": ["客户名称", "合同", "报价", "未脱敏截图", "内部策略"],
    },
}

PRODUCT_LEVELS = ["none", "light", "medium", "strong"]


def read_optional(path: str | None) -> str:
    if not path:
        return ""
    src = Path(path)
    if not src.exists():
        raise SystemExit(f"文件不存在：{src}")
    return src.read_text(encoding="utf-8-sig").strip()


def read_optional_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    src = Path(path)
    if not src.exists():
        raise SystemExit(f"文件不存在：{src}")
    return json.loads(src.read_text(encoding="utf-8-sig"))


def summarize_argument_chain(chain: dict[str, Any] | None) -> dict[str, Any]:
    if not chain:
        return {
            "provided": False,
            "core_claim": "待补充",
            "supporting_evidence": ["待补充"],
            "scope_boundary": "待补充",
            "reader_action": "待补充",
            "product_connection_boundary": "待补充",
        }
    dims = chain.get("dimensions", {})
    return {
        "provided": True,
        "core_claim": dims.get("core_claim", {}).get("value", "待补充"),
        "supporting_evidence": dims.get("supporting_evidence", {}).get("value", ["待补充"]),
        "scope_boundary": dims.get("scope_boundary", {}).get("value", "待补充"),
        "reader_action": dims.get("reader_action", {}).get("value", "待补充"),
        "product_connection_boundary": dims.get("product_connection_boundary", {}).get("value", "待补充"),
    }


def extract_outline_headings(text: str) -> list[str]:
    headings = [m.group(2).strip() for m in re.finditer(r"^(#{2,3})\s+(.+)$", text, flags=re.M)]
    return [item for item in headings if item and "待核验" not in item][:8]


def source_notes_summary(source_notes: str) -> dict[str, Any]:
    if not source_notes:
        return {
            "provided": False,
            "summary": "未提供外部材料；所有具体事实必须标注待核验。",
            "usable_lines": [],
        }
    lines = [line.strip("-* 　\t") for line in source_notes.splitlines() if line.strip()]
    usable = [line for line in lines if len(line) >= 4][:12]
    return {
        "provided": True,
        "summary": "已提供材料；只能使用材料中明示的信息，不能扩写成未提供的客户、数字或结论。",
        "usable_lines": usable,
    }


def product_policy(product_level: str) -> str:
    if product_level == "none":
        return "不主动加入产品表达，只保留中立分析和行动建议。"
    if product_level == "light":
        return "只在结尾或行动建议中轻量连接产品能力，不写销售口吻。"
    if product_level == "medium":
        return "可在正文中解释产品适用环节，但必须先讲场景和证据。"
    return "可作为产品说明稿处理，但仍需保留边界、证据和非夸大表达。"


def build_section_tasks(
    article_type: str,
    topic: str,
    audience: str,
    product_level: str,
    outline_text: str,
) -> list[dict[str, Any]]:
    spec = ARTICLE_TYPES[article_type]
    outline_headings = extract_outline_headings(outline_text)
    base_sections = outline_headings or [name for name, _ in spec["sections"]]
    section_notes = {name: note for name, note in spec["sections"]}
    tasks: list[dict[str, Any]] = []
    for index, section in enumerate(base_sections, start=1):
        default_note = section_notes.get(section, f"围绕“{section}”完成一个清晰段落任务。")
        tasks.append(
            {
                "index": index,
                "section": section,
                "writing_goal": default_note,
                "reader_value": f"让{audience}获得一个可判断、可行动的信息点。",
                "must_include": [
                    "本节结论",
                    "支撑依据或待核验标记",
                    "边界条件",
                ],
                "avoid": [
                    "空泛趋势词",
                    "无来源数字",
                    "未经提供的客户或产品效果",
                    "重复上一节结论",
                ],
                "model_prompt": (
                    f"请为公众号文章《{topic}》撰写“{section}”这一节。"
                    f"目标读者是{audience}。写作目标：{default_note}"
                    "只使用已提供事实；缺失事实写“待核验”；不要新增客户、数字、漏洞编号、产品指标。"
                    f"产品连接策略：{product_policy(product_level)}"
                    "段落要具体、克制、可读，避免营销腔。"
                ),
                "human_review": [
                    "本节是否有明确结论。",
                    "事实是否有来源或待核验标记。",
                    "是否存在夸大承诺或未经授权信息。",
                ],
            }
        )
    return tasks


def build_pack(args: argparse.Namespace) -> dict[str, Any]:
    spec = ARTICLE_TYPES[args.type]
    outline_text = read_optional(args.outline)
    source_notes = read_optional(args.source_notes)
    argument_chain = summarize_argument_chain(read_optional_json(args.argument_chain))
    angle = args.angle.strip() if args.angle else spec["thesis_pattern"]
    angle_sentence = angle.rstrip("。！？.!?")
    title = args.title or f"{args.topic}：{spec['label']}成稿写作包"
    source_state = source_notes_summary(source_notes)
    return {
        "ok": True,
        "metadata": {
            "topic": args.topic,
            "title": title,
            "article_type": args.type,
            "article_type_label": spec["label"],
            "audience": args.audience,
            "product_level": args.product_level,
            "target_length": args.target_length,
            "fact_status": "待核验",
        },
        "writing_strategy": {
            "core_angle": angle,
            "reader_job": spec["reader_job"],
            "quality_bar": [
                "标题、摘要、开头、正文、结尾必须兑现同一承诺。",
                "每节都要有结论、依据、边界和读者收益。",
                "具体事实没有来源时必须写待核验。",
                "产品表达必须先有场景，再有能力，最后才是 CTA。",
            ],
            "product_policy": product_policy(args.product_level),
        },
        "source_notes": source_state,
        "argument_chain": argument_chain,
        "fact_ledger": [
            {
                "fact": item,
                "status": "待核验",
                "source": "待补充",
                "used_in_section": "待分配",
            }
            for item in spec["must_evidence"]
        ],
        "section_tasks": build_section_tasks(args.type, args.topic, args.audience, args.product_level, outline_text),
        "model_collaboration": {
            "system_prompt": (
                "你是微信公众号资深内容编辑，写作对象是科技、安全、AI Agent、产品类读者。"
                "你必须保持专业、具体、克制；不得编造事实；不得新增客户、数字、漏洞编号、政策、产品指标。"
                "缺失事实写“待核验”，并保留人工复核点。"
            ),
            "user_prompt": (
                f"请根据写作包撰写公众号初稿。主题：{args.topic}。文章类型：{spec['label']}。"
                f"目标读者：{args.audience}。核心角度：{angle_sentence}。"
                f"论证链核心判断：{argument_chain['core_claim']}。"
                f"目标长度：约 {args.target_length} 字。"
                "输出 Markdown；保留 frontmatter；每个关键事实必须来自材料或标注待核验。"
            ),
            "iteration_protocol": [
                "第一轮只出初稿，不排版、不上传、不生成图片。",
                "第二轮根据审稿报告修复事实、结构、表达和风险问题。",
                "第三轮再进入视觉计划和排版预览。",
            ],
        },
        "forbidden_expressions": spec["forbidden"]
        + ["最强", "唯一", "100%", "永久解决", "不看就亏", "震惊", "吊打"],
        "human_decisions_required": [
            "确认标题是否采用推荐标题。",
            "补齐或删除待核验事实。",
            "确认产品连接强度是否合适。",
            "确认客户、案例、截图、数据是否授权可公开。",
            "确认是否进入审稿质检。",
        ],
        "acceptance_checklist": [
            "文章是否有一个清楚、可被正文兑现的核心判断。",
            "开头是否具体，不是模板化套话。",
            "每节是否避免重复同一句价值判断。",
            "事实台账中的待核验项是否已处理或保留标记。",
            "是否不存在绝对化、恐吓式或过度营销表达。",
        ],
    }


def render_markdown(pack: dict[str, Any]) -> str:
    meta = pack["metadata"]
    lines = [
        "---",
        f'title: "{meta["title"]}"',
        'author: "内容运营组"',
        f'digest: "围绕{meta["topic"]}形成可控成稿写作包，具体事实待核验。"',
        f'article_type: "{meta["article_type"]}"',
        f'audience: "{meta["audience"]}"',
        'fact_status: "待核验"',
        "---",
        "",
        f"# {meta['title']}",
        "",
        "## 写作策略",
        "",
        f"- 核心角度：{pack['writing_strategy']['core_angle']}",
        f"- 读者任务：{pack['writing_strategy']['reader_job']}",
        f"- 产品策略：{pack['writing_strategy']['product_policy']}",
        f"- 目标字数：{meta['target_length']}",
        "",
        "## 论证链",
        "",
        f"- 核心判断：{pack['argument_chain']['core_claim']}",
        f"- 适用边界：{pack['argument_chain']['scope_boundary']}",
        f"- 读者动作：{pack['argument_chain']['reader_action']}",
        f"- 产品连接边界：{pack['argument_chain']['product_connection_boundary']}",
        "",
        "## 事实台账",
        "",
    ]
    for item in pack["fact_ledger"]:
        lines.append(f"- {item['fact']}：{item['status']}，来源：{item['source']}")
    lines.extend(["", "## 分段写作任务", ""])
    for task in pack["section_tasks"]:
        lines.extend(
            [
                f"### {task['index']}. {task['section']}",
                "",
                f"- 写作目标：{task['writing_goal']}",
                f"- 读者收益：{task['reader_value']}",
                f"- 必须包含：{'；'.join(task['must_include'])}",
                f"- 避免：{'；'.join(task['avoid'])}",
                "",
                "模型写作提示：",
                "",
                f"> {task['model_prompt']}",
                "",
                "人工复核：",
            ]
        )
        for review in task["human_review"]:
            lines.append(f"- {review}")
        lines.append("")
    lines.extend(
        [
            "## 模型协作提示",
            "",
            "### system",
            "",
            pack["model_collaboration"]["system_prompt"],
            "",
            "### user",
            "",
            pack["model_collaboration"]["user_prompt"],
            "",
            "## 禁用表达",
            "",
            "、".join(pack["forbidden_expressions"]),
            "",
            "## 人工决策点",
            "",
        ]
    )
    for item in pack["human_decisions_required"]:
        lines.append(f"- {item}")
    lines.extend(["", "## 通过标准", ""])
    for item in pack["acceptance_checklist"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="生成面向模型协作和人工审稿的公众号成稿写作包。")
    parser.add_argument("--topic", required=True, help="文章主题。")
    parser.add_argument("--type", required=True, choices=sorted(ARTICLE_TYPES), help="文章类型。")
    parser.add_argument("--audience", default="内部运营团队", help="目标读者。")
    parser.add_argument("--product-level", choices=PRODUCT_LEVELS, default="light", help="产品连接强度。")
    parser.add_argument("--title", help="指定标题；默认生成待定标题。")
    parser.add_argument("--angle", help="核心写作角度；不填则使用文章类型默认角度。")
    parser.add_argument("--target-length", type=int, default=1800, help="目标字数。")
    parser.add_argument("--outline", help="已有大纲 Markdown，用于提取章节。")
    parser.add_argument("--source-notes", help="事实材料或采访纪要 Markdown/TXT。")
    parser.add_argument("--argument-chain", help="article_argument_chain.py 输出的论证链 JSON。")
    parser.add_argument("--format", choices=["json", "markdown"], default=None, help="输出格式；默认按扩展名推断。")
    parser.add_argument("--out", help="输出文件。")
    args = parser.parse_args()

    pack = build_pack(args)
    out_format = args.format
    if out_format is None:
        out_format = "markdown" if args.out and Path(args.out).suffix.lower() in {".md", ".markdown"} else "json"
    content = render_markdown(pack) if out_format == "markdown" else json.dumps(pack, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print(f"成稿写作包已生成：{args.out}")
    else:
        print(content)


if __name__ == "__main__":
    main()
