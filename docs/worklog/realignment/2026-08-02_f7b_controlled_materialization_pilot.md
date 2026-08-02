# 2026-08-02 — F7B Controlled materialization pilot

## Status

```text
F7B = BLOCKED BEFORE MATERIALIZATION
POST = NOT EXECUTED
PUSH = NOT EXECUTED
```

## Identity

HEAD `2ef99d6b` · remote `0c8a76cd` · ahead 6 · stash intact.

## Blockers

1. Original F7A.1 fixture not in durable `dev.db` (pytest-ephemeral only).
2. Recreated `880811`/`22` for preflight; STOP before POST per Owner rule.
3. Runtime DEC-009 next_dry still `973019`/`21` — HTTP POST on 880811 would 422; POST on 973019 is forbidden (protected baseline).
4. Retarget requires production gate change / restart — out of F7B pilot commit scope.

## Preflight artifact

`docs/qa/workos-f7b-controlled-product-linked-materialization-pilot-v1/`

## Next Owner GO

Accept fixture `880811`/`22` + authorize next_dry retarget + restart → then F7B POST×2 only.
