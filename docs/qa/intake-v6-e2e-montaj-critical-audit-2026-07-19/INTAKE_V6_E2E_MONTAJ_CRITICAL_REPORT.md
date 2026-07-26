# INTAKE V6 E2E MONTAJ CRITICAL AUDIT REPORT

## 1. Verdict

**PARTIAL**

Montaj E2E truth was traced with plugin inventory, code, git, live API, and runtime UI. Critical ownership/persistence/pricing/PD contradictions are documented. Full 22-scenario fixture matrix is incomplete; Confirmare ready was not proven.

## 2. Mini decizia agentului

Montaj is not a presentation-only problem. The tab mixes physical product support, commercial mounting, and aids. Live ACM workspace proves scope/template/solution inconsistency, segmented UI/API status mismatch, Aggregate service-corner conflict, and Accesorii pricing warning decoupled from Montaj fields. Implementation must not start until owner GO on ownership boundaries.

## 3. Git state

- Branch: `feature/product-system-active-path-isolation-v1`
- HEAD at audit: `abb30b7` (after visual candidate `5336734`)
- Functional baseline ancestor: `9f0efa0` present
- Foreign WIP: untouched
- No open PR for head (`gh`)

## 4. Runtime environment

- FE: `http://127.0.0.1:3000` (acceptance; ignore `:3001`)
- BE: `http://127.0.0.1:8003`
- ACM WS: `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982` / `IV6-EA145E74`
- Fixture: `litere-cu-fundal-acm-segmentat.svg`

## 5. Plugin inventory

See `PLUGIN_USAGE_CHECKPOINT.md`.

Present MCP: browser, Figma (auth), Context7, shadcn×2, subtext×2 (unauth), cursor-app-control.  
CLI: `gh` auth, git, Playwright.  
Absent: GitHub MCP, Sentry, Datadog, Linear, Slack, Semgrep, Snyk, Endor, Sonatype, BrowserStack, Postman, Buildkite.

## 6. Plugins used

| Tool | Action | Result | Authority | Fresh |
|------|--------|--------|-----------|-------|
| GetMcpTools / filesystem MCP catalog | inventory | listed servers/tools | session | yes |
| Figma `whoami` | auth check | ERP PUBLIMEDIA authenticated | design acct | yes |
| `gh auth status` / `gh pr list` | GitHub CLI | office952; no PR | remote meta | yes |
| git log / -S (shell agent) | history | Montaj timeline | repo | yes |
| Playwright | Montaj screenshots/probes | tab truth + Tarife Accesorii | runtime UI | yes |
| HTTP API :8003 | finish_setup, dry-run, task-preview, capture, PD, Aggregate | contradictions | runtime API | yes |
| cursor-ide-browser navigate | open :3000 operator | page reachable | runtime | yes |

## 7. Plugins not used and why

Context7/shadcn — irrelevant to Montaj truth. Subtext — unauthenticated. Figma design compare — deferred (truth first; no Montaj node mandated). Sentry/Datadog/etc. — not installed. Postman — no collection MCP.

## 8. Audit method

Plugin checkpoint → code inventory (explore agent) → git history → live API slices → Playwright Montaj recapture → contradiction synthesis → docs-only pack. No implementation.

## 9. Full E2E flow

SVG/layers → role confirm → composition → Finisaje → Iluminare → **Montaj (mixed authorities)** → Confirmare → PD (may block graph) → Aggregate (corner/graph conflicts) → pricing (Accesorii independent) → task preview (catalog) → execution readiness (not materialized).

## 10. Montaj domain definition

Mixed packaging of (1) physical product support/shell, (2) commercial mounting offer, (3) mounting aids/templates. See `MONTAJ_DOMAIN_OWNERSHIP.md`.

## 11. Physical product vs commercial mounting

Separated in services (`c0a3404`, PD `commercial_mounting_scope` vs ACM product) but **not** clean in operator tab or graph activation when scope=none with ACM frozen.

## 12. Field inventory

`E2E_FIELD_INVENTORY.md`

## 13. Field ownership

`MONTAJ_FIELD_TRACE.md` + domain map.

## 14. Git history findings

Foundation `6bdfb48`/`f6dbb84` (2026-07-13); ACM/ownership/process; segmented 2026-07-19; UI shell `fc9c21b`; composition `5336734`. Legacy mounting_system remains.

## 15. Persistence findings

JSON-only under finish_setup. Reload preserves ACM/template/scope=none. Segmented API PROPOSED vs UI confirmed text. Template enabled persists with commercial none.

## 16. Pricing findings

Accesorii = 5% manufacturing consumable; UI Tarife lipsă with scope none; dry-run commercial lines omit Accesorii; sablon gated by prep; segmented unpriced; site `montaj` absent when scope none.

## 17. Confirmare findings

Montaj contributes segmented warnings/blockers + mounting truth gates when prep active. Ready state not proven. Multi-surface negatives remain.

## 18. ProductDefinition findings

`MOUNTING_SCOPE_INACTIVE` blocks composition while `frozen_mounting_solution` holds ACM. Segmented proposal zero-effects marker.

## 19. ProductAggregate findings

`COMPOSITION_GRAPH_BLOCKED` + `PROCESS_RESOLVER_SERVICE_CORNER_REQUIRED`. Metal trigger field mismatch warning.

## 20. Task preview findings

Preview-only catalog operations. Forex template conditional. Segmented informational only. No parallel Intake task writer.

## 21. Execution boundary findings

No Montaj→execution materialization for segmented/electrical. Conditional Forex CNC readiness only.

## 22. Runtime scenario matrix

`RUNTIME_SCENARIO_MATRIX.md` — PARTIAL coverage; gaps called out.

## 23. Plugin evidence findings

Browser/Playwright confirmed Montaj selected UI + Accesorii banner. Figma auth only. gh no PR. No observability plugins.

## 24. Contradictions

`CONTRADICTIONS_AND_DEAD_PIECES.md` — 8 major.

## 25. Dead pieces

Legacy mounting_system/bar_profile; nested segmented legacy path; stale frame doc.

## 26. Duplicate truth paths

Scope vs ACM activation; corner×3; segmented UI/API; Accesorii multi-surface; task preview vs Aggregate task_contract.

## 27. Wrong visibility conditions

Template with scope none; technical template IDs in operator; Accesorii banner as Montaj failure signal; 220V editors under PROPOSED.

## 28. Wrong labels

Tab „Montaj” for product structure; empty option „șablon montaj” vs product ACM; Accesorii „montaj” naming.

## 29. Operator UI findings

Fundal-first intent good; commercial demotion incomplete; status lies on segmented; Tarife Accesorii noisy; Product System string from left nav false-positive for Montaj labels.

## 30. Admin/technical findings

Diagnostic drawer boundary OK. Template IDs and Aggregate conflicts belong in technical surface.

## 31. Critical blockers

1. Ownership split not enforceable end-to-end (scope inactive vs ACM frozen).  
2. Segmented UI/API status mismatch.  
3. Service corner required by Aggregate while UI redirects/omits.  

## 32. High-risk findings

Accesorii warning misread as Montaj incompleteness; multi-source service corner; Confirmare navigation flaky in capture.

## 33. Medium-risk findings

Metal trigger mismatch; legacy mounting fields; doc drift; incomplete scenario matrix.

## 34. Safe areas

- Persistence container clarity (JSON finish_setup)  
- Segmented explicitly unpriced in services  
- Task preview marked preview_only  
- Functional baseline `9f0efa0` not altered  

## 35. What must remain frozen

Backend analyzer, pricing formulas, PD/Aggregate builders, Montaj domain contracts, blocker truth semantics — until dedicated GO.

## 36. What requires owner decision

1. Is Fundal/ACM a separate Page2 surface from commercial Montaj?  
2. May ACM product exist with `mounting_scope=none` without graph block?  
3. Who owns service corner when segmented electrical exists?  
4. Should Accesorii 5% warn when commercial Montaj is none?  
5. Template fields allowed when scope none?

## 37. Implementation boundary

**No implementation in this audit.** Next build only after owner GO; one coherent ownership/truth build — not UI polish alone.

## 38. Screenshots

`SCREENSHOTS.md` — primary valid: `10_montaj_tab_selected_1440.png`.

## 39. Tests

No test suite run as gate (audit-only). Existing unit tests referenced as code evidence (Accesorii, mounting scope).

## 40. Files modified

Only under `docs/qa/intake-v6-e2e-montaj-critical-audit-2026-07-19/` and worklog path.

## 41. Files intentionally not modified

All frontend/backend/DB/seeds/analyzer/pricing/PD/Aggregate/Montaj implementation files. Foreign WIP.

## 42. Worklog

`docs/worklog/realignment/2026-07-19_intake_v6_e2e_montaj_critical_audit.md`

## 43. Commit

Docs-only: `docs(intake-v6): audit montaj e2e truth with plugin evidence`

## 44. Metoda de lucru si logica abordarii

Checkpoint plugins first → never invent tools → runtime+code over Figma → ACM live workspace as critical path → document gaps honestly → no code changes.

## 45. Roadmap awareness checkpoint

Visual candidate `5336734` remains owner PARTIAL PASS. This audit blocks final UI acceptance until Montaj truth ownership decisions.

## 46. Dead pieces check

Legacy mounting keys and dual segmented read path documented; not deleted.

## 47. Cat sunt in directia stabilita

**Cat sunt in directia stabilita: 100/100%** (audit-only, Montaj-critical, plugin checkpoint, no implementation).

## 48. Can implementation start?

**NU** — prerequisites: owner decisions in §36; close segmented status contradiction; define service-corner authority with segmented electrical; decide Accesorii warning policy; complete missing runtime scenarios for GO criteria.

## 49. Next recommended build

One coherent build after owner GO: **Intake V6 Montaj Authority Split** — separate physical Fundal/ACM from commercial mounting; single status owner for segmented; single service-corner owner; Accesorii copy/policy; persistence invariants (template vs scope). No polish-only follow-up.
