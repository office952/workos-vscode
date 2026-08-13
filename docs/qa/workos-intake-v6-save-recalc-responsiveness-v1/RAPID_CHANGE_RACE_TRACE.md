# RAPID_CHANGE_RACE_TRACE

## Existing protection (reused)

| Guard | Role |
|---|---|
| Autosave timer reset | Coalesces rapid discrete edits inside 100 ms window |
| `autosaveRequestRef` | Only latest PUT clears `saving` / applies hydrate |
| `localRevisionRef` | Skip applying server form if local edits during flight |
| GET `cancelled` flags | Drop stale pricedQuote / breakdown applies |
| Policy latch reset on success | Returns to short after persist |

## Runtime proof (QA clone)

| Sequence | Interval | PUTs | Final persisted UI | production/task GETs |
|---|---:|---:|---|---:|
| Depth 30→60→80→100 | 40 ms | **1** | **100** | 0 |
| Face 641→651→8500 | 40 ms | **1** | **oracal_8500** | 0 |

Older responses cannot overwrite newer selection when revision advances during flight; coalescing prevents write storms for bursty discrete changes.