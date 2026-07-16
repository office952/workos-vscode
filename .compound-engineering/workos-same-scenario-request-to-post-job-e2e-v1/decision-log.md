# Decision log — Same-Scenario Request → Post-Job E2E V1

**Program stamp:** **SAME-SCENARIO E2E OWNER GO — IMPLEMENTATION AUTHORIZED**  
**Date:** 2026-07-16 (plan) · **GO:** 2026-07-17  
**Prerequisite:** `WORKOS_POST_JOB_V1_ACCEPT_WITH_NONBLOCKING_LIMITATIONS`  
**Baseline plan:** `docs/plans/2026-07-16_workos_roadmap_reentry_next_build.md`

## Planning decisions (accepted with this plan)

| ID | Decision | Rationale |
|----|----------|-----------|
| **P-001** | Next major phase = same-scenario continuous E2E truth | Post-job V1 accepted; remaining risk is stitched demos |
| **P-002** | Scenario = `TPL-VOLUMETRIC-LETTERS_v2` | Only fully wired spine |
| **P-003** | Do **not** use order `23099` as subject | Polluted + commercially stitched vs Wave 7 quote |
| **P-004** | Prefer new local real-flow fixture; no persistent canonical seed | Avoid theater and seed debt |
| **P-005** | Active path excludes `/price` and legacy plan-from-order as primary | Preserve canonical Snapshot V2 → Plan V2 |
| **P-006** | Labor money remains out (PARTIAL profitability OK for phase success) | G2 from post-job still binds |
| **P-007** | PS redesign / FLEX polish / APP-AUTH stay deferred | Not required to prove continuous lineage |
| **P-008** | Planning writes docs only — no implementation | Superseded by 2026-07-17 GO |

## Owner GO decisions — CLOSED 2026-07-17

| ID | Question | Status |
|----|----------|--------|
| **G1** | Approve same-scenario E2E as next? | **YES** — `ALEGEM BUILDUL 1` |
| **G2** | Authorize new local order via real flow + cleanup? | **YES** — disposable/cloned local data |
| **G3** | Accept PARTIAL profitability (no labor money) as phase success? | **YES** — stock gaps explicit; labor $ still out |
| **G4** | Linked ACM mounting? | **Letters-first** — `TPL-VOLUMETRIC-LETTERS_v2` only; no Logo root; no new template; ACM only if existing composition already requires it |

### Binding re-entry gates (roadmap re-entry pack)

| ID | Binding |
|----|---------|
| **RE-G1** | Letters real template; identity Intake→Post-Job; no Logo root; no new template |
| **RE-G2** | Full commercial V1: pricing → Quote Snapshot → accept → Order Snapshot; freeze immutability |
| **RE-G3** | Controlled stock realism; do not block on advanced inventory |
| **RE-G4** | Strict PASS: full lineage + stable IDs + tests + HTTP + live UI; no manual bypass |

One-GO authorization: whole phase, not per-endpoint. **IMPLEMENTARE = GO.**

## Remains paused after GO

FLEX polish; `/operator` mirror; UI-TRUTH; APP-AUTH-06G; PS isolation as primary; capacity; Mobile V1; ShopFloor; HR labor money product; machine telemetry platform
