# FACE Component Truth Workshop v1 — Worklog

**Date:** 2026-07-09  
**Task:** FACE_COMPONENT_TRUTH_WORKSHOP_V1  
**Mode:** READONLY PRODUCT SYSTEM WORKSHOP / CONTRACT ONLY

---

## HEAD before

`a83706a` — Add canonical finish enum readonly map

---

## Owner decision source

- `docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md`
- `docs/architecture/product-system/CANONICAL_FINISH_ENUM_MAP_v1.md`
- `frontend/src/features/product-system/canonicalFinishEnumMap.ts`

---

## Files created / changed

| File | Action |
|------|--------|
| `frontend/src/features/product-system/componentFirstFaceTruthWorkshop.ts` | Created — readonly FACE contract |
| `frontend/src/features/product-system/FaceTruthWorkshopPanel.tsx` | Created — readonly UI panel |
| `frontend/src/features/product-system/componentFirstFaceTruthWorkshop.test.ts` | Created — unit tests |
| `frontend/src/features/product-system/ComponentFirstReadonlyCandidatePanel.tsx` | Updated — panel in guards/audit |
| `frontend/src/pages/ProductSystem.badges.test.tsx` | Updated — FACE panel assertions |
| `frontend/e2e/product-system-readonly-smoke.spec.ts` | Updated — FACE workshop smoke |
| `docs/worklog/owner-input/face_component_truth_owner_inputs_pending.md` | Created — owner questions |
| `docs/qa/face-component-truth-workshop-v1/screenshots/*` | Created — Playwright screenshots |

---

## Source audit summary

| Source | Finding |
|--------|---------|
| `intakeV6LayerRoleOptions.ts` | `INTAKE_V6_OWNER_ROLE_LABEL_LETTERS = "Vector Litere"` — owner_confirmed for source layer role |
| `componentFirstReadonlyProductTruthMapping.ts` | FACE paths: `face.material`, `face.thickness`, `face.cutting_method` — mapping only, no write |
| `componentFirstLettersProductTruthWorkshop.ts` | FACE skeleton with plexiglas 3/5/10 mm question — evidence_only |
| `ProductSystem.tsx` ownership audit | `TPL-VOLUMETRIC-FACE_v1`, `debitare_fata`, face area/perimeter form fields — legacy evidence |
| `returnCant owner inputs` | Perimeter from real contour — partial_confirmed upstream for RETURN-CANT |
| `canonicalFinishEnumMap.ts` | FINISH face entries blocked; mp_face_area quantity basis |
| Pricing / inventory | No FACE-specific MAT-* keys confirmed — marked owner_input_required |

---

## FACE ownership rules encoded

**FACE owns:** substrate, material family, thickness, cut geometry, mp_face_area, perimeter, Vector Litere layer role.

**FACE does not own:** vinyl/print/laminate (FINISH), cant finish (RETURN-CANT), pricing rates, commercial minimums, runtime execution.

**Downstream:** mp_face_area → FINISH; perimeter → RETURN-CANT; geometry ref → BACK/LED (future).

---

## Blockers

- Material family options — owner confirmation required
- Thickness per material — owner confirmation required
- Area basis (vector vs bounding) — owner decision pending
- Geometry handoff Intake V6 → FACE truth — not wired
- FACE pricing keys — not activated
- Product Truth live write — blocked
- ProductDefinition bridge — blocked
- FINISH workshop — blocked until FACE boundary stable

---

## Forbidden scope

No runtime bridge, no Product Truth write, no Pricing activation, no ProductDefinition bridge, no FINISH workshop, no RETURN-CANT changes, no backend/DB, no invented prices/material keys, no Save/Apply/Activate UI.

---

## Tests

```powershell
cd frontend
npm.cmd run test -- src/features/product-system/componentFirstFaceTruthWorkshop.test.ts src/features/product-system/canonicalFinishEnumMap.test.ts src/pages/ProductSystem.badges.test.tsx
npm.cmd run test -- src/features/product-system/componentFirstReturnCantCatalogPriceInputs.test.tsx src/features/product-system/componentFirstReturnCantOwnerInputs.test.ts
npm.cmd run test:e2e:product-system-readonly-smoke
```

---

## UI

**Touched:** yes — readonly FACE workshop panel in component-first guards/audit tab.

---

## Next step recommendation

**A. Owner answers for FACE materials/thickness/process** — primary blocker before FINISH workshop or inventory cross-reference.

Alternative: **B. FACE source/inventory cross-reference audit** after owner confirms material families.

Do **not** start FINISH workshop until FACE boundary has owner-confirmed material/thickness/geometry rules.
