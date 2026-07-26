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

## Figma tools — durable permission boundary

**Rule (single durable statement for this batch):**

> Figma is an approved design-intent source. Read operations are allowed. Any write operation requires explicit owner GO.

Do not duplicate this into `AGENTS.md` or `/governance` unless owner later decides it must apply to every task / product governance surface.

### Read-only verification (HEAD `a1e78d7`, 2026-07-16)

Owner prerequisite: manual disable of write-capable Figma tools in Cursor Customize (attempted / to be confirmed in UI).

| Check | Result |
|-------|--------|
| Auth (`whoami`) | PASS — authenticated |
| Metadata (`get_metadata` file `0CDPIuqoaZ1OQgNnvNyl1F` node `1:31`) | PASS — Cover labels unchanged (Intake V6 Step 2+3 OWNER REVIEW) |
| Screenshot (`get_screenshot` same node) | PASS |
| Design content modified by agent | No — write tools not invoked |
| Matching app route (code only) | `/intake-v6/:workspaceId/operator` |
| `.cursor/mcp.json` | Unchanged |

### Write-tool status (agent-visible)

**Classification:** `WRITE_TOOLS_STILL_EXPOSED`

Evidence: project MCP tool descriptors under `plugin-figma-figma` / `user-figma` still list all **26** tools, including write-capable:

`use_figma`, `create_new_file`, `generate_figma_design`, `upload_assets`, `add_code_connect_map`, `send_code_connect_mappings`, …

No per-tool `enabled: false` markers found in descriptor files. Agent cannot confirm Customize UI toggles from filesystem. Write tools were **not** invoked (even as a negative test).

If owner already toggled tools off in Customize, that UI state is opaque to this verification — treat gate as still required until tool count drops or owner confirms UI-only disable.

## Owner gates remaining

1. Confirm in Cursor Customize that Figma write tools are off (or accept operational GO gate while descriptors remain).
2. CI / LICENSE / observability only with separate product GO.
3. Do not add DB MCP.

## Impact

- `/modules` (Harta sistemelor): **NO PRODUCT IMPACT** — Figma is not a product system node.
- `/governance` (Guvernanta): **NO UPDATE REQUIRED** — Cursor MCP permission boundary is development/agent tooling; page does not fail for lacking this rule; do not add scan reports to Important Documents.

## Commit

Verification: docs-only update to this worklog when staged.
