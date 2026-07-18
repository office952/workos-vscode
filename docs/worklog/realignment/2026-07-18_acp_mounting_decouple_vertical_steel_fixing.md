# Worklog — ACP decouple from commercial mounting + vertical steel fixing

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_DECOUPLE_ACP_FROM_COMMERCIAL_MOUNTING_AND_ADD_VERTICAL_STEEL_FIXING_SYSTEM` |
| Baseline HEAD | `4a63d85` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Workspace | `f07058e2-3b40-4935-b55a-6a10b457241b` |

## Verdict

`ACP_PRODUCT_CONFIGURATION_DECOUPLED_FIXING_SYSTEM_GUARDED`

Guarded (not COMPLETE) because: live BE process on `:8001` served stale OpenAPI without `mounting_fixing_system` until restart; FE autosave through that process could not round-trip the field. Local schema/domain/PD builder + UI HMR validated.

## Root cause (mounting dependency)

| Layer | Old condition | Effect |
|-------|---------------|--------|
| FE | `disabled={!mountingPrepActive}` on ACM fields; opacity when scope=`none` | ACP looked like prep solution |
| FE/BE | `isMountingSolutionCompositionActive` required prep for all solutions | ACM inactive when scope none |
| Labels | „Soluție de pregătire” for ACM | Product mislabeled as prep |

## Fix

- ACP composition active independent of commercial `mounting_scope`
- Metal Premount still prep-gated
- Sections: Configurație Panou ACP / Pregătire și montaj / Sistem de prindere
- Contract `FIXING-SYSTEM-VERTICAL-STEEL-BRACKET` + `PROFILE-SHS-20X20X1_5` (not for ACP internal frame)
- Manual dimensions for cornier + bottom bar: `MANUAL_CONFIRMATION_REQUIRED`, `length_mm: null`
- Fastener 4.5×60 hex self-drill
- PD: `mounting_configuration` separates commercial scope vs fixing; aggregate projection quantity GUARDED/manual
- Internal frame profile gate remains `PROFILE_INITIAL_SET_OWNER_GATE_REQUIRED`

## Explicit owner rule

Dimensiunile cornierului superior și barei inferioare sunt manual-confirmed per lucrare.  
Nu există default sau formulă automată.

## Runtime evidence

- UI Step 2 Montaj: scope `Fără pregătire/montaj`, ACP fields enabled, metal premount option disabled, fixing section shows Brat otel vertical + 20×20×1.5 + manual dims + 4.5×60
- Local PD preview: `acp_panel_active=true`, scope `none`, fixing present, top/bottom lengths null
- Live OpenAPI at validation time: missing `mounting_fixing_system` → restart BE required for FE save round-trip

## Tests

- Backend: `test_mounting_fixing_system_v1.py`, `test_acp_internal_frame_domain_v1.py`
- Frontend: `mountingSolution.test.ts`, `mountingFixingSystem.test.ts`, `acpInternalFrame.test.ts`

## Out of scope

CPP · tasking · Execution · schema/migration/seed · pricing · Employee Mobile
