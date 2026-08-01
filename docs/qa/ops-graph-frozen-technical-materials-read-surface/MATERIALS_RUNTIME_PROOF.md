# Materials Runtime Proof — 92401

**URL:** `http://127.0.0.1:3000/execution/ops-graph?orderId=92401`  
**Viewport:** desktop browser automation (~1280-wide shell)

## API (GET `/api/v1/execution/plan/92401`)

| Check | Result |
|-------|--------|
| plan id | 13 |
| tasks | 18 |
| `material_inputs` nonempty | 0 |
| `frozen_technical_materials.entry_count` | **22** |
| quantity null count | **22** |
| title | Materiale tehnice conform comenzii |
| duplicate warning | MAT-ACM-BOND-PANEL, MAT-ORACAL-651, MAT-VOPSEA-RAL preserved |

## UI DOM

| Check | Result |
|-------|--------|
| Section present | yes |
| Count badge | `22 intrări` |
| Expanded rows | 22 |
| Qty labels | 22× `Nespecificată`, 0× `0` |
| Materials column on ops table | **absent** |
| SEQ multiset | 1–10,13,14,24–29 |
| Sessions / Actuals | 0 / 0 |

## DB after (read-only)

| Indicator | Value |
|-----------|-------|
| plan 13 ops | 18 |
| material_inputs nonempty | 0 |
| material_readiness_inputs key | absent |
| reality 92401 | 0 |
| authorize | false |

## Visual verification steps for Owner

1. Open URL above (authenticated).  
2. Confirm metrics Ops=18 · Sessions=0 · Actuals=0.  
3. Confirm section **Materiale tehnice conform comenzii** under metrics.  
4. Read semantic note (not stock/reservation/consumption).  
5. Click **Arată lista** → 22 rows; all Cantitate = Nespecificată.  
6. Confirm duplicate codes remain separate rows.  
7. Confirm ops table still has no Materials column; SEQ gaps unchanged.
