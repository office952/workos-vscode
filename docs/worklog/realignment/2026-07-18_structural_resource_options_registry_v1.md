# Worklog — Structural Resource Options Registry V1 + ACP Frame (guarded)

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_STRUCTURAL_RESOURCE_OPTIONS_REGISTRY_V1_AND_ACP_INTERNAL_FRAME_E2E` |
| **Verdict** | **`PROFILE_INITIAL_SET_OWNER_GATE_REQUIRED`** |
| HEAD docs commit | `32a3534` (owner rules) |
| App | Registry + domain + Step 2 guarded UI + PD nested + lifecycle warning |

## Owner-confirmed (implemented)

- Materials `MAT-STRUCT-STEEL` / `MAT-STRUCT-ALUMINIUM`
- Frame formula: panel − 2×thickness − 2 mm; fold-independent; example 2000×700×3 → 1992×692
- Crossbar spacing steel 1000 / aluminium 750; suggestion + confirm
- No global XOR frame↔premount
- Clearance min/max **NOT_APPLICABLE**; removed hidden 5 mm authority

## Deferred / gated

- **No owner-confirmed ACP profile sections** → `accepted_profile_codes=[]`
- Step 2 cannot reach `CONFIRMED`
- Aggregate quantity **GUARDED**
- CPP / tasking / Execution untouched
- Screenshots / full E2E workspace confirmation blocked by empty profiles

## Delivered

| Area | Path |
|------|------|
| Registry | `backend/data/product_system/structural_resource_options_v1.py` |
| API | `GET /api/v1/product-system/resource-options*` |
| Domain | `backend/services/acp_internal_frame_domain.py` |
| Mounting normalize | nested `internal_frame` |
| PD | nested `internal_frame` in canonical_values |
| Lifecycle | `PROFILE_INITIAL_SET_OWNER_GATE_REQUIRED` warning |
| FE | Step 2 section + `acpInternalFrame.ts` |
| Tests | `test_acp_internal_frame_domain_v1.py`, `acpInternalFrame.test.ts` |

## Next safe step

**Option 2 — STOP FOR INITIAL PROFILE OWNER CONFIRMATION**  
Owner must approve ≥1 real shop profile (e.g. SHS WxHxT) before E2E COMPLETE.

## Roadmap

Score 7/10 · Alignment 85/100%  
Stops at technical registry + guarded frame config (no CPP).

## STOP
