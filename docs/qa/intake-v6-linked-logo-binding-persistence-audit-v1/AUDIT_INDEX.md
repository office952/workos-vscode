# Intake V6 Linked Logo Binding Persistence Audit V1 — Index

| Field | Value |
|-------|-------|
| Task | `INTAKE_V6_LINKED_LOGO_BINDING_PERSISTENCE_AUDIT_V1` |
| Verdict | **BINDING_NOT_PERSISTED** (with **PARALLEL_BINDING_TRUTH**) |
| Accepted HEAD | `10a17fd` |
| Fixture | `22ef834d-f2d0-453b-a7a7-118928c98a39` / IV6-189D2F12 |
| Template | `TPL-VOLUMETRIC-LETTERS_v2` + linked `TPL-VOLUMETRIC-LOGO_v1` (contract) |

## Primary answer

**Where binding should be saved:** `payload.layer_role_setup.layer_bindings[]` (`target_template_code`, `binding_status`, per logo segment).

**Where it is saved now:** Partially in derived `product_composition_recommendation` (suggested, not confirmed); **not** in `layer_bindings` (count **0** on fixture).

**Where it is lost:** Canonical save paths (`save_layer_roles`, `save_analysis_bundle`) never write `layer_bindings`. Segment extractor and ProductDefinition read empty bindings → `binding_status: missing`.

## Runtime captures (read-only)

| Artifact | Endpoint |
|----------|----------|
| `captures/workspace_binding_summary.json` | GET workspace (sanitized summary) |
| `captures/linked_segments_summary.json` | GET linked-template-segments |
| `captures/endpoint_index.json` | All GET metadata |
| `captures/*.json` | Full sanitized responses |

Regenerate:

```powershell
cd backend
.\.venv\Scripts\python.exe ..\docs\qa\intake-v6-linked-logo-binding-persistence-audit-v1\read_only_audit_capture.py
```

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_product_definition_gradi_composition.py tests/test_intake_v6_assembly_preview.py tests/test_intake_v6_product_composition_recommendation.py tests/test_selected_layer_refs_derivation.py tests/test_product_truth_promotion_planner_service.py tests/test_intake_v4_material_breakdown.py -q -k "logo or linked or gradi or vector_logo or letters_plus"
```

**Result:** 20 passed, 2 failed (pre-existing: `test_logo_modular_form_contract_exists_as_preview_supported`, `test_raw_vector_total_includes_unclassified_logo_perimeter`), exit 1.

## Worklog

`docs/worklog/realignment/2026-07-10_intake_v6_linked_logo_binding_persistence_audit_v1.md`
