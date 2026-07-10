#!/usr/bin/env python3
"""生成公众号主题与组件预览目录。

默认输出到 skill 的 assets/theme-previews/，方便后续挑选主题和检查组件效果。
"""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPT_ROOT = SCRIPT_DIR.parent
SKILL_DIR = SCRIPT_ROOT.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from wechat_format_presets import PRESETS, render, wrap_page  # noqa: E402


SAMPLE_MARKDOWN = """---
title: 公众号主题预览样稿
author: 内容运营组
digest: 用一篇短样稿同时检查标题、正文、列表、表格、代码、图片占位和创意组件。
---

# 公众号主题预览样稿

这是一篇用于检查微信公众号排版主题的样稿。它不追求完整表达，只用来观察标题层级、正文密度、重点块、组件样式和移动端阅读节奏。

:::question
为什么同一篇稿子，换一个主题后阅读感会完全不同？
:::

## 一、信息层级

好的公众号排版不是把每一段都装饰起来，而是让读者快速判断：哪里是结论，哪里是依据，哪里是下一步。

:::quote
排版的目标不是“更花”，而是让复杂信息更容易被读完、读懂、读后能行动。
:::

## 二、结构化表达

- 开头先交代问题和价值。
- 中段用小标题、列表和模块承接信息。
- 结尾给出明确但克制的行动建议。

:::definition 判断链路
把资产、风险、证据、影响和处置动作串起来的分析路径，而不是孤立地罗列信息。
:::

:::warning 发布前风险
如果图片仍然是本地路径，或稿件里存在尚未核实的内容，就不能进入草稿箱。
:::

## 三、技术内容

技术稿件常常包含命令、配置和表格。主题需要保证这些元素在手机宽度下仍然可读。

```bash
python scripts/orchestration/wechat_local_to_draft.py article.md --preset tech
```

| 检查项 | 要求 |
| --- | --- |
| 标题 | 不夸张，不误导 |
| 图片 | 可显示，有来源 |
| 草稿箱 | 明确区别于正式群发 |

:::summary 本节小结
- 信息层级要比装饰更重要
- 组件数量要克制
- 草稿箱前必须有质量检查
:::

:::source 依据与说明
本样稿仅用于本地预览，不代表真实文章事实结论。
:::

:::cta 下一步
选择适合当前账号和文章目的的主题，再进入正式排版。
:::
"""


def write_index(out_dir: Path, pages: list[tuple[str, str, str]]) -> None:
    links = []
    for key, label, filename in pages:
        links.append(
            '<li style="margin:8px 0;line-height:1.7;">'
            f'<a href="{html.escape(filename)}" style="color:#0f5f8c;text-decoration:none;">'
            f"{html.escape(key)} - {html.escape(label)}</a></li>"
        )
    index = (
        "<!doctype html>\n<html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>公众号主题预览目录</title></head>"
        "<body style=\"margin:0;background:#f7f8fa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;color:#172033;\">"
        "<main style=\"max-width:760px;margin:0 auto;padding:28px 18px 42px;box-sizing:border-box;\">"
        "<h1 style=\"font-size:24px;line-height:1.4;margin:0 0 10px;\">公众号主题预览目录</h1>"
        "<p style=\"font-size:15px;line-height:1.8;color:#64748b;margin:0 0 18px;\">"
        "用于快速比较主题密度、标题层级、组件风格和移动端阅读感。</p>"
        f"<ul style=\"padding-left:22px;margin:0;\">{''.join(links)}</ul>"
        "</main></body></html>\n"
    )
    (out_dir / "index.html").write_text(index, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="生成公众号主题与组件预览目录。")
    parser.add_argument("--out-dir", default=str(SKILL_DIR / "assets" / "theme-previews"), help="输出目录。")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_path = out_dir / "sample.md"
    sample_path.write_text(SAMPLE_MARKDOWN, encoding="utf-8")

    pages: list[tuple[str, str, str]] = []
    for key, preset in PRESETS.items():
        body, title = render(SAMPLE_MARKDOWN, preset)
        filename = f"{key}.html"
        (out_dir / filename).write_text(wrap_page(body, preset, title), encoding="utf-8")
        pages.append((key, preset.label, filename))

    write_index(out_dir, pages)
    print(f"主题预览目录已生成：{out_dir / 'index.html'}")
    print(f"主题数量：{len(pages)}")


if __name__ == "__main__":
    main()

