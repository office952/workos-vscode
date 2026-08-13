# PERFORMANCE_BEFORE_AFTER

## Official numbers (required)

| Metric | Before | After |
|---|---:|---:|
| PRICED_QUOTE_BEFORE_MS (fan-out / alone) | 1535–1877 / 816–990 | — |
| PRICED_QUOTE_AFTER_MS (fan-out / alone) | — | **699–767 / 238–366** |
| CLICK_TO_CURRENT_PRICE_BEFORE_MS | 1923–2089 | — |
| CLICK_TO_CURRENT_PRICE_AFTER_MS | — | **1842–1989** (PQ done; see note) |
| SQL_QUERY_COUNT_BEFORE | 114 | — |
| SQL_QUERY_COUNT_AFTER | — | **61** |

## Target check

| Target | Alone after | Fan-out after |
|---|---|---|
| &lt;750 ms preferred | **PASS** (238–366) | borderline / PASS (500–767) |
| &lt;1000 ms acceptable | **PASS** | **PASS** |
| &gt;1200 ms warning | no | no |

## Notes

1. In-process service work halved (~84 → ~42 ms); HTTP alone dropped ~3× vs prior alone baseline.
2. End-to-end click→current still ~1.8–2.0 s on this capture because sibling GETs + `logical-list-read-model` (nested dry-run) still fan out; SELECT→PUT start measured ~1.0 s under dual-PUT Strict Mode noise (policy still 100 ms — not changed).
3. Residual next lever (not this GO): stop nested dry-run inside logical-list, or defer logical-list off official money path.

## Config matrix (service path)

All measured configs share the same stage shape: CPP dominates after OPTION B; MB/EIC absent on default path.

| Config | Context | total_ms (in-proc after) | cpp_ms | eic_ms | mb_ms |
|---|---|---:|---:|---:|---:|
| A/H blocked incomplete | owner + QA clone | ~41–48 | ~38–43 | 0 | 0 |
| C Oracal 8500 face | QA clone HTTP alone | 238–366 | (in HTTP) | deferred | deferred |
| D/E depth 80↔100 | QA clone click | PQ 699–767 | (in HTTP) | deferred | deferred |
| B Oracal 641 / F mixed / G lighting | not separately mutated this GO | same code path | — | deferred | deferred |
