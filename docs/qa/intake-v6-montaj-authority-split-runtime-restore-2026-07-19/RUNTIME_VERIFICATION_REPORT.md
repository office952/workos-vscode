# RUNTIME VERIFICATION REPORT

**Commit under test:** `184b9dc`  
**Topology after restore:** FE `:3000` → `BACKEND_PORT=8003` → BE `:8003`  
**Workspace:** `3fb7a2b5-ec60-48e4-8b5c-c8649c0c8982`

## Checklist

| # | Requirement | Verdict | Evidence |
|---|-------------|---------|----------|
| 1 | mounting_scope=none | PASS | finish probes |
| 2 | ACM support active | PASS | ACM node included |
| 3 | PD no MOUNTING_SCOPE_INACTIVE | PASS | blockers `[]` |
| 4 | Aggregate no MOUNTING_SCOPE_INACTIVE | PASS | conflicts `[]` |
| 5 | ACM node included | PASS | PD nodes |
| 6 | solution_status=confirmed | PASS | PD |
| 7 | segmented UI/API match | PASS | API `CONFIRMED` / UI `Confirmat` |
| 8 | no irrelevant legacy corner blocker | PASS | agg empty; Confirmare no PROCESS_RESOLVER_SERVICE_CORNER |
| 9 | legacy template retained inactive | PASS | finish `template_enabled=true`; UI legacy note present; template control absent |
| 10 | template inactive under none (pricing/readiness) | PASS | no false commercial blockers; PD confirmed |
| 11 | Consumabile producție label | PASS | logical-list + UI |
| 12 | Confirmare no false commercial blocker | PASS | UI probe |
| 13 | save/reload consistent | PASS | reload UI fundal + Confirmat (no DB mutation beyond normal navigation) |
| 14 | FE :3000 == BE :8003 | PASS | proxy match |

## Database / config

| Item | Value |
|------|-------|
| DATABASE_URL shape | `sqlite+aiosqlite:///./dev.db` (secret: none) |
| File | `C:\w\psiso\backend\dev.db` (~27 MB) |
| Same data :8003/:8013 | yes (`updated_at` identical before restore) |
| Discrepancy cause | orphan pre-184b9dc workers on ghost :8003, not data |

## Tests

| Suite | Result |
|-------|--------|
| `test_montaj_authority_split_v1.py` + composition contract | **31 passed** |
| FE handoff / corner / LiveCalculationSummary | **51 passed** |

## Screenshots

`screenshots/01_montaj_canonical_8003.png`  
`screenshots/02_commercial_legacy_template.png`  
`screenshots/03_confirmare_canonical.png`  
`screenshots/04_reload_montaj.png`
