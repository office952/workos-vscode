# 2026-07-16 — Cursor WorkOS read-only pilots

## Scope

Owner-approved evaluation only:

- Figma MCP = PILOT READ-ONLY
- Agent Compatibility = PILOT READ-ONLY (no silent install)
- Native Git/`gh` = USE NOW
- Bugbot and other SaaS plugins = deferred / confirm-first

No application code, Rules, or `AGENTS.md` changes. No new MCP servers.

## Gate

- repo: `C:/w/psiso`
- remote: `https://github.com/office952/workos-vscode.git`
- branch: `feature/product-system-active-path-isolation-v1`
- HEAD: `c4cf5ec92685fa58a89ff75a811e8bb9cd82e1c6`

## Figma pilot

### Configuration

| Item | Result |
|------|--------|
| Project config | `.cursor/mcp.json` → HTTP `https://mcp.figma.com/mcp` (no secrets in file) |
| Server identity | `plugin-figma-figma` / `user-figma` (duplicate bindings; use one) |
| Auth | OAuth; `whoami` succeeded (team plan seat present) |
| Credentials storage | Cursor OAuth session — not in git |

### Tools / permissions

- **Read used:** `whoami`, `get_metadata`, `get_screenshot`
- **Write-capable tools present (not used):** `use_figma`, `create_new_file`, `generate_figma_design`, `upload_assets`, `add_code_connect_map`, `send_code_connect_mappings`, …
- **MCP config does not constrain read-only** — disable unused write tools in Customize (owner gate for hardening)

### Real use case (read-only)

File: `https://www.figma.com/design/0CDPIuqoaZ1OQgNnvNyl1F` (Intake V6 Step 2+3 operational redesign)

Retrieved Cover frame `1:31` labels via `get_metadata` + screenshot:

- `WORKOS · Intake V6`
- `Step 2 + Step 3 Operational Redesign`
- Status: `OWNER REVIEW · Desktop-only · No product-code implementation`
- Index lists Finisaje / Iluminare / Montaj / Live Pricing / Confirmare / …

App comparison (code routes only — no runtime claim):

- Matching operator surface: `/intake-v6/:workspaceId/operator` in `frontend/src/App.tsx`
- Figma cover explicitly states design/review intent, not product-code implementation → correct SoT boundary

`get_design_context` for node `62:2` failed without a Figma desktop selection (tool limitation); metadata + screenshot were sufficient for this pilot.

### Figma answers

| Question | Answer |
|----------|--------|
| What truth? | UX/design intent, frame labels, page structure, visual composition |
| What not? | Runtime behavior, API/DB, CostEngine/pricing, architecture authority |
| Safely read-only? | **Pilot behavior yes; tool surface no** — write tools still enabled |
| Reduces manual copy? | **Yes** for frame structure/labels/screenshots |
| Continue? | **Yes**, design-only; harden by disabling write tools |

### Owner gates (Figma)

1. Disable write tools in Customize for day-to-day agents.  
2. Prefer single Figma MCP binding (drop duplicate `user-figma` vs `plugin-figma-figma` if both active).  
3. Separate owner GO before any Figma write/publish task.

## Agent Compatibility pilot

### Installation status

| State | Result |
|-------|--------|
| Cursor plugin local install (`~/.cursor/plugins/local/agent-compatibility`) | **Absent** |
| User plugin cache | **Present** (`cursor-public/agent-compatibility/3fe2823ce17c1656…`) |
| Marketplace / npm CLI | Available (`agent-compatibility@0.1.7`) |
| Scan performed this session | **No** — no silent install |

**Classification:** available / cached, **not installed** → `OWNER INSTALLATION GATE REQUIRED`

### Minimal installation proposal (owner GO required)

**Option A — Cursor plugin (preferred for skill/agents):**

1. Customize → Plugins → install **Agent Compatibility** (`agent-compatibility`), **or** symlink cache → `~/.cursor/plugins/local/agent-compatibility`.
2. Permissions: local filesystem + terminal; no SaaS auth.
3. Run: invoke skill `check-agent-compatibility` **or** CLI only (Option B).
4. Constraint: read-only scan; do not auto-edit configs or commit from findings.

**Option B — CLI-only (no plugin enablement):**

```powershell
npx -y agent-compatibility@0.1.7 scan --md C:\w\psiso
```

Same constraint: interpret findings; do not apply drive-by fixes.

### Anticipated finding classes (pre-scan, from `AGENTS.md` / repo — not CLI output)

| Topic | Likely class |
|-------|----------------|
| `validate:frontend` FAIL (~TS debt) | real defect / known gate — already documented |
| Env injection via helpers vs bare uvicorn | missing-doc risk for agents — already in `AGENTS.md` |
| No `.github/workflows` | optional improvement / N/A for CI plugins |
| Playwright + Vitest/pytest present | accelerator — duplicate of `AGENTS.md` if reported as “add tests” |
| Dirty worktree size | agent risk — process, not scanner false positive |

## Git / `gh` status

| Check | Result |
|-------|--------|
| Remote | GitHub `office952/workos-vscode.git` |
| `git` | works (`2.54.0`) → `NATIVE_GIT_READY` |
| `gh` installed | yes (`2.95.0`) |
| `gh auth status` | **not logged in** → `GH_NOT_AUTHENTICATED` |
| In-repo Actions | absent → CI not operational here |
| PR workflow | not verified without `gh` auth → treat as `PR_WORKFLOW_NOT_USED` until auth |
| Bugbot | remains **DEFER** |

Owner may run `gh auth login` when ready — not done in this pilot.

## Security summary

| Item | Figma | Agent Compatibility |
|------|-------|---------------------|
| Access | OAuth to Figma | Local FS/terminal (when installed) |
| Read/write | Write tools available | Scan is read-oriented; agents could edit if allowed |
| Command execution | Via MCP tools | CLI/npx + subagents if skill used |
| Repo scope | N/A (design cloud) | This checkout |
| Secrets | Not in git; OAuth in Cursor | None required for CLI |
| Prompt injection | Design text/annotations | Report text → do not auto-apply |
| Revocation | Disable MCP / disconnect Figma OAuth | Uninstall plugin / stop using CLI |
| Owner gate | Disable write tools; no write tasks without GO | Install/enable before first scan |

## Deferred tools (unchanged)

Sentry/Datadog, Linear/Jira/Slack, analytics, BrowserStack/Postman, SCA platforms, DB MCPs, WorkOS.com plugin, orchestrate, continual-learning, Bugbot.

## Impact

- `/modules`: **NO PRODUCT IMPACT**
- `/governance`: no update now; future owner-gated agent-permission / evidence-source topics

## Recommendation

1. Keep using Figma MCP for design intent; disable write tools.  
2. Owner GO to install/enable Agent Compatibility, then one `--md` scan.  
3. Use native Git now; authenticate `gh` when PR workflow starts; keep Bugbot deferred.

## Commit

Included with research docs commit when staged (exact paths listed in final report).
