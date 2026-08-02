# F7A — Tests

## Executed (green)

```text
pytest tests/test_f7a_product_linked_task_contract_enrichment.py
      tests/test_golden_pilot_task_contract_dag.py
      tests/test_step9_materialization_audit.py
      tests/test_execution_plan_v2_preview.py
      tests/test_dec009_materialize_gate.py
      tests/test_quote_snapshot_v2_accept_gate.py
→ 78+ passed (core EP/snapshot/F7A set)

pytest tests/test_product_process_live_aggregate_bridge.py
      tests/test_product_aggregate_dossier_gating.py
      tests/test_execution_plan_v2_persist.py -k "not test_no_migration_needed_for_step_9_3_3"
→ 74 passed, 1 deselected
```

Final focused re-run after DEC-007 linear-fallback removal:

```text
64 passed (f7a + golden dag + step9 audit + preview + dec009 gate)
```

## Not executed

- Full backend suite
- Frontend / TypeScript (`tsc`) — no FE files touched
- Live HTTP server smoke against running uvicorn
- Browser / U7 visual re-audit

## Preexisting failure observed (not F7A)

```text
tests/test_execution_plan_v2_persist.py::test_no_migration_needed_for_step_9_3_3
```

Asserts migration tip still includes `s56_…`; tip has advanced to `s57+`. Deselected for F7A gate; not caused by F7A diff.

## New / updated tests

- `test_f7a_product_linked_task_contract_enrichment.py` — DEC-001…007 + DEC-009 chain
- `test_dag_no_universal_linear_fallback_when_deps_absent` in golden pilot DAG suite
