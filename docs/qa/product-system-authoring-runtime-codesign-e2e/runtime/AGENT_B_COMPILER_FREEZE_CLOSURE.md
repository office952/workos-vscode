# Agent B — Compiler & Freeze Closure (CP-B/C/D/E)

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `705a701a6e48f2bee1f638e44031f32f6d19d751` |
| Foundation | `ef349ef`, `136f38b`, `70b2fdf`, `6a1c1d1` |

## Checkpoint verdicts

| CP | Verdict | Evidence |
|----|---------|----------|
| CP-B Same revision PD/Agg/Qty | **PARTIAL** | Pin preference shared (PD+Agg `apply_pinned_bags`); PD emits `product_truth_job_revision`; Agg/Qty do **not** surface same revision fields |
| CP-C EIC → Qty Builder | **PARTIAL** | Qty Builder = `letter_group_instance_authority` / `letters_commercial_measurement`; EIC has **no** import; parallel `_extract_quantity`; no pricing reopen |
| CP-D Freeze from pin | **PASS** | Gate + cases: unconfirmed/stale/wrong hash/accepted terminal/confirmed clears PT gate |
| CP-E Order + EP provenance | **PASS** | Order copies revision/hash + `no_live_workspace_reread`; EP from OrderSnapshotV2 only; no materialization |

## Evidence commands

```text
cd backend
.\.venv\Scripts\python.exe -m pytest tests/test_product_truth_job_confirm_v1.py tests/test_active_scope_snapshot_freeze.py -q
→ 29 passed

.\.venv\Scripts\python.exe -m pytest tests/test_execution_preview_from_frozen_build4c.py -q
→ 18 passed

.\.venv\Scripts\python.exe ..\docs\qa\product-system-authoring-runtime-codesign-e2e\runtime\compiler_freeze_closure_proof.py
→ PROOF_OK → runtime/compiler_freeze_closure_evidence.json
```

## Freeze gate cases

| Case | Result | Where |
|------|--------|-------|
| Unconfirmed | BLOCKED `V6_SNAPSHOT_PRODUCT_TRUTH_NOT_CONFIRMED` | `test_v6_freeze_blocks_without_confirmed_product_truth` |
| Stale after edit | BLOCKED + `stale_after_edit` | `test_v6_freeze_blocks_when_product_truth_stale` |
| Wrong content hash | 409 `content_hash_mismatch` | `test_content_hash_mismatch_409` |
| Accepted quote | BLOCKED `V6_SNAPSHOT_QUOTE_TERMINAL` | `test_v6_freeze_blocks_accepted_quote_terminal` |
| Confirmed pin | PT gate cleared (dry-run may still block) | `test_v6_freeze_passes_product_truth_gate_when_confirmed` |
| Live draft drift | pin restored via `apply_pinned_bags_onto_payload` | `test_apply_pinned_bags_ignores_live_draft_drift` |

## Failure classifications observed

| Item | Class |
|------|-------|
| `test_quote_snapshot_component_scope` create_v6 (2 fails) | **STALE_TEST** — seed lacks ConfirmJobProductTruth after `70b2fdf`; not on allowlist |
| `test_product_e2e_readiness_v1` collector ImportError | **DIRTY_TREE_INTERACTION** — WT edits on readiness service (other agent); untouched |
| EIC ≠ Qty Builder | **PREEXISTING_RELEVANT** — known PARTIAL; no CostEngine/pricing change |
| Agg/Qty missing revision provenance fields | **PREEXISTING_RELEVANT** / **NEEDS_OWNER_DECISION** — fix would touch non-allowlist compiler services |

## Files changed (allowlist only)

- `backend/tests/test_product_truth_job_confirm_v1.py`
- `backend/tests/test_active_scope_snapshot_freeze.py`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/SNAPSHOT_CLASSIFICATION.md`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/compiler_freeze_closure_proof.py`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/compiler_freeze_closure_evidence.json`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/AGENT_B_COMPILER_FREEZE_CLOSURE.md`

No ProductSystem.tsx / App.tsx. No formula/CostEngine/Execution materialization. No push/PR/reset/stash.
