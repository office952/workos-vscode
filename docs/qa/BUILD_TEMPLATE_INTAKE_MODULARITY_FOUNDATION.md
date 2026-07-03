# BUILD: Template Intake Modularity Foundation

**Date:** 2026-06-08  
**Status:** **PASS**  
**Route:** `/intake-v2/:id`  
**Active template:** `TPL-VOLUMETRIC-LETTERS` only  
**Future (not activated):** `TPL-ACM-CASSETTED-PANEL`

---

## 1. Purpose

Minimal architectural refactor so WorkIntake V2 can support future product templates without duplicating shell, readiness, or handoff wiring. Follows audit direction **C** — extract shared contracts, no large registry, no ACM UI.

---

## 2. Context (audit)

Prior audit confirmed:

- UX shell (zones, scroll, header, save, handoff CTA) is reusable
- Product content is volumetric-specific
- `IntakeProductSpec` bloat risk for ACM/Bond
- Quote preview and readiness are template-coupled

This build introduces thin config + strategy interfaces; volumetric remains the only runtime implementation.

---

## 3. What was hardcoded before

| Area | Hardcoding |
|------|------------|
| `WorkIntakeV2Flow` | Direct imports of `VolumetricRulesCard`, `ReadinessHandoffCard` with inline volumetric logic |
| Readiness | Direct calls to `buildWorkIntakeV2RepairItems`, `isWorkIntakeV2StageComplete` |
| Quote preview | Embedded in `ReadinessHandoffCard` with volumetric finish helpers |
| Stage→zone | Global `mapStageIdToZoneId` in scroll hook |
| Header | `TPL_VOLUMETRIC_LETTERS` constant for badge/title |
| Spec seed | `applyFrontlitConstructionDefaults` inline in Flow |

---

## 4. New contracts

### `WorkIntakeTemplateConfig`

Location: `frontend/src/lib/workIntakeV2/templateConfig/types.ts`

| Field | Role |
|-------|------|
| `templateCode`, `label`, `headerTitle` | Template identity |
| `zones` | DOM zone ids (header, jobDetails, graphics, productRules, readiness) |
| `mapStageIdToZoneId` | Per-template stage routing |
| `seedSpec` | Initial spec seeding |
| `isTemplateConfirmed` | Template confirmation gate |
| `renderProductRulesCard` | Product-specific zone D |
| `renderQuotePreview` | Handoff preview slot |
| `readinessStrategy` | Repair + completion rules |

### `WorkIntakeTemplateReadinessStrategy`

| Method | Role |
|--------|------|
| `getRepairItems` | Repair panel list |
| `isStageComplete` | Per-stage gate |
| `isHandoffReady` | Verification / CTA gate |
| `getFirstBlockerLabel` | CTA blocker message |

Volumetric implementation delegates to existing `repairPanel.ts` and `stageCompletion.ts` — **rules not rewritten**.

---

## 5. Volumetric config

File: `frontend/src/lib/workIntakeV2/templateConfig/volumetricLettersTemplateConfig.tsx`

| Binding | Implementation |
|---------|----------------|
| Product rules | `WorkIntakeV2VolumetricRulesCard` |
| Quote preview | `VolumetricLettersQuotePreview` (extracted) |
| Readiness | `volumetricReadinessStrategy` |
| Stage→zone | Existing `mapStageIdToZoneId` |
| Resolver | `resolveWorkIntakeTemplateConfig()` — returns config only for `TPL-VOLUMETRIC-LETTERS` |

---

## 6. WorkIntakeV2Flow changes

- Resolves template config from `confirmedTemplateCode`
- **Unsupported template:** `work-intake-v2-unsupported-template` message (defense in depth; page gate unchanged)
- Shell unchanged: header, job details, graphics layers
- Product rules + readiness driven by config
- Scroll hook receives `mapStageIdToZoneId` from config

**Operator-visible behavior for volumetric:** unchanged.

---

## 7. Quote preview slot

- Extracted: `frontend/src/components/workos/workIntakeV2/previews/VolumetricLettersQuotePreview.tsx`
- `ReadinessHandoffCard` accepts `renderQuotePreview` + `readinessStrategy`
- `formatVolumetricFinishSummary` unchanged
- QuoteWizard untouched

---

## 8. Future template payload plan

Document: `frontend/src/lib/workIntakeV2/templateConfig/FUTURE_TEMPLATE_PAYLOAD.md`

Summary:

- Root fields remain for volumetric backward compatibility
- New products use `template_payload` or namespaced keys (e.g. `acm_cassette`)
- No DB migration in this build
- ACM stage→zone mapping documented, not activated

---

## 9. Tests

| Suite | Result |
|-------|--------|
| `templateConfig.test.tsx` | 7/7 PASS |
| `WorkIntakeV2Flow.test.tsx` | 24/24 PASS |
| `stageCompletion.test.ts` | PASS |
| `workIntakeV2.test.ts` | PASS |
| `geometrySync.test.ts` | PASS |
| `lightingPlanning.test.ts` | PASS |
| `psuAllocation.test.ts` | PASS |
| `QuoteWizard.volumetricRouting.test.tsx` | PASS |
| `volumetricFinishDisplay.test.ts` | PASS |
| `stageIdToZoneId.test.ts` | PASS |

**Total regression:** 86/86 PASS

### E2E triage (2026-06-08, post-refactor)

**Symptom:** `npm run test:e2e:workintake-finish` failed — CTA `work-intake-v2-open-quote-wizard` not enabled within 30s at initial load (before RAL/8500 color exercise).

**Root cause:** **Fixture DB / seed state (#1)** — not a template-config regression. After re-running `backend/scripts/seed_commercial_e2e_fixture.py` against the active `backend/dev.db`, the finish-display intake (`WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001`, id 33) matches `WORKINTAKE_V2_FINISH_DISPLAY_SPEC`. Node evaluation of that spec through `applyFrontlitConstructionDefaults` + `isWorkIntakeV2StageComplete("verification")` returns **all stages true**, zero repair blockers. `volumetricReadinessStrategy.isHandoffReady` delegates unchanged to existing gates.

**Ruled out:**

| Hypothesis | Evidence |
|------------|----------|
| Template config bypass / unsupported fallback | `resolveWorkIntakeTemplateConfig` resolves volumetric; E2E sees `work-intake-v2-flow` + zone headers |
| Readiness gate regression | Same `repairPanel.ts` / `stageCompletion.ts` via `volumetricReadinessStrategy`; gates not weakened |
| Missing fixture prereqs in seed definition | Spec includes geometry, PSU, return depth, `face_vinyl_enabled: false`, template confirmed |
| Timing / save slowness | E2E passes in ~4s after re-seed; CTA enabled immediately |
| Selector fragility | No selector changes required |

**Fix applied:** Re-seed only (no production, fixture, or test code changes).

**E2E re-run:**

```bash
cd backend && .venv/Scripts/python.exe scripts/seed_commercial_e2e_fixture.py
cd frontend && PW_SKIP_WEB_SERVER=1 npm run test:e2e:workintake-finish
```

| Command | Result |
|---------|--------|
| Vitest (templateConfig, WorkIntakeV2Flow, stageCompletion, QuoteWizard.volumetricRouting, volumetricFinishDisplay) | **52/52 PASS** |
| `test:e2e:workintake-finish` | **1/1 PASS** (~4s) |

**Readiness gates:** unchanged — no weakening, no CTA bypass.

**If E2E fails again:** Re-seed first; confirm `frontend/e2e/.commercial-fixture.json` → `finish_display_fixture.intake_id` matches DB; inspect `work-intake-v2-cta-blocker-reason` on failure.

---

## 10. Boundary (confirmed)

| Area | Touched? |
|------|----------|
| CostEngine | No |
| Pricing | No |
| Inventory | No |
| Backend | No |
| WorkIntake V1 | No |
| ACM UI / geometry / DXF | No |
| QuoteWizard logic | No |
| `IntakeProductSpec` schema | No new fields |

---

## 11. Risks

| Risk | Mitigation |
|------|------------|
| Config object stable reference in useEffect | `volumetricLettersTemplateConfig` is module singleton |
| ACM page gate vs Flow unsupported | Page still gates volumetric; Flow shows explicit fallback if misrouted |
| Full registry deferred | Next product adds second config file + resolver branch |

---

## 12. Next candidates

1. **TPL-ACM-CASSETTED-PANEL Intake Spec Design** — payload types + normalizer sketch
2. **ACM template config + ProductRulesCard** — second config implementation
3. **Quote flow registry entry** — wire `acmQuoteInput.ts` fields to dedicated flow

---

## Files created

- `frontend/src/lib/workIntakeV2/templateConfig/types.ts`
- `frontend/src/lib/workIntakeV2/templateConfig/volumetricReadinessStrategy.ts`
- `frontend/src/lib/workIntakeV2/templateConfig/volumetricLettersTemplateConfig.tsx`
- `frontend/src/lib/workIntakeV2/templateConfig/resolveWorkIntakeTemplateConfig.ts`
- `frontend/src/lib/workIntakeV2/templateConfig/templateConfig.test.tsx`
- `frontend/src/lib/workIntakeV2/templateConfig/FUTURE_TEMPLATE_PAYLOAD.md`
- `frontend/src/components/workos/workIntakeV2/previews/VolumetricLettersQuotePreview.tsx`
- `docs/qa/BUILD_TEMPLATE_INTAKE_MODULARITY_FOUNDATION.md`

## Files modified

- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2Flow.tsx`
- `frontend/src/components/workos/workIntakeV2/WorkIntakeV2OperationalHeader.tsx`
- `frontend/src/components/workos/workIntakeV2/cards/WorkIntakeV2ReadinessHandoffCard.tsx`
- `frontend/src/components/workos/workIntakeV2/hooks/useWorkIntakeV2ZoneScroll.ts`
