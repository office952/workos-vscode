# PERFORMANCE_BEFORE_AFTER

## Fan-out

| Metric | Before | After |
|---|---|---|
| face_finish domain groups | 8 | **4** |
| Production GETs on configure remount | present | **0** (drawer closed) |
| pricedQuote still refreshed | Y | Y |
| Debounce | 700/1400 | unchanged |

## Case matrix (domain-derived + audit before)

| Case | BEFORE_GET_COUNT (domain) | AFTER_GET_COUNT (domain) | MONEY_CORRECT | STALE_FLASH |
|---|---|---|---|---|
| A none→641 | 8 | 4 (+logical-list) | Slice 0 locked | pendingSave marks rail |
| B 641→651 | 8 | 4 | Y | pendingSave |
| C 651→8500 | 8 | 4 | Y | pendingSave |
| D cant stock→Oracal | 8 | 4 | Y | pendingSave |
| E cant Oracal→RAL | 8 | 4 | Y | pendingSave |
| F back option | 8 | 4 | Y (bevel commercial honesty = later slice) | pendingSave |
| G lighting | 8 | 4 | Y | pendingSave |
| H commercial markup | 2 | 2 | Y | pendingSave |

`OWNER_DEV_DB_MUTATIONS = 0` — no live selector mutations on Owner workspace; AFTER domain counts proven by unit tests + Step 2 remount network capture.

## Latency model

```text
Before: debounce + PUT + 8-group fan-out (incl. production) → often >1.5 s
After:  debounce + PUT + 4 offer groups (+ logical-list) → production removed from critical path
```

pricedQuote alone ~300–700 ms; removing 4–5 production GETs reduces contention and wasted work.
