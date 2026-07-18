# WORKOS TOOLING AND INTEGRATION BASELINE REPORT

| Field | Value |
|-------|-------|
| Date | 2026-07-19 |
| Repo | `C:/w/psiso` |
| Scope | Cursor / MCP / CLI / integrations inventory — **no product code changes** |
| Verdict | **PARTIAL** — inventory + decision matrix complete; Round-1 installs awaiting owner GO |

## 1. Verdict

**PARTIAL**

Inventory, classification, overlap, and owner gates are complete.  
No new paid services, tokens, system agents, or product SDK wiring were introduced.  
Round-1 local installs (`gh auth`, Semgrep CLI, Postman decision) wait on owner GO.

## 2. Mini decizia agentului

**Now (already present / keep):** Figma MCP (ready), Cursor browser MCP, Context7, Compound Engineering skills/plugins, Thunder Client (API client), Playwright (local E2E), `gh`+`git` CLIs (unauthenticated).

**Install/connect next — only after owner GO (Round 1):**

1. `gh auth login` (read-focused GitHub)  
2. Semgrep CLI local-only (no Semgrep Cloud / no `SEMGREP_APP_TOKEN`)  
3. Postman: **prefer Thunder Client already installed** OR owner chooses Postman desktop — do not dual-install without reason  

**Round 2 — only if company accounts confirmed:** Linear, Slack, Sentry, Datadog.

**Conditional / later:** BrowserStack, Buildkite, SCA vendor, product analytics, JFrog, 1Password, Zscaler.

**Never for this product identity:** WorkOS.com vendor plugin (name collision only).

## 3. Environment

| Item | Value |
|------|-------|
| OS | Windows 10.0.26200 |
| Cursor | 3.12.10 (`24a12dbd…`, x64) |
| VS Code CLI | 1.128.0 (compatible side-by-side) |
| Repo | `C:/w/psiso` → `https://github.com/office952/workos-vscode.git` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD (audit start) | `4399875` |
| Git status | Dirty unrelated WIP — **untouched** |
| Backend Python | `backend/.venv` → 3.12.10 |
| Node | v24.15.0 |
| Playwright | 1.58.1 (via frontend pnpm) |

## 4. Existing inventory

### Cursor extensions (installed)

| Extension | Version |
|-----------|---------|
| `anysphere.remote-ssh` | 1.1.11 |
| `midudev.better-svg` | 0.5.1 |

### VS Code extensions (installed)

| Extension | Version | Note |
|-----------|---------|------|
| `ms-python.python` + pylance/debugpy/envs | 2026.x | Dev Python |
| `rangav.vscode-thunder-client` | 2.41.0 | **API client — overlaps Postman** |

### MCP servers (this project `c-w-psiso`)

| Server | Type | Auth / status |
|--------|------|----------------|
| `user-figma` | HTTP MCP (`mcp.figma.com`) | **ready** (tools available) |
| `plugin-figma` / repo `.cursor/mcp.json` | HTTP Figma | Configured |
| `cursor-ide-browser` | Cursor built-in | ready |
| `cursor-app-control` | Cursor built-in | ready |
| `plugin-context7-plugin-context7` | Docs MCP | ready |
| `user-shadcn` / `plugin-shadcn-shadcn` | CLI via npx | ready |
| `plugin-subtext-subtext-eu1` / `user-subtext` | FullStory Subtext HTTP | **needsAuth** — do not auto-auth |
| User `mcp.json` also lists | figma, shadcn, subtext | User-global |

### Cursor plugins (local enabled / cache)

**Local plugins:** agent-compatibility, browse, compound-engineering, cursor-team-kit, figma, shadcn, subtext  

**Cache only (not proof of company use):** amplitude, datadog, linear, aws-agents, cloudinary, magicpath, merge-agent-handler, modern-web-guidance, runlayer, context7-plugin, figma, compound-engineering, agent-compatibility

### CLI

| Tool | Present | Notes |
|------|---------|-------|
| git | Yes 2.54.0 | |
| gh | Yes 2.95.0 | **Not logged in** |
| node / npx / pnpm | Yes | |
| semgrep / snyk / newman / postman | **No** | |
| sentry-cli / datadog-ci | **No** | |
| docker / op / browserstack / buildkite | **No** | |
| playwright (global) | No | Available via frontend pnpm |

### Repo integration signals

| Signal | Finding |
|--------|---------|
| CI pipelines | **None** in repo (no Actions/Buildkite/GitLab/Azure/Jenkins) |
| Sentry/Datadog SDK | **Not** in frontend `package.json` or backend requirements |
| Analytics SDK | **Not** in app deps |
| WorkOS.com SDK | **Not** present — internal ERP name ≠ vendor |
| Prior research | `docs/qa/cursor-workos-method-and-plugins-research/` (2026-07-16) |

### Accounts / secrets

Env key **names** probed (values never printed): all listed vendor tokens **unset** in process env (`GH_TOKEN`, `SENTRY_*`, `DD_API_KEY`, `LINEAR_API_KEY`, `SEMGREP_APP_TOKEN`, etc.).

Unavailable without owner: company Linear/Slack/Sentry/Datadog/Postman org membership.

## 5. Decision matrix

| Instrument | Exists already | Integration form | Account | Real case | Risk | Decision | Reason |
|------------|----------------|------------------|---------|-----------|------|----------|--------|
| GitHub | CLI yes; auth **no** | CLI + remote URL + (optional MCP later) | Unauthenticated | Yes — PRs/issues/blame | Medium if write | **INSTALL NOW** = `gh auth` after GO | CORE; prefer least privilege (repo read + PR as needed) |
| Figma | MCP ready | MCP HTTP + Cursor plugin | Appears connected | Yes — UI/design | Medium (write tools exist) | **KEEP** — no new install | CORE; do not modify Figma files in this task |
| Linear | Plugin cache only | MCP / plugin | Unknown | Unconfirmed | High (issues write) | **CONNECT LATER** | CORE *if* company uses Linear — confirm first |
| Slack | Not configured | Marketplace / MCP | Unknown | Unconfirmed | High (messages) | **CONNECT LATER** | Only with minimal channel scope |
| Semgrep | Not installed | CLI (prefer) / IDE | Not needed for local | Yes — SAST | Low local; High cloud | **INSTALL NOW** after GO (CLI local) | CORE; no Cloud/token until separate GO |
| Supply-chain (Snyk / Endor / Sonatype) | None | CLI / GH App / SaaS | None | Deps exist | High (upload) | **CONNECT LATER** — recommend **Snyk** *if* SCA needed | Single vendor; needs account+GO; Semgrep ≠ SCA |
| Sentry | Not in app | Plugin / SDK / MCP | None | No DSN/SDK | High | **CONNECT LATER** | CONFIRM_SERVICE_EXISTS first; no DSN in code |
| Datadog | Plugin cache | Plugin / agent / MCP | None | No agent/SDK | High | **CONNECT LATER** | No infra evidence; no agent install |
| Postman | No; **Thunder Client yes** | Desktop / API | Unknown | OpenAPI on :8001 | Medium (secrets in env) | **DUPLICATE / OPTIONAL** | Prefer Thunder Client or one Postman workspace — not both |
| BrowserStack | No | Cloud + CLI | Unknown | Playwright local exists | Medium–High cost | **OPTIONAL / CONNECT LATER** | Only if cross-browser cloud required |
| Buildkite | No | CI | N/A | No CI files | — | **NOT RELEVANT** | Project has no Buildkite (or any in-repo CI) |
| Analytics (PostHog/Amplitude/Mixpanel/Pendo) | Amplitude cache only; Subtext MCP needsAuth | Plugin / MCP / SDK | Unconfirmed | No app SDK | High (PII/GDPR) | **OWNER DECISION** | At most one platform; Subtext/FullStory may already be the candidate — confirm |
| JFrog | No | Registry | Unknown | No Artifactory evidence | Medium | **NOT RELEVANT** (until evidence) | |
| 1Password | No CLI | Vault / CLI | Unknown | Useful later | High if misused | **CONNECT LATER** | No vault moves without GO |
| Zscaler | No | Corporate network | Unknown | Unknown | — | **NOT RELEVANT** preventive | |
| WorkOS.com vendor | No | Marketplace plugin | N/A | Internal ERP ≠ AuthKit | Confusion | **NOT RELEVANT** | Do not install for name collision |

## 6. Installed now

**None newly installed in this task.**

Already validated as present:

| Item | Source | Version / state | Auth | Disable |
|------|--------|-----------------|------|---------|
| Figma MCP | Official `mcp.figma.com` + Cursor Figma plugin | ready | Connected | Remove from user/repo `mcp.json` / disable plugin |
| Thunder Client | VS Code Marketplace | 2.41.0 | Local | `code --uninstall-extension rangav.vscode-thunder-client` |
| Playwright | frontend pnpm | 1.58.1 | Local | Remove frontend dep (product change — out of scope) |
| gh / git | Official installers | 2.95.0 / 2.54.0 | gh not logged in | Uninstall OS packages |
| Context7 / shadcn / CE | Cursor plugins | ready | N/A | Disable plugin in Cursor |

## 7. Installed but not connected

| Item | State |
|------|-------|
| `gh` | Installed; needs `gh auth login` (owner GO) |
| Subtext / FullStory MCP | Configured; **needsAuth** — owner GO before `mcp_auth` |
| Cached plugins (Linear, Datadog, Amplitude, …) | On disk; not company-account proof |

## 8. Deferred tools

Linear, Slack, Sentry, Datadog, BrowserStack, SCA SaaS, 1Password CLI, analytics SDKs — deferred until account confirmation and owner GO (Round 2+).

## 9. Rejected or irrelevant

| Tool | Why |
|------|-----|
| WorkOS.com plugin | Product is P-Media ERP “WorkOS”, not workos.com AuthKit/SSO |
| Buildkite | Not the project CI (no CI files found) |
| Installing all three SCA vendors | Explicitly forbidden; pick one later |
| Installing all analytics vendors | Forbidden; confirm one |
| Datadog agent | No GO; no infra evidence |

## 10. Security review

| Concern | Stance |
|---------|--------|
| Permissions | Prefer read-only GitHub; constrain Figma write via Cursor Customize |
| Code upload | No Semgrep Cloud / Snyk / SCA until GO |
| Message access | No Slack until scoped GO |
| Production | Not accessed |
| Secrets | None written to repo/docs/chat |
| Paid services | None activated |

## 11. Overlap review

| Pair | Guidance |
|------|----------|
| Sentry vs Datadog | Sentry = app errors; Datadog = logs/metrics/traces — coexist only if both services exist |
| Semgrep vs SCA | Semgrep = SAST/patterns; SCA = dependency CVEs — complementary, not duplicates |
| Postman vs Thunder Client vs OpenAPI/pytest | Prefer **one** interactive API client; keep automated tests as SoT |
| BrowserStack vs Playwright | Prefer Playwright local; BrowserStack only for real device/browser matrix gap |
| Analytics options | Confirm FullStory Subtext vs Amplitude cache vs none — pick ≤1 |

## 12. Owner gates (remaining)

1. **GO_GH_AUTH** — `gh auth login` (declare scopes: prefer repo read + PR)  
2. **GO_SEMGREP_CLI_LOCAL** — install Semgrep CLI; **no** app token / Cloud  
3. **GO_POSTMAN_OR_THUNDER** — keep Thunder Client **or** adopt Postman workspace (pick one)  
4. **GO_SUBTEXT_MCP_AUTH** — only if FullStory Subtext is company-approved  
5. **GO_LINEAR / GO_SLACK** — Round 2 if used operationally  
6. **GO_SENTRY / GO_DATADOG** — only after service existence confirmed; no SDK in product without separate build  
7. **GO_SCA_VENDOR** — if dependency scanning required (recommended candidate: Snyk)  
8. **GO_ANALYTICS_PLATFORM** — confirm which (if any) is real  

## 13. Configuration files (secret-free)

| Path | Scope | Secrets |
|------|-------|---------|
| `C:/Users/offic/.cursor/mcp.json` | User MCP: figma, shadcn, subtext URLs only | None in file |
| `C:/w/psiso/.cursor/mcp.json` | Repo MCP: figma URL only | None |
| `C:/w/psiso/.vscode/extensions.json` | Recommends `midudev.better-svg` | None |

No new secret-bearing config created.

## 14. Validation

Commands run (representative):

- `cursor --version` → 3.12.10  
- `cursor --list-extensions --show-versions`  
- `code --list-extensions --show-versions`  
- `gh --version` / `gh auth status` → not logged in  
- CLI presence probe (semgrep/snyk/postman/… absent)  
- `git remote -v` → github.com/office952/workos-vscode.git  
- CI path absence check  
- Grep app deps for sentry/datadog/analytics/workos.com → none  
- Env key presence check → all unset (names only)  

## 15. Worklog

`docs/worklog/realignment/2026-07-19_cursor_plugin_mcp_integration_baseline.md`

## 16. Git

See commit of this report + worklog only (exact-path staging). Unrelated dirty WIP not staged.

## 17. Risks (real)

1. Dirty worktree + many untracked docs → accidental broad `git add` risk (mitigated: exact-path only).  
2. Figma MCP includes write-capable tools — constrain for read-only audits.  
3. Subtext MCP auth prompt — do not authenticate casually (external session data).  
4. Cached marketplace plugins can be mistaken for “we use this in production”.  

## 18. Dead tools check

| Item | Classification |
|------|----------------|
| Amplitude / Datadog / Linear cache | Trial/cache only — not evidence of use |
| Dual shadcn MCP (user + plugin) | Mild duplicate — harmless |
| Postman + Thunder Client | Avoid dual install |
| WorkOS.com plugin | Abandoned/irrelevant for this product |

## 19. Roadmap awareness checkpoint

| Score | 8/10 |
|-------|------|
| Helps Product System | Better audit/docs/UI via Figma + GitHub + local Semgrep; no runtime change |
| Do not integrate yet | Sentry/Datadog/analytics SDKs, SCA cloud, Slack global, Buildkite invention |
| Employee Mobile | Remains **final-final** — out of tooling scope |

## 20. Direction alignment

**Cat sunt in directia stabilita: 70/100%**

Inventory + gates done; Round-1 local installs not executed pending GO.

## 21. Next recommended action

**Owner: approve Round 1 with a single GO message**, e.g.  
`GO_ROUND1_GH_AUTH + GO_SEMGREP_CLI_LOCAL + KEEP_THUNDER_CLIENT`  
Then agent installs/connects only those three outcomes — nothing else.
