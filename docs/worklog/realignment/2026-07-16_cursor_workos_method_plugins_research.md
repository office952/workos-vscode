# 2026-07-16 — Cursor WorkOS method and plugins research

## Scope

Research only: Cursor working method + trustworthy sources-of-truth plugins/MCP for WorkOS.

No installs, no Rules/`AGENTS.md`/MCP config changes, no application code, no W0-B6.

## Gate

- repo: `C:/w/psiso`
- remote: `https://github.com/office952/workos-vscode.git`
- branch: `feature/product-system-active-path-isolation-v1`
- HEAD: `c4cf5ec92685fa58a89ff75a811e8bb9cd82e1c6`
- staged: none
- dirty: ~257 unrelated entries (untouched)

## Deliverable

`docs/qa/cursor-workos-method-and-plugins-research/CURSOR_WORKOS_METHOD_AND_PLUGINS_RESEARCH.md`

## Findings (short)

- Durable law already in `AGENTS.md` (~162 lines); no `.cursor/rules`; project MCP = Figma only.
- No in-repo GitHub Actions; Playwright present; no confirmed Sentry/Datadog/analytics wiring in app code.
- Internal product WorkOS ≠ workos.com plugin.
- Keep CE for multi-step builds; do not treat CE folders as architecture SoT.
- Dirty tree remains the main staging/context risk.

## Pilots proposed (not installed)

1. Figma — design-only SoT discipline (`PILOT READ-ONLY`)
2. Agent Compatibility — one local scan (`PILOT READ-ONLY`)
3. Native `gh`/Git (+ Bugbot only after service confirmation)

## Impact

- `/modules`: NO PRODUCT IMPACT
- `/governance`: no update now; possible future agent-permission / evidence-source topics after owner GO

## Follow-up

After parallel Track A (official docs) and Track B (forum) subagents completed, the research report §6 was enriched with additional forum patterns (skills reliability, concurrent-chat workspace sharing, MCP/git/worktree hazards, Figma cloud limits) and an official capability addendum.

Owner decisions applied 2026-07-16 (evaluation only). Read-only pilots recorded in `2026-07-16_cursor_workos_readonly_pilots.md`. Accuracy note: Agent Compatibility was **cached, not installed** — scan gated.

## Commit

See research + pilots docs commit (`docs(cursor): record WorkOS method and plugin research`).
