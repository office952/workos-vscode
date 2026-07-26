# Worklog — Intake V6 E2E Montaj Critical Audit

**Date:** 2026-07-19  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Visual candidate:** `5336734` (owner PARTIAL PASS)  
**Functional baseline:** `9f0efa0`  
**Audit pack:** `docs/qa/intake-v6-e2e-montaj-critical-audit-2026-07-19/`

## Scope

Audit only. No FE/BE/DB/domain changes. Plugin checkpoint mandatory before deep audit.

## Plugins

Used: MCP catalog, Figma whoami, gh CLI, git history, Playwright, HTTP API `:8003`, browser navigate `:3000`.  
Not present: Sentry, Datadog, Linear, Slack, Semgrep/Snyk/Endor/Sonatype, BrowserStack, Postman MCP, Buildkite, GitHub MCP.

## Critical findings

1. Montaj tab mixes product Fundal/ACM/segmented with commercial scope/template.  
2. ACM WS: `mounting_scope=none` + `mounting_template_enabled=true` + ACM solution + segmented `PROPOSED`.  
3. UI claims segmented confirmed; API PROPOSED.  
4. Aggregate: `MOUNTING_SCOPE_INACTIVE` + `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED`.  
5. Tarife lipsă Accesorii is 5% manufacturing consumable, not Montaj scope field.  

## Verdict

**PARTIAL** — truth traced; scenario matrix incomplete; implementation must not start.

## Commit

`docs(intake-v6): audit montaj e2e truth with plugin evidence`
