# 2026-07-19 — Cursor plugin / MCP / integration baseline

| Field | Value |
|-------|-------|
| Date | 2026-07-19 |
| System | Windows 10.0.26200 · Cursor 3.12.10 · VS Code CLI 1.128.0 |
| Repo | `C:/w/psiso` · branch `feature/product-system-active-path-isolation-v1` |
| Scope | Inventory → Round 1 activation — **no product changes** |

## Deliverable

`docs/qa/tooling-integration-baseline-2026-07-19/WORKOS_TOOLING_AND_INTEGRATION_BASELINE.md`

---

## A. Audit (initial — before Round 1 GO)

HEAD ~`4399875` → docs commit `aa8ace1`.

- **CLI:** git, gh (**unauthenticated**), node/pnpm; **no** semgrep/postman  
- **Thunder Client:** 2.41.0 already installed  
- **MCP ready:** Figma, Context7, shadcn, browser  
- **MCP needsAuth:** Subtext — not authenticated  
- Round 1 blocked pending owner GO  

---

## B. Owner GO received

```text
GO_ROUND1_GH_AUTH
GO_SEMGREP_CLI_LOCAL
KEEP_THUNDER_CLIENT
```

Activation start HEAD: `aa8ace1`.

---

## C. Activation results

| Gate | Result |
|------|--------|
| GO_ROUND1_GH_AUTH | **PASS** — `gh` 2.95.0 · logged in `office952` · host github.com · protocol https · scopes `gist`,`read:org`,`repo` · keyring · read-only validated · **zero write** |
| GO_SEMGREP_CLI_LOCAL | **PASS** — Semgrep **1.170.0** in `%LOCALAPPDATA%\workos-tooling\semgrep` · User PATH updated · **not** in `backend/.venv` · no cloud login · smoke scan outside repo with `--metrics=off` |
| KEEP_THUNDER_CLIENT | **PASS** — 2.41.0 kept · Postman not installed · no collections created |

### Semgrep uninstall

1. Remove `...\workos-tooling\semgrep\Scripts` from User PATH  
2. Delete folder `%LOCALAPPDATA%\workos-tooling\semgrep`

### GitHub logout (if needed)

`gh auth logout -h github.com`

---

## D. Still closed

Subtext, Linear, Slack, Sentry, Datadog, Snyk, BrowserStack, analytics, 1Password, JFrog, Zscaler, WorkOS.com, Postman.

## E. Dirty tree

Unrelated WIP left untouched; exact-path staging only for baseline docs + this worklog.
