# Worklog — UTF-8 / Romanian diacritics permanent fix (2026-07-17)

## Verdict

`UTF8_DIACRITICS_PERMANENT_FIX_PASS` for operator-visible active path (source → product_templates → execution_plan → API → UI).

Frozen commercial snapshots remain **explicitly gated** (not mutated): `quote_snapshots_v2.snapshot_json`, `orders.snapshot_v2_json` (and related). Encoding restoration there requires a separate owner GO.

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

- Backend: `pytest tests/test_utf8_text_integrity.py` → 10 passed
- Frontend: `vitest run src/lib/utf8TextIntegrity.test.ts` → 3 passed
- Frontend build: `pnpm run build` → success

## /modules impact

No new system node. Harta sistemelor left unchanged (transport already UTF-8; defect was source/persisted text). Evidence note only in this worklog + QA folder.

## /governance impact

Added guardrail **G13** — UTF-8 end-to-end for operator text (`frontend/src/lib/governanceData.ts`). Visible under Reguli de protecție → Integritate text.

## Remaining risks

1. Frozen snapshot JSON still contains mojibake until owner GO + `--include-frozen`.
2. Historical QA JSON / worklog evidence intentionally retains defect quotes — do not “clean” archives.
3. Seed is insert-only; existing DBs need repair script (or re-seed after delete) for new environments that already loaded corrupt templates.

## Next safe step

Owner decision on frozen snapshot encoding restoration (`quote_snapshots_v2` / `orders.snapshot_v2_json`) with dry-run + backup — or leave historically frozen as-is.
