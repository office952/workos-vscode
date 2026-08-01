# DEAD_PIECES_CHECK

| Piece | Class | Note |
|-------|-------|------|
| PA materials + freeze apply | ACTIVE_CORRECT | new contract path |
| Ops-graph frozen materials RO | ACTIVE_CORRECT | v2 status labels |
| Exact-key material dedupe | ACTIVE_CORRECT | not code-only |
| Null→Nespecificată / status labels | ACTIVE_CORRECT | |
| EIC `_estimate_material_quantity` | ACTIVE_MISLEADING if reused as freeze qty | kept out of contract path |
| Template seed `quantity: 0` | LEGACY_STILL_CALLED | discarded at aggregate compile (not copied) |
| Unregistered return_wrap/paint formulas | ACTIVE_CORRECT as source_missing | not invented |
| Inventory stock as BOM qty | ACTIVE_MISLEADING if used | rejected Model E |
| Pricing as technical qty | ACTIVE_MISLEADING if used | rejected |
| Global dedupe by material_code | DEAD_CANDIDATE | not introduced |
| Docs treating all null as identical | ACTIVE_MISLEADING historically | superseded by status enum |
| material_readiness_inputs persist | DEAD_CANDIDATE for 92401 | unused |
| Parallel material requirement DTO | not created | avoided |

No deletions in this build.
