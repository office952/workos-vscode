# PLUGIN USAGE CHECKPOINT — Intake V6 E2E Montaj Critical Audit

**Date:** 2026-07-19  
**Repo:** `C:/w/psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD at audit start:** `abb30b7` (docs hash note after visual candidate `5336734`)  
**Method:** Inventory of *actually present* Cursor MCP servers + CLI tools. Nothing installed. Nothing configured.

---

## 1. Installed / present integrations (observed)

| ID | Type | Status | Notes |
|----|------|--------|-------|
| `cursor-ide-browser` | MCP | **ready** | Live UI / CDP / screenshots |
| `user-figma` | MCP | **ready + authenticated** | `whoami` → ERP PUBLIMEDIA / office@p-media.ro |
| `plugin-figma-figma` | MCP alias (same catalog family) | present in session catalog | Overlaps `user-figma` |
| `plugin-context7-plugin-context7` | MCP | **ready** | Library docs only |
| `plugin-shadcn-shadcn` / `user-shadcn` | MCP | **ready** | UI registry helpers (duplicate pair) |
| `plugin-subtext-subtext-eu1` / `user-subtext` | MCP | tools expose `mcp_auth` only | **Not authenticated** for useful work |
| `cursor-app-control` | MCP | **ready** | Cursor workspace controls only |
| **GitHub CLI (`gh`)** | CLI (not MCP) | **authenticated** as `office952` | scopes: gist, read:org, repo |
| **Git** | local | available | Primary history authority for this audit |
| **Playwright** (frontend dep) | local | available | Runtime capture scripts |

## 2. Authenticated?

| Tool | Auth |
|------|------|
| Figma MCP | Yes (`whoami` succeeded) |
| Browser MCP | Ready (no separate auth) |
| GitHub CLI | Yes (`gh auth status`) |
| Subtext | **No** (only `mcp_auth` tool visible) |
| Context7 / shadcn | Ready; no project auth needed |

## 3. Can access this repo?

| Tool | Repo access |
|------|-------------|
| Git / filesystem tools | Yes — primary |
| GitHub CLI | Yes — remote history/PR if exists |
| Browser | Yes — via local FE `127.0.0.1:3000` proxying BE `:8003` |
| Figma | Design files only — **not** repo code truth |
| Context7 / shadcn / subtext | No meaningful repo Montaj truth |

## 4. Runtime / logs / design / CI / issues / security?

| Capability | Available? |
|------------|------------|
| Runtime UI | **Yes** — browser MCP + Playwright; FE:3000 BE:8003 live |
| Design | **Yes** — Figma MCP (intent only) |
| Commit/PR history | **Yes** — git + `gh` |
| Issues (GitHub) | Via `gh` if used; **no open PR** for this branch head |
| Sentry | **Not present** |
| Datadog | **Not present** |
| Linear | **Not present** |
| Slack | **Not present** |
| Semgrep / Snyk / Endor / Sonatype | **Not present** |
| BrowserStack | **Not present** |
| Postman MCP | **Not present** |
| Buildkite | **Not present** |
| Product analytics | **Not present** |

## 5. Relevant to this audit

- Browser / Playwright — live Montaj conditions, save/reload, screenshots  
- Git + `gh` — ownership history  
- Local API (`/api/v1/intake-v6/...`, product-system routes) — persistence/pricing/PD  
- Figma — optional visual comparison only after runtime truth  
- Context7 / shadcn / subtext — **not** relevant to Montaj E2E truth  

## 6. Will be used

1. **Git** — field/path introduction and major changes  
2. **GitHub CLI** — auth/PR context (`gh pr list` empty for head)  
3. **cursor-ide-browser** and/or **Playwright** — live UI + screenshots on `:3000`  
4. **HTTP API against `:8003`** — workspace payload, priced dry-run, task-preview, runtime-capture, PD/Aggregate  
5. **Figma MCP** — only if a known Intake Montaj node is needed for visual delta; never as functional truth  

## 7. Will not be used (and why)

| Tool | Why not |
|------|---------|
| Context7 | Library docs ≠ Montaj product truth |
| shadcn (both) | Component registry; no Intake ownership |
| Subtext | Unauthenticated; not Montaj authority |
| cursor-app-control | Workspace chrome only |
| Sentry/Datadog/Linear/Slack/Semgrep/Snyk/Endor/Sonatype/BrowserStack/Postman/Buildkite | **Not installed / not in MCP catalog** |

## 8. Installed but unavailable / unauthenticated

- **Subtext** — present, needs `mcp_auth`, unused  
- Browser tab was open on **`:3001`** — rejected for acceptance; audit uses **`:3000` only**

## 9. Overlap

- `user-figma` vs `plugin-figma-figma` — same Figma capability family  
- `user-shadcn` vs `plugin-shadcn-shadcn` — duplicate registry servers  
- `user-subtext` vs `plugin-subtext-subtext-eu1` — duplicate auth stubs  
- Git CLI vs GitHub CLI — git is authoritative for local commits; `gh` for remote PR/issue  

## 10. Stale / non-authoritative plugin risk

- Figma may lag runtime composition (`5336734`); design never overrides code/API.  
- Historical QA reports under `docs/qa/` may describe older Montaj shells (`fc9c21b` era).  
- Browser tabs on wrong port (`:3001`) would falsify evidence — avoided.  
- ProductDefinition/Aggregate endpoints may be slow or 404 if wrong path; path verified against routers.  
- List workspaces API returns full payloads — easy to misread truncated PowerShell views; prefer sliced JSON dumps.

---

## Source-of-truth order (enforced)

1. Live runtime (`:3000`/`:8003`)  
2. Live code  
3. Persisted workspace/API  
4. Git history  
5. Pricing / PD / Aggregate outputs  
6. Canonical docs  
7. Figma / historical reports (lowest)

**Plugin output must not override runtime/code truth.**
