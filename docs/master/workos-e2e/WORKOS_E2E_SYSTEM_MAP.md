# WorkOS E2E — System Map

**Program:** `WORKOS_E2E_MASTER_ALIGNMENT_AND_FINALIZATION_V1`  
**Role:** BASELINE ownership / boundary map  
**Evidence baseline HEAD:** `fe6c6f7`  
**Living status:** `WORKOS_E2E_STATUS.md`  
**B2:** Outside Important Documents unless owner promotes.

## Connected flow (operator stages)

```
CERERE → INTAKE V6 → DEFINIRE PRODUS → PRODUCT AGGREGATE → CALCUL
    → OFERTA → COMANDA → PLAN DE EXECUTIE → EXECUTIE EFECTIVA → RECONCILIERE
```

Aligns with program canonical chain: Intake V6 → ProductDefinition → ProductAggregate → Pricing/Cost → Quote → Order → ExecutionPlan.

**Product System** (parallel authority): template registry, dossier, linked modules — supports truth; not a mandatory operator stop.

---

## System ownership matrix

| System | Purpose | Canonical inputs | Canonical outputs | Stored truth | Editable until | Frozen at | Consumers | Forbidden |
|--------|---------|------------------|-------------------|--------------|----------------|-----------|-----------|-----------|
| **Cerere** | Request intake list | client, brief | request ID, route to Intake | request metadata | Intake open | request archived | Intake V6 | pricing, execution |
| **Intake V6** | Operator product configuration | SVG, layers, finishes, montaj | workspace state, capture read model | `finish_setup`, `mounting_solution`, layer roles | handoff to Offer | workspace confirmed + handed off | PD preview, Aggregate API, Cost preview, handoff | invent readiness; override PS templates |
| **Definire produs** | Composed product graph | Intake workspace | composition Cases A–D, blockers | product definition graph | pre-Offer | Offer creation | Aggregate, Cost | standalone re-inference of montaj |
| **Product System** | Template & module registry | template codes, dossier | catalog, module triggers | template metadata, linked modules | admin only | template version at Offer freeze | Aggregate builder, Cost | operator workflow stage (today) |
| **Product Aggregate** | Unified product graph for pricing/execution | PD + PS + workspace | aggregate modules, components | aggregate JSON | pre-Offer | Order snapshot | Cost, Offer lines, Execution plan | re-derive mounting from legacy fields |
| **Calcul** | Internal cost + commercial price | aggregate graph, rates | priced lines, blockers | rate snapshots at quote | pre-Offer accept | Offer/Order snapshot | Ofertă | inventory as price source |
| **Ofertă** | Commercial proposal | handoff package | quote ID, commercial totals | quote + snapshot v2 | until accepted | Order creation | Comandă | invent readiness status |
| **Comandă** | Sold truth container | accepted Offer | order ID, frozen snapshot | order snapshot | never post-freeze | execution start | Plan execuție | recalc from live templates |
| **Plan de execuție** | Operational task graph | frozen order | tasks, dependencies | execution plan v2 | until execution start | first actual | Execuție | re-infer operations |
| **Execuție efectivă** | Shop floor reality | frozen plan | actuals, status | task actuals | during execution | reconciliation close | Reconciliere | mutate sold product |
| **Reconciliere** | Plan vs actual closure | actuals + plan | variance, final status | reconciliation record | admin review | period close | Rapoarte | — |

---

## API / contract boundaries (key)

| Boundary | Contract owner | Evidence |
|----------|----------------|----------|
| Intake workspace GET/PATCH | `intake_v6_workspace_service` | runtime capture JSON |
| Runtime capture read model | `form_system_runtime_capture_read_model_service` | TE2E-001 root |
| PD preview | `product_definition_builder_service` (paused) | pd_preview_workspace.json |
| Aggregate GET | `product_aggregate_service` | aggregate_workspace.json |
| Commercial proposal (7G) | `commercial_price_proposal` router | code |
| Internal cost (7H) | `estimated_internal_cost` router | code |
| Quote list/create | Quote orchestrator + snapshot v2 | quotes_list.json |
| Order list/freeze | Order snapshot services | orders_list.json |
| Execution dashboard | `GET /api/v1/execution/dashboard` | execution_dashboard.json |

---

## Current truth divergence points (confirmed)

1. **Intake:** `mounting_solution` persisted but `support_type` gate blocks (TE2E-001)
2. **Intake:** readiness ignores capture blockers (TE2E-002)
3. **Intake:** finish truth not written (TE2E-003)
4. **Handoff:** policy does not merge capture (TE2E-014, 015)
5. **Calcul:** dual authority CostEngine vs 7G/7H (TE2E-025)
6. **Commercial spine:** same-scenario Request→Post-Job **PROVEN_V1** on Letters `DETERMINISTIC_LOCAL_SCENARIO` (TE2E-013 **closed**; residuals TE2E-028) — IR `IR-BUILD1-1784237119` → order `92402` → plan `8`

---

## Product composition cases (canonical)

| Case | Chain | Trigger |
|------|-------|---------|
| A | Letters only | default volumetric |
| B | Letters → ACM | `mounting_solution_active` |
| C | Letters → Premount | `metal_support_required` |
| D | Letters → ACM → Premount | both triggers |

Source: `product_definition_composition_contract` (paused/uncommitted) + Figma PD03–05 + aggregate optional modules.
