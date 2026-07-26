# AcmPanel Naming / Ownership / Assembly / Inventory Binding V1 — worklog

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Build | `WORKOS_ACM_PANEL_NAMING_OWNERSHIP_ASSEMBLY_AND_INVENTORY_BINDING_V1` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Feature commit | `f2adf6b` |
| Mode | Slice A+B combined — no Pricing formulas, no Offer/Exec, no task_rules |
| Fixture | `IV6-DB2F86B7` / `a7b0162b-dc91-467f-aa24-c1279fb3a073` |

## Locked decisions applied

1. Explicit `assembly_width_mm` / `assembly_height_mm` (never overload `panel_*`).
2. ACM-root PD cross-template read only when workspace has real AcmPanel; provenance `linked_workspace_template_code` + `read_mode=cross_template_acm_parity`.
3. Inject/verify assembly keys; commercial area still on `panel_*` (Slice C).
4. Preferred SKU `MAT-ACM-BOND-3MM`; `MAT-ACP-3MM` legacy alias.
5. No seed `task_rules` / MIXED DAG / Pricing Preview / Offer / Execution changes.
6. FE/BE tolerance **1 mm**; fixture assembly **2000×350**, envelope **1000×350**.

## Files

| Area | Path |
|------|------|
| FE extent | `frontend/src/lib/intakeV6/acmPanel/assemblyExtent.ts` |
| FE blueprint | `frontend/src/lib/intakeV6/acmPanel/blueprintReadModel.ts` |
| BE extent | `backend/services/acm_assembly_extent.py` |
| BE PD projection | `backend/services/acm_panel_pd_projection.py` |
| BE PD builder | `backend/services/product_definition_builder_service.py` |
| BE quote merge | `backend/services/acm_quote_input_helpers.py` |
| Naming | `backend/seeds/material_canonical_naming.py`, FE catalog, architecture doc |

## Commands

```powershell
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_acm_assembly_extent.py tests/test_acm_panel_pd_proposal_observability_v1.py tests/test_acm_panel_pd_cross_template_parity_v1.py -q
cd frontend; npx pnpm@8.10.0 exec vitest run src/lib/intakeV6/acmPanel/assemblyExtent.test.ts src/lib/intakeV6/acmPanel/blueprintReadModel.test.ts
python docs/audits/_evidence/2026-07-20_acm-panel-naming-assembly-binding/proof_pd_assembly.py
node docs/audits/_evidence/2026-07-20_acm-panel-naming-assembly-binding/capture-ui.mjs
```

## Proof

- PD Letters + ACM-root: assembly 2000×350; ACM provenance cross-template — `pd-assembly-proof.json` **ok: true**
- UI Blueprint L1-P: `data-assembly-width=2000` / height 350 — `ui-proof.json` **ok: true**
- Screenshots: `docs/audits/_evidence/2026-07-20_acm-panel-naming-assembly-binding/shots/`

## Slice C blockers (documented, not fixed)

- `derive_acm_casetted_quote_input` / CPP still commercial-area on `panel_width_mm` / `panel_height_mm`.
- ACM-root merge can still surface `panel_width_mm=1000` (envelope) alongside `assembly_*=2000`.
- Any consumer treating contour envelope as multi-panel overall must switch to `assembly_*` before pricing preview.
