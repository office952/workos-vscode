# WORKOS TOOLING AND INTEGRATION BASELINE REPORT

| Field | Value |
|-------|-------|
| Date | 2026-07-19 |
| Repo | `C:/w/psiso` |
| Scope | Cursor / MCP / CLI / integrations inventory — **no product code changes** |
| Verdict (audit) | **PARTIAL** — inventory complete; Round 1 was awaiting GO |
| Verdict (after Round 1 GO) | **PASS** — `gh` authenticated · Semgrep local · Thunder Client kept |

## 1. Verdict

**PASS** (Round 1 activation)

Audit inventory remains historical below. Round 1 owner GO was consumed and activated:

- `GO_ROUND1_GH_AUTH` → GitHub CLI authenticated as `office952` (keyring; https)
- `GO_SEMGREP_CLI_LOCAL` → Semgrep **1.170.0** in isolated user venv (not app `.venv`)
- `KEEP_THUNDER_CLIENT` → Thunder Client **2.41.0** kept; Postman **not** installed

No product code, CI, Cloud Semgrep, Subtext, Linear/Slack/Sentry/Datadog, or SCA SaaS.

## 1b. Round 1 activation log (2026-07-19)

| Step | Result |
|------|--------|
| Baseline HEAD at activation start | `aa8ace1` |
| Auth method | `gh auth login` device/web flow → github.com |
| Account | `office952` |
| Scopes observed | `gist`, `read:org`, `repo` (default gh; **write actions not used**) |
| Read-only checks | `gh repo view` → `office952/workos-vscode` PUBLIC; commits readable; PR/issue lists empty |
| Semgrep install | Isolated venv `%LOCALAPPDATA%\workos-tooling\semgrep` via bootstrap `python -m venv` from backend interpreter (packages **not** added to project venv) |
| Semgrep PATH | User PATH += `...\workos-tooling\semgrep\Scripts` |
| Semgrep metrics | `--metrics=off` on validation scan |
| Semgrep cloud | No `semgrep login`; no `SEMGREP_APP_TOKEN`; settings.yml has only local/anonymous keys (no API token) |
| Validation scan | Temp dir outside repo + `p/python`; exit 0; ~2.1s; no autofix |
| Uninstall Semgrep | Remove User PATH entry; delete `%LOCALAPPDATA%\workos-tooling\semgrep` |
| Thunder Client | KEEP `rangav.vscode-thunder-client@2.41.0` |
| Postman | Absent (CLI + AppData) |

## 2. Mini decizia agentului

**Audit-time (historical):** Figma MCP, Thunder Client, Playwright, CE/Context7 present; `gh` unauthenticated; Semgrep absent.

**After Round 1 GO:** GitHub CLI usable for repo read/PR inspection; Semgrep available for local SAST; Thunder Client remains sole interactive API client.

**Still closed (Round 2+):** Linear, Slack, Sentry, Datadog, Subtext auth, Snyk/SCA, BrowserStack, analytics, 1Password, JFrog, Zscaler, WorkOS.com.

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

## 12. Owner gates

### Consumed (Round 1)

1. **GO_ROUND1_GH_AUTH** — done  
2. **GO_SEMGREP_CLI_LOCAL** — done (local-only)  
3. **KEEP_THUNDER_CLIENT** — done (Postman deferred as duplicate)

### Still closed

4. **GO_SUBTEXT_MCP_AUTH** — only if FullStory Subtext is company-approved  
5. **GO_LINEAR / GO_SLACK** — Round 2 if used operationally  
6. **GO_SENTRY / GO_DATADOG** — only after service existence confirmed; no SDK in product without separate build  
7. **GO_SCA_VENDOR** — if dependency scanning required (recommended candidate: Snyk)  
8. **GO_ANALYTICS_PLATFORM** — confirm which (if any) is real  
9. **GO_POSTMAN** — only if Thunder Client proves insufficient

## 13. Configuration files (secret-free)

| Path | Scope | Secrets |
|------|-------|---------|
| `C:/Users/offic/.cursor/mcp.json` | User MCP: figma, shadcn, subtext URLs only | None in file |
| `C:/w/psiso/.cursor/mcp.json` | Repo MCP: figma URL only | None |
| `C:/w/psiso/.vscode/extensions.json` | Recommends `midudev.better-svg` | None |

No new secret-bearing config created.

## 14. Validation

### Audit (historical)

- `gh auth status` → not logged in  
- Semgrep absent from PATH  

### Round 1 activation

- `gh --version` → 2.95.0  
- `gh auth status` → logged in `office952` (keyring); scopes `gist`, `read:org`, `repo`  
- `gh repo view` → `office952/workos-vscode` PUBLIC, default `main`  
- `gh api .../commits?per_page=3` → SHAs readable  
- `gh pr list` / `gh issue list` → empty (OK)  
- Zero write: no issue/PR/push/settings  
- `semgrep --version` → 1.170.0  
- Local smoke: temp `sample.py` outside repo, `semgrep --config=p/python --metrics=off` → exit 0  
- `pip show semgrep` in `backend/.venv` → not installed (isolated)  
- Thunder Client → 2.41.0; Postman absent

## 15. Worklog

`docs/worklog/realignment/2026-07-19_cursor_plugin_mcp_integration_baseline.md`

## 16. Git

See commit of this report + worklog only (exact-path staging). Unrelated dirty WIP not staged.

## 17. Risks (real)

1. Dirty worktree + many untracked docs → accidental broad `git add` risk (mitigated: exact-path only).  
2. Figma MCP includes write-capable tools — constrain for read-only audits.  
3. Subtext MCP auth prompt — do not authenticate casually (external session data).  
4. Cached marketplace plugins can be mistaken for “we use this in production”.  
5. `gh` scopes include `repo` (default) — agent must continue avoiding write actions unless a later GO authorizes them.  
6. Semgrep User PATH change requires new shells to pick up; uninstall = remove PATH + delete isolated venv.

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

**Cat sunt in directia stabilita: 92/100%** (for Round-1 tooling activation)

Inventory retained; Round 1 activated and validated. Remaining gap is Round-2 services only when a real case appears.

## 21. Next recommended action

**Do not auto-start Round 2.** Next coherent build should be a **product/audit task that uses the activated tools** (e.g. `gh`-backed PR review or a scoped local Semgrep pass on a nominated path) — not connecting Linear/Slack/Sentry without a concrete need.
