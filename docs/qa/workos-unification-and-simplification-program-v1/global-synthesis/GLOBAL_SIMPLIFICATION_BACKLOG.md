# Global simplification backlog

Deduplicated from Waves 1–5. Visual cleanup alone is not P0.

| ID | TITLE | WAVES | PROBLEM | EVIDENCE | USER | ARCH | RISK | DEPS | OWNER | OUTCOME | SIZE | PRI |
|----|-------|-------|---------|----------|------|------|------|------|-------|---------|------|-----|
| GS-01 | Remove Produse from commercial FLUX | 2,4 | Nav teaches wrong workflow | C5, W4-C7, TML-1 | High | IA | Low if label/move only | OD-1 | OD-1 | Cerere→Intake→Ofertă | S | P0 |
| GS-02 | Label V6 money as preview not offer | 2 | “OFERTĂ CLIENT” looks sold | Wave 2 rail | High | display | Low | — | — | Preview vs snapshot | S | P0 |
| GS-03 | Fix readiness chip vs V6 confirm | 2 | List says 0 ready; workspace has money | C4 | High | display | Low | — | — | One readiness story | S | P0 |
| GS-04 | Label reports as live projection | 5 | Revenue ≠ frozen snapshot | W5-C5 | Med | display | Med if ignored | OD-7 | OD-7 | No sold-money claim | S | P1 |
| GS-05 | Documents mock honesty / hide | 5 | Hub looks like DMS | W5-C4 | Med | IA | Low | OD-2 | OD-2 | Not a live module | S | P1 |
| GS-06 | Evidență HR DEMO persist | 5 | Live names + demo file | W5-C2 | Med | honesty | Low | OD-3 | OD-3 | Not HR SoT | S | P1 |
| GS-07 | IR vs IV6 primary display | 2 | Dual work ids | C1 | Med | display | Low | — | — | One primary id | S | P1 |
| GS-08 | EUR/RON projection labels | 2,3 | Same journey, two currencies | C2, W3-C6 | Med | display | Low | — | — | Labeled projections | S | P1 |
| GS-09 | Move Plăți/Avansuri to Oameni | 5 | Money split from people | Wave 5 IA | Med | IA | Low | OD-10 | OD-10 | One people group | S | P2 |
| GS-10 | Demote audit from Producție | 3,4 | Ops-Graph in everyday nav | Wave 3 AUDIT | Med | IA | Low | — | OD | Sistem group | S | P2 |
| GS-11 | Hide planned PS shells | 4 | Unwired looks like product | Wave 4 planned | Med | honesty | Low | — | — | Only live catalog | S | P1 |
| GS-12 | Freeze banner on modules/gov | 4 | Pages omit freeze | W4-C5 | Low | gov | Low | OD-8 | — | Honest reference repo | S | P1 |
| GS-13 | Stale governance products tab | 4 | Static ≠ live catalog | W4-C2 | Low | gov | Low | OD-8 | OD-8 | Mark STALE | S | P2 |
| GS-14 | Client registry vs 19 cards | 2 | Badge lies | C3 | Med | display | Low | — | OD | Clarify list | S | P1 |
| GS-15 | WC enum / English Shop Floor | 1,3 | Technical leak | Wave 1/3 | Med | leak | Low | — | — | Romanian labels | S | P2 |
| GS-16 | Unbounded /operator list | 3 | 234 tasks / 75k px | Wave 3 | High | UX model | Med | OD-6 | OD-6 | Cap/filter | M | P2 |
| GS-17 | Action-home decision | 3 | Monitor ≠ action | W3-C2 | High | architecture | High | OD-6 | OD-6 | One action story | L | P2 |
| GS-18 | Premount scope drift | 4 | FE omit vs BE offerable | W4-C4 | Low | scope | Med if activated | OD-9 | OD-9 | Document only | S | P2 |
| GS-19 | Attendance RBAC MIXED | 5 | Manager UI / 403 | W5-C1 | Med | RBAC | Med | OD-11 | OD-11 | Later people GO | M | P2 |
| GS-20 | Supplier dual entry | 5 | Two doors, one API | W5-C3 | Low | IA | Low | OD-4 | OD-4 | Keep both | S | P3 |
| GS-21 | Utilaje → MachineRun link | 5 | Catalog ≠ occupancy | W5-C7 | Low | nav | Low | — | — | “Stare execuție” | S | P3 |
| GS-22 | Light sidebar incomplete | 1 | Day-mode rail | Wave 1 | Low | visual | Low | primitives | — | Shared tokens | M | P3 |
| GS-23 | Orphan MaterialPriceRegistry | 5 | Unwired file | Wave 5 G | None | dead | Low | proof | — | Delete later | S | P3 |
| GS-24 | Quote→client dead end | 2 | No reverse edge | C6 | Low | journey | Low | — | — | Later edge | S | P3 |
| GS-25 | `/intake-v4` E2E residue | 2 | Unrouted leftover | Wave 2 legacy | None | dead | Low | prove no contract | — | Delete leftover later | S | P3 |

```text
P0_COUNT = 3
P1_COUNT = 8
P2_COUNT = 8
P3_COUNT = 6
```

## S1 implementation status (2026-08-14)

Status only. Do not treat this as a rewrite of the synthesis table.

| ID | STATUS | NOTE |
|----|--------|------|
| GS-01 | IMPLEMENTED | FLUX Cereri → Oferte → Comenzi. Sidebar Produse deferred. |
| GS-02 | IMPLEMENTED | V6 rail = Estimare curentă. Amounts unchanged by S1. |
| GS-03 | IMPLEMENTED | Display Marcat intern. Enum/API/DB unchanged. No V6 join. |

S2+ items remain open. Evidence: `../s1-runtime/S1_COMMERCIAL_TRUTH_REPORT.md`.

## S2 implementation status (2026-08-14)

Status only. Do not treat this as a rewrite of the synthesis table.

| ID | STATUS | NOTE |
|----|--------|------|
| GS-04 | IMPLEMENTED | `/reports` = Proiecție operațională. Numeric logic unchanged. |
| GS-05 | IMPLEMENTED | Documente removed from primary Relații. `/documents` kept as MOCK. |
| GS-06 | IMPLEMENTED | Evidență HR hybrid honesty. `/employees` not DEMO. |

S3+ items remain open. Evidence: `../s2-runtime/S2_MOCK_DEMO_PROJECTION_HONESTY_REPORT.md`.

## S3 implementation status (2026-08-14)

Status only. Do not treat this as a rewrite of the synthesis table.

| ID | STATUS | NOTE |
|----|--------|------|
| GS-09 | IMPLEMENTED | Plăți + Avansuri primary nav moved to Oameni. Routes/RBAC unchanged. |
| GS-10 | DEFERRED_PARTIAL | Ops-Graph stays in Producție with existing AUDIT badge. No Sistem / Audit group in S3. |

S4+ items remain open. Evidence: `../s3-runtime/S3_PEOPLE_MONEY_NAV_REPORT.md`.
