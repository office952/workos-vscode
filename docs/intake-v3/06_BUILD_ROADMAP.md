# Intake V3 — Build Roadmap

---

## Done

| # | Build | Status |
|---|-------|--------|
| 1 | `INTAKE_V3_ARCHITECTURE_CONTRACTS` | ✅ `959d53c` |
| 2 | Task logic doc (no shared support) | ✅ `51365a8` |
| 3 | `INTAKE_V3_MD_DOSSIER_AND_TEMPLATE_OPERATION_MODEL` | ✅ `d78bc4d` |
| 4 | `INTAKE_V3_VECTOR_AND_LETTER_MODEL` | ✅ `57dac0e` |
| 5 | `INTAKE_V3_FINISH_AND_MATERIAL_WORKFLOW` | ✅ `6c6e72c` |
| 6 | `INTAKE_V3_PRICING_INPUT_ADAPTER` | ✅ local |
| 7 | `INTAKE_V3_PRODUCTION_HANDOFF_ADAPTER` | ✅ local |
| 8 | `AUDIT/FIX — Volumetric execution task order` | ✅ `225e054` |
| 9 | `INTAKE_V3_END_TO_END_INTEGRATION_AND_UI_SHELL_FOUNDATION` | ✅ `e6c3361` |
| 10 | `INTAKE_V3_READ_ONLY_BACKEND_PREVIEW_ENDPOINT_AND_UI_SCENARIO_SWITCHER` | ✅ `fa580de` |
| 11 | `INTAKE_V3_WORKSPACE_PERSISTENCE_FOUNDATION` | ✅ `ed36e9f` |
| 12 | `INTAKE_V3_CONTROLLED_FIELD_EDITOR_FOUNDATION` | ✅ `c131545` |
| 13 | `INTAKE_V3_EDITOR_FLOW_HARDENING_AND_OPERATIONAL_UX_POLISH` | ✅ `f776eaf` |
| 14 | `INTAKE_V3_SVG_UPLOAD_AND_RAW_ANALYSIS_FOUNDATION` | ✅ `e4b9766` |
| 15 | `INTAKE_V3_CONFIRMED_PRODUCTION_MODEL_REVIEW_FOUNDATION` | ✅ `a1a07f1` |
| 16 | `INTAKE_V3_FINISH_ASSIGNMENT_PER_LETTER_GROUP_FOUNDATION` | ✅ `e431173` |
| 17 | `INTAKE_V3_FINISH_VARIATION_MATERIAL_AND_PRICING_PREVIEW_SUMMARY` | ✅ `81468dc` |
| 18 | `INTAKE_V3_QUOTE_READINESS_GATE_AND_PREQUOTE_REVIEW_FOUNDATION` | ✅ `0b1fc07` |
| 19 | `INTAKE_V3_GEOMETRY_PATH_PERIMETER_CLASSIFICATION` | ✅ `9787398` |
| 20 | `INTAKE_V3_OPERATOR_LAYER_ROLE_CONFIRMATION` | ✅ local |

---

## Recommended sequence

| # | Build | Intră | Nu intră |
|---|-------|-------|----------|
| 20 | `INTAKE_V3_QUOTE_CREATION_GUARD_POLICY` | disabled-by-default policy + UI lock | Real quote enablement |
| 21 | `INTAKE_V3_COMMERCIAL_QUOTE_BRIDGE` | ✅ mapping preview disabled-by-policy | CostEngine / real quote |
| 22 | `INTAKE_V3_OWNER_APPROVED_QUOTE_CREATION_ENABLEMENT` | ✅ enablement policy + final blocker check | Real quote creation |
| 23 | `INTAKE_V3_REAL_QUOTE_CREATION` (future) | owner-approved wire from bridge | CostEngine / real quote |
| 24 | `REAL_QUOTE_CREATION_OWNER_DECISION_RECORD_AND_SNAPSHOT_POLICY` | ✅ owner decision + snapshot + anti-duplicate + recovery contracts | Real quote creation |
| 25 | `INTAKE_V3_REAL_COMMERCIAL_QUOTE_CREATION_GUARDED_DRAFT_FOUNDATION` | ✅ guarded POST creates draft Quote in notes/IV3 linkage | Pricing / order conversion |
| 26 | `INTAKE_V3_DRAFT_QUOTE_REVIEW_AND_PRICING_HANDOFF_ALIGNMENT` | ✅ `9c6849a` read-only review + handoff checklist | Explicit pricing review |
| 27 | `INTAKE_V3_PRICING_REVIEW_COMPLETION_AND_DRAFT_QUOTE_PRICING_FINALIZATION` | ✅ `2e3e705` manual priced draft completion | Accept/convert guards |
| 28 | `INTAKE_V3_PRICED_DRAFT_ACCEPT_CONVERT_READINESS_AUDIT_AND_GUARD` | ✅ `8cd2b86` read-only accept/convert readiness | Guarded accept only |
| 29 | `INTAKE_V3_GUARDED_ACCEPT_FLOW` | ✅ `934b8fc` guarded accept POST (draft→priced→accepted) | Guarded convert |
| 30 | `INTAKE_V3_GUARDED_CONVERT_TO_ORDER` | ✅ `2336bbd` guarded convert POST (accepted→Order locked) | Production readiness audit |
| 31 | `INTAKE_V3_ORDER_HANDOFF_AND_PRODUCTION_READINESS_AUDIT` | ✅ `26d4296` read-only production readiness GET | Task generation dry-run or material breakdown |
| 32 | `INTAKE_V3_MATERIAL_QUANTITY_GEOMETRY_AND_MATERIAL_COST_BREAKDOWN_INFORMATIVE` | ✅ `1d326c0` materials-only breakdown GET + UI panel | Task generation dry-run |
| 33 | `INTAKE_V3_PRODUCTION_TASK_GENERATION_DRY_RUN_CONTRACT` | ✅ local preview-only candidate tasks GET | Geometry metrics snapshot |
| 34 | `INTAKE_V3_GEOMETRY_METRICS_SNAPSHOT_FROM_SVG_PATHS` | ✅ `4751c88` geometry snapshot persist + GET | Path perimeter classification |
| 35 | `INTAKE_V3_GEOMETRY_PATH_PERIMETER_CLASSIFICATION` | ✅ `9787398` role-based perimeter classification + GET | Layer role propagation audit |
| 36 | `INTAKE_V3_LAYER_ROLE_CONFIRMATION_QUOTE_PROPAGATION_AUDIT` | ✅ `222ef9d` stale detection + propagation GET + guarded refresh | Material availability check |
| 37 | `INTAKE_V3_MATERIAL_AVAILABILITY_READ_ONLY_CHECK` | ✅ `707030a` read-only inventory preview GET + UI panel | Procurement preview |
| 38 | `INTAKE_V3_PROCUREMENT_PREVIEW_FROM_MATERIAL_AVAILABILITY` | ✅ `7f9c93c` read-only procurement recommendations GET + UI panel | Production preview consolidation |
| 39 | `INTAKE_V3_PRODUCTION_PREVIEW_CONSOLIDATION_UI` | ✅ local grouped Production Preview panel + flow metadata | Backend summary endpoint |
| 22 | Granular pricing per finish group | quantities, labor splits | Inventory as price source |
| 21 | Visual SVG letter selection | click-to-select assignments | — |
| 22 | `PRODUCTSYSTEM_TEMPLATE_OPERATION_CATALOG` (optional) | first-class registry | Employee Mobile |

---

## Dependency graph (simplified)

```text
Contracts (done)
  → MD Dossier (done)
    → Vector/Letter Model
    → Finish/Material Workflow
      → Pricing Adapter
      → Production Handoff Adapter
        → Execution AUDIT/FIX (parallel possible)
          → UI Shell
```

---

## Owner fork

Dacă Operation Catalog devine entitate ProductSystem **înainte** de vector build, ordinea 4 și 9 se inversează parțial — vezi [07_DECISIONS_LOG.md](./07_DECISIONS_LOG.md).
