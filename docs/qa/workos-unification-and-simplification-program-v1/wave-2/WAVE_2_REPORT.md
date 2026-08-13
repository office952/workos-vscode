# Wave 2 report — commercial spine and Intake V6 reality

| Field | Value |
|-------|--------|
| Date | 2026-08-13 |
| Program | `WORKOS_UNIFICATION_AND_SIMPLIFICATION_PROGRAM_V1` |
| Wave | `WAVE_2_COMMERCIAL_SPINE_AND_INTAKE_REALITY_AUDIT_V1` |
| Authorization | READ-ONLY MEGA-AUDIT / RUNTIME / DOCS / SCREENSHOTS |
| Freeze | `CURRENT_WORKOS_FROZEN_AS_REFERENCE` |
| Baseline HEAD | `513bd54a` |
| Remote parity | LOCAL=REMOTE, AHEAD=0, BEHIND=0 |
| Implementation | NO |
| Cleanup | NO |
| Unfreeze | NO |
| Owner DB mutations | 0 |
| Frontend | `http://127.0.0.1:3000` (reused live stack) |
| Backend | `http://127.0.0.1:8000` (healthy) |
| Next task | **NOT_AUTHORIZED** |

## Verdict

**PASS — Wave 2 closed as evidence (gap closure 2026-08-13).**

Primary commercial remainder was traversed read-only. Request-to-order remains **PARTIAL** as a *journey quality* finding (not an evidence gap): Cereri → V6 works; handoff on the opened workspace is blocked; client is a Relații side door; quote has no client link.

Gap closure proved Straturi, Panou / carcasă, sales×dark on all primaries, back-nav, hover/focus, and client placeholders. See `WAVE_2_GAP_CLOSURE_REPORT.md`.

This GO does **not** claim page `FINAL`, cleanup, or Wave 3.

## Scope

| Item | Value |
|------|--------|
| Primary routes | `/intake`, `/intake-v6/:id/operator`, `/orders`, `/orders/:id`, `/clients`, `/clients/:name` |
| Observed only | `/quotes` (Wave 1 owns the card) |
| Excluded | Product System full audit (edge recorded only) |
| Workspace used | existing `/intake-v6/IR-MSRB28PU/operator` — bootstrap **not** opened |
| RT | original 42/106 + gap closure 56/214; scroll FAIL=0 |

## Orchestration

| Role | Writer | Status |
|------|--------|--------|
| A | `lane-a-commercial/PAGE_CARDS.md` | PASS |
| F | `lane-f-ui-system/OBSERVATIONS.md` | PASS |
| G | `lane-g-legacy-dead/CLASSIFICATION.md` | PASS |
| H | `lane-h-nav-journeys/EDGES.md` | PASS |
| RT | `runtime/rt-capture-log.json` + `rt-gap-closure-log.json` | PASS |
| ORCH | this file + canonical indexes | PASS |
| REV | `review/WAVE_2_CONSISTENCY_REVIEW.md` | PASS |

## 1. What these pages collectively do

They are the operator path from **cerere** to **accepted snapshot**, plus a lateral **client 360**.

- Cereri chooses which request to open.
- Intake V6 is where finish/offer confirmation is supposed to happen.
- Oferte (Wave 1) is the commercial list/detail.
- Comenzi shows locked snapshots, not live re-price.
- Clienți merges activity around a name, mostly without fiscal identity.

They do **not** yet tell one story. FLUX teaches Cerere → Produse → Oferte. Work teaches Cerere → V6. Clients live under Relații.

## 2. Is request-to-order understandable?

**PARTIAL.**

An operator can open a real V6 workspace from Cereri. Confirm honesty is good (handoff disabled, 1 blocker). Completing to quote was not possible without mutation. Quote → order exists as a list jump. Quote → client does not exist. Client → cereri/oferte/comenzi exists as tabs.

## 3. Where user context is lost

- List/URL `IR-MSRB28PU` vs V6 header `IV6-F823AA06`.
- Quote observe opened a **different** workspace (`IV6-734601c4-…`).
- Pipeline “Gata pt. Ofertă: 0” vs V6 showing 725,25 EUR and confirm 2/3.
- Browser back not proven (UNKNOWN).

## 4. Where technical internals leak

12 `TECHNICAL_MODEL_LEAK_TO_UI` rows. Highest: Produse in the commercial FLUX; dual order flux strips; IR/IV6 dual identity; “25 linii” / internal mappings on the first V6 fold; two client stores.

Bevel lesson applies: commercial service grain ≠ execution/catalog grain. Produse in Lucrări is the same class of leak.

## 5. Where information duplicates

- Cereri list vs Client → Cereri tab.
- CommercialFlowStrip on intake and orders.
- Master-detail cards on Cereri / Oferte / Comenzi.
- Money shown as EUR (V6/quotes) and RON (orders/clients).
- V4 filenames still wrapping V6 runtime.

## 6. Where UI is too dense

Cereri first fold: pipeline + 10-row list + detail + delivery radios. V6 Configurare: finish anatomy + OFERTĂ CLIENT rail + warnings on one fold. Orders: two flux strips before the list.

## 7. Where page purpose is unclear

Clients look like a CRM hub but 18/19 cards lack fiscal identity and the page sits outside Lucrări. Orders “Înghețat” is snapshot-true and operator-opaque. V6 header identity is not the list identity.

## 8. Where ownership is contradictory

Workspace identity (IR vs IV6). Client registry (1 entity vs 19 cards). Readiness (list chip vs confirm checklist). Money projection (EUR vs RON). See C1–C6.

## 9. Where navigation does not match ownership

FLUX inserts Product System between Cereri and Oferte. Actual edit goes to V6. Clients are not in the Lucrări strip. Quote client name is text, not a `/clients` edge. Empty order detail “Vezi produse” is a Product System door (not traversed).

## 10. Light/dark systemic patterns

Admin light+dark on all Wave 2 primaries. Sales light on intake+V6. Systemic: incomplete day-mode shell (Wave 1, still true). V6 money rail and disabled handoff remain readable in both. Hover/focus not isolated.

## 11. Hardcoded UI repeat patterns

V6 parallel `v6` token world. Clients zero design-system imports. Repeated master-detail + flux strip. Shared_OK on Cereri badges/PageShell only.

## 12. Legacy/dead candidates

One REMOVE_CANDIDATE_ONLY: FE `/intake-v4` residue. V4 filename shims = COMPAT. `IntakeDetail.tsx` = LEGACY unrouted. Client stub tabs = HIDDEN. Bootstrap `/intake-v6/operator` = ACTIVE/dangerous (not opened). No deletions.

## 13. Simplification opportunities

See `WAVE_2_SIMPLIFICATION_CANDIDATES.md`. Constraint-rich: do not locally “fix” currency, identity, or V4 shims. IA honesty (demote Produse from FLUX) is the highest-leverage candidate and still blocked by Product System freeze.

## 14. Dependencies that prevent local cleanup

Product System freeze; CPP money authority; dual client stores; snapshot lock semantics; V6/V4 filename compat; Owner `dev.db` must not be mutated to complete a blocked handoff.

## 15. Findings that require later system-level audit

- Identity scheme (IR vs IV6 vs quote UUID).
- Currency projection policy.
- Client entity vs activity-merge.
- Commercial FLUX vs actual work path (includes Product System).
- Nested V6 scrollers / unnamed inner panes.
- Role coverage for sales on orders/clients.

## STATE_NOT_REACHED (mutating only)

See `WAVE_2_STATE_NOT_REACHED_FINAL.md`. **11** entries, all with explicit blockers. Straturi, Panou, sales orders/clients, stubs, back-nav, and hover/focus are no longer SNR.

## Explicit non-claims

- No page FINAL.
- No Wave 3.
- No product/pricing/schema/unfreeze.
- Product System not audited.
- `/intake-v6/operator` bootstrap not opened.

## Stop

`NEXT_TASK = NOT_AUTHORIZED`.
`COMMIT = NO`. `PUSH = NO`.
Evidence under `docs/qa/workos-unification-and-simplification-program-v1/` is currently **uncommitted**.
