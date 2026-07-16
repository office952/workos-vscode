# Pre-Order Execution Plan Preview Boundary Contract

## 1. Status / Purpose

- Date: 2026-07-05
- Verdict: CONTRACT_V1 / DOCS_ONLY
- Runtime changes: NONE
- Implementation: NONE

Purpose: define the boundary between Product Truth / ProductDefinition / Component Dossier task metadata and a future Pre-Order Execution Plan Preview.

This contract defines:

- what a pre-order technical execution preview may read;
- what it may output;
- what it must never do;
- how it remains separate from Order Snapshot, ProductAggregate, TaskGraph, and real ExecutionPlan.

This contract does not implement a preview adapter, TaskGraph, ExecutionPlan, ProductAggregate runtime, task materialization, UI, backend runtime, frontend runtime, Pricing, Quote, Order, Execution, DB schema, seeds, or migrations.

## 2. Why This Contract Exists

`PRODUCT_COMPONENT_DOSSIER_TASK_DEPENDENCY_CONTRACT.md` is now defined.

`PRODUCT_COMPONENT_DOSSIER_TASK_DEPENDENCY_IMPLEMENTATION_READINESS_V1` says:

- ready for next docs boundary prompt: YES;
- ready for implementation direct: PARTIAL / NO;
- ready for TaskGraph / ExecutionPlan: NO.

The missing boundary is the exact meaning of Pre-Order Execution Plan Preview.

Risks this contract prevents:

- confusing preview with task materialization;
- wiring Intake V6 Confirmare directly to ExecutionPlan;
- writing ProductAggregate, TaskGraph, ExecutionPlan, or task rows too early;
- treating V6 dry-run output as shop-floor tasks;
- using partial Product Truth, fallback values, or Pricing Registry to repair missing operational truth.

This contract closes the boundary before any read-only adapter is considered.

## 3. System Boundary

### Product Truth

Product Truth is confirmed runtime truth from Intake V6 and Form System.

It may feed technical preview decisions.

It must not:

- produce real tasks;
- write ExecutionPlan;
- create order/execution;
- bypass Product Truth confirmation rules.

### ProductDefinition

ProductDefinition reads Product Truth and builds a read-only technical definition.

It may feed preview context.

It must not:

- materialize TaskGraph;
- materialize ExecutionPlan;
- invent missing fields;
- write Quote/Order/DB.

### Component Dossier

Component Dossier describes task metadata, inputs, outputs, dependencies, files, and quality gates.

It must not:

- create tasks;
- create Execution;
- write runtime DB state;
- repair Product Truth.

### Pre-Order Execution Plan Preview

Pre-Order Execution Plan Preview is:

- read-only;
- before Order;
- operational simulation / technical preview;
- derived from Product Truth + ProductDefinition + Product/Component Dossier contracts;
- not an ExecutionPlan;
- not a persisted TaskGraph;
- not a shop-floor queue.

### Order Snapshot

Order Snapshot exists after accepted offer/order flow. It freezes commercial and technical truth before downstream systems.

It remains the boundary before ProductAggregate, TaskGraph, and real ExecutionPlan.

### ProductAggregate / TaskGraph / ExecutionPlan

These are later, post-order, owner-gated systems.

They are not implemented by this contract.

## 4. Allowed Inputs For Pre-Order Preview

Allowed inputs:

- Product Truth confirmed values;
- ProductDefinition read-only result;
- Product Template metadata;
- Component Template metadata;
- Component Dossier task metadata;
- required_inputs / produced_outputs contract;
- dependency definitions;
- quality gates;
- file readiness state;
- material consumption estimate state;
- operator confirmed estimates;
- known blockers/warnings;
- commercial readiness status only as context, not as task source.

Forbidden as inputs:

- mutable Product System live values after snapshot;
- unconfirmed SVG suggestions as truth;
- fallback/hydrated values as confirmed truth;
- Pricing Registry as a Product Truth repair mechanism;
- persisted ExecutionPlan V2 state;
- Shop Floor actuals;
- Operator production actuals;
- stock movement;
- employee assignment;
- machine capacity as quote blocker.

## 5. Preview Output Model

Future conceptual output may include:

- `preview_id`;
- `source_request_id` / `intake_id`;
- `product_truth_status`;
- `product_definition_status`;
- `preview_status`;
- `task_preview_nodes`;
- `dependency_preview_edges`;
- `blockers`;
- `warnings`;
- `missing_inputs`;
- `required_files`;
- `quality_gates_preview`;
- `material_readiness_notes`;
- `exception_candidates`;
- `assembly_level_notes`;
- `logo_letters_composition_notes`;
- `no_write_guards`;
- `generated_at`;
- `source_hash`;
- `contract_version`.

A task preview node must be:

- read-only;
- not executable;
- not assignable;
- not startable/stoppable;
- not persisted as an execution task;
- not visible as shop-floor work item.

## 6. What Preview Must NOT Do

Pre-Order Preview must NOT:

- create Order;
- create ExecutionPlan;
- create ExecutionTask;
- create persisted TaskGraph;
- write ProductAggregate;
- write DB runtime state;
- reserve stock;
- consume stock;
- reserve machine capacity;
- assign employees;
- create Shop Floor tasks;
- create Operator production tasks;
- create Atelier Tablet tasks;
- create actuals;
- change Pricing;
- write Quote;
- mutate accepted snapshots;
- activate Logo root;
- activate component quote/root.

## 7. Preview Statuses

| Status | When it appears | Internal draft allowed? | Client offer allowed? | Order allowed? | Execution allowed? |
| --- | --- | --- | --- | --- | --- |
| `not_ready_missing_product_truth` | Required Product Truth is absent or partial | No | No | No | No |
| `not_ready_missing_required_inputs` | Required technical inputs are missing | No | No | No | No |
| `ready_with_warnings` | Preview can be displayed but has non-blocking warnings | Maybe, if commercial gates allow | No by itself | No | No |
| `ready_with_operator_estimates` | Operator-confirmed estimates are used | Maybe, with explicit guard | No by itself | No | No |
| `ready_for_internal_draft_preview` | Preview is coherent enough for internal review | Yes for internal review only | No by itself | No | No |
| `blocked_by_hard_dependency_gap` | Hard dependency cannot be satisfied | No | No | No | No |
| `blocked_by_file_missing` | Critical file state is missing | No | No | No | No |
| `blocked_by_unconfirmed_component` | Component truth/binding is unconfirmed | No | No | No | No |
| `blocked_by_forbidden_scope` | Requested behavior would cross forbidden boundary | No | No | No | No |
| `post_order_only_required` | Action belongs after Order Snapshot | No | No | No | No |

Execution is always NO in pre-order preview.

## 8. Dependency Preview Rules

Display rules:

- hard dependency = blocking edge;
- recommended dependency = advisory edge, warning if inverted;
- optional dependency = appears only when `applies_when` is true;
- external dependency = note only, no HUB routing;
- file dependency = blocker if critical file is missing;
- quality gate = checkpoint, not executable pre-order task.

Examples:

```text
cut_plexi_face -> apply_cant_to_face
cut_forex_back -> mount_led_on_forex_back
mount_led_on_forex_back -> wire_leds
face_with_cant + back_with_led -> assemble_body
```

Dependency preview must expose missing inputs and blocked edges without creating tasks.

## 9. Exception Preview Boundary

Preview may propose exception candidates.

Preview must not:

- approve exceptions automatically;
- change real task order;
- bypass Product Truth;
- bypass Order Snapshot;
- persist exception state.

Future exception candidate fields:

- `exception_candidate_key`;
- `dependency_key`;
- `requested_change`;
- `reason_required`;
- `approver_required`;
- `risk_note_required`;
- `preview_visibility`;
- `execution_visibility_later`.

Real approval is later and owner-gated.

## 10. Logo + Letters Preview Boundary

Current boundary:

- `TPL-VOLUMETRIC-LETTERS_v2` is current root offerable.
- `TPL-VOLUMETRIC-LOGO_v1` remains candidate/not offerable.
- Logo root/quote is not activated.

Preview may show conceptually:

- logo/shape component candidate;
- letters component;
- assembly-level notes;
- possible shared tasks;
- possible dedupe candidates.

Preview must not:

- activate Logo offerability;
- create component quote;
- create real composed root without owner GO;
- create real TaskGraph.

## 11. Commercial / Quote / Order Boundary

Pre-order technical preview is not an offer.

It does not calculate final commercial price.

Separate systems remain separate:

- CommercialPriceProposal handles client-facing price after truth completeness.
- Quote Snapshot freezes accepted commercial truth.
- Order Snapshot freezes accepted order truth.

Preview may help with:

- technical risk;
- warnings;
- internal notes;
- missing file/input visibility.

Preview must not:

- trigger accept;
- trigger convert;
- create Order;
- mutate Quote;
- mutate accepted snapshots.

## 12. UI Boundary

No UI is implemented by this contract.

Future display may be considered in:

- Intake V6 Review;
- Intake V6 Confirmare;
- Executie downstream-ready view.

If displayed, it must be read-only and include explicit copy:

```text
Previzualizare tehnica. Nu creeaza taskuri, executie, stoc sau asignari.
```

It must not:

- look like Shop Floor;
- expose Start/Stop;
- expose Assign;
- allow real drag/drop ordering;
- imply execution readiness.

## 13. API / Adapter Boundary

Possible future adapter:

```text
COMPONENT_TASK_COMPOSITION_READONLY_ADAPTER_V1
```

Principles:

- GET/read-only;
- no DB writes;
- no ExecutionPlan service calls that persist/materialize;
- no Quote/Order mutation;
- deterministic output from Product Truth + contracts;
- tests prove no writes.

This contract does not implement the adapter.

## 14. Existing Repo Mapping

| Existing Surface | Current Role | Can Feed Preview? | Risk |
| --- | --- | --- | --- |
| Intake V6 dry-run endpoints | CONFIRMED_RUNTIME_READONLY / PARTIAL diagnostics | Yes, as reference only | Not mature dependency-aware preview |
| ProductDefinition builder | CONFIRMED_IN_CODE / read-only technical definition | Yes, if from confirmed Product Truth | Must not invent missing truth |
| Product/Component Dossier | PARTIAL design-time contract | Yes, core metadata source | Authority incomplete today |
| `task_rules_json` | CONFIRMED_IN_CODE / PARTIAL | Yes, after contract normalization | Too thin today |
| `ProductAggregateTaskRule` | PARTIAL / RUNTIME_RISK | Maybe later | Too thin for DAG/exception/output model |
| `production_operations` | CONFIRMED_IN_CODE | Maybe as operation metadata | Not canonical task graph alone |
| `task_templates` | CONFIRMED_IN_CODE | Maybe as resource metadata | Parallel source risk |
| ExecutionPlan V2 preview | CONFIRMED_RUNTIME_READONLY / PARTIAL | No as pre-order source | Post-order only; linearization risk |
| `task_dependency_rules_service.py` | CONFIRMED_IN_CODE hard rules | Reference evidence only | Hardcoded, not dossier-owned |
| mini-module task metadata | PARTIAL | Maybe as hints | Must not materialize tasks now |
| ProductSystem preview | PARTIAL | Maybe as diagnostics | Runtime route not proven PASS on order 88002 |

## 15. Acceptance Criteria

This contract is PASS if it:

- defines allowed inputs;
- defines preview output;
- defines forbidden behavior;
- separates preview from real ExecutionPlan;
- separates preview from Quote/Order;
- separates preview from Shop Floor/Operator/Tablet;
- protects Logo/component root boundaries;
- prepares future read-only adapter without implementing it;
- does not modify runtime.

## 16. Next Recommended Slice

Recommended next prompt:

```text
COMPONENT_TASK_COMPOSITION_READONLY_ADAPTER_AUDIT_V1
```

Scope:

- audit whether existing data can feed a read-only adapter;
- no implementation;
- no writes;
- no TaskGraph real;
- no ExecutionPlan real.

First possible implementation after audit and owner GO:

```text
COMPONENT_TASK_COMPOSITION_READONLY_ADAPTER_V1
```

## 17. Not Ready For

Not ready for:

- TaskGraph real;
- ExecutionPlan real;
- task materialization;
- Shop Floor task execution;
- Operator task execution;
- Atelier Tablet task execution;
- Employee Mobile;
- Logo offerability;
- component quote/root;
- Pricing rewrite;
- Quote rewrite;
- Order rewrite;
- Execution rewrite.

## Source Note

Requested downstream files were not present at these exact paths:

- `docs/export/chatgpt-sources/06_DOWNSTREAM_SYSTEMS_AND_EXECUTION_ROADMAP.md`
- `docs/export/chatgpt-sources/08_FORBIDDEN_SCOPE_AND_GUARDS.md`

Equivalent recent export files were used:

- `docs/export/chatgpt-sources-workos-implementation-2026-07-04/06_DOWNSTREAM_SYSTEMS_AND_EXECUTION_ROADMAP.md`
- `docs/export/chatgpt-sources-workos-implementation-2026-07-04/08_FORBIDDEN_SCOPE_AND_GUARDS.md`
