# Authorization matrix (F4)

| Role | Read movements | Record issue/return/scrap | Raw valuation |
|---|---:|---:|---:|
| admin / manager | Yes | Yes (`inventory.material_actual.write`) | Yes |
| operator | Yes (`inventory.view_movements`) | No | No (API strips snapshots) |
| sales / unknown | No / fail-closed | No | No |

Browser-supplied identity is not trusted; FastAPI `get_current_user` + `require_permission`.
