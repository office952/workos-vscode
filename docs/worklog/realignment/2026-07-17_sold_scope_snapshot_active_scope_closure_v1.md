# SOLD_SCOPE_SNAPSHOT_ACTIVE_SCOPE_CLOSURE_V1

**Date:** 2026-07-17  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Baseline HEAD:** `c0d5358230d5f81cb703f823238ad919c0b7fcb1`  
**Owner GO:** `GO: SOLD_SCOPE_SNAPSHOT_ACTIVE_SCOPE_CLOSURE_V1`

## Owner law

```text
INTAKE V6 DEFINES INTENT.
THE COMPILER RESOLVES SCOPE.
THE SNAPSHOT FREEZES IT.
DOWNSTREAM NEVER REINTERPRETS IT.
```

## Compound Engineering

| Phase | Result |
|-------|--------|
| 1 Parallel research | Intake freeze-path + Quote/Order/Exec traces |
| 2 Synthesis | `.compound-engineering/.../sold-scope-snapshot-closure-synthesis.md` |
| 3 Single writer | Enriched freeze + Exec primary path |
| 4 Adversarial review | GO_WITH_FIXES → Letters-only stamp, mismatch fail-closed, unknown version block |
| 5 Fix pass | Applied |
| 6 Proof + commits | Targeted pytest + Control Center Vitest |

## What shipped

1. **`QuoteSnapshotActiveScope`** embeds compiled `ActiveScopeResult` on Quote/Order/FrozenComponentScope (JSON only — no DB migration).
2. **Freeze** calls `compile_active_scope` for `TPL-VOLUMETRIC-LETTERS_v2` only; ACM remains thin `offer_scope_snapshot`.
3. **Semantic compare** helper (sorted sets, null≈[], exclude `compiled_at`).
4. **Intent mismatch** workspace vs quote_input → fail closed.
5. **Order** passthrough copies `active_scope_snapshot` (no recompile).
6. **Execution** primary = frozen `execution_scope_modules` + `composition_excluded_operations`; RETURN-CANT hardcode = `legacy_scope_fallback` only; unknown snapshot version blocks preview.
7. **Control Center** — `as.scope_snapshot` = PROVEN FOR LETTERS SLICE 1; Logo BLOCKED; ACM PARTIAL unchanged.

## Tests

- `backend/tests/test_active_scope_snapshot_freeze.py` (RETURN-CANT, FACE/BACK/LIGHTING/ELECTRICAL, passthrough, Exec enriched, legacy, workspace independence, ACM skip, unknown version, intent mismatch)
- Existing sold-scope reader + component scope suites (V6 official dry-run fixture debt remains orthogonal)

## Remaining gates

- Official V6 snapshot dry-run fixture blockers (`V6_SNAPSHOT_DRY_RUN_REPRICE_BLOCKED` / payload schema) — out of this build
- FINISH/MOUNTING sold chips — deferred
- Logo root / ACM cassette — BLOCKED / do not activate
- Task materialization — out of scope

## Verdict

`SOLD_SCOPE_SNAPSHOT_ACTIVE_SCOPE_CLOSURE_PASS` for Letters Slice 1 freeze contract.
