# RUNTIME_PROOF

```text
OWNER_DEV_DB_MUTATIONS = 0
QA_CLONE = 09cea6e2-41d3-44a3-a862-add13b01af84  (IV6-7EF4715C)
OWNER_REF = 03a1da1e-003a-4139-9668-59ac6bcec812  (read-only profile)
STACK = Vite :3000 + uvicorn :8000 --reload
```

## Live HTTP (browser fetch with session token)

Alone priced-quote-dry-run:

| Run | ms | deferred | diag |
|---:|---:|:---:|:---:|
| 1 | 262 | yes | no |
| 2 | 238 | yes | no |
| 3 | 366 | yes | no |

Concurrent fan-out wall: 703 / 563 ms  
pricedQuote under fan-out: 646 / 500 ms  
logical-list under fan-out: 702 / 559 ms  

## Discrete depth change (QA clone)

| Metric | Capture 1 | Capture 2 |
|---|---:|---:|
| PRICED_QUOTE_MS | 767 | 699 |
| TOTAL_CLICK_TO_PQ_DONE_MS | 1989 | 1842 |
| production_task_gets | 0 | 0 |
| lifecycle | Ofertă actualizată | Ofertă actualizată |

## Mutations

Depth 80↔100 on QA clone only (commercial-affecting discrete save). Owner workspace not mutated.
