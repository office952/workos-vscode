# BUILD: Intake V3 Operator Workspace — Phase 2 ColorRegistry + V2 Finish UX

**Date:** 2026-06-19  
**Build:** `BUILD_INTAKE_V3_OPERATOR_WORKSPACE_PHASE2`  
**Status:** PASS (frontend-only)

---

## 1. Verdict

**PASS** — Operator Finishes tab now uses ColorRegistry-backed operator cards with V2-style face/return/backing UX on existing `finish_assignment.*` patch paths. No backend/schema/pricing coupling.

---

## 2. Branch / HEAD

| Field | Before | After |
|-------|--------|-------|
| Branch | `local/integration-pr4-plus-svg-path` | same |
| HEAD | `ce51589456e3c81fc3444d3d72454b26b393ab6c` | _(updated at commit)_ |

---

## 3. Git status

**Before:** tracked tree clean (`ce51589`); untracked `tmp/`  
**After:** Phase 2 frontend + QA doc committed; `tmp/` remains untracked

---

## 4. Files changed

| Area | Files |
|------|-------|
| Finish form state + patches | `frontend/src/lib/intakeV3/operatorGlobalFinishForm.ts` (new) |
| Operator finish cards | `frontend/src/components/workos/intake-v3/operator-workspace/IntakeV3OperatorGlobalFinishSetup.tsx` (new) |
| Finishes tab | `frontend/src/components/workos/intake-v3/operator-workspace/IntakeV3OperatorFinishesTab.tsx` |
| Readiness repair jumps | `frontend/src/components/workos/intake-v3/operator-workspace/IntakeV3OperatorReadinessTab.tsx` |
| Tests | `IntakeV3OperatorWorkspaceApp.test.tsx`, `operatorGlobalFinishForm.test.ts` (new) |
| QA | this document |

---

## 5. Implemented (Phase 2 scope)

1. **ColorRegistry in Finishes** — `ColorRegistrySelect` for Oracal 8500/651 face vinyl, Oracal 651 return/cant, RAL return paint; swatch + code/name on selection.
2. **Face vinyl controls** — enabled toggle, finish type, roll width, operator confirm checkbox.
3. **Return / cant controls** — finish type options (wrapped, 651, prefinished, RAL paint, raw, vinyl, none), depth selector (`ALLOWED_RETURN_DEPTH_MM`), “Same color as face”, global fallback notice (Phase 3 for dedicated layer).
4. **Backing card** — material, thickness, color, confirm checkbox.
5. **Operator-facing cards** — replaced primary legacy field editor with `IntakeV3OperatorGlobalFinishSetup`; group/letter overrides remain in collapsed Advanced `<details>`.
6. **Readiness repair jumps** — finish/color/backing/return blockers map to Finishes tab with explicit repair buttons.
7. **Phase boundaries** — Phase 3 native layer finish notice; Phase 4 printed artwork notice; explicit no-CostEngine/no-pricing copy.

---

## 6. Intentionally deferred

- Native `layer_finish_assignments[]` (Phase 3)
- Backend schema / migrations for layer finish
- Policromie / printed artwork backend (Phase 4)
- LED/PSU planning (Phase 5)
- Inventory mutations, ExecutionTask/Plan, PO
- CostEngine / automatic pricing from ColorRegistry

---

## 7. Tests run

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/pages/IntakeV3OperatorWorkspaceApp.test.tsx src/lib/intakeV3/operatorGlobalFinishForm.test.ts src/lib/colorRegistry/colorRegistry.test.ts src/components/workos/colorRegistry/ColorRegistrySelect.test.tsx
```

**Result:** 36/36 PASS

New coverage:
- ColorRegistry renders on Finishes tab (Oracal face + return)
- RAL selector + approx note when return finish is painted
- Phase 3 notice + no-pricing boundary copy
- Readiness repair navigates to Finishes for finish blockers
- Patch paths limited to `finish_assignment.*`
- Advanced group/letter overrides remain collapsed

---

## 8. Boundary confirmations

| Rule | Status |
|------|--------|
| No backend/schema changes | ✓ |
| No CostEngine / pricing coupling | ✓ |
| No inventory mutation | ✓ |
| No ExecutionTask / PO | ✓ |
| Guarded quote unchanged | ✓ |
| Materials tab read-only | ✓ |
| Technical route preserved | ✓ |
| Fail-closed validation on save | ✓ |

---

## 9. Safe to continue to Phase 3?

**Yes**, pending owner confirmation. Phase 3 requires backend `layer_finish_assignments[]` contract — separate build boundary.

---

## 10. Commit

```
feat(intake-v3): add color registry finish ux to operator workspace
```

No push.
