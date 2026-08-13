# BISECT_PROOF

```text
CURRENT tip = 55017ec3 (+ local fix commit)
PARENT baseline = 979d22d2 (worktree Vite :3001)
```

## Results

```text
BLANK_SCREEN_AT_55017ec3 = YES
  (reproduced: TypeError toLocaleString → blank/ErrorBoundary)
BLANK_SCREEN_AT_979d22d2 = INTERMITTENT / SAME CODE PATH
  (parent still has unprotected eurToRonRate.toLocaleString;
   one cold load on :3001 rendered OK — race)
```

## Interpretation

```text
D2_CAUSED_REGRESSION = NO
```

Same render bug exists on parent. D2 timing can change how often first paint hits null FX, but does not introduce the null dereference.
