# 2026-07-16 — Agent Compatibility scan + Figma permissions

## Scope

Owner GO: enable Agent Compatibility; one read-only scan; classify findings; no auto-fixes; harden Figma write tools if safely possible.

## Gate

- HEAD before: `9e85ebc31540c969ca32edc207c5fbea349478c7`
- branch: `feature/product-system-active-path-isolation-v1`

## Installation

| Item | Detail |
|------|--------|
| Path | Official local enable: junction `%USERPROFILE%\.cursor\plugins\local\agent-compatibility` → marketplace cache |
| Plugin manifest | `agent-compatibility` v1.0.0 |
| CLI | `agent-compatibility@0.1.7` via `npx -y` (version verified) |
| App manifests | untouched |

## Scan

```powershell
npx -y agent-compatibility@0.1.7 --text C:\w\psiso
```

Score: **80/100** (heuristic). TUI mode blocked in non-interactive shell; `--text` used.

Report: `docs/qa/agent-compatibility-readonly-scan/AGENT_COMPATIBILITY_READONLY_SCAN.md`

## Findings (summary)

Useful signals: no in-repo CI; weak observability; no LICENSE — mostly `OPTIONAL_IMPROVEMENT` / `OWNER_DECISION_REQUIRED`.

False / ignore: “AGENTS.md not seen” while citing 1138 words; DB MCP recommendation; chase-score layout nits.

Already covered: startup/env/validation truth in `AGENTS.md`.

**No fixes applied.**

## Figma tools

- Write tools still exposed (tool-level Customize control not automatable here).
- Operational rule recorded: Figma write tools forbidden without explicit owner GO.
- `.cursor/mcp.json` unchanged; read tools preserved.

## Owner gates remaining

1. Manual Figma write-tool disable in Customize (if UI supports).
2. CI / LICENSE / observability only with separate product GO.
3. Do not add DB MCP.

## Impact

- `/modules`: NO PRODUCT IMPACT
- `/governance`: FUTURE GOVERNANCE UPDATE (optional) — not applied

## Commit

Docs-only when staged: scan report + this worklog.
