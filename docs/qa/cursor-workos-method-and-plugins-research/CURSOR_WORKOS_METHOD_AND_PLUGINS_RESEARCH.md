# Cursor × WorkOS — Working Method and Sources-of-Truth Research

**Date:** 2026-07-16  
**Repo:** `C:/w/psiso` (`https://github.com/office952/workos-vscode.git`)  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD at research start:** `c4cf5ec92685fa58a89ff75a811e8bb9cd82e1c6`  
**Mode:** research only — no installs, no Rules/`AGENTS.md` edits, no app code changes, no W0-B6

---

## 1. Verdict

`PLUGIN_PILOTS_RECOMMENDED`

Research is complete against current official Cursor docs, the official plugin marketplace, forum patterns (clearly labeled), and this repository’s real configuration. Maximum **three** pilots are proposed. Nothing was installed.

---

## 2. Mini decision

**How to use Cursor for WorkOS:** keep durable commands/boundaries in `AGENTS.md`; put task scope in the chat prompt + `docs/qa/BUILD_*.md` / CE plan; discover truth from the repo and runtime; stage/commit only with explicit path lists; use Figma MCP for design intent only; prefer native Git/`gh`/Vitest/pytest/Playwright over new SaaS MCPs until those services actually exist.

**Already good:** concise durable `AGENTS.md`; Figma MCP already project-configured; Compound Engineering used for structured research/plan/validation; protected-area discipline; dirty-tree staging discipline in recent cleanup commits.

**Should change (later, owner-gated):** reduce prompt length for small tasks; avoid treating CE folders as product truth; disable unused MCP tools; do not auto-grow `AGENTS.md` via continual-learning without review; optionally add thin `.cursor/rules/*.mdc` only for path-scoped hotspots (CostEngine, Intake V6) — **not in this research task**.

**Tools that deserve attention now:** Figma MCP (project-configured; write tools still exposed — constrain via Customize), Agent Compatibility (official; **cached under user plugins, not installed** until owner install gate), native Git/`gh` + Bugbot when PR flow is used — not Datadog/Linear/Sentry/WorkOS.com until services are confirmed.

### Owner decisions recorded (2026-07-16)

```text
FIGMA = PILOT READ-ONLY
AGENT COMPATIBILITY = PILOT READ-ONLY
NATIVE GIT/GH = USE NOW
BUGBOT = DEFER UNTIL REAL PR WORKFLOW
SENTRY/DATADOG = CONFIRM SERVICE EXISTS FIRST
LINEAR/JIRA/SLACK = CONFIRM OPERATIONAL USE FIRST
ANALYTICS = DEFER UNTIL REAL WORKOS DATA EXISTS
WORKOS.COM PLUGIN = NOT APPLICABLE
```

Evaluation/read-only only. Installation, auth expansion, or write permission needs a separate owner gate.

---

## 3. Repository state (gate)

| Check | Result |
|--------|--------|
| Repo | `C:/w/psiso` |
| Remote | `https://github.com/office952/workos-vscode.git` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `c4cf5ec92685fa58a89ff75a811e8bb9cd82e1c6` |
| Staged | none |
| Dirty tree | ~257 porcelain entries (unrelated active/prototype/docs) |
| `.cursor/` | `mcp.json` only (Figma HTTP MCP); **no** `.cursor/rules/` |
| `.cursorrules` | absent |
| `AGENTS.md` | tracked; ~162 lines / ~9.5 KB |
| `.github/workflows` | **absent** (no in-repo GitHub Actions) |
| Compound Engineering | `.compound-engineering/` present; ~111 paths tracked historically; local plugin skills available |
| Project MCP | Figma only |
| Enabled MCP surfaces (IDE project) | `user-figma` / `plugin-figma-figma`, `cursor-ide-browser`, `cursor-app-control`, Context7 |
| User plugin cache (not necessarily enabled) | includes `compound-engineering`, `agent-compatibility`, `figma`, `datadog`, `linear`, `amplitude`, others |

---

## 4. Sources and dates

### Official (Tier 1)

| Source | URL | Context |
|--------|-----|---------|
| Cursor Rules | https://cursor.com/docs/rules.md | Project / User / Team Rules; AGENTS.md; `.mdc` required for project rules; precedence Team → Project → User |
| Cursor Agent overview | https://cursor.com/docs/agent/overview | Tools, Browser, Checkpoints (local, not Git) |
| MCP | https://cursor.com/docs/context/mcp.md | transports, `mcp.json` locations, OAuth, security considerations, tool approval |
| Bugbot | https://cursor.com/docs/bugbot | PR review integration; GitHub/GitLab/Bitbucket |
| Help: Rules | https://cursor.com/help/customization/rules | AGENTS.md vs `.cursor/rules` |
| Marketplace | https://cursor.com/marketplace | Featured plugins (Figma, Datadog, Linear, Slack, Sentry, …) |
| Official plugins repo | https://github.com/cursor/plugins | marketplace.json listing: `agent-compatibility`, `continual-learning`, `cursor-team-kit`, `orchestrate`, `docs-canvas`, `pr-review-canvas`, … |
| marketplace.json (raw) | fetched 2026-07-16 | authoritative plugin name list for Cursor-authored plugins |

### Vendor / product docs (Tier 2)

| Source | Note |
|--------|------|
| agents.md standard | https://agents.md/ — portable agent instructions; nested files supported by Cursor |
| Figma MCP | Project uses `https://mcp.figma.com/mcp` (official remote MCP URL pattern) |

### Forum / community (Tier 3) — not official facts

| Topic | Classification | Source |
|-------|----------------|--------|
| `AGENTS.md` / `alwaysApply` not auto-injected (Cursor 3.0.x regression; fix targeted 3.2) | **version-specific**, **repeated pattern** | https://forum.cursor.com/t/agents-md-not-automatically-injected/158448 (staff updates Apr 2026) |
| Conflicting `alwaysApply` + `globs` | **repeated pattern** | https://forum.cursor.com/t/alwaysapply-true-rules-and-cursorrules-both-silently-treated-as-requestable…/157431 |
| MCP tool count / disable unused tools | **repeated pattern** (limits evolved; dynamic discovery claimed) | https://forum.cursor.com/t/regarding-the-quantity-limit-of-mcp-tools/153432 ; older 40-tool threads |
| Worktree + Agents Window trust / MCP failures | **version-specific**, **repeated pattern** | https://forum.cursor.com/t/shell-and-mcp-not-working-properly-in-worktree-folder-in-agents-window/160365 |
| `move_agent_to_root` fails with linked worktrees | **version-specific** | https://forum.cursor.com/t/move-agent_to-root-mcp-fails-in-git-worktrees/159576 |

### Repository evidence

- `AGENTS.md`, `.cursor/mcp.json`, `.compound-engineering/*`, Playwright under `frontend/e2e`, SQLite/dev helpers, absence of `.github/workflows`, architecture note that internal WorkOS ≠ workos.com (`docs/architecture/realignment/00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md`).

---

## 5. Current Cursor capabilities (WorkOS-relevant)

For each: what / current? / WorkOS problem / when unnecessary / risks / need now? / smallest pilot.

### Project Rules (`.cursor/rules/*.mdc`)

1. Path-/description-scoped durable instructions with frontmatter.  
2. Official and current (docs/rules.md, 2026). Legacy `.cursorrules` is superseded by Rules/`AGENTS.md`.  
3. Could scope CostEngine / Intake V6 / Pricing without bloating always-on context.  
4. Unnecessary while `AGENTS.md` remains short and followed.  
5. Too many always-on rules burn context; forum reports of injection bugs (version-specific).  
6. **Not now** for config changes; optional later.  
7. Pilot: one `.mdc` with `globs` for `backend/services/*cost*` — owner GO later.

### Team Rules

1. Dashboard-enforced org rules; precedence over project/user.  
2. Official (Team/Enterprise).  
3. Shared “never CostEngine without build” across machines.  
4. Unnecessary for a single-owner / small team if `AGENTS.md` is enough.  
5. Over-enforcement can fight local experiments.  
6. **Defer** until multi-seat policy needed.

### User Rules

1. Global Agent preferences (already used heavily for git safety, communication).  
2. Official.  
3. Personal commit/staging discipline.  
4. Do not put WorkOS product law only in User Rules (not shared via git).  
5. Drift between machines.  
6. Keep as-is; do not duplicate into project.

### `AGENTS.md`

1. Always-available project agent guide (commands, validation truth, protected areas).  
2. Official Cursor + agents.md ecosystem.  
3. Cold-start correctness for agents.  
4. Do not dump task-specific prompts here.  
5. Injection regressions (forum, version-specific); compaction forgetting (anecdotal/staff-ack). Workaround: `@AGENTS.md` if needed.  
6. **Keep** as primary durable file (~162 lines is appropriate).  
7. Pilot: none — maintain manually.

### Skills

1. Invokable workflows (`SKILL.md`); agent loads when relevant.  
2. Official (skills docs + plugin skills). User has `skills-cursor/*` and CE/Figma skills.  
3. Repeatable CE/review/browser flows without stuffing Rules.  
4. Unnecessary for one-off edits.  
5. Skill sprawl → wrong workflow selection.  
6. Prefer existing CE/Figma/cursor-guide skills; do not invent new project skills yet.

### Agent / Ask / Plan / Debug modes

1. Agent edits+tools; Ask/Plan read-only or design; Debug evidence loops (product modes).  
2. Official product surfaces (Agent overview + IDE modes).  
3. Research vs implementation separation — already matches WorkOS gates.  
4. Tiny edits can stay in Agent.  
5. Wrong mode → accidental writes.  
6. Keep: research → Plan/Ask; implement → Agent after owner GO.

### Subagents / Task tool

1. Parallel read-only research or specialized reviewers.  
2. Official agent orchestration in Cursor.  
3. Parallel Track A/B/C for large audits.  
4. Unnecessary for narrow file fixes.  
5. Parallel **writes** without orchestrator → conflicts.  
6. Allow inspect-only subagents; one orchestrator stages/commits.

### Background / cloud agents / worktrees

1. Isolated or cloud execution; worktree isolation.  
2. Official (`orchestrate` plugin; Agent/worktree tooling).  
3. Parallel features without dirty-tree collisions.  
4. Unnecessary when dirty tree already has the active branch work.  
5. Forum: worktree trust/MCP failures (**version-specific**).  
6. **Defer** cloud/orchestrate until dirty tree is smaller; use worktrees only for conflicting parallel features.

### MCP

1. External tools/data via stdio/HTTP/SSE; project `.cursor/mcp.json` or user config.  
2. Official (mcp.md). Security: verify source, least privilege, approve tools.  
3. Design (Figma), later observability/issue trackers **if services exist**.  
4. Do not MCP what CLI already proves (pytest, git, Playwright).  
5. Prompt injection via external content; write scopes; tool clutter.  
6. Keep Figma; freeze new MCPs pending pilots.

### Plugins (Marketplace)

1. Bundle skills/rules/MCP (Figma, Datadog, Sentry, official Cursor kits).  
2. Official marketplace + github.com/cursor/plugins (fetched 2026-07-16).  
3. Only when they expose **authoritative** service data.  
4. Reject novelty installs.  
5. Conflicting SoT; secret sprawl.  
6. See §9–11.

### Bugbot / security review

1. PR-diff review comments; local security-review skill also exists.  
2. Official Bugbot docs.  
3. Catch regressions on Pricing/Intake before merge.  
4. Unnecessary if no PR workflow.  
5. Noise / false positives.  
6. **Defer** until regular PRs; then enable on this repo only.

### Terminal + browser

1. Run scripts; verify UI (cursor-ide-browser).  
2. Official Agent tools.  
3. Runtime truth for `/intake-v6`, `/modules`, `/governance`.  
4. Skip browser for pure docs.  
5. Auth/session blockers; ghost listeners on :8000.  
6. Keep as primary runtime evidence path.

### Checkpoints / recovery

1. Local agent snapshots before big edits; restore in chat.  
2. Official Agent overview.  
3. Recover from bad agent runs **without** `git reset --hard`.  
4. Not a substitute for Git commits.  
5. Local-only; easy to confuse with Git.  
6. Use checkpoints + explicit-path git commits.

### Hooks / automations

1. Lifecycle automations (marketplace “Automations”; create-hook skill).  
2. Official product direction; verify before relying.  
3. Could auto-remind staging discipline.  
4. Unnecessary while prompts already enforce gates.  
5. Silent automation risk.  
6. **Defer**.

---

## 6. Forum findings (labeled)

| Finding | Label | Implication for WorkOS |
|---------|-------|------------------------|
| Rules/`AGENTS.md` sometimes not auto-injected on certain Cursor 3.0.x builds; staff pointed to 3.2 fix; `@AGENTS.md` workaround | version-specific, repeated | Keep Cursor updated; if agent ignores boundaries, force `@AGENTS.md` |
| Disable unused MCP tools to reduce noise | repeated pattern | Keep only Figma tools needed for design tasks |
| Worktree Agents Window trust breaks shell/MCP | version-specific | Prefer sequential work on primary checkout while dirty tree is large |
| Dynamic context discovery reduces old “40 tools” pain | community claim + Cursor blog reference in forum | Still prefer few high-value MCPs for SoT clarity |
| Skills often not auto-invoked; AGENTS.md / explicit attach more reliable | repeated pattern (community evals cited) | Prefer durable law in `AGENTS.md`; invoke CE/Figma skills explicitly when needed |
| Concurrent chats share workspace/git state; histories isolated | repeated pattern + staff acknowledgment | Parallel WorkOS streams → separate Cursor windows or worktrees, not two chats on one dirty tree |
| MCP tool-poisoning / prompt-injection class; historical Cursor MCP CVEs | security community + version-specific disclosures | Keep MCP allowlist tiny; disable Auto-Run for untrusted tools; update Cursor |
| Agent may `git stash` / `git restore` / broad VCS when Auto-Run allowed | repeated pattern | Explicit-path staging only; never Auto-Run destructive git |
| Silent Worktree mode → edits under `~/.cursor/worktrees` | repeated pattern + staff “known issue” | Verify Local vs Worktree before agent edits on this checkout |
| Figma MCP: OAuth/tool-routing flaky; often unsupported on Cloud Agents | repeated pattern + staff note | Use Figma MCP in IDE local agents; verify tools actually called |
| Windows: duplicate remote MCP connections if global+project duplicated | repeated pattern, version-specific | Keep Figma only in project `mcp.json`; avoid duplicate user config |

Do **not** treat forum posts as product guarantees.

### Official capability addendum (Track A, 2026-07-16)

Additional official surfaces confirmed via Cursor docs index (`cursor.com/llms.txt`) that reinforce the operating model:

- Mode switch (Agent/Ask/Plan/Debug) **starts a fresh context** — plan research in Ask/Plan, then implement in a new Agent turn with a short handoff.
- Cloud Agents are the current name for former Background Agents; local `~/.cursor/hooks.json` does **not** run on cloud VMs.
- First-party marketplace plugins verified by name: `orchestrate`, `agent-compatibility`, `continual-learning`, `cursor-team-kit`, `docs-canvas`, `pr-review-canvas` (plus catalog entries such as Compound Engineering / Thermos).
- Local **Agent Review** and cloud **Bugbot** / **Security Agents** are distinct; Bugbot findings often CI-`neutral` unless fail-on-unresolved is configured.
- `.cursorrules` is **legacy / will be deprecated** in favor of `.cursor/rules` + `AGENTS.md` (WorkOS already has no `.cursorrules`).

---

## 7. Current WorkOS setup audit

| Question | Finding |
|----------|---------|
| Rules duplicated/contradictory? | No project `.cursor/rules`; durable law lives in `AGENTS.md` + User Rules. Mild overlap (git safety in User Rules vs commit sections in prompts) — acceptable. |
| `AGENTS.md` size? | Appropriately durable (~162 lines). Not too large. |
| Task instructions as permanent rules? | Mostly kept in CE folders / long prompts / worklogs — good. Risk: CE artifacts and root session notes (recently cleaned) were polluting context. |
| Skills used correctly? | CE + Figma + cursor-guide used; good. |
| CE vs native Cursor? | CE adds structured research/plan/validation folders; overlaps Plan mode and native review skills. Keep CE for multi-step builds; do not invent a second parallel “memory” system. |
| Prompts too prescriptive/long? | **Yes for small tasks** — recent cleanup/research prompts are excellent for high-risk hygiene, heavy for tiny edits. Proportional prompts recommended. |
| Agent freedom? | Research tracks with inspect-only subagents are healthy. |
| Owner gates clear? | Yes when prompts list Decizii / GO. Keep. |
| Worklogs useful or excessive? | Useful when one worklog per batch; bulk untracked worklogs still noise. |
| Too many files in context? | Dirty tree (~257) + large CE trees + docs/qa packs → high pollution risk. |
| Stale docs? | Historical chatgpt-path citations remain in some dirty worklogs; architecture authority policy exists — agents must prefer Level-ranked docs. |
| Dirty tree staging risk? | **High** — explicit path staging remains mandatory. |
| Build sizing? | Recent commits show good isolation; continue. |
| Commit boundaries? | Clear when owner authorizes; do not auto-commit research. |

**Minimum useful corrections (recommend only — not applied):**

1. Prefer short prompts for ≤1-file fixes; reserve mega-prompts for hygiene/architecture.  
2. Treat `.compound-engineering/<task>/` as working memory, not Level-1 architecture.  
3. Keep MCP allowlist minimal (Figma + browser).  
4. Later: optional path-scoped `.mdc` for CostEngine — owner GO.  
5. Do not enable continual-learning auto-writes to `AGENTS.md` without review.

---

## 8. Recommended WorkOS Cursor operating model

### Permanent rules — where things live

| Layer | Belongs here | Does not belong |
|-------|--------------|-----------------|
| `AGENTS.md` | Ports, canonical scripts, validation truth, protected areas, do-not-do | Task checklists, Decizie one-offs, long QA matrices |
| `.cursor/rules/*.mdc` (future) | Path-scoped domain law (e.g. CostEngine) | Global duplicates of `AGENTS.md` |
| User Rules | Personal communication + git safety | Product architecture |
| Skills / CE | Repeatable workflows (plan, review, browser test) | One-off owner decisions |
| Worklogs / `docs/qa/BUILD_*` | What happened this batch | Forever agent law |

Avoid copying the same rule into all four layers.

### Task workflow (proportional)

| Step | Tiny fix | Normal feature | High-risk (Pricing/CostEngine/templates) |
|------|----------|----------------|------------------------------------------|
| Research | optional | yes | mandatory |
| Architecture decision | — | if needed | owner gate |
| Owner GO | — | if boundary unclear | mandatory |
| Implement | yes | yes | yes, narrow scope |
| Tests | targeted | targeted | targeted + related |
| Runtime | if UI | preferred | required when operator path |
| Review | diff glance | CE/native review | Bugbot or security-review skill |
| Commit | owner ask | owner ask | owner ask + exact paths |
| Worklog | skip / one line | short | required |
| Closure | stop | stop | stop |

### Context management

- **New chat** when: topic changes, agent loops, assumptions stale, or after large compaction.  
- **Include:** goal, branch/HEAD gate, boundary (“do not touch X”), paths if known.  
- **Discover from repo:** imports, contracts, tests — do not paste entire docs trees.  
- **Avoid stale assumptions:** re-read `git status` / HEAD; prefer tracked architecture over old session notes.  
- **Summarize/reset:** after a PASS batch, start fresh for the next Decizie.

### Multitasking

| Situation | Choice |
|-----------|--------|
| One area, few files | single agent |
| Parallel read-only research | subagents; orchestrator decides |
| Conflicting feature branches | worktrees (after dirty tree shrinks) |
| Staging/commit | **only orchestrator / human** |
| Parallel writes to same files | forbidden |

### Review and recovery

1. `git diff` / cached diff for staged set  
2. Targeted tests from `AGENTS.md`  
3. Browser/runtime when UI claimed  
4. Optional Bugbot on PR  
5. Checkpoints for mid-chat rollback; Git for durable history  
6. Never `git clean` / `reset --hard` / `git add .`  
7. Bad run → restore checkpoint or discard unstaged paths; re-prompt with narrower scope  

---

## 9. Plugin / MCP evaluation

**Principle:** useful only if the service is real, authoritative, least-privilege, and does not create a competing SoT.

| Tool/plugin | Source of truth | Service exists? | Access | Benefit | Risk | Overlap | Setup | Recommendation | Pilot |
|-------------|-----------------|-----------------|--------|---------|------|---------|-------|----------------|-------|
| **Figma MCP** (project `.cursor/mcp.json`) | UX/design frames, Code Connect | **Confirmed** (used in WorkOS design/QA) | OAuth; design read/write via MCP tools | Align Intake/Product System UI to MASTER frames | Design mistaken for runtime/architecture truth; prompt injection via file content | Native screenshots/browser | Low (already configured) | `PILOT_READ_ONLY` (harden usage) | Design-only tasks; never pricing/architecture SoT |
| **cursor-ide-browser** | Live DOM/runtime UI | Confirmed (Cursor built-in) | Browser control | `/modules`, `/governance`, Intake proof | Session/auth friction | Playwright CLI | Already on | `USE_NATIVE_CURSOR_FEATURE` | Runtime verification |
| **Agent Compatibility** (`agent-compatibility`) | Repo startup/docs/validation friction score | Official plugin; **user cache present, not installed locally** (2026-07-16 check) | Local CLI + agents; no SaaS | Surfaces docs vs `AGENTS.md` vs real boot gaps | Heuristic score ≠ product quality | Manual audits / CE startup notes | Low | `PILOT_READ_ONLY` → **OWNER INSTALLATION GATE** before scan | Enable plugin or approve `npx agent-compatibility@0.1.7 scan --md` |
| **GitHub / `gh` CLI** | Remote PRs, issues, git history | Confirmed remote exists | Token scopes | PR/review delivery truth | Broad token | Native git in Cursor | Low | `USE_NATIVE_CURSOR_FEATURE` | Prefer `gh` over GitHub MCP until needed |
| **GitHub Actions / CI MCP** | CI status | **Not in repo** (no `.github/workflows`) | N/A | — | Fake CI SoT | Local npm/pytest | — | `CONFIRM_SERVICE_EXISTS` | Add CI first, then integrate |
| **Bugbot** | PR diff findings | Unknown if org-enabled | GitHub app | High-risk PR review | Noise | CE code-review / security-review skill | Medium | `DEFER` | Enable when PR cadence exists |
| **Datadog plugin** | Logs/metrics/traces | **Unknown** (plugin cached; **no** app dependency found) | Org OAuth / API | Runtime incidents | Prod data exposure | — | High | `CONFIRM_SERVICE_EXISTS` | None until service confirmed |
| **Sentry plugin** | Error events | **Unknown** (not in app deps) | OAuth | Crash truth | PII in events | — | High | `CONFIRM_SERVICE_EXISTS` | None |
| **Linear / Slack** | Issues / chat decisions | **Unknown** | Read/write issues/messages | Workflow glue | Chat becomes fake SoT | Worklogs / Decision logs | Medium | `DEFER` | Keep decisions in `docs/` |
| **Postman / BrowserStack** | API collections / device cloud | Unknown / Playwright local exists | Cloud creds | Extra QA | Cost + duplicate of Playwright | Local Playwright | Medium–High | `REJECT` for now | Prefer `test:e2e:*` |
| **Semgrep / Snyk / JFrog / Endor** | Vuln/deps | Unknown | Repo scan tokens | Supply chain | Overlap if multiple | Manual review | Medium–High | `CONFIRM_SERVICE_EXISTS` → at most one later | None now |
| **PostHog / Amplitude / Mixpanel / Pendo** | Product analytics | Amplitude plugin cached; **no** confirmed WorkOS deployment in code | Analytics read | Usage truth | Wrong product assumptions | — | Medium | `CONFIRM_SERVICE_EXISTS` | None |
| **PostgreSQL MCP** | Live schema/data | Local **SQLite** primary per `AGENTS.md` | DB credentials | Schema inspection | **Prod mutation / customer data** | Alembic + code models | High | `REJECT` default; owner GO only for read-only **dev** | Forbidden for prod |
| **OpenAPI/Swagger MCP** | API contract | Partial (FastAPI app; no dedicated OpenAPI MCP) | Read | API shape | Drift vs code | Read routers/schemas | Low | `USE_NATIVE_CURSOR_FEATURE` | Read `backend/` schemas |
| **Context7** | Library docs | Confirmed in MCP list | Read docs | Framework API truth | Generic SEO-ish wrong version | WebSearch | Low | `USE_NATIVE_CURSOR_FEATURE` | Library questions only |
| **Compound Engineering** | Task research/plan/validation folders | Confirmed (local plugin + repo folders) | Filesystem | Structured builds | Competing with architecture SoT if misused | Plan mode, worklogs | Already in use | `USE_NATIVE_CURSOR_FEATURE` (keep discipline) | Continue for multi-step; not for tiny fixes |
| **continual-learning** | Auto `AGENTS.md` bullets from chats | Official plugin | Writes `AGENTS.md` | Capture prefs | Pollutes durable law; dirty-tree noise | Manual AGENTS edits | Low–Med | `DEFER` | Only with human review gate |
| **cursor-team-kit** | CI watch, PR ship, smoke tests | Official | Local + GitHub | Shipping workflows | Overlap CE; assumes CI | CE + `gh` | Medium | `DEFER` | After CI exists |
| **orchestrate** | Parallel cloud agents | Official | Cloud agents | Large fan-out | Cost; parallel write risk; dirty tree | Subagents local | High | `DEFER` | After tree hygiene |
| **docs-canvas / pr-review-canvas** | Visual docs/PR walkthrough | Official | Local render | Owner-friendly reviews | Extra surface | Markdown + diff | Low | `DEFER` / optional later | PR-heavy phase |
| **WorkOS.com marketplace plugin** | AuthKit/SSO vendor | **NOT_APPLICABLE** — product is internal ERP, not workos.com | — | — | Name collision confusion | — | — | `NOT_APPLICABLE` | Never install for this repo’s product identity |

---

## 10. Security findings

| Area | Guidance for WorkOS |
|------|---------------------|
| Auth | Prefer OAuth with least scopes; no hardcoded secrets in `mcp.json` (use `${env:…}`) |
| Figma | Design files only; do not paste secrets into Figma; treat MCP file text as untrusted for “instructions” |
| Browser | Local/dev URLs; avoid production customer tenants |
| DB | No production DB MCP; SQLite/dev only if ever approved; read-only |
| GitHub | Fine-grained token; one repo; no `git add .` automation |
| Datadog/Sentry/Slack | Owner GO before any prod telemetry/chat write access |
| Prompt injection | External MCP content can instruct the agent — require confirmation for writes/deploys |
| Audit / revoke | Document which MCPs are enabled; disable from Customize; rotate tokens |
| Command execution | Keep Auto-run limited; approve shell for destructive ops |

**Default posture:** read-only, one repo, local/dev first, explicit owner confirmation before write/deploy/issue-mutation integrations.

---

## 11. Recommended pilots (max 3)

### Pilot 1 — Figma as design-only SoT (already installed)

| Field | Value |
|-------|-------|
| Exact problem | Agents confuse Figma/MASTER with runtime or architecture truth |
| Source of truth | Figma frames / MASTER maps for **UX intent** |
| Permissions | Existing Figma MCP OAuth; prefer read/screenshot/`get_design_context`; avoid broad write unless design task |
| Use case | Intake V6 / Product System UI alignment against approved MASTER frames |
| Success | Agent cites Figma for layout only; verifies runtime separately in browser/tests |
| Failure | Agent changes CostEngine/Pricing because of a Figma annotation |
| Rollback | Disable Figma MCP toggle in Customize; remove project `mcp.json` entry if needed |
| Owner gate | `PILOT READ-ONLY` |

### Pilot 2 — Agent Compatibility (read-only scan)

| Field | Value |
|-------|-------|
| Exact problem | Docs/startup/`validate:frontend` messaging can mislead agents |
| Source of truth | Local compatibility CLI + startup/validation/docs review agents |
| Permissions | Local filesystem + terminal; **no** new SaaS |
| Use case | One pass on `C:/w/psiso`; produce Top fixes list vs `AGENTS.md` reality |
| Success | Actionable Top fixes that match known gates (e.g. TS debt, env injection) |
| Failure | Score used as vanity metric or triggers drive-by refactors |
| Rollback | Uninstall/disable plugin; delete any generated report if unwanted |
| Owner gate | `PILOT READ-ONLY` |

### Pilot 3 — Native delivery truth (`gh` + optional Bugbot later)

| Field | Value |
|-------|-------|
| Exact problem | Need PR/review truth without inventing CI MCP |
| Source of truth | Git remote + `gh` PR view; Bugbot only after PRs are routine |
| Permissions | GitHub token read (PR) / Bugbot app if enabled |
| Use case | Open/review PRs for isolation/cleanup commits |
| Success | Agent uses `gh pr` instead of scraping; no fake Actions status |
| Failure | Install GitHub MCP + Datadog “because marketplace” without services |
| Rollback | Revoke GitHub app; stop using Bugbot |
| Owner gate | `CONFIRMAM MAI INTAI SERVICIUL` for Bugbot org enablement; until then `USE_NATIVE` only |

---

## 12. Defer / reject list

| Item | Status | Why |
|------|--------|-----|
| Datadog / Sentry | `CONFIRM_SERVICE_EXISTS` | Cached plugins ≠ deployed product telemetry |
| Linear / Slack as SoT | `DEFER` | Decisions belong in docs/decision logs |
| Postman / BrowserStack | `REJECT` (now) | Playwright already present |
| Multiple SCA tools | `DEFER` | Pick at most one after confirmation |
| Analytics (Amplitude/PostHog/…) | `CONFIRM_SERVICE_EXISTS` | No confirmed WorkOS product analytics wiring found |
| Postgres/prod DB MCP | `REJECT` | SQLite/dev; prod forbidden |
| WorkOS.com plugin | `NOT_APPLICABLE` | Name collision only |
| continual-learning auto-AGENTS | `DEFER` | Dirty tree + durable-law risk |
| orchestrate / cloud fan-out | `DEFER` | Dirty tree + parallel write risk |
| cursor-team-kit full kit | `DEFER` | No in-repo Actions yet; overlaps CE |

---

## 13. Owner decision pack (RO)

### Pilot A — Figma (design-only)

**Ce este:** MCP Figma deja configurat în `.cursor/mcp.json`.  
**Ce adevăr ne oferă:** intenție UX / frame-uri MASTER — nu runtime, nu CostEngine.  
**Ce acces primește:** OAuth Figma (design).  
**Ce problemă rezolvă:** aliniere UI fără copy manual din Figma.  
**Riscul principal:** Figma tratat ca arhitectură/pricing.  
**Se suprapune?** Da, parțial cu screenshot-uri browser / Playwright — complementar.  
**Recomandarea agentului:** `PILOT READ-ONLY` (disciplina de folosire, fără instalare nouă).

### Pilot B — Agent Compatibility

**Ce este:** plugin oficial Cursor `agent-compatibility`.  
**Ce adevăr ne oferă:** frecare startup / docs / validation loop vs realitate.  
**Ce acces primește:** local CLI + citire repo.  
**Ce problemă rezolvă:** agenți care declară PASS pe `validate:frontend` sau inventează pași de boot.  
**Riscul principal:** score vanity / refactor necerut.  
**Se suprapune?** Parțial cu CE startup notes — acceptabil ca scan punctual.  
**Recomandarea agentului:** `PILOT READ-ONLY`.

### Pilot C — GitHub delivery (native)

**Ce este:** `gh` + git nativ; Bugbot opțional mai târziu.  
**Ce adevăr ne oferă:** PR/remote — nu CI (inexistent în repo acum).  
**Ce acces primește:** token GitHub limitat.  
**Ce problemă rezolvă:** review/ship fără MCP redundant.  
**Riscul principal:** token prea larg; instalare MCP „de rezervă”.  
**Se suprapune?** Cu CE commit/PR skills.  
**Recomandarea agentului:** native acum; Bugbot = `CONFIRMAM MAI INTAI SERVICIUL`.

**Owner answers (choose per pilot):**  
`PILOT READ-ONLY` · `INSTALAM` · `AMANAM` · `RESPINGEM` · `CONFIRMAM MAI INTAI SERVICIUL`

---

## 14. Impact Harta sistemelor (`/modules`)

`NO PRODUCT IMPACT`

Do not register Cursor plugins as product systems.  
**Future (after approval):** if an evidence provider is adopted (e.g. Figma MASTER, CI), it may appear under development infrastructure / Surse și dovezi — **not implemented now**.

---

## 15. Impact Guvernanta sistemului (`/governance`)

No update during research.

**Possible later governance topics (after install + owner GO):**

- agent permissions / MCP allowlist  
- evidence source authority (Figma ≠ architecture)  
- owner gates for write-capable integrations  
- Important Documents unchanged by this research; B2 contracts remain out of scope  

---

## 16. Files created or changed

| Path | Action |
|------|--------|
| `docs/qa/cursor-workos-method-and-plugins-research/CURSOR_WORKOS_METHOD_AND_PLUGINS_RESEARCH.md` | created |
| `docs/worklog/realignment/2026-07-16_cursor_workos_method_plugins_research.md` | created |

**Not modified:** `AGENTS.md`, `.cursor/**` (except reading), Skills, MCP enablement, application code.

---

## 17. Commit status

Research docs only. **Not committed** (await owner authorization for a docs-only commit if desired).

Suggested message if authorized:

`docs(qa): research Cursor method and source-of-truth plugins`

---

## 18. Method used

- Verified repo gate first.  
- Parallel tracks: official Cursor docs/marketplace + forum patterns + local config inspection.  
- Compound Engineering **not** run as a full CE feature loop — native research was sufficient.  
- Official sources prioritized; forum labeled.  
- Plugin overlap judged against existing Figma MCP, Playwright, `AGENTS.md`, CE, and absence of CI/telemetry.  
- Rejected shopping-list installs; max three pilots.

---

## 19. Next safe step

Owner chooses answers for Pilots A–C above. **Do not install** anything until those answers are recorded. If authorized, optionally commit these two research docs only.
