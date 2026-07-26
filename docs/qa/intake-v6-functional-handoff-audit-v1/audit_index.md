# Intake V6 Functional Handoff Audit V1 — Index

**Date:** 2026-07-10  
**Task:** INTAKE_V6_FUNCTIONAL_HANDOFF_AUDIT_V1  
**Accepted HEAD:** `cba4edd`  
**Verdict:** ALIGNED_WITH_GAPS  
**Workspace:** `22ef834d-f2d0-453b-a7a7-118928c98a39`  
**Template:** `TPL-VOLUMETRIC-LETTERS_v2`  
**SVG:** `gradi-curat.svg`

## Captures (read-only GET)

| File | Method | URL |
| --- | --- | --- |
| `captures/workspace.json` | GET | `/api/v1/intake-v6/workspaces/{id}` |
| `captures/template_form_contract.json` | GET | `/api/v1/intake-v6/workspaces/{id}/template-form-contract` |
| `captures/runtime_capture.json` | GET | `/api/v1/intake-v6/workspaces/{id}/runtime-capture-read-model` |
| `captures/quote_handoff.json` | GET | `/api/v1/intake-v6/workspaces/{id}/quote-handoff-preview` |
| `captures/pricing_input.json` | GET | `/api/v1/intake-v6/workspaces/{id}/pricing-input-preview` |
| `captures/product_binding.json` | GET | `/api/v1/intake-v6/workspaces/{id}/product-system-binding` |
| `captures/linked_segments.json` | GET | `/api/v1/intake-v6/workspaces/{id}/linked-template-segments` |
| `captures/form_contract.json` | GET | `/api/v1/intake-v6/form-contract/TPL-VOLUMETRIC-LETTERS_v2` |
| `captures/product_definition.json` | GET | `/api/v1/product-system/product-definition/TPL-VOLUMETRIC-LETTERS_v2?workspace_id={id}` |
| `captures/product_aggregate.json` | GET | `/api/v1/product-system/aggregate/TPL-VOLUMETRIC-LETTERS_v2` |
| `captures/material_breakdown.json` | GET | `/api/v1/intake-v6/workspaces/{id}/material-breakdown` |

**Writes:** NONE on all calls.

## Scripts

- `scripts/extract_audit_summary.py` — summarize captures (read-only)
- `scripts/fetch_readonly_captures.ps1` — re-fetch GET captures

## Worklog

`docs/worklog/realignment/2026-07-10_intake_v6_functional_handoff_audit_v1.md`
