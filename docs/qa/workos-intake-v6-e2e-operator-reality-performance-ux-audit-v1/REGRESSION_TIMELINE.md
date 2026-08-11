# REGRESSION_TIMELINE

Branch `feat/f7i-owner-rate-activation` · HEAD `303add0f`  
Do **not** blind-revert. Many commits fixed honesty; regressions are side effects.

## Highest-confidence candidates

| Commit | Date | Behavior | Possible regression | Conf |
|--------|------|----------|---------------------|------|
| `36c499de` | 2026-08-11 | Confirm gate readiness; clear dry-run on refetch | Totals flash blank; lag feel | HIGH |
| `bf7960c9` | 2026-08-11 | FE display-only commercial_totals | No local preview → inert until dry-run | HIGH |
| `17ae316f` | 2026-08-11 | Fail-closed FX | Manual RON / some paths blocked | MED |
| `7575e2c6` / `e0a8d738` / `00496d99` | 2026-08-03 | EUR CPP / Owner rules / finish integrity | Unpublished rates fail-closed; heavier totals | HIGH |
| `2c3d5381` | 2026-07-14 | Official 7G dry-run authority | Foundational lag / no FE fallback | HIGH |
| `ab514f32` | 2026-07-20 | ACM provisional pricing | Dual money story | MED |
| `1edccf2c` | 2026-07-20 | ACM debounce 500ms | Added latency | MED |
| `fc9c21b7` + July 19 wave | 2026-07-19 | ReviewStep IA growth | Orchestration weight | MED |
| `dc0b2dfa` / `8f3d74d0` | 2026-07-16 | Hydrate/autosync/confirm checkbox | Drift / overwrite feel | HIGH |
| `6637aa2d` / `570bd229` | 2026-07-14..08 | Cant Product Truth bridges | Cant UI vs pricing lag | MED |
| `90e834ab` / `f2f69175` / `f75fdb5e` | 2026-07-09..06 | Parallel read models | UI heaviness + GETs | MED |
| `b45d3e33` | 2026-07-12 | Sold scope filters | Out-of-scope “no effect” | MED |

## Face token collapse

Not introduced by Aug 11 commercial-input alone — rooted in `intake_v4_pricing_input_service` template mapping (`oracal_641` → template `oracal_651`, top-level `vinyl`). Surfaced as Operator deception once FE stopped inventing offer math and operators trusted the rail.

## Non-recommendations

- Do not revert `2c3d5381` / `bf7960c9` / `36c499de` without replacement money authority.
- Prefer shared fixes: adapter token fidelity + critical-path GET reduction.
