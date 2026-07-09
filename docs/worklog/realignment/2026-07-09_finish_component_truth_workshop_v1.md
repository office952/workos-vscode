# FINISH Component Truth Workshop v1 — Worklog

**Date:** 2026-07-09  
**Task:** `FINISH_COMPONENT_TRUTH_WORKSHOP_V1`  
**Mode:** READONLY COMPONENT TRUTH WORKSHOP  
**HEAD before:** `894516c`

---

## What was added

- `componentFirstFinishTruthWorkshop.ts` — readonly FINISH contract (identity, owns/does-not-own, variants, dependencies, quantity basis questions, pricing evidence, blockers)
- `FinishTruthWorkshopPanel.tsx` — readonly UI panel in Guards/Audit
- Wired after FACE workshop in `ComponentFirstReadonlyCandidatePanel.tsx`
- Tests: `componentFirstFinishTruthWorkshop.test.ts`, `ProductSystem.badges.test.tsx`
- Owner inputs pending: `finish_component_truth_owner_inputs_pending.md`

---

## Owner decisions respected

- FACE boundary stable — FINISH consumes FACE outputs (`mp_face_area`, `face_material_usage_area_m2`, `face_piece_boxes`, Vector Litere)
- FACE 3 mm `MAT-ACP-FATA-LITERE` 16 EUR/mp belongs to FACE — not FINISH
- RETURN-CANT boundary preserved — cant Stock/Oracal/RAL + 100 lei minimum not owned by FINISH
- Canonical finish enum FINISH entries represented (9 variants)
- Generic retired paths (`finish.oracal_code`, `ral_code`, `stock_color`, `type`) not reintroduced

---

## What was not changed

- No Pricing Registry write
- No Product Truth live write
- No ProductDefinition bridge
- No FACE/RETURN-CANT pricing values
- No backend/seed/migration/DB
- No Work Intake / Quote / Order / Execution

---

## Test results

See final report — targeted Vitest suite.

---

## Screenshots

`docs/qa/finish-component-truth-workshop-v1/screenshots/` — see capture script output.

---

## Remaining blockers

- Owner answers pending (variants, quantity basis, catalog refs, LOGO split)
- Pricing activation blocked
- Product Truth live write blocked
- ProductDefinition bridge blocked
- Runtime Intake V6 handoff blocked
- Pricing Registry alignment blocked

---

## Next recommendation

**`FINISH_OWNER_INPUTS_ANSWERS_WORKSHOP_V1`** — collect owner answers before any pricing/registry activation.
