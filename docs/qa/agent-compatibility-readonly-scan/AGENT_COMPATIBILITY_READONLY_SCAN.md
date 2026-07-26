# Agent Compatibility — Read-Only Scan (WorkOS)

**Date:** 2026-07-16  
**Repo:** `C:/w/psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `9e85ebc31540c969ca32edc207c5fbea349478c7`  
**Mode:** read-only scan — no auto-fixes, no app/config edits

---

## Verdict

`AGENT_COMPATIBILITY_SCAN_PASS`  
(Figma tool-level write disable: `FIGMA_TOOL_LEVEL_CONTROL_UNAVAILABLE` — see § Figma)

---

## Installation

| Item | Value |
|------|--------|
| Plugin | Cursor **Agent Compatibility** (`agent-compatibility`) |
| Plugin version (manifest) | `1.0.0` |
| Official source | https://github.com/cursor/plugins/tree/main/agent-compatibility |
| Enablement path | Junction: `%USERPROFILE%\.cursor\plugins\local\agent-compatibility` → cached marketplace copy `…\cache\cursor-public\agent-compatibility\3fe2823ce17c1656…` (official README local-install path) |
| CLI package | `agent-compatibility@0.1.7` (verified via `npm view` + `npx … --version`) |
| Scope | User-local plugin junction + npx cache — **not** added to frontend/backend manifests |
| Permissions used | Read repository files; terminal CLI; **no** write/auto-fix |

---

## Exact scan command

Interactive TUI (`scan` / default `--tui`) failed in this environment (Ink raw-mode / stdin). Non-interactive full report:

```powershell
npx -y agent-compatibility@0.1.7 --text C:\w\psiso
```

Also captured (same content family):

```powershell
npx -y agent-compatibility@0.1.7 --md C:\w\psiso
npx -y agent-compatibility@0.1.7 --json C:\w\psiso
```

**Scanner headline:** Compatibility (heuristic) **80/100** · ecosystems `node`, `python` · monorepo.

Raw CLI dumps were used for classification only and are **not** committed.

---

## Pillar scores (scanner)

| Pillar | Score |
|--------|------:|
| Documentation | 100 |
| Testing | 97 |
| Code Quality | 85 |
| Dev Environment | 83 |
| Build & Tasks | 76 |
| Style & Validation | 69 |
| Security & Governance | 55 |
| Observability | 50 |

Accelerators reported: **3/8** (with contradictory AGENTS.md cue — see findings).

---

## Findings (manual classification)

| Finding | Scanner claim | Classification | Evidence | Recommendation |
|---------|---------------|----------------|----------|----------------|
| No in-repo CI | Add CI that runs validation/tests from the repository | `OPTIONAL_IMPROVEMENT` / `OWNER_DECISION_REQUIRED` | No `.github/workflows`; validation is local (`npm run validate:*`, pytest). Matches prior Cursor research. | Defer until owner chooses a CI provider; do not invent Actions in this task |
| No root formatter command | Add formatter + repo-root/CI exposure | `OPTIONAL_IMPROVEMENT` | Frontend has ESLint via scripts; no single root `format` script | Optional later; not a blocker for agents that use existing lint |
| Pre-commit hooks partial | Use pre-commit/pre-push for validation | `OPTIONAL_IMPROVEMENT` | Hooks mentioned in docs; not a hard agent gate | Optional; keep explicit-path staging discipline |
| Coverage tooling partial | Add coverage thresholds/reports | `OPTIONAL_IMPROVEMENT` | Vitest/pytest exist; coverage optional | Defer |
| Runtime/toolchain pinning partial | Pin runtime/language version | `MISSING_DOCUMENTATION` (partial) | `AGENTS.md` documents `pnpm@8.10.0`, Python via `WORKOS_PYTHON` / venv; no root `.python-version` / engines hard pin everywhere | Optional pin files later; `AGENTS.md` already guides agents |
| Layout / alembic cue | Separate source/tests/config more clearly | `FALSE_POSITIVE` / low value | `backend/`, `frontend/`, `backend/tests/`, `frontend/e2e` already clear; alembic is expected | No change |
| Observability weak | Add metrics/tracing/error reporting | `OUT_OF_SCOPE` (for agent boot) / `CONFIRM_SERVICE_EXISTS` | No Sentry/Datadog in app (prior research) | Confirm service first; do not add MCP for vanity score |
| Ad hoc logging | Adopt structured logging | `OPTIONAL_IMPROVEMENT` | Python/TS logging exists unevenly | Separate observability build |
| No LICENSE | Add license file/metadata | `OWNER_DECISION_REQUIRED` | No `LICENSE` at root | Owner legal decision — not an agent auto-fix |
| CODEOWNERS partial | Add CODEOWNERS | `OPTIONAL_IMPROVEMENT` | README ownership signals only | Optional for multi-contributor phase |
| Security scan / CI security partial | Add dependency audit in CI/local | `OPTIONAL_IMPROVEMENT` | Partial tooling signals; no CI | After CI exists |
| AGENTS.md “not seen” accelerator | Add AGENTS.md (cue: `AGENTS.md (1138 words)`) | `FALSE_POSITIVE` | `AGENTS.md` exists (~1138 words, tracked) — scanner cue contradicts claim | Ignore; do **not** rewrite `AGENTS.md` for score |
| Cursor project tooling missing | Add `.cursor/rules`, skills, agents | `ALREADY_COVERED_IN_AGENTS_MD` / `OPTIONAL_IMPROVEMENT` | Durable law is `AGENTS.md`; no `.cursor/rules` by design (prior research) | Keep `AGENTS.md`; path-scoped `.mdc` only if repeated failures |
| MCP setup ok | `.cursor/mcp.json` present | Accelerator OK | Figma MCP configured | Keep; design-only |
| Dependency-to-MCP (DB/browser/llm) | Add MCP for DB/browser/llm | `FALSE_POSITIVE` / `REJECT` for DB | Local SQLite; browser via Cursor built-in; prior research rejects prod DB MCP | Do **not** add DB MCP; browser already available as native Cursor tool |
| Large QA JSON skipped | Warnings about large `docs/qa/**/*.json` | Informational | Scanner skipped large evidence files | Good; no action |
| Bounded source sample | Read subset of 400 source files | Informational | Heuristic limit | Score is incomplete by design — do not treat as full audit |

### Alignment with `AGENTS.md`

Already correctly documented (scanner noise if restated as “missing”):

- Ports 8000/3000; `dev:frontend` / `dev:backend` / `dev:stack`
- `validate:frontend` currently FAIL (TS debt) — agents must not declare green
- Prefer targeted Vitest/pytest
- Env injection via helpers; bare uvicorn does not load `backend/.env`
- Protected areas (CostEngine, Pricing, Inventory, snapshots, templates)

---

## Figma permission result

| Item | Result |
|------|--------|
| Project MCP URL | Unchanged: `https://mcp.figma.com/mcp` |
| Read tools | Still available: `whoami`, `get_metadata`, `get_screenshot`, … |
| Write tools | Still exposed in MCP tool descriptors: `use_figma`, `create_new_file`, `generate_figma_design`, `upload_assets`, Code Connect write tools, … |
| Agent-driven disable | **Not available** — no safe API from this session to toggle per-tool enablement in Customize without risking read access / inventing a wrapper |
| Operational rule | **`Figma write tools forbidden without explicit owner GO`** |

Owner should manually disable write tools in **Customize → MCP → Figma → tool toggles** if the UI allows. This agent did not change `.cursor/mcp.json`.

---

## Security

- Scan: repository-local read; no production credentials; no customer data.
- Plugin enablement: user-local junction only; not committed.
- Figma: write tools remain a prompt-injection / accidental-edit risk until manually disabled.
- No tokens printed.

---

## Impact

| Surface | Result |
|---------|--------|
| Harta sistemelor (`/modules`) | `NO PRODUCT IMPACT` |
| Guvernanta (`/governance`) | `FUTURE GOVERNANCE UPDATE` (optional): approved read-only scan tool; Figma write owner-gate — **not applied now** |

---

## Next recommendation (one)

Manually disable Figma write tools in Cursor Customize (preserve read tools), then optionally open a separate owner-gated task for CI/LICENSE only if product priority warrants — **do not** chase the 80→100 score with auto-fixes.
