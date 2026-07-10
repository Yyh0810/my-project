#!/usr/bin/env python3
"""公众号文章内容专业度与审稿质检。

该脚本只做本地静态审稿，不联网核验事实。它的目标是把进入排版、草稿箱
之前常见的结构、事实边界、夸大表达、合规风险和发布完整性问题显式化。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PLACEHOLDERS = [
    r"TODO",
    r"placeholder",
    r"待补充",
    r"待确认",
    r"待核验",
    r"这里补",
    r"xxx+",
]

EXAGGERATED = [
    r"最强",
    r"第一",
    r"唯一",
    r"颠覆",
    r"革命性",
    r"秒杀",
    r"吊打",
    r"彻底解决",
    r"永久解决",
    r"绝对安全",
    r"零风险",
    r"100%",
]

FEAR_MARKETING = [
    r"不看就亏",
    r"再不.*就晚",
    r"必须马上",
    r"立刻转发",
    r"全网都在",
    r"震惊",
]

SECRET_PATTERNS = [
    r"access[_-]?token\s*[:=]\s*['\"]?[A-Za-z0-9._-]{12,}",
    r"appsecret\s*[:=]\s*['\"]?[A-Za-z0-9._-]{12,}",
    r"api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9._-]{12,}",
    r"AKIA[0-9A-Z]{16}",
    r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----",
]

FACT_LIKE_PATTERNS = [
    r"CVE-\d{4}-\d{4,7}",
    r"\b\d+(?:\.\d+)?%",
    r"\d+(?:\.\d+)?\s*(?:倍|万|亿|个|家|次|分钟|小时|天)",
    r"\d{4}年\d{1,2}月\d{1,2}日",
    r"根据[^，。；\n]{2,20}(?:报告|数据|统计|研究)",
]

EVIDENCE_MARKERS = [
    "来源",
    "依据",
    "参考",
    "官方",
    "报告",
    "研究",
    "公告",
    "披露",
    "链接",
    "http://",
    "https://",
    ":::source",
    "data-creative-block=\"source\"",
]


DIMENSIONS = [
    ("title_alignment", "标题兑现度"),
    ("structure", "结构完整度"),
    ("fact_reliability", "事实可信度"),
    ("professional_tone", "专业表达"),
    ("risk_compliance", "风险合规"),
    ("product_expression", "产品表达"),
    ("reader_value", "读者收益"),
    ("publish_readiness", "发布就绪度"),
]


def dump(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def strip_frontmatter(text: str) -> tuple[str, dict[str, str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text, {}
    meta: dict[str, str] = {}
    end = None
    for idx in range(1, min(len(lines), 80)):
        if lines[idx].strip() == "---":
            end = idx
            break
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", lines[idx])
        if match:
            meta[match.group(1).lower()] = match.group(2).strip().strip('"').strip("'")
    if end is None:
        return text, {}
    return "\n".join(lines[end + 1 :]), meta


def strip_html(text: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;|&#160;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_title(path: Path, raw: str, body: str, meta: dict[str, str]) -> str:
    if meta.get("title"):
        return meta["title"]
    h1 = re.search(r"^#\s+(.+)$", body, flags=re.M)
    if h1:
        return re.sub(r"`|\*|_", "", h1.group(1)).strip()
    html_title = re.search(r"<title>(.*?)</title>", raw, flags=re.I | re.S)
    if html_title:
        return strip_html(html_title.group(1))
    return path.stem


def headings(body: str, raw: str, is_html: bool) -> list[str]:
    if is_html:
        found = re.findall(r"<h[1-6]\b[^>]*>(.*?)</h[1-6]>", raw, flags=re.I | re.S)
        return [strip_html(x) for x in found if strip_html(x)]
    return [m.group(2).strip() for m in re.finditer(r"^(#{1,6})\s+(.+)$", body, flags=re.M)]


def paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n|(?<=[。！？!?])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) >= 12]


def word_like_count(text: str) -> int:
    chinese = len(re.findall(r"[\u4e00-\u9fff]", text))
    latin = len(re.findall(r"\b[A-Za-z0-9_+-]+\b", text))
    return chinese + latin


def unique_matches(patterns: list[str], text: str, flags: int = re.I) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        if re.search(pattern, text, flags=flags):
            found.append(pattern)
    return found


def has_any(markers: list[str], text: str) -> bool:
    lower = text.lower()
    return any(marker.lower() in lower for marker in markers)


def title_tokens(title: str) -> set[str]:
    tokens = set(re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z0-9_+-]{3,}", title))
    stop = {"公众号", "文章", "为什么", "如何", "我们", "一个", "一种", "这次", "什么"}
    return {x for x in tokens if x not in stop}


def dim(score: int, issues: list[str] | None = None, suggestions: list[str] | None = None, blocking: list[str] | None = None) -> dict[str, Any]:
    return {
        "score": max(0, min(5, score)),
        "issues": issues or [],
        "suggestions": suggestions or [],
        "blocking": blocking or [],
    }


def evaluate(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8-sig")
    body, meta = strip_frontmatter(raw)
    is_html = path.suffix.lower() in {".html", ".htm"} or "<html" in raw.lower()
    plain = strip_html(raw) if is_html else re.sub(r"```.*?```", " ", body, flags=re.S)
    title = extract_title(path, raw, body, meta)
    hds = headings(body, raw, is_html)
    paras = paragraphs(plain)
    length = word_like_count(plain)
    dimensions: dict[str, dict[str, Any]] = {}
    suggested_fixes: list[str] = []

    title_issues: list[str] = []
    title_suggestions: list[str] = []
    title_blocking: list[str] = []
    if not title or title == path.stem:
        title_issues.append("缺少明确标题。")
        title_blocking.append("进入草稿箱前必须确认最终标题。")
    else:
        overlap = [t for t in title_tokens(title) if t in plain]
        if title_tokens(title) and not overlap:
            title_issues.append("标题中的核心词没有在正文中得到明显承接。")
            title_suggestions.append("补充一段回应标题承诺的正文，或重拟更贴近正文的标题。")
        if len(title) > 34:
            title_issues.append("标题偏长，微信列表页可能被截断。")
            title_suggestions.append("将标题压缩到 18-30 个中文字符附近。")
    dimensions["title_alignment"] = dim(5 - len(title_issues) - len(title_blocking), title_issues, title_suggestions, title_blocking)

    structure_issues: list[str] = []
    structure_suggestions: list[str] = []
    if length < 600:
        structure_issues.append("正文偏短，难以支撑完整公众号图文。")
        structure_suggestions.append("补足背景、分析、行动建议或产品连接。")
    if len(hds) < 2:
        structure_issues.append("小标题不足，长文扫读性偏弱。")
        structure_suggestions.append("至少拆出背景、分析、建议/下一步等层级。")
    if paras and max(len(p) for p in paras) > 360:
        structure_issues.append("存在过长段落，手机端阅读压力较大。")
        structure_suggestions.append("将长段落拆成 2-3 段，或改成列表。")
    if not re.search(r"(建议|下一步|检查|清单|行动|实践|落地|处置|总结)", plain):
        structure_issues.append("结尾或正文缺少行动导向。")
        structure_suggestions.append("补充读者可以检查、调整或决策的具体动作。")
    dimensions["structure"] = dim(5 - len(structure_issues), structure_issues, structure_suggestions)

    fact_issues: list[str] = []
    fact_suggestions: list[str] = []
    fact_blocking: list[str] = []
    placeholder_hits = unique_matches(PLACEHOLDERS, raw)
    if placeholder_hits:
        fact_issues.append("存在占位或待核验内容：" + "、".join(placeholder_hits))
        fact_blocking.append("所有待确认/待核验内容必须处理后才能进入草稿箱。")
    fact_hits = unique_matches(FACT_LIKE_PATTERNS, plain)
    if fact_hits and not has_any(EVIDENCE_MARKERS, raw):
        fact_issues.append("出现漏洞编号、日期、比例或数量等事实型信息，但未看到来源/依据说明。")
        fact_suggestions.append("补充来源说明，或用 `source` 组件标注事实边界。")
    if re.search(r"(据说|听说|网传|有人说|疑似)", plain):
        fact_issues.append("存在传闻式表达。")
        fact_suggestions.append("改为保守表述，并标注待核验或删除。")
    dimensions["fact_reliability"] = dim(5 - len(fact_issues) - len(fact_blocking), fact_issues, fact_suggestions, fact_blocking)

    tone_issues: list[str] = []
    tone_suggestions: list[str] = []
    exaggerated = unique_matches(EXAGGERATED, plain)
    fear = unique_matches(FEAR_MARKETING, plain)
    if exaggerated:
        tone_issues.append("存在夸大或绝对化表达：" + "、".join(exaggerated))
        tone_suggestions.append("改成可验证、有限定条件的表达。")
    if fear:
        tone_issues.append("存在恐吓式或营销号表达：" + "、".join(fear))
        tone_suggestions.append("改成专业、克制、面向行动的表达。")
    if re.search(r"(竞品|友商).{0,20}(垃圾|不行|落后|完败)", plain):
        tone_issues.append("存在贬损竞品或机构的表达风险。")
        tone_suggestions.append("改成对能力、场景和取舍的客观比较。")
    dimensions["professional_tone"] = dim(5 - len(tone_issues), tone_issues, tone_suggestions)

    risk_issues: list[str] = []
    risk_suggestions: list[str] = []
    risk_blocking: list[str] = []
    secrets = unique_matches(SECRET_PATTERNS, raw)
    if secrets:
        risk_issues.append("疑似包含密钥、token 或私钥。")
        risk_blocking.append("删除敏感凭证，并确认截图/代码块中没有泄露。")
    if re.search(r"(可复现|复现步骤|payload|exploit|攻击脚本|命令执行).{0,80}(步骤|代码|命令|脚本)", plain, flags=re.I):
        risk_issues.append("可能包含可滥用的攻击复现细节。")
        risk_suggestions.append("保留风险原理和防护建议，删除可直接复现的操作细节。")
    if re.search(r"(未公开|内部资料|客户名单|真实客户|合同|报价)", plain):
        risk_issues.append("可能涉及未公开客户或内部信息。")
        risk_blocking.append("确认授权范围，未确认前不得发布。")
    dimensions["risk_compliance"] = dim(5 - len(risk_issues) - len(risk_blocking), risk_issues, risk_suggestions, risk_blocking)

    product_issues: list[str] = []
    product_suggestions: list[str] = []
    product_like = re.search(r"(产品|平台|能力|方案|版本|发布|AgentBox|智能体|功能)", plain, flags=re.I)
    if product_like:
        if not re.search(r"(场景|问题|痛点|使用|部署|客户|团队|运营|安全)", plain):
            product_issues.append("产品表达缺少使用场景或读者问题。")
            product_suggestions.append("先写场景和问题，再连接产品能力。")
        if not re.search(r"(证据|案例|示例|结果|指标|截图|路径|流程|能力边界|限制)", plain):
            product_issues.append("产品能力缺少证据、示例或边界说明。")
            product_suggestions.append("补充能力边界、示例路径或可验证证据。")
    dimensions["product_expression"] = dim(5 - len(product_issues), product_issues, product_suggestions)

    value_issues: list[str] = []
    value_suggestions: list[str] = []
    if not re.search(r"(读者|团队|运营|安全人员|产品经理|开发者|客户|用户|企业)", plain):
        value_issues.append("目标读者不够明确。")
        value_suggestions.append("在开头或结尾点明文章面向谁、解决什么问题。")
    if not re.search(r"(可以|需要|建议|检查|避免|如何|步骤|清单|下一步|判断)", plain):
        value_issues.append("读者读完后能采取的动作不够明确。")
        value_suggestions.append("增加检查清单、判断标准或下一步行动。")
    dimensions["reader_value"] = dim(5 - len(value_issues), value_issues, value_suggestions)

    publish_issues: list[str] = []
    publish_suggestions: list[str] = []
    publish_blocking: list[str] = []
    if not is_html and not meta.get("digest"):
        publish_issues.append("Markdown 缺少 digest 摘要元数据。")
        publish_suggestions.append("补充 1 句不夸张、能概括正文收益的摘要。")
    if not is_html and not meta.get("author"):
        publish_issues.append("Markdown 缺少 author 作者元数据。")
        publish_suggestions.append("补充作者或团队署名。")
    if re.search(r"(javascript|vbscript):", raw, flags=re.I):
        publish_issues.append("存在危险链接协议。")
        publish_blocking.append("删除危险链接后才能进入草稿箱。")
    if placeholder_hits:
        publish_blocking.append("存在占位内容，发布就绪失败。")
    dimensions["publish_readiness"] = dim(5 - len(publish_issues) - len(publish_blocking), publish_issues, publish_suggestions, publish_blocking)

    for key, label in DIMENSIONS:
        d = dimensions[key]
        for suggestion in d["suggestions"][:2]:
            suggested_fixes.append(f"{label}：{suggestion}")

    blocking = []
    for _, label in DIMENSIONS:
        key = next(k for k, v in DIMENSIONS if v == label)
        for item in dimensions[key]["blocking"]:
            blocking.append(f"{label}：{item}")

    avg = round(sum(dimensions[key]["score"] for key, _ in DIMENSIONS) / len(DIMENSIONS), 2)
    return {
        "ok": avg >= 4 and not blocking,
        "score": avg,
        "file": str(path),
        "kind": "html" if is_html else "markdown",
        "title": title,
        "word_like_count": length,
        "blocking": blocking,
        "dimensions": dimensions,
        "suggested_fixes": suggested_fixes[:12],
        "note": "本结果为本地静态审稿，不等于事实联网核验；不确定事实仍需人工查证。",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="公众号文章内容专业度与审稿质检。")
    parser.add_argument("file", help="Markdown 或 HTML 文件。")
    parser.add_argument("--out", help="输出 JSON 文件。")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        raise SystemExit(f"文件不存在：{path}")
    result = evaluate(path)
    data = dump(result)
    if args.out:
        Path(args.out).write_text(data + "\n", encoding="utf-8")
        print(f"审稿质检结果已生成：{args.out}")
    else:
        print(data)


if __name__ == "__main__":
    main()
