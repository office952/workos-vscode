# RUNTIME_PROOF

## Environment

- Stack: detached Vite `:3000` + uvicorn `:8000`
- Owner reference: `http://127.0.0.1:3000/intake-v6/03a1da1e-003a-4139-9668-59ac6bcec812/operator`
- Mutations on QA clone only: `09cea6e2-41d3-44a3-a862-add13b01af84` (`IV6-7EF4715C`)
- `OWNER_DEV_DB_MUTATIONS = 0`

## Verified

| Case | Result |
|---|---|
| Face 8500 → 651 → 641 → 8500 | Persisted; lifecycle visible; 1 PUT per intent / coalesced burst |
| Depth 30→60→80→100 rapid | Final **100**; 1 PUT |
| Cant stock→Oracal / Oracal→RAL | Not required for latency proof; selectors share same short policy |
| Lifecycle “Se salvează…” + stale | CDP: `phase=pending_save`, `stale=true` |
| Lifecycle “Ofertă actualizată” | Seen after successful user-driven reprice |
| GET diet | production/task GETs = 0 |

## Screenshots

- `screenshots/step2_offer_rail_after_face_641.png`
- `screenshots/step2_after_depth_change.png`

## Network

- `network/discrete_selector_timings.json`