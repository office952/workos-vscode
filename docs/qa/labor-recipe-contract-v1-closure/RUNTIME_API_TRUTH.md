# LABOR_RECIPE_CONTRACT_V1_CLOSURE — Runtime Truth

| Field | Value |
|-------|--------|
| Kickoff HEAD | `1518b6ac` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Proof port | `127.0.0.1:8020` |

## Ports

| Port | Owning process | HTTP | Notes |
|------|----------------|------|-------|
| 8000 | Ghost PIDs 16652/18484/24828/31936 (DEAD) | docs may 200; `/templates/.../pricing` **404** | environment |
| 8020 | `python -m uvicorn main:app --port 8020` (alive) | pricing 200, schema 1.1.0 | proof |
| 3000 | Vite | — | set `BACKEND_PORT=8020` |

## Kickoff API (8020)

| Template | labor_summary |
|----------|---------------|
| Volum Aluminiu | total 2 |
| VL | total 12 |
| ACM | total 3; acm 5/0; treatment=false |
