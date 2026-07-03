# BUILD QA — Intake Persistence & Handoff Coherence

**Date:** 2026-06-07  
**Branch:** `master`  
**Base HEAD:** `c952293`  
**Verdict:** **PASS**

---

## Scope

Runtime build wiring Work Intake persistence and quote handoff. No pricing, CostEngine, or commercial readiness policy changes.

---

## Pre-flight

| Check | Result |
|-------|--------|
| Required commits present | c952293, a6c1480, 8292871, 98bda64, 012408a |
| Backend health | `GET /health` → healthy |
| Frontend | `:3000` up |
| Counts before | intakes=11, quotes=7, orders=8 |

---

## Tests

| Suite | Result |
|-------|--------|
| `intakeReadiness.test.ts` | 4 passed |
| `intakeSiteAudit.test.ts` | 3 passed |
| `volumetricQuoteFlowState.test.ts` | 15 passed |
| `QuoteWizard.volumetricRouting.test.tsx` | 4 passed |
| `test_intake_persistence_handoff.py` (unittest) | 4 passed |

---

## Browser smoke — WI-SMOKE-P001

| Step | Result |
|------|--------|
| Confirm template suggestion | `confirmed_template_code=TPL-VOLUMETRIC-LETTERS` persisted |
| Template badge | "Template confirmat: TPL-VOLUMETRIC-LETTERS" |
| Assign operator | Local gate satisfied; persist on mark-ready (post-fix) |
| Mark ready | `status=ready_for_quote`; no quote/order created |
| Open preliminary quote | `VolumetricLettersQuoteFlow` on `/quotes` |
| Prefill values | 4800, 600, 60, 2.88, 18, 9 |
| Preliminary simulation | **844.41 EUR** |
| Commercial quote CTA | Disabled (blockers remain) |
| Terrain in quote workspace | Read-only "Teren: 0/3 verificări" |
| Counts after | intakes=11, quotes=7, orders=8 |

---

## Migration note

`s42_intake_persistence_handoff` adds `confirmed_template_code`, `confirmed_template_name`, `site_audit_json`. Local dev DB may require `alembic upgrade head` or manual ALTER if alembic version table is out of sync.

---

## Confirmations

- No pricing changes
- No CostEngine changes
- No quote/order created during validation
- No readiness bypass
- No fake geometry / photo-derived pricing
- Other templates unaffected (generic QuoteWizard path preserved)
