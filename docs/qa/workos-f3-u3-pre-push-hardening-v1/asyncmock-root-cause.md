# AsyncMock root cause

## Reproduction

```text
pytest backend/tests/test_profitability_actual_read_model.py::test_missing_labor_and_materials_not_zero
```

Warning: `RuntimeWarning: coroutine was never awaited` from AsyncMock used as `db`.

## Call path

F3 profitability path awaited:

```text
await self.db.execute(select(ActualLaborCostLine|ExecutionJobClosure)...)
result.scalars().all() / scalar_one_or_none()
```

Bare `AsyncMock()` as session made `.all()` return an unawaited coroutine. A broad `except (AttributeError, TypeError)` then set `closure = None`, hiding the contract break without awaiting.

## Production risk

Closure lookup is async. A wrong mock interface is a test defect; the try/except could also swallow real interface bugs. Fail-closed composition remains: missing labor/material/closure ⇒ unavailable, never zero.

## Correction

1. Extract awaited `_load_actual_cost_facts`.
2. Remove the broad try/except silence path.
3. Test monkeypatches `_load_actual_cost_facts` with an `AsyncMock(return_value=(...,))` so await completes.

## Proof

```text
pytest tests/test_profitability_actual_read_model.py -W error::RuntimeWarning
→ 1 passed
```

(`-W error` alone fails on pre-existing Starlette/httpx TestClient deprecation at conftest import — unrelated to F3.)
