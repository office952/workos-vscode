# Readiness and Blockers Model

**Contract:** `ReadinessReport` (`backend/schemas/intake_v3.py`)  
**Service:** `evaluate_intake_v3_readiness()` — in-memory; compus în `build_intake_v3_workspace_preview()`.

---

## Principiu

Readiness este **contract**, nu decor UI.

- **Blockers** opresc acțiunea (ex. „Trimite la ofertare”).
- **Warnings** permit continuarea cu atenționare.
- **CTA eligibility** derivă din readiness real, nu din procent arbitrar.

---

## Structură ReadinessReport

| Câmp | Rol |
|------|-----|
| `status` | draft → blocked_for_quote → ready_for_quote → … |
| `blockers` | listă `ReadinessIssue` severity=blocker |
| `warnings` | listă `ReadinessIssue` severity=warning |
| `completion_by_section` | progres per zonă proces |
| `can_create_quote` | CTA ofertă |
| `can_generate_production_handoff` | preview seed eligibil |
| `next_action` | hint operator |

---

## Blockers implementați

| Code | Condiție |
|------|----------|
| `MISSING_DIMENSIONS` | lipsă width/height |
| `UNCONFIRMED_LETTER_MODEL` | model producție neconfirmat |
| `MISSING_FACE_VINYL_ROLL_WIDTH` | face vinyl activ |
| `MISSING_RETURN_DEPTH` | return wrapped activ |
| `MISSING_RETURN_PAINT_COLOR` | return painted fără culoare |
| `MISSING_FINISH_ASSIGNMENT` | finisaj neconfirmat |
| `MISSING_GROUP_FINISH_ASSIGNMENT` | group mode neconfirmat |
| Vector blockers | `CUT_CONTOUR_COUNT_MISMATCH`, etc. |

---

## Warnings (exemplu)

| Code | Semnificație |
|------|--------------|
| `RAW_CONFIRMED_LETTER_COUNT_MISMATCH` | raw ≠ litere confirmate |
| `RETURN_PAINT_REQUIRES_FACE_PROTECTION` | cant vopsit |
| `FACE_VINYL_AFTER_RETURN_PAINTING` | față + cant vopsit |
| `NO_SHARED_SUPPORT_PSU_PACKED` | surse în colet |
| `MATERIAL_ESTIMATE_ONLY` | MaterialIntent estimativ |
| `LETTER_CUSTOM_FINISH_ADVANCED_MODE` | mod avansat |

---

## Secțiuni readiness (pilot volumetric)

---

## Quote readiness gate (build 18)

**Service:** `evaluate_intake_v3_quote_readiness()` / `build_prequote_review()`  
**UI:** Pre-Quote Review panel + command bar counts

Distinct from general readiness:

- **`can_create_quote` is always `false`** in Intake V3 foundation (even when data complete).
- Maximum status: **`ready_preview_only`** (not “quote enabled”).
- Composes pricing input preview + handoff preview summaries without final commercial price or execution tasks.

Sources: `readiness_service`, `pricing_input_adapter`, `production_handoff_adapter`, `finish_variation_summary_service`, workspace payload/metadata.

---

## Quote creation dry-run (build 19)

**Service:** `build_intake_v3_quote_creation_dry_run()`  
**Endpoint:** `GET .../quote-creation-dry-run` (read-only)

Simulates payload + snapshot that a future quote build would consume. **`can_create_quote_now` always false.** Does not call `quotes.py` or CostEngine.

---

## Quote creation guard policy (build 20)

**Service:** `evaluate_quote_creation_guard_policy()`  
**Endpoint:** `GET .../quote-creation-guard-policy` (read-only)

Explicit policy lock: **`real_quote_creation_enabled` always false**, **`disabled_by_policy` always true**, even when readiness is `ready_preview_only` and dry-run is complete.

Quote readiness checklist includes **`QUOTE_CREATION_POLICY_DISABLED`** (info severity — not an operational blocker).

Dry-run embeds `guard_policy`; disabled reason derives from policy message.

---

`context` · `vector` · `litere` · `finisaje` · `materiale` · `iluminare` · `handoff`

Procentele reflectă completarea câmpurilor obligatorii per secțiune.

---

## Field editor ↔ blockers (controlled patch)

După `PATCH .../workspaces/{id}/fields` cu `regenerate_preview=true`, readiness se recalculează din payload sanitizat:

| Patch | Blocker eliminat / introdus |
|-------|----------------------------|
| `finish_assignment.face_finish.roll_width_mm` pozitiv | elimină `MISSING_FACE_VINYL_ROLL_WIDTH` |
| `finish_assignment.return_finish.depth_mm` pozitiv | elimină `MISSING_RETURN_DEPTH` (wrapped) |
| `return_finish.finish_type=painted` fără culoare | păstrează / introduce `MISSING_RETURN_PAINT_COLOR` |
| `return_finish.finish_type=painted` + culoare | activează painting în handoff preview; return vinyl inactiv |

UI afișează fiecare blocker cu: cod, problemă, fix recomandat, „editable here” (da/nu) — vezi `frontend/src/lib/intakeV3/blockerMessages.ts`.

**SVG upload:** prezența `raw_svg_analysis` **nu** elimină `UNCONFIRMED_LETTER_MODEL`. Upload-ul nu setează `confirmed_production_model`.

**Production model confirm:** `POST .../production-model/confirm` cu `confirmed=true` elimină `UNCONFIRMED_LETTER_MODEL` când counts sunt valide și modelul trece validarea vector. Raw analysis rămâne în payload pentru diagnostic.

**Finish assignments:** per-letter/group overrides sunt **opționale**. Preview include `finish_variation_summary` cu note pentru pricing/handoff — fără formule sau preț final.

---

## Quote enablement vs preview blockers (2026-06-18)

După dry-run, guard policy, și commercial bridge, Intake V3 expune **final blocker check** separat de readiness:

| Status | Semnificație |
|--------|--------------|
| `preview_status` | Workspace/preview OK pentru review enablement |
| `real_creation_status` | Întotdeaune `blocked` până la build owner-approved |

Blockers real-creation-only (exemple):

- `OWNER_APPROVAL_MISSING`
- `REAL_QUOTE_CREATION_DISABLED_BY_POLICY`
- `FINAL_PRICE_NOT_CALCULATED` (expected — nu se inventează preț)
- `BRIDGE_DISABLED_BY_POLICY`

Info la acest stadiu: `COST_ENGINE_NOT_CALLED`.

---

## Owner decision + snapshot policy (2026-06-18)

Policy contracts (preview only):

| Policy | Defined | Executed |
|--------|---------|----------|
| Owner decision record | ✅ required fields | ❌ not captured |
| Snapshot | ✅ v1 sections + integrity rules | ❌ not persisted |
| Anti-duplicate | ✅ idempotency keys | ❌ check not run |
| Recovery | ✅ failure modes + actions | ❌ no runtime |

Endpoint: `GET .../real-quote-creation-enablement-readiness`

---

## Guarded draft quote creation (2026-06-18)

First real Quote write — **draft only**:

| Check | Behavior |
|-------|----------|
| Owner decision | Required in POST body (`approved` + checkbox + reason) |
| Snapshot | Persisted in `Quotes.notes` JSON (`intake_v3_linkage_v1`) |
| Anti-duplicate | `Quotes.intake_code = IV3-{workspace_id}` |
| Pricing | Variant B — `requires_pricing_review`, no CostEngine |
| Side effects | No order / execution / inventory |

Endpoint: `POST .../create-draft-quote`

Readiness GET contracts unchanged (`can_create_quote_now=false`).

---

## Draft quote review + pricing handoff (2026-06-19)

After draft quote exists:

| Check | Behavior |
|-------|----------|
| Review | Read-only GET by workspace or quote id |
| Notes parse | Safe JSON + `intake_v3_linkage_v1` |
| Pricing handoff | Checklist only — no final price, no CostEngine |
| Accept/convert | Blocked while `requires_pricing_review=true` |
| Side effects | None (read-only) |

Endpoints: `GET .../draft-quote-review`, `GET .../quotes/{id}/draft-review`

---

## Pricing review completion (2026-06-19)

After operator completes manual pricing review:

| Check | Behavior |
|-------|----------|
| Method | Manual review POST only — no CostEngine |
| Quote status | Remains `draft` (priced draft) |
| Linkage | `requires_pricing_review=false`, `priced_draft=true`, `pricing_review.status=completed` |
| Totals | `subtotal`, `discount`, `total_before_vat`, `vat`, `grand_total` on Quote |
| Accept/convert | Still blocked — `INTAKE_V3_ACCEPT_CONVERT_SEPARATE_FLOW` |
| Side effects | Quote update only — no Order/Execution/Inventory |

Endpoints: `GET/POST .../pricing-review-state`, `GET/POST .../complete-pricing-review`

---

## Accept/convert readiness audit (2026-06-19)

After priced draft exists:

| Check | Behavior |
|-------|----------|
| Accept readiness | Preview when pricing review complete + snapshot + owner decision + final price |
| Convert readiness | Blocked until quote accepted + separate convert build |
| Actions | `can_accept_now=false`, `can_convert_now=false` in this build |
| Side effects | GET read-only — no Order/Execution/Inventory |

Endpoints: `GET .../accept-convert-readiness`

---

## Guarded accept flow (2026-06-18)

After priced draft + pricing review:

| Check | Behavior |
|-------|----------|
| Accept action | `POST .../accept` with explicit confirmations |
| Status path | `draft → priced → accepted` (validate_transition each step) |
| Notes | `intake_v3_linkage_v1.accept_decision` merged — snapshot preserved |
| Convert | Still blocked — `can_convert_now=false` |
| Side effects | Quote status + notes only — no Order/Execution/Inventory/CostEngine |

Endpoints: `GET/POST .../accept-state`, `GET/POST .../accept`

---

## Guarded convert to order (2026-06-18)

After IV3 quote accepted via guarded accept:

| Check | Behavior |
|-------|----------|
| Convert action | `POST .../convert-to-order` with explicit confirmations |
| Strategy | Variant B — direct `OrdersService.create()` (IV3 line_items not canonical snapshot) |
| Order | `status=locked`, `quote_id` set, linkage in notes + snapshot_line_items |
| Notes | `intake_v3_linkage_v1.convert_decision` merged — accept/snapshot preserved |
| Production | Still blocked — no ExecutionPlan/ExecutionTask/Inventory |
| Side effects | Order + quote notes only — no CostEngine |

Endpoints: `GET/POST .../convert-to-order-state`, `GET/POST .../convert-to-order`

After convert: convert readiness → `converted_to_order`, `can_convert_now=false`.

---

## Order production readiness audit (2026-06-18)

After IV3 Order exists (`locked`):

| Check | Behavior |
|-------|----------|
| Audit action | `GET .../production-readiness` — read-only |
| Data source | Order linkage + quote snapshot sections |
| Blockers | Explicit missing requirements model |
| Preview | Handoff + task generation + material readiness contracts |
| Actions | All `can_*_now=false` — no Execution/Inventory/production |

Endpoints: `GET .../orders/{id}/production-readiness`, `GET .../quotes/{id}/order-production-readiness`, workspace wrapper

---

## Geometry metrics snapshot (2026-06-18)

After confirmed production model (and optionally SVG upload path summary):

| Check | Behavior |
|-------|----------|
| Snapshot action | `GET .../geometry-metrics-snapshot` — read-only |
| Persist | Workspace on confirm; quote linkage section on draft quote creation |
| Counts | `real_letter_count`, `cut_contour_count`, `inner_hole_count` — holes ≠ letters |
| Perimeters | Null when not derivable — `perimeter_missing` warning, not invented |
| Readiness | `available_data.geometry_snapshot_available`, `geometry_status` |
| Consumers | Material Breakdown, Production Readiness, Task Dry-Run |

Status values: `geometry_complete`, `geometry_partial`, `geometry_missing`.

---

## Path perimeter classification (2026-06-18)

After SVG upload with layer-group path metrics:

| Check | Behavior |
|-------|----------|
| Classification action | `GET .../geometry-path-perimeter-classification` — read-only |
| Persist | Merged into `geometry_metrics_snapshot.path_perimeter_classification` |
| Roles | Face/backing/return/bevel only when layer id/name maps to known role |
| Missing | `backing_perimeter_missing`, `return_perimeter_missing`, etc. — not invented |
| Readiness | `perimeter_classification_status`, `face_cutting_perimeter_available`, … |
| Consumers | Material Breakdown, Production Readiness, Task Dry-Run |

Classification status: `complete`, `partial`, `missing`, `unsupported`.

---

## Operator layer role confirmation (2026-06-18)

After SVG upload with `path_geometry_summary.layers`:

| Check | Behavior |
|-------|----------|
| Confirmation action | `GET/PUT .../layer-role-confirmation` on workspace |
| Persist | `workspace.payload.layer_role_confirmation_snapshot` |
| Auto vs confirmed | `auto_role` (medium) separate from `confirmed_role` (high) |
| Ignore / unknown | Excluded from perimeter classification |
| Readiness | `layer_role_confirmation_status`, confirmed/unconfirmed/ignored counts |
| Consumers | Path perimeter classification, geometry snapshot, material breakdown, task dry-run |

Confirmation status: `complete`, `partial`, `missing`.

---

## Layer role propagation / stale snapshot (2026-06-18)

| Check | Behavior |
|-------|----------|
| Propagation audit | `GET .../layer-role-confirmation/propagation` (workspace/quote/order) |
| Effective source | Workspace live when linked; else quote linkage snapshot |
| Stale detection | Role diff or newer workspace `confirmed_at` vs quote snapshot |
| Refresh | `POST .../refresh-technical-snapshot` — draft/priced draft only; updates linkage technical sections only |
| Readiness | `layer_role_confirmation_snapshot_stale`, `layer_role_confirmation_effective_source`, `can_refresh_quote_snapshot` |
| Consumers | Same as operator confirmation — with stale warnings |

---

## Production task dry-run (2026-06-18)

After material breakdown path (or sufficient IV3 snapshot):

| Check | Behavior |
|-------|----------|
| Dry-run action | `GET .../production-task-dry-run` — read-only |
| Data source | IV3 context + handoff task seeds + geometry/material rows |
| Output | Candidate groups/tasks, dependencies, blockers/warnings |
| Actions | All mutation flags false — no Execution/Inventory/production |

Dry-run blocker codes include: `missing_confirmed_production_model`, `missing_finish_assignments`, `production_readiness_not_ready`, `geometry_partial`, `missing_material_breakdown` (warning), `material_shortage_detected`, `material_manual_check_required`.

---

## Material availability preview (2026-06-18)

After material breakdown (read-only):

| Check | Behavior |
|-------|----------|
| Endpoint | `GET .../material-availability` (workspace/quote/order) |
| Source quantities | Material Breakdown rows only — no geometry recomputation |
| Inventory | Read-only `inventory_materials.stock_current` |
| Statuses | `available`, `shortage`, `manual_check`, `indirect_consumable`, `no_match`, … |
| Readiness | `material_availability_*` counts in `available_data`; warnings for shortage/manual check |
| Task dry-run | Summary fields + per-task material `availability_status` |
| Boundary | No reservation, StockMovement, PO, CostEngine, execution creation |

---

## Procurement preview (2026-06-18)

After material availability (read-only):

| Check | Behavior |
|-------|----------|
| Endpoint | `GET .../procurement-preview` (workspace/quote/order) |
| Source | Material Availability rows only — no availability recomputation |
| Registry hints | Read-only `source_name`, `source_url`, `source_review_status`, `unit_cost` |
| Statuses | `purchase_recommended`, `owner_decision_required`, `manual_check`, `indirect_consumable`, … |
| Readiness | `procurement_preview_*` counts; warnings `procurement_owner_decision_required`, … |
| Task dry-run | Summary + `procurement_status` on candidate task inputs |
| Boundary | No PO, Supplier Order, reservation, StockMovement, CostEngine |

---

## Production Preview consolidation UI (2026-06-19)

Single **Production Preview** container groups geometry/layers, materials/stock, procurement decisions, and task dry-run previews. Layer Role Confirmation remains separate operator input. Frontend-only aggregation via `productionPreviewSummary.ts` — no new backend endpoint.

---

## Ce nu este readiness

- Nu înlocuiește `VolumetricQuoteReadyResult` runtime actual (coexistă până la migrare).
- Nu calculează preț.
- Nu generează taskuri.

---

## Legături

- Contracts: [../architecture/INTAKE_V3_ARCHITECTURE_CONTRACTS.md](../architecture/INTAKE_V3_ARCHITECTURE_CONTRACTS.md)
- Finish rules: `templates/TPL-VOLUMETRIC-LETTERS/03_FINISH_MODEL.md`
