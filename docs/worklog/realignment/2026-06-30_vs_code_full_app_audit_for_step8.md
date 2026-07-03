# VS Code Full App Audit For Step 8 — 2026-06-30

## Status

**PARTIAL**

Audit-only pass completed on repo truth from `C:\Users\offic\Desktop\workos-active`, with **no code changes** and **no app start** by this agent. Root cause is clear in code. Direct DB/pytest execution from this session was blocked by terminal/task tooling output capture, so executable results below are split between:

- direct source audit performed in this session;
- previously recorded same-day worklogs already present in the repo;
- git/ref inspection performed in this session.

## Scope

Full VS Code audit for Step 8 readiness blockage only:

- 7G CommercialPriceProposal
- 7H EstimatedInternalCost
- Step 8 Quote Snapshot V2 freeze/readiness/accept boundary
- Accept/convert boundary
- Pricing registry and dev bridge state

Out of scope and not touched:

- Step 9 implementation
- ExecutionPlan/task graph changes
- CostEngine rewrite
- QuoteOrchestrator rewrite
- `/price`
- migrations / Alembic / seed / DB reset
- UI work
- repo `C:\Users\offic\workos`

## Architecture Docs Read

Read back before conclusions:

- `docs/architecture/realignment/README.md`
- `docs/architecture/realignment/00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md`
- `docs/architecture/realignment/01_INTAKE_V6_PRODUCT_TRUTH.md`
- `docs/architecture/realignment/02_PRODUCT_SYSTEM_TEMPLATE_CONTRACT.md`
- `docs/architecture/realignment/03_PRODUCT_DEFINITION_COMPILER.md`
- `docs/architecture/realignment/04_PRODUCT_AGGREGATE_TECHNICAL_GRAPH.md`
- `docs/architecture/realignment/05_COMMERCIAL_PRICE_PROPOSAL.md`
- `docs/architecture/realignment/06_ESTIMATED_INTERNAL_COST.md`
- `docs/architecture/realignment/07_COST_ENGINE_REALIGNMENT.md`
- `docs/architecture/realignment/08_PRICING_REGISTRY_SEPARATION.md`
- `docs/architecture/realignment/09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md`
- `docs/architecture/realignment/10_EXECUTION_PLAN_TASK_GRAPH.md`
- `docs/architecture/realignment/16_PROFITABILITY_ANALYSIS.md`
- `docs/architecture/realignment/17_UI_NAVIGATION_AND_LABELING_POLICY.md`
- `docs/architecture/realignment/18_GOVERNANCE_SETTINGS_POLICY.md`
- `docs/architecture/realignment/19_LEGACY_DEAD_PIECES_CLEANUP_POLICY.md`
- `docs/architecture/realignment/20_ROADMAP_STEPS_7G_TO_12.md`

Confirmed from architecture contract:

- CommercialPriceProposal and EstimatedInternalCost are separate systems.
- Commercial price must not be calculated as hourly pricing.
- CostEngine and QuoteOrchestrator are out of path for Step 8.
- `/price` is forbidden for this audit and forbidden for Step 8 path.
- Step 8 stops at quote snapshot / accept / order snapshot boundary.
- Step 9 must not continue without clear live accept/convert validation.
- ExecutionPlan / execution_tasks are out of scope for this audit.

## Git Preflight

Initial preflight in this session:

- Branch: `feature/step-7g-commercial-price-proposal`
- `git log` at start showed HEAD `c8d86d1` (`fix(step8): unblock dev snapshot readiness`)
- Expected user baseline `1ee3cd7` was already behind current repo state at audit start
- No code modifications were present at start
- Pre-existing untracked worklogs existed in `docs/worklog/realignment/`

Additional repo-truth finding during this audit:

- `.git` ref inspection later showed branch advanced again to `70d004d4c5c2564fa52389e9c1558586d4569d0d`
- Reflog shows the move `c8d86d1 -> 70d004d` as a docs-only commit: `docs(step8): record live qa after readiness unblock`

Interpretation:

- audit started after `1ee3cd7`
- code truth inspected here is at least `c8d86d1`
- branch tip advanced to `70d004d` during/just before this audit with additional Step 8 documentation, not code changes

## Files Audited

Primary code/files audited directly:

- `backend/services/commercial_price_proposal_service.py`
- `backend/services/estimated_internal_cost_service.py`
- `backend/services/quote_snapshot_v2_service.py`
- `backend/services/quote_snapshot_v2_accept_gate_service.py`
- `backend/services/order_snapshot_v2_convert_service.py`
- `backend/services/intake_v6_quote_to_order_service.py`
- `backend/data/commercial_rules_volumetric_v2.py`
- `backend/data/internal_cost_rules_volumetric_v2.py`
- `backend/data/dev_volumetric_v2_registry_bridge.py`
- `backend/models/quote_snapshot_v2.py`
- `backend/schemas/quote_snapshot_v2.py`
- `backend/routers/quote_snapshot_v2.py`
- `backend/routers/orders.py`
- `backend/routers/quotes.py`
- `backend/tests/test_commercial_price_proposal_preview.py`
- `backend/tests/test_estimated_internal_cost_preview.py`
- `backend/tests/test_quote_snapshot_v2.py`
- `backend/tests/test_quote_snapshot_v2_accept_gate.py`
- `backend/tests/test_order_snapshot_v2_convert.py`
- `backend/tests/test_orders_update_immutability.py`

Secondary runtime evidence audited read-only from repo worklogs:

- `docs/worklog/realignment/2026-06-30_step8_live_accept_convert_qa.md`
- `docs/worklog/realignment/2026-06-30_step8_dev_registry_readiness_unblock.md`
- `docs/worklog/realignment/2026-06-30_step8_live_qa_after_readiness_unblock.md`

## DB Read-Only Findings

Direct SQLite execution requested by audit was attempted from this session but terminal/task output could not be captured reliably by tooling. No DB writes were performed.

Latest repo-recorded read-only findings available in audited worklogs:

### Before readiness unblock live QA (`docs/worklog/realignment/2026-06-30_step8_live_accept_convert_qa.md`)

- `intake_v6_workspaces`: 67
- `quote_snapshots_v2`: 1
- `quotes`: 4
- `quotes` with `accepted_snapshot_v2_id`: 0
- `orders`: 2
- `execution_plan`: 1
- `execution_tasks`: table absent in dev SQLite schema

### After readiness unblock stale-backend check (`docs/worklog/realignment/2026-06-30_step8_live_qa_after_readiness_unblock.md`)

- `intake_v6_workspaces`: 67
- `quote_snapshots_v2`: 1
- `quotes`: 4
- `quotes` with `accepted_snapshot_v2_id`: 0
- `orders`: 2
- `execution_plan`: 1

Interpretation:

- there is no evidence in repo worklogs of live accept having run successfully;
- there is no evidence of new live Step 8 snapshot persistence beyond the pre-existing single snapshot row;
- Step 9 remains correctly blocked by missing live accept/convert progression.

## Tests Run

Direct command execution from this session was attempted for:

```powershell
cd C:\Users\offic\Desktop\workos-active\backend
.\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_convert.py tests/test_orders_update_immutability.py -q
```

Tooling limitation in this session:

- terminal output capture returned empty output even for trivial commands;
- VS Code task execution could not be established because no workspace was open and command/task tooling failed to attach cleanly.

Therefore, executable evidence used for this audit comes from same-day worklogs already committed in the repo:

- `2026-06-30_step8_live_accept_convert_qa.md`: **97 passed** for Step 8 accept/convert suite
- `2026-06-30_step8_dev_registry_readiness_unblock.md`: **122 passed** after dev bridge + flatten fixes

Audit interpretation of test truth:

- pytest validates persist/accept/convert logic in isolated test DB and controlled fixtures;
- pytest does **not** prove default live payload readiness;
- pytest uses test-only helpers such as `allow_freeze_readiness` and direct snapshot insertion.

## Root Cause Summary

### Short answer

`blocked_snapshot_conflict` is emitted by production code in `compute_readiness()` when **both** 7G and 7H return `status="blocked"` at the same time. Pytest can still validate persist/accept/convert because tests either:

- monkeypatch readiness with `allow_freeze_readiness`; or
- insert persisted snapshots directly into the test DB.

So the mismatch is real and expected: live freeze is guarded by readiness, while tests can bypass or seed around that guard to validate the downstream contract.

### Current repo truth

There are two different runtime truths in the current branch history:

1. Older live QA truth on `0b33f0b` / `1ee3cd7`:
   - default `_full_quote_input()` payload kept **both** 7G and 7H blocked;
   - freeze returned `blocked_snapshot_conflict` live;
   - accept/convert were not run live.

2. Newer code truth from `c8d86d1` onward:
   - Step 8 dev bridge was added for 7H plus nested payload flattening;
   - with the **paper sablon** QA payload, 7H should degrade from `blocked` to `partial` or `ready`;
   - 7G still remains blocked by design because `debitare_spate` commercial basis is still owner-pending;
   - expected combined readiness becomes `partial_with_owner_decisions`, not `blocked_snapshot_conflict`.

3. Newer live QA truth recorded after `c8d86d1`:
   - backend HTTP still returned old `blocked_snapshot_conflict` for paper payload;
   - the repo worklog explicitly classified that as **stale backend process**, not code truth.

### Audit conclusion on the user’s question

Live freeze remains `blocked_snapshot_conflict` for one of two reasons, depending on which exact live situation is being referenced:

- default/full live payload still activates dual critical blockers on both 7G and 7H; or
- backend process is stale and has not loaded the readiness-unblock code introduced at `c8d86d1`.

In both cases, pytest passing is not contradictory, because test fixtures are intentionally narrower and can bypass readiness persistence conditions.

## 7G CommercialPriceProposal Finding

### Status

`blocked` on the default/full volumetric payload.

### What blocks 7G

From `backend/services/commercial_price_proposal_service.py` and `backend/data/commercial_rules_volumetric_v2.py`:

- critical geometry missing would block 7G
- `COMMERCIAL_RULE_MISSING` for an active critical module would block 7G
- `COMMERCIAL_BASIS_UNKNOWN` blocks when a critical line has `basis_type="unknown"`
- critical owner decisions also force `blocked`

Current critical owner decisions/rules:

- `DEBITARE_SPATE_BASIS_ML_VS_M2`
- `SABLON_FOREX_COMMERCIAL_PRICE`

### Missing commercial rules / owner decisions

- back CNC commercial basis for `debitare_spate` is still unresolved: ml vs m2
- forex mounting template commercial price is still owner-pending
- packaging and site mounting are still optional/future owner decisions, but those do not drive the main freeze blocker

### What live payload produces the blockage

The default test/live-style payload `_full_quote_input()` uses:

- `mounting_template_material_type = "forex"`
- `debitare_spate` active

That combination triggers both:

- `COMMERCIAL_BASIS_UNKNOWN` for back cutting
- `SABLON_FOREX_COMMERCIAL_PRICE` critical owner decision

### Is the 7G block correct or a bug?

For the default/full payload, the 7G block is **correct by current contract**, not a bug.

### Any hourly commercial pricing?

No live 7G implementation audited here uses hourly commercial pricing. Code explicitly scans and blocks hourly contamination. No HIGH RISK hourly commercial path was found in Step 8 preview code.

### Minimum completion for unblocked freeze

Minimal 7G completion is **not** full 7I. It is:

- use the paper sablon QA payload to avoid the forex critical commercial owner blocker; and/or
- owner decision for `debitare_spate` commercial basis; and/or
- owner decision for forex sablon commercial rule if forex must stay in the QA payload.

## 7H EstimatedInternalCost Finding

### Status

- historically `blocked` on live/default payload;
- in current code, expected to be `partial` or `ready` for the paper sablon QA payload after the dev bridge changes.

### What blocks 7H

From `backend/services/estimated_internal_cost_service.py`:

- `INTERNAL_GEOMETRY_MISSING`
- `INTERNAL_MATERIAL_COST_MISSING`
- `INTERNAL_OPERATION_BASIS_UNKNOWN`
- `INTERNAL_OPERATION_RULE_MISSING`
- critical owner decisions `INTERNAL_DEBITARE_SPATE_ML_VS_M2` or `INTERNAL_SABLON_FOREX_COST`

### What was missing

From audited code and repo worklog `2026-06-30_step8_dev_registry_readiness_unblock.md`:

- missing inventory unit_cost coverage for required materials in dev
- nested `finish_setup` / `quote_geometry` flattening bug for BOM variant resolution
- no internal dev bridge operation costs for several operations
- internal back-cut basis had to be temporarily bridged as m2 for dev QA

### Registry, mapping, payload, or bug?

This is a mixed case:

- registry/dev data gap: missing material unit_cost values in dev
- mapping bug: nested IV6 payload not flattened correctly for BOM variant resolution
- payload sensitivity: forex sablon keeps a critical internal owner-decision blocker active

### Separate from commercial?

Confirmed. 7H remains separate from 7G in code, schema, notes, provenance, tests, and readiness composition.

### Minimum completion for unblocked freeze

Minimal completion is already partially implemented in current code:

- dev registry bridge for missing material costs
- dev internal operation costs
- nested payload flattening

What still matters operationally:

- use paper sablon QA payload for dev live QA; or
- make owner decision for internal forex sablon cost if forex must remain in the QA payload.

## Step 8 Quote Snapshot Finding

### Where `blocked_snapshot_conflict` is calculated

`backend/services/quote_snapshot_v2_service.py` in `compute_readiness()`.

### Exact meaning

It means:

- `commercial.status == "blocked"`
- `internal.status == "blocked"`

at the same time.

### When freeze writes `quote_snapshots_v2`

Freeze persists only when all of the following are true:

- persistence table available
- at least one of `quote_id` or `workspace_id` is supplied
- readiness is **not** in hard-blocked set
- readiness is one of `ready_for_owner_review` or `partial_with_owner_decisions`

### When freeze fail-closes

Freeze returns `persist_status="blocked"` and does not write when:

- persistence unavailable
- no `quote_id` and no `workspace_id`
- readiness in hard blocked set, including `blocked_snapshot_conflict`
- readiness outside allowed persist values

### Acceptable readiness values

- `ready_for_owner_review`
- `partial_with_owner_decisions`

### Test-only vs production behavior

Production behavior:

- freeze honors real `compute_readiness`
- accept requires frozen persisted snapshot with valid hash and allowed readiness
- convert requires `quotes.accepted_snapshot_v2_id`

Test-only behavior:

- `allow_freeze_readiness` monkeypatch forces allowed readiness for persistence tests
- `_insert_snapshot()` inserts frozen snapshot rows directly into test DB

### Risk of wrong persistence

Low-to-medium, but controlled:

- persistence is guarded by readiness and identity requirements
- existing tests verify no order/plan/task side effects on freeze
- main practical risk is misunderstanding test-only persistence as live readiness parity

## Accept / Convert Finding

### `accepted_snapshot_v2_id`

Confirmed: `accept_v6_quote()` updates `quotes.accepted_snapshot_v2_id` to the resolved frozen snapshot id.

### Convert requires accepted snapshot

Confirmed: `convert_accepted_quote_snapshot_v2_to_order()` hard-fails with `MISSING_ACCEPTED_SNAPSHOT_V2` when the quote has no accepted snapshot FK.

### Convert creates only Order Snapshot V2

Confirmed for V2 convert path:

- creates locked order
- persists `snapshot_v2_json`
- sets `execution_plan_created=False`
- does not create execution plan in this convert step

### Convert creates execution_plan/task?

No. Code and tests both assert this must remain false.

### Convert uses `/price`, CE, or QO?

No. The V2 convert service explicitly documents and tests that it does not call `/price`, CostEngine, or QuoteOrchestrator.

### What remains live-unvalidated

- successful live freeze persistence on a fresh backend process with allowed payload
- successful live accept writing `accepted_snapshot_v2_id`
- successful live convert on a dedicated safe IV6 quote/workspace

## Pricing Registry / Dev Data Finding

### What exists now

In current repo truth:

- local commercial rules catalog for `TPL-VOLUMETRIC-LETTERS_v2`
- local internal cost rules catalog for `TPL-VOLUMETRIC-LETTERS_v2`
- dev material registry bridge in `backend/data/dev_volumetric_v2_registry_bridge.py`
- dev internal operation bridge costs in `backend/data/internal_cost_rules_volumetric_v2.py`

### What is missing for `TPL-VOLUMETRIC-LETTERS_v2`

- owner-confirmed commercial basis for back cutting
- owner-confirmed forex sablon commercial rule if that payload path is needed
- owner-confirmed internal forex sablon rule if that payload path is needed
- full 7I registry separation and formalization

### Is 7I full needed now?

No. Step 8 does **not** need full 7I to continue on a safe dev path.

### Pricing UI misleading risk

Yes, but not the immediate blocker. Architecture docs correctly flag unified pricing surfaces and hourly labels as misleading. That remains Step 11/7I territory, not the next Step 8 action.

### Dead / confusing pieces

Yes:

- legacy `/price` path and QuoteOrchestrator commercial transform remain frozen but still present
- unified pricing registry mental model is still misleading
- older runtime worklogs can mislead if read without noting the later readiness-unblock code/docs

### Minimal safe dev unblock for one IV6 quote

Minimal safe unblock is:

- fresh backend process on current branch tip
- dedicated IV6 quote/workspace identity
- paper sablon QA payload
- existing pricing review + owner approval linkage on the quote

That is smaller and safer than Step 7I full, UI work, or CE/QO changes.

## Recommended Next Fix

### Primary recommendation

**Operational live-validation task, not engine rewrite:**

Manually restart the backend outside this audit, then re-run Step 8 live QA on a dedicated IV6 quote/workspace using the paper sablon payload plus explicit `workspace_id` or `quote_id`.

Why this is the correct next move:

- current code already contains a targeted Step 8 readiness unblock for 7H in local/dev/test
- live `blocked_snapshot_conflict` after `c8d86d1` is already documented as stale-backend behavior for the paper payload
- default/full payload still legitimately blocks on unresolved commercial/internal owner decisions, especially forex sablon and back-cut basis
- Step 8 should be validated first on the narrow safe payload before any larger pricing/registry work

If implementation is later required, the most likely files are:

- `backend/services/quote_snapshot_v2_service.py`
- `backend/services/commercial_price_proposal_service.py`
- `backend/services/estimated_internal_cost_service.py`

but only **after** fresh-backend live re-check proves the current code still blocks on the paper payload.

### Risk level

**MEDIUM**

Reason:

- code path is narrow and already partially de-risked by tests and same-day worklogs;
- but live runtime parity, payload choice, and quote linkage gates still need explicit confirmation;
- the bigger risk is moving prematurely into Step 9 or 7I/CE/QO changes based on stale runtime signals.

## What Not To Do

Do not do any of the following now:

- do not start Step 9
- do not do full 7I registry separation first
- do not work on Pricing UI
- do not rewrite CostEngine
- do not rewrite QuoteOrchestrator
- do not use `/price`
- do not global-seed dev data
- do not do broad docs sync unless official truth changes again

## No-Side-Effects Confirmation

Confirmed for this audit session:

- no code changes
- no DB write
- no migration
- no Alembic upgrade/stamp
- no seed
- no accept/convert live
- no order creation
- no execution_plan creation
- no execution task creation
- no UI changes
- no push
- no work in `C:\Users\offic\workos`
- app/backend/frontend were **not started** by this agent

## Tooling Limitation Note

The only execution blocker in this session was tooling output capture:

- `run_in_terminal` returned empty output even for trivial commands
- workspace/task runner tooling could not be attached cleanly from a no-workspace session

This blocked direct reproduction of the requested SQLite and pytest commands from this session, but did **not** block source audit, git/ref inspection, or worklog-based runtime truth comparison.

## Roadmap Awareness Checkpoint

- Position: VS Code audit for Step 8 unblock only
- Step 8 can continue with a minimal operational re-validation path on current code
- Step 9 remains blocked until live accept + convert are clear on safe data
- 7I / 10 / 11 remain downstream and should not be pulled forward

**Cât sunt în direcția stabilită: 86/100%**
