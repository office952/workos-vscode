# BUILD — Restore Pre-DB-Rebuild Functional State

## 1. Why this build

After Option B fresh `dev.db` + controlled reseed, owner reported Work Intake / QuoteWizard / layer-tablet UI feeling "dated back", while Employee Payments, ProductSystem, Orders empty state, and commercial document fixes remained good.

Goal: audit pre-fresh backups vs current DB, then **recover functional fixture state** via idempotent seeds — without restoring the old DB wholesale or breaking `s50` schema.

## 2. Owner decision

**Approved: Option A + partial B**

- **A:** Richer canonical E2E fixtures in `seed_commercial_e2e_fixture.py` (min. `WI-E2E-COMMERCIAL-001` with 3 layers).
- **Partial B:** `IR-M3Q8C69E` only if safe; otherwise canonical fixture equivalent.
- **Orders:** not restored (empty state OK).
- **Inventory:** no `seed_sync_all` rerun.

## 3. Backups audited (read-only)

| Label | Path | Alembic |
|-------|------|---------|
| **CURRENT** | `backend/dev.db` | `s50_employee_payment_records` |
| **BAK_215801** | `workos-local-backups/.../dev.db.bak-20260611-215801-pre-employee-payments-live-wiring` | `s51` ⚠️ phantom |
| **BROKEN_pre_fresh** | `.../dev.db.broken-pre-fresh-rebuild.sqlite` | `s49` |
| **ACTIVE_PATH_REMOVED** | `.../dev.db.active-path-removed.sqlite` | `s49` |
| **BAK_190107** | `workos-local-backups/.../dev.db.bak-20260611-190107-...` | `s48` |
| **BAK_194502** | `.../dev.db.bak-20260611-194502-...` | `s49` (early payment shape) |

## 4. IR-M3Q8C69E / partial B outcome

| Finding | Detail |
|---------|--------|
| Code in backup | **`IR-MQ3C869E`** (not `IR-M3Q8C69E` — owner typo) |
| Backup richness | 3 layers (LITERE/DIBOND/CADRU), `workos-geometry-smoke.svg`, volumetric finish (`oracal_651`) |
| Linked quotes | None |
| ID collision | None (backup id 12, current max id 3 before seed) |
| SVG on disk | **`workos-geometry-smoke.svg` missing** from repo/backups |
| Decision | **No selective DB restore** — created canonical fixture **`WI-E2E-GEOMETRY-SMOKE-001`** in seed + added `frontend/e2e/fixtures/workos-geometry-smoke.svg` |

## 5. What was implemented (Option A)

### Seed enrichments (`backend/scripts/seed_commercial_e2e_fixture.py`)

| Fixture | Change |
|---------|--------|
| `WI-E2E-COMMERCIAL-001` | 3 layers (Cadru / Litere_x0020_volumetrice / Emblema), primary layer, mapping summary, parsed SVG metadata |
| `WI-E2E-COMMERCIAL-WARN-001` | Same 3-layer tablet spec (`pbl-color.svg`) — seed no longer resets to 0 layers on rerun |
| `WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001` | 3-layer spec aligned with WARN tablet layout |
| **`WI-E2E-GEOMETRY-SMOKE-001`** (new) | 3 layers LITERE/DIBOND/CADRU, finish volumetric sample from backup `IR-MQ3C869E` lineage |

### New asset

- `frontend/e2e/fixtures/workos-geometry-smoke.svg` — viewBox `0 0 1000 200`, layer ids match seed spec.

### Idempotency

- Upsert by `code` on all fixture intakes; quote codes unchanged (`QT-E2E-COMMERCIAL-001`, `QT-E2E-COMMERCIAL-WARN-001`).
- No duplicate intakes on rerun.

## 6. What was NOT restored

| Data | Reason |
|------|--------|
| Full backup DB | Forbidden (s51 phantom + legacy payments) |
| `IR-M3Q8C69E` / `IR-MQ3C869E` as manual code | SVG dead + safer canonical `WI-E2E-GEOMETRY-SMOKE-001` |
| Bulk 42 intakes / 28 quotes | Owner declined |
| 10 orders | Owner declined |
| `employee_payment_records` legacy | s50 model kept |
| `seed_sync_all` / inventory gap 56 vs 74 | Owner declined |

## 7. DB counts

| | Before seed | After seed |
|---|-------------|------------|
| intake_requests | 3 | **4** (+ `WI-E2E-GEOMETRY-SMOKE-001`) |
| quotes | 4 | 4 |
| orders | 0 | 0 |

### Post-seed verification

| Check | Result |
|-------|--------|
| `WI-E2E-COMMERCIAL-001` layers | **3**, primary `Litere_x0020_volumetrice` |
| `WI-E2E-GEOMETRY-SMOKE-001` | **3** layers, primary `LITERE`, status `in_review` |
| `TPL-VOLUMETRIC-LETTERS` active | yes |
| `Q-1781196429` | 934.79 / 1131.09 EUR unchanged |
| Employee payments | Andrei 500 + Vali 300 confirmed; Calin 4250 cancelled |

## 8. Commands run

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/Users/offic/workos/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
cd backend
.\.venv\Scripts\python.exe scripts\seed_commercial_e2e_fixture.py
```

## 9. Tests

| Command | Result |
|---------|--------|
| `pytest tests/test_quote_commercial_document.py tests/test_employee_payments_live.py tests/test_employee_internal_pay_base.py -q` | **52 passed** |
| `vitest run src/pages/Orders.empty.test.tsx src/pages/EmployeePayments.test.tsx src/components/workos/QuoteCommercialDocument.test.tsx` | **17 passed** |

## 10. UI smoke (localhost :3000 / :8000)

| Area | Result |
|------|--------|
| `/intake-v2/WI-E2E-COMMERCIAL-001` | 3 layere · 522 elemente; layer cards Cadru/Litere/Emblema; primary layer UI; zones 5/5 — **not empty** |
| `/intake-v2/WI-E2E-GEOMETRY-SMOKE-001` | 3 layere LITERE/DIBOND/CADRU; Oracal 651 face finish; geometry warnings from backup |
| Employee Payments | Chirila 3500 calculat; Andrei 500 / Vali 300 parțial; Calin anulată; total plătit **800 RON** |
| Orders | empty state (0 rows) — not re-tested in browser this run |
| Commercial document | regression tests pass; `Q-1781196429` totals unchanged in DB |

## 11. Files changed

| File | Change |
|------|--------|
| `backend/scripts/seed_commercial_e2e_fixture.py` | Richer parsed specs + geometry smoke fixture |
| `frontend/e2e/fixtures/workos-geometry-smoke.svg` | New canonical SVG asset |
| `docs/qa/BUILD_WORKOS_RESTORE_PRE_DB_REBUILD_FUNCTIONAL_STATE.md` | This doc |
| `frontend/e2e/.commercial-fixture.json` | Updated by seed run (manifest) |

No changes: schema, migrations, CostEngine, pricing registry, ProductSystem templates, commercial document code, Orders, Employee Payments logic, App shell/CSS.

## 12. Boundaries confirmed

- No commit
- No raw DB restore over fresh `dev.db`
- No schema/migration / Alembic stamp / drop table
- No legacy `employee_payment_records` restore
- No CostEngine / pricing registry mutation
- Employee Payments PASS (code + DB + UI)
- Orders empty state PASS (tests)
- Commercial document PASS (tests + `Q-1781196429` DB totals)

## 13. Remaining risks

1. Manual `IR-*` sessions (~39) remain in backup only — not in seeds.
2. `workos-geometry-smoke.svg` exists in `frontend/e2e/fixtures/` but is not auto-uploaded to server storage; UI uses persisted `product_spec_json` layer data.
3. Inventory materials 56 vs 74 — noted, not blocking.
4. `QT-E2E-COMMERCIAL-001` grand_total may differ slightly after repricing on seed rerun (1104.33 RON at last run) — E2E quote only, not `Q-1781196429`.
