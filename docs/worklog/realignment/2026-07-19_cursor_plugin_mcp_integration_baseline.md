# 2026-07-19 — Cursor plugin / MCP / integration baseline

| Field | Value |
|-------|-------|
| Date | 2026-07-19 |
| System | Windows 10.0.26200 · Cursor 3.12.10 · VS Code CLI 1.128.0 |
| Repo | `C:/w/psiso` · branch `feature/product-system-active-path-isolation-v1` · HEAD ~`4399875` |
| Scope | Inventory + decision matrix — **no product changes**, **no new paid services** |

## Deliverable

`docs/qa/tooling-integration-baseline-2026-07-19/WORKOS_TOOLING_AND_INTEGRATION_BASELINE.md`

## Inventory (summary)

- **Cursor extensions:** remote-ssh, better-svg  
- **VS Code extensions:** Python suite, Thunder Client 2.41.0  
- **MCP ready:** Figma, Context7, shadcn, cursor-ide-browser, cursor-app-control  
- **MCP needsAuth:** Subtext (FullStory) — not auto-authenticated  
- **CLI:** git, gh (unauthenticated), node/npx/pnpm; **no** semgrep/snyk/postman/newman/sentry-cli/datadog-ci/docker  
- **CI:** none in-repo  
- **App SDKs:** no Sentry/Datadog/analytics/workos.com  

## Decisions (high level)

| Round | Tools | Status |
|-------|-------|--------|
| Keep | Figma MCP, Thunder Client, Playwright, CE/Context7 | Already present |
| Round 1 after GO | `gh auth`, Semgrep CLI local, Postman **or** keep Thunder | **Blocked by owner GO** |
| Round 2 | Linear, Slack, Sentry, Datadog | Confirm accounts first |
| Single SCA later | Prefer Snyk **if** needed | CONNECT LATER |
| Analytics | ≤1 platform; Subtext may be candidate | OWNER DECISION |
| Reject | WorkOS.com plugin, Buildkite (not CI), multi-SCA | NOT RELEVANT |

## Owner gates

See report §12. No tokens stored. No installs executed this session.

## Potential costs

None started. SaaS (Snyk/Sentry/Datadog/BrowserStack/Slack/Linear) would incur cost only after separate GO.

## Next step

Owner issues Round-1 GO; agent installs only approved items and re-validates versions.

## Dirty tree

Large unrelated WIP left untouched; exact-path staging only for this worklog + baseline report.
