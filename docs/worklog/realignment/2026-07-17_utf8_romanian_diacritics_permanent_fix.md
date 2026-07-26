# Worklog — UTF-8 / Romanian diacritics permanent fix (2026-07-17)

## Verdict

1. `UTF8_DIACRITICS_PERMANENT_FIX_PASS` — operator-visible active path (source → product_templates → execution_plan → API → UI).
2. `FROZEN_SNAPSHOT_UTF8_RESTORATION_PASS` — local/dev frozen Quote/Order Snapshot V2 encoding restoration after explicit owner GO.

## Root cause

UTF-8 Romanian bytes were historically mis-decoded as Windows-1252/CP1252 and re-saved as Unicode in authoritative source files (primarily `backend/seeds/seed_build4_templates.py`, plus hardcoded Product System UI copy and a few Intake V6 messages). SQLite/FastAPI/fetch were not the first corruption boundary — they faithfully transported already-corrupt strings.

Confirmed repair codec: `value.encode("cp1252").decode("utf-8")` (latin-1 fails on CP1252-only glyphs such as `ƒ` / `›` / `€`).

## First corruption boundary

| Sample displayed | Expected | Source | Stored (pre-repair) | API (pre) | Frontend | First boundary |
|---|---|---|---|---|---|---|
| PregÄƒtire vector / font | Pregătire vector / font | `seed_build4_templates.py` → `product_templates.components_json` → `execution_plan.tasks_json` | mojibake | mojibake | render-as-is | **seed/source file** |
| TÄƒiere CNC faÈ›Äƒ litere | Tăiere CNC față litere | same lineage | mojibake | mojibake | render-as-is | seed/source |
| ManoperÄƒ … feÈ›e | Manoperă … fețe | same lineage | mojibake | mojibake | render-as-is | seed/source |
| Lipire cant pe faÈ›Äƒ | Lipire cant pe față | same lineage | mojibake | mojibake | render-as-is | seed/source |
| â€” in labels | — | same lineage | mojibake | mojibake | render-as-is | seed/source |

Dossier `task_rules` remained English/clean; clean RO labels also existed in other seeds — split-brain confirmed.

## Encoding contract audit

| Layer | Status |
|---|---|
| Source charset | UTF-8; `.editorconfig` added (`charset = utf-8`) |
| HTML | `frontend/index.html` `<meta charset="UTF-8" />` |
| DB | SQLite Unicode text; corruption was application/historical insert content |
| SQLAlchemy / aiosqlite | No latin1/cp1252 codec transforms found |
| FastAPI JSON | Native UTF-8 body; probe `/api/v1/execution/plan/92402` clean after repair |
| Frontend fetch | `Response.json()` — no legacy decode |
| Prevention | `core/utf8_text_integrity.py` + seed fail-fast; FE `assertNoMojibake` for tests/dev warn |

## Repair

- Dry-run: `docs/qa/utf8-romanian-diacritics-2026-07-17/dry-run-report.json`
- Backup: `docs/qa/utf8-romanian-diacritics-2026-07-17/dev.db.backup-20260717T035320Z` (gitignored) + checksum meta
- Applied sources: seed_build4, intake_v6_workspace_service, ProductSystem.tsx, intakeV6WorkspaceCache, 4 volumetric test docstrings
- Applied DB (non-frozen): `product_templates` (3 rows), `execution_plan` (2 rows: plans 8 & 9)
- Frozen skipped without `--include-frozen`

### Rollback

```powershell
Copy-Item docs/qa/utf8-romanian-diacritics-2026-07-17/dev.db.backup-20260717T035320Z backend/dev.db -Force
```

Source rollback: `git checkout -- <paths>` for committed source repairs.

## Runtime proof

- Frontend: `http://127.0.0.1:3000`
- Backend: `http://127.0.0.1:8001`
- Page: `http://127.0.0.1:3000/execution/92402`
- Order: `92402` / plan id `8`
- After: `Pregătire`, `Tăiere CNC față`, `Manoperă`, `Lipire cant pe față`, `Șablon` — no `Äƒ`/`È›`/`â€` in page text
- Screenshot: `docs/qa/utf8-romanian-diacritics-2026-07-17/execution-92402-utf8-after.png`

## Tests

- Backend: `pytest tests/test_utf8_text_integrity.py` → 14 passed (includes frozen snapshot invariants)
- Frontend: `vitest run src/lib/utf8TextIntegrity.test.ts` → 3 passed
- Frontend build: `pnpm run build` → success

## Frozen snapshot UTF-8 restoration (Owner GO)

Owner decision recorded: `FROZEN SNAPSHOT UTF8 RESTORATION — GO`  
Scope: local/dev `backend/dev.db` only. Encoding restoration, not commercial mutation. Production not authorized.

### Tooling

- `backend/scripts/restore_frozen_snapshot_utf8.py` (requires `--include-frozen` to mutate)
- Default `repair_utf8_mojibake.py` still excludes frozen unless `--include-frozen`

### Dry-run

- Evidence: `docs/qa/utf8-romanian-diacritics-2026-07-17/frozen-snapshot-dry-run.json`
- Result: **6 CONFIRMED_SAFE**, 0 ambiguous, 0 fingerprint drift
- Rows:
  - `quote_snapshots_v2` id 1,2,3 (`snapshot_json`) — 37 string repairs each
  - `orders` id 92401,92402,92403 (`snapshot_v2_json`) — 37 string repairs each
- Build 1 focus: quote `3` / `QSN2-2026-0002` / order `92402`

### Backup (pre-frozen-apply)

- Path: `docs/qa/utf8-romanian-diacritics-2026-07-17/dev.db.frozen-backup-20260717T040112Z` (gitignored)
- Meta: `frozen-db-backup-20260717T040112Z.json`
- sha256: `d7a28f5d0430ccb24e7507ba293cf9854263dcc30d52abf5ca586fa40beca175`
- bytes: 4714496; backup open verified

### Apply

- Applied 6 rows; structural/commercial fingerprint unchanged on every row
- Idempotent re-dry-run: confirmed_safe=0
- Quote↔Order label alignment for Build 1: **aligned_labels=true**
- Plan 8 not regenerated / not rewritten in this step

### Commercial fingerprint proof (Build 1)

| Field | Before | After |
|---|---|---|
| Snapshot `QSN2-2026-0002` / quote_snapshots_v2 id 2 | frozen / v1.0.0 | unchanged |
| Order 92402 status / quote_snapshot_v2_id | locked / 2 | unchanged |
| Order `total_amount` | 3549.1286 | 3549.1286 |
| Snapshot `commercial_total` | 3549.1286 | 3549.1286 |
| Snapshot `internal_total` | 1560.3836 | 1560.3836 |
| Template code | TPL-VOLUMETRIC-LETTERS_v2 | unchanged |
| Sample label | `FaÈ›Äƒ plexi…` | `Față plexi…` |

Evidence: `frozen-snapshot-commercial-fingerprint.json`, `frozen-snapshot-commercial-before-after.json`, `frozen-snapshot-repair-result.json`

### LOCAL FROZEN SNAPSHOT UTF8 PROOF

- `GET /api/v1/product-system/quote-snapshot-v2/QSN2-2026-0002` → 200, `Față` present, no mojibake, total 3549.1286
- `GET /api/v1/entities/orders/92402` → 200, total 3549.1286, no mojibake
- `GET /api/v1/entities/quotes/3` → 200, no mojibake
- `GET /api/v1/execution/plan/92402` → 200, clean Romanian task labels
- UI: `http://127.0.0.1:3000/execution/92402` — clean diacritics; screenshot `execution-92402-frozen-utf8-after.png`
- Orders list shows `ORD-IV6-V2-1784237123-3` value **3.549,13 RON** unchanged; screenshot `orders-commercial-total-utf8.png`
- Proof note: `LOCAL_FROZEN_SNAPSHOT_UTF8_PROOF.md`

### Frozen rollback

```powershell
# stop backend writers first, then:
Copy-Item docs/qa/utf8-romanian-diacritics-2026-07-17/dev.db.frozen-backup-20260717T040112Z backend/dev.db -Force
```

Full rollback was not executed (backup checksum + open verified). Execute only if validation fails.

## /modules impact

NO SYSTEM NODE CHANGE. Evidence updated under QA folder + this worklog only.

## /governance impact

**G13** remains accurate: semantic source owns text; transport preserves Unicode; frontend renders, not repairs; frozen restoration requires explicit owner GO; production remains separately gated. No duplicate rule added.

## Remaining risks

1. Production / non-local DBs are unmodified and remain separately gated.
2. Historical QA JSON / screenshots that intentionally quote the defect remain untouched.
3. Seed is insert-only; new environments that already loaded corrupt templates still need the repair scripts.

## Next safe step

Resume the previously approved roadmap task (post-encoding closure). Do not auto-start W7-T02/W7-T03.
