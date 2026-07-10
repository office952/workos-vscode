# INTAKE_V6_PRODUCTAGGREGATE_WORKSPACE_LINKED_LOGO_COMPOSITION_V1 — Plan

**Phase:** PLAN COMPLETE  
**Plan verdict:** READY_FOR_BOUNDED_IMPLEMENTATION  
**Scope verified:** YES  
**Forbidden scope touched:** NO  
**Accepted HEAD:** 9d18806

## Objective

Enable **one coherent workspace-aware ProductAggregate** for:

```text
TPL-VOLUMETRIC-LETTERS_v2
  + bound logo segment(s) from layer_bindings[]
  + TPL-VOLUMETRIC-LOGO_v1 (per segment)
  = single composed technical product graph
```

Without second binding truth, without pricing/Quote/Order/Execution changes, without ProductSystem template edits.

## Accepted truth (unchanged)

See previous task `INTAKE_V6_LINKED_LOGO_LAYER_BINDINGS_PERSISTENCE_V1` — binding persistence is **done** and **out of scope** for implementation.

## Selected architecture

**Option A — ProductAggregate consumes ProductDefinition output**

```text
workspace_id + ROOT template
  → ProductDefinitionBuilderService.build_preview(ROOT, workspace_id)
       ├─ letters ProductAggregate (existing internal call)
       └─ linked_template_runtime_segments (confirmed segments only)
  → ProductAggregateWorkspaceCompositionService.compose(pd, letters_aggregate)
  → composed ProductAggregate (ROOT template_code, expanded graph)
```

### Rejected options

| Option | Why rejected |
|---|---|
| B — PA reads bindings directly | Duplicates segment compiler; risks recommendation/binding drift |
| C — New public composition contract now | Larger schema surface; PD segments sufficient for v1 |
| D — PD owns aggregate assembly | Couples Step 6 preview to aggregate expansion; harder rollback |

## Component instance model

**Recommendation (DEC-PA-01): two traceable component instances, not quantity=2 on one row.**

| Aggregate component | Identity | Template owner | Quantity | Finish owner | Geometry owner | Provenance |
|---|---|---|---|---|---|---|
| `comp_face_litere` etc. | letters dossier ids | LETTERS_v2 | 1 assembly | letters finish_setup | quote_geometry letters | dossier/parent |
| `comp_logo_face::logo-stanga` | namespaced id | LOGO_v1 | 1 segment | artwork_finishes[logo-stanga] | segment geometry refs | linked_segment:logo-stanga |
| `comp_logo_finish::logo-stanga` | namespaced id | LOGO_v1 | 1 segment | artwork_finishes[logo-stanga] | segment | linked_segment:logo-stanga |
| `comp_logo_face::logo-dreapta` | namespaced id | LOGO_v1 | 1 segment | artwork_finishes[logo-dreapta] | segment | linked_segment:logo-dreapta |

**Namespacing convention (no schema migration):**

- `component_id = "{base_component_id}::{segment_key}"`
- Materials/operations use `component_ref` with same namespaced id
- Dedupe key extended: `{material_code}|{source_template_code}|{component_ref}|{provenance}`

Same template code for both segments → **two instances**, not merged.

## Material merge strategy

| Material category | Letters source | Logo source | Shared? | Dedupe key candidate | Risk |
|---|---|---|---|---|---|
| Face plexi (letters) | LETTERS dossier/modules | — | no | letter component_ref | LOW |
| Print vinyl / laminate | — | LOGO finish module per segment | no | segment component_ref | MED — must not collapse segments |
| Return/cant aluminum | letters lateral module | LOGO return module per segment | no | component_ref + segment | MED |
| Backing Forex | letters back | LOGO back per segment | no | segment | MED |
| LEDs / PSU | letters LED module | LOGO lighting per segment | maybe shared SKU | **definition dedupe only** | HIGH if qty merged |
| Mounting template | letters/shared | LOGO mounting per segment | possible SHARED_ONCE | operation-level merge | MED |
| Consumables | parent rows | child template rows | batchable | explicit merge class | MED |

**Rules:**

1. **Never** merge two segment-required quantities into one row.
2. Dedupe only identical **definitions** (same code + same component_ref + same source).
3. Shared parent consumables (e.g. assembly QC) may appear once with provenance `shared_assembly`.
4. Logo finish values stay in workspace `artwork_finishes[]`; aggregate references segment via `component_ref`, does not embed finish payload.

## Operation merge strategy

| Operation | Letters | Logo | Shared execution? | Merge rule | Task impact |
|---|---|---|---|---|---|
| SVG prep / nesting | letters geometry | per-segment artwork box | SHARED_ONCE setup possible | `SHARED_ONCE` if same workcenter+setup | one setup task |
| CNC face cut | `face_cnc_cut` | `logo_face_cnc_cut` per segment | no | `COMPONENT_SPECIFIC` | per segment |
| Print / laminate | — | logo print ops per segment | batchable | `SHARED_BATCHABLE` with segment qty | batch task w/ segment list |
| Return/cant forming | `side_forming` | logo return ops | no | `COMPONENT_SPECIFIC` | separate |
| LED install / wiring | letters | logo per segment | no | `COMPONENT_SPECIFIC` | separate |
| Final QC / packaging | letters dossier | — | likely once | `SHARED_ONCE` | single task |

Classification enum for merge planner: `COMPONENT_SPECIFIC | SHARED_ONCE | SHARED_BATCHABLE | INFORMATIONAL_ONLY | UNKNOWN`.

**Do not** assume same operation code ⇒ run once.

## Task rule merge strategy

**Owner (DEC-PA-03): `ProductAggregateWorkspaceCompositionService` owns merge.**

| Task rule | Source template | Component/segment | Merge key | Shared? | Planning complete? | Proposed behavior |
|---|---|---|---|---|---|---|
| `cnc_face_cut` | LETTERS | letters | task_name\|priced_operation\|letters | no | dossier yes | keep |
| `logo_face_*` | LOGO | per segment | task_name\|priced_operation\|segment_key | no | seed yes | suffix or separate rules |
| `packaging_letters` | LETTERS | assembly | task_name\|priced_operation | yes | partial | `SHARED_ONCE` |
| informational | any | — | — | — | — | exclude from task materialization |

ExecutionPlan materialization remains **out of scope**; composed rules are preview-only.

## Provenance strategy

| Aggregate row type | Minimum provenance | Existing support? | Gap |
|---|---|---|---|
| Letter component | source_template_code, component_id, provenance=dossier | yes | none |
| Logo component instance | + segment_key, owning_template_code, workspace_id | partial (component_id string) | encode segment in id |
| Material | component_ref, source_template_code, provenance | yes | extend dedupe key |
| Operation | component_ref, source_template_code | yes | same |
| Task rule | provenance + mini_module_code | yes | add segment note in details/warning |

Use existing schema fields; no new public fields in v1 unless implementer proves namespacing insufficient.

## Readiness / blocker strategy

| Condition | PD state | Aggregate state | Handoff state | Expected blocker |
|---|---|---|---|---|
| Binding + finish confirmed | segment ready | logo instances included, full ops/materials | preview allowed | none for aggregate |
| Binding confirmed, finish missing | segment blocked finish | logo instances **partial** (structure only, warnings) | preview allowed read-only | `LINKED_SEGMENT_FINISH_MISSING` |
| Binding missing | segment blocked | **no logo expansion** | preview allowed | no invented logo template |
| Geometry missing | PD partial | no fabricated quantities | blocked downstream | geometry blockers |
| Final Step 3 not confirmed | independent | **aggregate preview still allowed** (DEC-PA-05) | handoff blocked separately | operator confirmation |

Do not merge final operator confirmation with technical aggregate readiness.

## Endpoint / service plan

**Recommendation (DEC-PA-04): extend existing aggregate GET with optional `workspace_id`.**

| Endpoint/service | Current input | Proposed input | Response change | Compatibility risk |
|---|---|---|---|---|
| `GET .../aggregate/{template_code}` | template_code | + `workspace_id` optional query | composed aggregate when workspace provided | **LOW** — absent param = unchanged |
| `ProductAggregateService.build` | template_code | unchanged | unchanged | none |
| **NEW** `ProductAggregateWorkspaceCompositionService.compose` | PD preview + letters aggregate | internal | composed ProductAggregate | none public |

**No new public endpoint** unless implementer finds query-param wiring blocked.

Flow:

```text
GET /aggregate/TPL-VOLUMETRIC-LETTERS_v2?workspace_id={uuid}
  → if workspace_id absent: ProductAggregateService.build (today)
  → if present:
       pd = ProductDefinitionBuilderService.build_preview(ROOT, workspace_id)
       letters = ProductAggregateService.build(ROOT)
       return compose(pd, letters)
```

## Snapshot boundary (future)

```text
live workspace → PD → composed PA → (future) immutable Order/Quote snapshot
```

Frozen snapshot must store:

- segment keys and owning template codes
- namespaced component ids
- composed materials/operations/task_rules
- workspace/PD hash at freeze time

Live binding must not be re-resolved after snapshot. **Implementation deferred.**

## Implementation sequence

| Step | File/function | Change | Reason | Test |
|---|---|---|---|---|
| 1 | `product_aggregate_workspace_composition_service.py` (NEW) | `compose_from_product_definition(...)` | core adapter | unit tests |
| 2 | same | `_expand_logo_segment_aggregate(segment, logo_aggregate)` | per-segment expansion | multi-segment tests |
| 3 | same | `_merge_materials/_merge_operations/_merge_task_rules` | explicit merge classes | dedupe tests |
| 4 | `product_aggregate_service.py` | `build_for_workspace(template_code, workspace_id)` thin orchestrator | single entry | integration |
| 5 | `routers/product_system_aggregate.py` | optional `workspace_id` query param | API surface | router test |
| 6 | `tests/test_product_aggregate_workspace_linked_logo_composition.py` (NEW) | full matrix | validation gate | pytest |

**Do not modify:** `intake_v6_layer_binding_persistence_service.py`, frontend, pricing, Quote/Order/Execution, ProductSystem seeds/templates, DB schema.

### Exact functions (proposed)

```python
# product_aggregate_workspace_composition_service.py
async def build_workspace_composed_aggregate(db, *, template_code: str, workspace_id: str) -> ProductAggregate | None
def compose_from_product_definition(*, pd: ProductDefinitionPreview, letters_aggregate: ProductAggregate, logo_aggregates_by_segment: dict[str, ProductAggregate]) -> ProductAggregate
def _confirmed_linked_segments(pd: ProductDefinitionPreview) -> list[dict]
def _namespace_component(component_id: str, segment_key: str) -> str
def _merge_materials(letters, segment_expansions, merge_plan) -> list[ProductAggregateMaterial]
def _merge_operations(letters, segment_expansions, merge_plan) -> list[ProductAggregateOperation]
def _merge_task_rules(letters, segment_expansions, merge_plan) -> ProductAggregateTaskContract
```

## Test plan

### Composition

- letters-only workspace → identical to template aggregate (no logo rows)
- one confirmed segment → one namespaced logo component set
- two segments → two traceable instances; same template code
- missing binding → no logo components invented
- missing finish → partial logo structure + warning; letters unchanged
- logo finish remains in workspace path (not copied to binding)

### Materials / operations / task rules

- per-segment print/laminate materials present with distinct component_ref
- duplicate definition dedupe does not remove segment consumption
- SHARED_ONCE ops appear once; COMPONENT_SPECIFIC remain separate
- informational ops not promoted to tasks

### Provenance / regression

- every logo row traces to segment_key and LOGO_v1
- letters rows trace to LETTERS_v2
- `test_product_aggregate_volumetric_v2.py` passes
- `test_product_definition_gradi_composition.py` passes
- `test_intake_v6_layer_binding_persistence.py` passes
- selected_layer_refs + return/cant tests pass
- E2E three-step smoke unchanged

## Rollback

Remove new service + router query param branch + tests. Template-only aggregate path unchanged.

## Risk register

| Risk | P | I | Mitigation | Test |
|---|---|---|---|---|
| Duplicate materials | MED | HIGH | segment-aware component_ref dedupe | two-segment material test |
| Duplicate operations | MED | HIGH | merge class registry | operation merge tests |
| Duplicate task rules | MED | HIGH | explicit merge keys | task rule tests |
| Lost segment identity | LOW | HIGH | namespaced component_id | provenance tests |
| Wrong finish ownership | LOW | HIGH | no finish in aggregate components | finish independence test |
| Recommendation as truth | LOW | HIGH | only PD segments w/ confirmed binding | negative test |
| PA recompiles bindings | MED | HIGH | ban direct binding reads in adapter | code review gate |
| Letters-only regression | LOW | HIGH | workspace without logo unchanged | regression test |
| Response schema break | LOW | MED | optional param default | router test |
| Circular PD dependency | LOW | MED | PA calls PD; PD does not call compose | import lint |
| Snapshot incompatibility | MED | MED | document namespacing for future freeze | plan note only |
| Accidental pricing coupling | LOW | HIGH | forbidden path audit | diff check |

## Owner decisions required

### DEC-PA-01 — Segment instance model

- **Problem:** Two segments, same template — one component vs two instances?
- **Evidence:** gradi logical list uses per-segment rows; binding persistence is per `layer_key`.
- **Options:** (A) two instances (recommended) (B) quantity=2 single instance
- **Recommended:** A — two instances with `::{segment_key}` suffix
- **Risk if wrong:** traceability loss in execution/snapshot
- **Blocked until GO:** YES

### DEC-PA-02 — Partial aggregate when finish missing

- **Problem:** Include logo structure without finish?
- **Evidence:** segment readiness blocks on finish; PD exposes finish separately.
- **Options:** (A) partial structure + warnings (recommended) (B) exclude logo entirely
- **Recommended:** A
- **Blocked until GO:** YES

### DEC-PA-03 — Task rule merge owner

- **Problem:** Where do merge semantics live?
- **Options:** (A) composition service (recommended) (B) task contract composer later
- **Recommended:** A for preview aggregate
- **Blocked until GO:** NO — default A in plan

### DEC-PA-04 — Endpoint shape

- **Problem:** How to expose workspace aggregate?
- **Options:** (A) optional workspace_id on existing GET (recommended) (B) new endpoint
- **Recommended:** A
- **Blocked until GO:** NO — default A

### DEC-PA-05 — Preview without final Step 3 confirmation

- **Problem:** Allow aggregate preview before final operator confirm?
- **Recommended:** YES read-only preview; handoff remains blocked separately
- **Blocked until GO:** NO

## Forbidden scope check

- Binding persistence reopened: **NO**
- Recommendation as truth: **NO**
- ProductAggregate independent binding resolution: **NO** (uses PD)
- UI: **NO**
- Pricing / Quote / Order / Execution: **NO**
- DB / migration / seed: **NO**
- ProductSystem template changes: **NO**

## Plan review checklist

| Check | Status |
|---|---|
| One architecture selected | YES — Option A |
| No parallel binding truth | YES |
| No PA recommendation resolution | YES |
| No ProductSystem template change | YES |
| No pricing | YES |
| No DB schema | YES |
| No Quote/Order/Execution | YES |
| No UI | YES |
| Letters-only preserved | YES |
| Segment identity preserved | YES (pending DEC-PA-01 GO) |
| Material dedupe explicit | YES |
| Operation merge explicit | YES |
| Task rule owner explicit | YES |
| Provenance explicit | YES |
| Tests specific | YES |
| Rollback possible | YES |
| Owner decisions isolated | YES |

## Pending artifacts (not created in plan phase)

- `implementation-log.md` — pending
- `validation.md` — pending
- `review.md` — pending
- WorkOS implementation worklog — pending until `/ce-work`

## Implementation table (executable by /ce-work)

| Step | File/function | Change | Reason | Test |
|---|---|---|---|---|
| 1 | NEW composition service | adapter core | bounded PA workspace compose | unit |
| 2 | product_aggregate_service | orchestrator method | single call site | integration |
| 3 | product_system_aggregate router | workspace_id param | optional API | router |
| 4 | NEW pytest file | matrix coverage | gate | pytest |
| 5 | Compound validation/review/worklog | post-impl | discipline | manual |
