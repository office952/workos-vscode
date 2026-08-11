# ROOT_CAUSE_MAP

Max 7 shared roots — not one fix per field.

## 1. PRODUCT_TRUTH_TO_CPP_MAPPING (P0)

**Face Oracal token collapse** in quote_input adapter:
- Operator/persisted: `oracal_641`
- quote_input: `face_finish_type=vinyl`
- handoff: `face_finish_type=oracal_651` with raw `oracal_641`
- CPP gates: `finish_setup.face_finish_type == oracal_641`
- Result: **no face Oracal commercial lines** while UI shows Oracal 641

Systems: `intake_v4_pricing_input_service.py`, CPP material gates, dry-run.

## 2. FRONTEND_ORCHESTRATION_OVERLOAD (P1)

ReviewStep eager ~17 GETs; finish dirty refreshes production/diagnostic groups; debounce 700–1400 ms.
Operator feels “price updates very slowly” even when CPP is ~50 ms.

Systems: `IntakeV6ReviewStep.tsx`, `intakeV6ReviewRefetchDomains.ts`.

## 3. PRICING_RULE_NOT_CONSUMED (P1)

Back Forex șanfren + stock cant depth: Product Truth / MB know the choice; CPP sell lines ignore bevel / depth on stock.
Looks like “selection does nothing”.

Systems: `commercial_rules_volumetric_v2.py`, CPP `_rule_applies` / qty paths.

## 4. UI_TECHNICAL_LEAKAGE + VOCABULARY (P2)

“Fără finisaj — plexiglas brut”, cant “Oracal 651 · 60 mm”, SVG technical ids, primary technical accordion, “Tarife lipsă” beside Ofertă gross.

## 5. PARALLEL_READ_MODEL_DRIFT (P1/P2)

Logical list vs material breakdown; ACM provisional vs official Ofertă; checklist “finisaje confirmate” vs `letter_group.confirmed=false`.

## 6. STATE_INVALIDATION (P1)

Confirm clears dry-run on refetch (honesty) → blank/stale flash; autosave→refetch races possible.

## 7. INTENTIONAL_CATALOG_GAPS (document, not always defect)

Stock cant color ZERO_DELTA; PSU sold as 1 unit; color codes not rate-tiered — must be explained in UI or priced.

---

**PRIMARY_ROOT_CAUSE:** #1 Face token collapse (wrong/missing money)  
**SECONDARY:** #2 orchestration lag · #3 CPP non-consumption · #4 vocabulary/leakage
