# Scripts Directory Map

`scripts/` is organized by capability boundary. Keep executable tools in the smallest matching directory, and keep reusable article/theme/template material out of executable modules.

## Directories

| Directory | Purpose |
| --- | --- |
| `orchestration/` | End-to-end entrypoints and guided workflow commands. |
| `content/` | Research ledger, argument chain, title, outline, writing pack, and draft prompt generation. |
| `review/` | Preflight checks, content quality review, rigor review, revision planning, and rewrite modes. |
| `formatting/` | WeChat HTML rendering, creative blocks, component planning, and theme preview generation. |
| `assets/` | Visual asset planning, image manifest inspection, and image source rewrite utilities. |
| `wechat/` | WeChat API dry-run/execute helpers, handoff reports, release gates, and API error handling. |
| `qa/` | Regression tests and visual self-tests. |
| `templates/` | Reusable templates, presets, snippets, schemas, and prompt packs. Avoid putting Python executables here unless they are template maintenance tools. |
| `lib/` | Reserved for shared helper modules once duplication justifies extraction. |

## Rules

- Do not add new Python files directly under `scripts/`.
- Prefer adding new article, layout, or prompt variants under `scripts/templates/` or `assets/` before adding new code.
- Keep public commands in `SKILL.md` and `references/*.md` aligned with these paths.
- If a script imports across directories, add only the specific peer directories it needs to `sys.path`; do not rely on the current working directory.
