#!/usr/bin/env python3
"""用浏览器检查公众号 HTML 预览的基础视觉问题。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_viewport(value: str) -> tuple[int, int]:
    if "x" not in value.lower():
        raise argparse.ArgumentTypeError("视口格式应为 375x812")
    width, height = value.lower().split("x", 1)
    return int(width), int(height)


def launch_browser(pw, browser_name: str):
    if browser_name == "edge":
        return pw.chromium.launch(channel="msedge")
    if browser_name == "chrome":
        return pw.chromium.launch(channel="chrome")
    return pw.chromium.launch()


def main() -> None:
    parser = argparse.ArgumentParser(description="使用 Edge/Playwright 对 HTML 做移动端/桌面端视觉自测。")
    parser.add_argument("html", help="待检查 HTML 文件。")
    parser.add_argument("--viewport", action="append", type=parse_viewport, help="视口，如 375x812；可重复。")
    parser.add_argument("--out-dir", help="截图输出目录；默认在 HTML 同目录。")
    parser.add_argument(
        "--browser",
        choices=["edge", "chrome", "chromium"],
        default="edge",
        help="用于截图的浏览器。默认 edge，使用系统 Microsoft Edge。",
    )
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover - 取决于本机环境
        raise SystemExit(
            "未安装 Playwright，无法做浏览器视觉自测。"
            "可在具备依赖的环境中安装 playwright；默认浏览器使用系统 Microsoft Edge。"
            f" 原始错误：{exc}"
        )

    html_path = Path(args.html).resolve()
    if not html_path.exists():
        raise SystemExit(f"文件不存在：{html_path}")
    out_dir = Path(args.out_dir).resolve() if args.out_dir else html_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    viewports = args.viewport or [(375, 812), (414, 896), (768, 1024)]

    results = []
    with sync_playwright() as pw:
        try:
            browser = launch_browser(pw, args.browser)
        except Exception as exc:
            if args.browser == "edge":
                fix = "确认本机已安装 Microsoft Edge；或改用 --browser chromium 并执行 playwright install chromium。"
            elif args.browser == "chrome":
                fix = "确认本机已安装 Google Chrome；或改用 --browser edge。"
            else:
                fix = "执行 playwright install chromium 后重试；或改用 --browser edge。"
            raise SystemExit(
                json.dumps(
                    {
                        "ok": False,
                        "browser": args.browser,
                        "message": "Playwright 已安装，但指定浏览器不可用，视觉自测未执行。",
                        "fix": fix,
                        "error": str(exc).splitlines()[0],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        page = browser.new_page()
        for width, height in viewports:
            page.set_viewport_size({"width": width, "height": height})
            page.goto(html_path.as_uri(), wait_until="networkidle")
            screenshot = out_dir / f"{html_path.stem}.{args.browser}.{width}x{height}.png"
            page.screenshot(path=str(screenshot), full_page=True)
            metrics = page.evaluate(
                """() => {
                  const doc = document.documentElement;
                  const body = document.body;
                  const vw = doc.clientWidth;
                  const all = Array.from(document.querySelectorAll('body *'));
                  const overflow = all
                    .filter(el => el.scrollWidth > vw + 2)
                    .slice(0, 20)
                    .map(el => ({
                      tag: el.tagName.toLowerCase(),
                      text: (el.innerText || el.alt || '').trim().slice(0, 80),
                      scrollWidth: el.scrollWidth
                    }));
                  const badImages = Array.from(document.images)
                    .filter(img => !img.complete || img.naturalWidth === 0)
                    .map(img => img.getAttribute('src') || '');
                  return {
                    viewportWidth: vw,
                    bodyTextLength: (body.innerText || '').trim().length,
                    scrollHeight: doc.scrollHeight,
                    overflowCount: overflow.length,
                    overflow,
                    imageCount: document.images.length,
                    badImages
                  };
                }"""
            )
            results.append({"viewport": f"{width}x{height}", "screenshot": str(screenshot), **metrics})
        browser.close()

    blocked = [
        result
        for result in results
        if result["bodyTextLength"] == 0 or result["overflowCount"] > 0 or result["badImages"]
    ]
    print(
        json.dumps(
            {
                "ok": not blocked,
                "browser": args.browser,
                "html": str(html_path),
                "results": results,
                "blocking_count": len(blocked),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
