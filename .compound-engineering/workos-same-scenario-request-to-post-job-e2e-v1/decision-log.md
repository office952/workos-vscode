# Decision log — Same-Scenario Request → Post-Job E2E V1

**Program stamp:** **SAME-SCENARIO E2E PLAN READY FOR OWNER REVIEW**  
**Date:** 2026-07-16  
**Prerequisite:** `WORKOS_POST_JOB_V1_ACCEPT_WITH_NONBLOCKING_LIMITATIONS`

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
| **P-008** | Planning writes docs only — no implementation | Separate `/ce-work` GO |

## Owner GO decisions (required before implementation)

| ID | Question | Status |
|----|----------|--------|
| **G1** | Approve same-scenario E2E as next (vs PS / APP-AUTH / HR money)? | **OPEN** |
| **G2** | Authorize new local order via real flow + cleanup? | **OPEN** |
| **G3** | Accept PARTIAL profitability (no labor money) as phase success? | **OPEN** |
| **G4** | Require linked ACM mounting in composition, or letters-only if allowed? | **OPEN** |

One-GO authorization: whole phase, not per-endpoint.

## Remains paused after GO

FLEX polish; `/operator` mirror; UI-TRUTH; APP-AUTH-06G; PS isolation as primary; capacity; Mobile V1; ShopFloor; HR labor money product; machine telemetry platform
