# Worklog — RETURN-CANT Commercial Depth / Finish Matrix Integrity V1

**Date:** 2026-08-11  
**GO:** `AUTHORIZE_WORKOS_INTAKE_V6_RETURN_CANT_COMMERCIAL_DEPTH_FINISH_MATRIX_INTEGRITY_V1`  
**Continuation:** RETURN-CANT Oracal labor authority closure  
**Baseline remote:** `2d495b60`

## Commits (local only — PUSH = NO)

1. `fa3437a8` — depth fidelity / RAL / mixed groups  
2. *(second commit)* — Oracal labor → `RETURN_CANT_VINYL_APPLICATION_LABOR` @ 1 EUR/ml

## Verdict

**PASS** — owner-confirmed Oracal labor rule satisfied; depth/finish matrix intact; face F7F 3 EUR/m² untouched; registry values unchanged; GET-diet intact.

## Fixes

### Commit 1 (`fa3437a8`)
- Bridge/restore `return_depth_mm` (+ return finish) into quote_input / dry-run enrich  
- CPP per-group Oracal wrap area and RAL tier aggregation  
- Focused 12-case + mixed-group tests  

### Commit 2 (labor authority)
- Audit: F7F 3 EUR/m² is face/generic; dedicated key already existed  
- `finisaje_cant_oracal_labor` → `basis_type=ml`, registry `RETURN_CANT_VINYL_APPLICATION_LABOR`  
- CPP labor qty = real return perimeter (depth-independent)  
- Material remains perimeter × depth m²  
- Evidence: `RETURN_CANT_ORACAL_LABOR_AUTHORITY_TRACE.md`, `ORACAL_DEPTH_LABOR_MATRIX.md`

## Next

Not authorized. PUSH = NO until Owner GO.
