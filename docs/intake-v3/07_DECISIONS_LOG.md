# Intake V3 — Decisions Log

---

## Decizii luate

| # | Decizie | Data / ref |
|---|---------|------------|
| D1 | Intake V3 greenfield, nu refactor V2 | Architecture Contracts |
| D2 | Atoms V6 = design reference only | Audit 2026-06-17 |
| D3 | Raw SVG Analysis ≠ Confirmed Production Model | Contracts + dossier |
| D4 | Model HUB: 18 litere / 27 contururi / 9 goluri | Atoms + owner |
| D5 | MaterialIntent ≠ Inventory; `inventory_mutation_allowed=false` | Contracts |
| D6 | ProductionHandoff preview only | Contracts |
| D7 | EmployeePreviewSeed non-executable | Contracts |
| D8 | Fără hardcodare persoane în template | Skills doc |
| D9 | Taskuri = logică operațională condiționată, nu listă statică | Task logic doc |
| D10 | Fără suport comun → surse în colet, nu task cablare pe suport | Owner update |
| D11 | Cant colantat → colantare cant **înainte** de modelare | Owner update |
| D12 | Cant vopsit → vopsire **după** asamblare, față protejată | Owner update |
| D13 | Colantare fețe doar dacă specificată în comandă | Owner update |
| D14 | Colantare fețe după asamblare; dacă cant vopsit, după vopsire/uscare/protecție | Owner update |
| D15 | Task final = infoliere stretch + colet (nu „Ambalare/predare” generic) | Owner update |
| D16 | Raw/confirmed mismatch = warning; vector validation în serviciu pur | Vector build |
| D17 | Inner hole fără parent + cut count mismatch = blocker | Vector build |
| D18 | MaterialIntent derivat din finish — estimate only, no inventory | Finish/material build |
| D19 | Return wrapped vs painted = ramuri operaționale distincte | Finish/material build |
| D20 | No shared support → PSU în colet, nu montaj pe suport | Finish/material build |
| D21 | PricingInput adapter maps facts only — CostEngine separate | Adapters packet |
| D22 | ProductionHandoff preview ≠ ExecutionPlan | Adapters packet |
| D23 | Volumetric runtime: face vinyl după assembly; return vinyl înainte forming | `225e054` |
| D24 | `intake_v3_workspace_preview_service` = orchestrator, nu logică nouă | E2E shell build |
| D25 | UI shell `/intake-v3` fixture-only; boundary flags false pentru acțiuni reale | E2E shell build |
| D26 | `GET /api/v1/intake-v3/preview` read-only — scenarii in-memory, fără DB write | Backend preview API build |
| D27 | UI încearcă backend preview; fallback local fixture cu mesaj explicit | Backend preview API build |
| D28 | `intake_v3_workspaces` table — draft payload JSON only, no quote/order FK | Workspace persistence build |
| D29 | `sanitize_intake_v3_workspace_payload` resetează boundary flags periculoase | Workspace persistence build |
| D30 | Field editor = allowlist patches only; all-or-nothing validation | Field editor build |
| D31 | `dimensions.*` aliases map to `client_request.*` in payload | Field editor build |
| D32 | `support_context` optional on workspace; synced with `mounting_intent` | Field editor build |
| D33 | Return `finish_type=painted` dezactivează return vinyl chiar dacă material Oracal rămâne | Field editor build |
| D34 | Flow stepper = UI derivat din stare existentă, nu workflow engine | UX polish build |
| D35 | Blocker copy frontend-only (`blockerMessages.ts`) — backend codes rămân contract | UX polish build |
| D36 | Pricing/handoff UI wording explicit „preview only” | UX polish build |
| D37 | SVG upload = payload JSON only; no disk storage in V3 | SVG raw analysis build |
| D38 | External href http(s) rejected; xmlns namespace allowed | SVG raw analysis build |
| D39 | Raw analysis warning codes separate from readiness blockers | SVG raw analysis build |
| D40 | Production model confirm requires explicit `confirmed=true` POST | Model review build |
| D41 | Count-only confirm uses placeholder letter/contour scaffold for vector validation | Model review build |
| D42 | HUB 18/27/9 valid — holes not letters | Model review build |
| D43 | Finish overrides stored in payload (`letter_group_finish_assignments`, `letter_finish_assignments`) | Finish assignment build |
| D44 | Precedence: letter > group > global; `enabled=false` stored but ignored | Finish assignment build |
| D45 | Per-letter assignments optional — global finish alone remains valid for readiness | Finish assignment build |
| D46 | Hole contour IDs (`C-HOLE-*`) cannot be finish targets | Finish assignment build |
| D47 | Finish variation summary = preview notes only; no CostEngine | Variation summary build |
| D48 | `requires_grouped_finish_review` when variations present — pricing note, not blocker | Variation summary build |
| D49 | Quote readiness gate distinct from general readiness; `can_create_quote` always false in V3 foundation | Quote readiness build |
| D50 | Max quote gate status = `ready_preview_only` — never enables real quote CTA | Quote readiness build |
| D51 | Quote dry-run = GET contract only; never calls quote creation endpoints | Dry-run build |
| D52 | Dry-run snapshot is preview payload, not DB snapshot row | Dry-run build |
| D53 | Quote creation guard policy = disabled-by-default; separate from readiness blockers | Guard policy build |
| D54 | `QUOTE_CREATION_POLICY_DISABLED` is info-only in readiness checklist | Guard policy build |
| D55 | Real quote enablement requires owner-approved build — no env flag in guard foundation | Guard policy build |
| D56 | Commercial quote bridge = mapping preview only; never calls quote endpoints or CostEngine | Bridge build |
| D57 | Bridge missing fields must not be invented — final price always absent in preview | Bridge build |
| D58 | Bridge snapshot plan is preview-only — no DB snapshot persistence in foundation | Bridge build |

---

## Decizii pending

| # | Subiect | Status |
|---|---------|--------|
| P1 | Suport comun (bare / ACM / casetă) — logică completă | `OWNER_ANALYSIS_REQUIRED` |
| P2 | Granularitate task real vs checklist în Mobile | open |
| P3 | Operation Catalog first-class în ProductSystem DB | open |
| P4 | Custom pe literă în pilot V3 | defer — all/group first |
| P5 | Persistență: `intake_schema_version=3` vs tabel nou | ✅ `intake_v3_workspaces` (greenfield table) |
| P6 | Migrare intake-uri V2 → V3 | open |
| P7 | Skill matrix / fișă post ↔ planning real | open |
| P8 | Când activăm UI Intake V3 | ✅ minimal shell `/intake-v3` (backend preview + fallback) |

---

## STOP rule

Dacă logica operațională pentru un caz concret nu este clară în acest log sau în Operation Catalog → **nu inventa** — adaugă în Open Questions și cere owner decision.

---

## 2026-06-18 — Owner approval required before real quote creation

**Decision:** Intake V3 real quote creation cannot be enabled without a dedicated owner-approved build.

**Implementation:** `INTAKE_V3_REAL_QUOTE_CREATION_REQUIRES_OWNER_APPROVAL` enablement policy + final blocker check. `owner_approval_present` remains false in foundation; no approval capture UI in this build.

**Rationale:** Separates technical readiness (preview pass) from commercial enablement rights.

---

## 2026-06-18 — Owner decision record and snapshot policy contracts

**Decision:** Before real quote creation, owner decision capture and immutable snapshot persistence must be defined as explicit contracts.

**Implementation:** Owner decision record policy, snapshot policy v1, anti-duplicate policy, recovery policy, final enablement readiness — all preview-only; no DB model in this build.

**Rationale:** Closes the gap between "owner approval required" and safe enablement without activating quote creation.

---

## 2026-06-18 — Guarded draft commercial quote creation

**Decision:** First Quote write uses existing `Quotes` row with `intake_code` linkage and JSON snapshot in `notes` — no schema migration.

**Implementation:** `POST .../create-draft-quote` with owner approval, anti-duplicate, Variant B pricing (`requires_pricing_review`), no CostEngine/order/execution/inventory.

**Rationale:** Minimal, auditable first write path before pricing enablement or order conversion builds.

---

## 2026-06-19 — Draft quote review and pricing handoff alignment

**Decision:** Post-create review is read-only; reuse `notes` JSON linkage — no migration.

**Implementation:** Review + pricing handoff GET endpoints, Intake V3 UI panel, Quotes IV3 badges, commercial guard for `requires_pricing_review`.

**Rationale:** Operators can audit snapshot and blocked accept/convert before explicit pricing review build.

---

## 2026-06-19 — Manual pricing review completion (priced draft)

**Decision:** Variant B — manual pricing review POST; no CostEngine; quote stays `draft`.

**Implementation:** `complete-pricing-review` endpoints; `notes.intake_v3_linkage_v1.pricing_review`; Quote monetary columns updated; accept/convert remain blocked (separate build).

**Rationale:** Canonical `quotes/price` path transitions to `priced` via CostEngine — out of scope for IV3 first priced-draft layer.

---

## 2026-06-19 — Accept/convert readiness audit (actions blocked)

**Decision:** Accept and convert are separate readiness tracks; no actions enabled in this build.

**Implementation:** Read-only GET readiness endpoints; UI panel; IV3 Quotes badges Accept blocked / Convert blocked.

**Rationale:** Accept is status-only via quotes PATCH; convert is `POST orders/from-quote/{id}` with Order creation — must not be enabled for IV3 until guarded builds land.

---

## 2026-06-18 — IV3 guarded accept uses lifecycle chain draft→priced→accepted

**Decision:** IV3 priced drafts remain `status=draft` after manual pricing; guarded accept performs validated `draft→priced→accepted` in one POST without CostEngine or Order side effects.

**Rejected:** Direct `draft→accepted` (blocked by `validate_transition`).

**Next:** `INTAKE_V3_GUARDED_CONVERT_TO_ORDER` — separate build.

---

## 2026-06-18 — IV3 guarded convert uses OrdersService.create (Variant B)

**Decision:** Do not reuse `POST orders/from-quote/{id}` for IV3 — IV3 quotes lack canonical `QuoteCalculationSnapshot` in `line_items`.

**Implementation:** Guarded convert service creates Order via `OrdersService.create()` with pricing-review totals + EUR→RON conversion; `quote_id` linkage; `convert_decision` in quote notes; Order notes/snapshot carry `intake_v3_order_linkage_v1`.

**Rejected:** Variant A (existing from-quote) — would fail snapshot validation for IV3 quotes.

**Side effects:** Order only — no ExecutionPlan, ExecutionTask, Inventory, CostEngine.

**Next:** Order handoff / production readiness audit — still no auto Execution creation.

---

## 2026-06-18 — IV3 order production readiness audit (read-only)

**Decision:** After guarded convert, evaluate production handoff readiness via GET endpoints only — no ExecutionPlan, ExecutionTask, Inventory, or production start.

**Implementation:** `intake_v3_order_production_readiness_service`; blockers from quote snapshot sections; task/material preview contracts; UI audit panel.

**Next:** Material quantity/cost breakdown informative build OR production task generation dry-run contract.

---

## 2026-06-18 — IV3 material breakdown informative (materials-only)

**Decision:** Expose geometry + material quantities + material acquisition costs as read-only GET breakdown — no labor, operations, markup, profit, VAT, CostEngine, Inventory, or Execution mutations.

**Implementation:** `intake_v3_material_quantity_breakdown_service`; optional `geometry_metrics_snapshot`; registry lookup + documented owner-confirmed fallbacks; UI `IntakeV3MaterialBreakdownPanel`.

**Rejected:** Using CostEngine or Inventory for quantity/price resolution in this build.

**Next:** Production task generation dry-run contract OR inventory availability read-only check.

---

## 2026-06-18 — IV3 production task generation dry-run (preview only)

**Decision:** Expose candidate task groups, preview tasks, dependencies, and blockers via read-only GET — no ExecutionPlan, ExecutionTask, WorkSession, Inventory, CostEngine, or production start.

**Implementation:** `intake_v3_production_task_dry_run_service`; reuses material breakdown context + handoff `build_task_seed_candidates()`; eight TPL-VOLUMETRIC preview groups; UI `IntakeV3ProductionTaskDryRunPanel`; flow step `task_dry_run`.

**Rejected:** Writing preview tasks to `ExecutionPlan.tasks_json` or calling `ExecutionPlanService.from_order()` in this build.

**Next:** Geometry metrics snapshot persistence OR inventory availability read-only check OR guarded ExecutionPlan/ExecutionTask creation foundation.

---

## 2026-06-18 — IV3 geometry metrics snapshot (`geometry_metrics_snapshot_v1`)

**Decision:** Persist technical geometry metrics snapshot from confirmed production model + dimensions + optional SVG path summary at upload — read-only GET endpoints; no perimeter invention; holes ≠ letters.

**Implementation:** `intake_v3_geometry_metrics_snapshot_service`; workspace persist on confirm; quote linkage section on draft quote creation; Material Breakdown / Production Readiness / Task Dry-Run consume snapshot; UI `IntakeV3GeometryMetricsPanel`; flow step `geometry_snapshot`.

**Rejected:** POST recompute (SVG text not stored); mapping raw SVG total perimeter to letter cutting perimeter; CostEngine / Inventory / Execution mutations.

**Next:** Path perimeter classification by layer/role OR guarded SVG re-upload recompute build.

---

## 2026-06-18 — IV3 geometry path perimeter classification (`path_perimeter_classification_v1`)

**Decision:** Classify SVG layer path perimeters into production roles (face/backing/return/bevel) only when layer role mapping + path metrics allow — merge into geometry snapshot; no perimeter invention; holes ≠ letters.

**Implementation:** `intake_v3_geometry_path_perimeter_classification_service`, `intake_v3_svg_layer_path_geometry`; GET endpoints; UI `IntakeV3PathPerimeterClassificationPanel`; flow step `perimeter_classification`.

**Rejected:** Bbox/total SVG perimeter as face cutting perimeter; backing/return/bevel derived from face; CostEngine / Inventory / Execution mutations.

**Next:** Operator-confirmed layer role mapping for high-confidence classification.

---

## 2026-06-18 — IV3 operator layer role confirmation (`layer_role_confirmation_v1`)

**Decision:** Operator confirms SVG layer→production role mapping in workspace draft; `confirmed_role` overrides auto synonym mapping with high confidence; persisted in workspace payload and propagated to quote linkage sections on draft quote creation.

**Implementation:** `intake_v3_layer_role_confirmation_service`; PUT rebuilds geometry snapshot only; UI `IntakeV3LayerRoleConfirmationPanel`; flow step `layer_role_confirmation`.

**Rejected:** Forced roles without operator input; unknown/ignore treated as face; CostEngine / Inventory / Execution / commercial status mutations.

**Next:** Quote refresh after workspace re-confirm; optional audit log for operator decisions.

---

## 2026-06-18 — IV3 layer role propagation / stale snapshot policy

**Decision:** Workspace live confirmation is the **effective** technical source when `source_workspace_id` is available. Quote linkage snapshot is preserved at draft create; workspace re-confirm marks quote snapshot **stale** (warnings, not silent overwrite). Downstream previews use effective source. Guarded POST refresh updates only technical IV3 linkage sections for draft/priced draft quotes; accepted/converted quotes block refresh.

**Implementation:** `intake_v3_layer_role_confirmation_propagation_service`; GET propagation endpoints; optional `refresh-technical-snapshot` POST; `IntakeV3LayerRolePropagationPanel`; flow step `layer_role_propagation`.

**Rejected:** Implicit refresh on GET; quote/order status or pricing mutation; accepted quote auto-resnapshot.

---

## 2026-06-18 — IV3 read-only material availability preview

**Decision:** Material Breakdown remains the sole source of required quantities. Availability compares breakdown rows to `inventory_materials` read-only (code match first). Shortages computed only when units are compatible. Indirect consumables (cables, connectors, screws, silicone) are policy rows — not strict stock shortage. No reservation, StockMovement, PO, CostEngine, or execution creation.

**Implementation:** `intake_v3_material_availability_service`; GET `.../material-availability`; `IntakeV3MaterialAvailabilityPanel`; flow step `material_availability`; readiness + task dry-run consume summary fields.

**Rejected:** Auto-procurement; inventory mutation from preview; geometry recomputation in availability layer.

---

## 2026-06-18 — IV3 read-only procurement preview from material availability

**Decision:** Material Availability remains the sole upstream source. Procurement Preview translates availability into recommended actions (purchase, owner decision, manual check, preventive restock) read-only. Major materials (plexi, forex, aluminum return, face vinyl, LED PSU, ACM) require owner decision + advance hint on shortage. Indirect consumables are policy rows, not strict shortage. Source hints from `inventory_materials` are informative only.

**Implementation:** `intake_v3_procurement_preview_service`; GET `.../procurement-preview`; `IntakeV3ProcurementPreviewPanel`; flow step `procurement_preview`; readiness + task dry-run consume summary fields.

**Rejected:** Purchase Order / Supplier Order creation; inventory mutation; CostEngine; auto-buy buttons in UI.

---

## 2026-06-19 — IV3 Production Preview consolidation UI

**Decision:** Group existing read-only preview panels under a single Production Preview container with overview, centralized warnings/blockers, and expandable sections. Layer Role Confirmation stays outside as operator input. Frontend-only aggregation — no backend summary endpoint in this build.

**Implementation:** `IntakeV3ProductionPreviewPanel`, `productionPreviewSummary.ts`, flow step `group: "Production Preview"` metadata.

**Rejected:** Hiding sub-panel data; real execution buttons; backend logic changes for aggregation.
