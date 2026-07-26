# Fixture Activation Audit — PRODUCT_SYSTEM_V2_RUNTIME_FIXTURE_ACTIVATION_AUDIT_V1

**Date:** 2026-07-14  
**Parent:** `PRODUCT_SYSTEM_ACTIVE_PATH_ISOLATION_V1_V2_RUNTIME_PROOF_FINAL_RETRY`  
**Worktree:** `C:\w\psiso`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**HEAD:** `9366a74`

## 1. Verdict

**`PARTIAL_SEED_FOUND_SNAPSHOT_FIXTURE_MISSING`**

Repository-owned **canonical Product System seed pipeline exists** (`scripts/seed_sync_all.py`) and covers all three required template codes. **No existing production seed** populates the Quote Snapshot V2 → Order Snapshot V2 → ExecutionPlan V2 chain for runtime proof.

## 2. Repository safety

| Check | Result |
|-------|--------|
| Workspace | `C:\w\psiso` |
| Git root | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `9366a74` |
| Main workspace | untouched |
| DB mutated during audit | **NO** |
| Application code changed | **NO** |

## 3. Stack shutdown proof

| Target | Action | Post-stop |
|--------|--------|-----------|
| Backend PID 11352 | `Stop-Process` / `taskkill /F /T` | Process **not in tasklist** (already exited) |
| Frontend PID 20616 | `Stop-Process` | **No listener on :3000** |
| Port :8000 | — | **Ghost LISTENING PID 11352** remains in `netstat` (process absent) — known Windows stale-socket pattern; not a live backend |

**Runtime stopped:** YES (no live frontend; backend process gone)  
**Ports free:** **PARTIAL** (:3000 free; :8000 shows stale LISTENING entry only)

## 4. Active runtime DB

| Field | Value |
|-------|--------|
| Dev stack resolver | `scripts/start-dev.ps1` → `$DevDbPath = Join-Path $BackendDir "dev.db"` |
| Resolved URL | `sqlite+aiosqlite:///C:/w/psiso/backend/dev.db` |
| Absolute file | `C:\w\psiso\backend\dev.db` |
| Tables | 51 (schema created via `Base.metadata.create_all`) |
| `product_templates` | **0** |
| `product_blueprint_dossier` | **0** |
| `quote_snapshots_v2` | table may exist (ORM: `QuoteSnapshotV2Record`); **0 rows** |
| V2 order columns | `orders.quote_snapshot_v2_id`, `orders.snapshot_v2_json` — no seeded proof rows |

**DB target is unambiguous for `npm run dev:stack` in this worktree.** Risk only if operator sets `DATABASE_URL` to main workspace path (documented in `AGENTS.md` E2E example pointing at `C:/Users/offic/workos/backend/dev.db`).

## 5. Existing seed inventory

| Candidate | Command | Write set (summary) | Idempotent | Verdict |
|-----------|---------|---------------------|------------|---------|
| **`scripts/seed_sync_all.py`** | `cd backend && python -m scripts.seed_sync_all` | families, workcenters, materials, BUILD4 templates, **letters v2 + premount + volum aluminum**, ACM pack, **ACM boxed mounting**, pricing registries, active scope, retired cleanup | **YES** (test-guarded) | **RECOMMENDED** |
| `seeds/seed_tpl_volumetric_letters_v2.py` | `python -m seeds.seed_tpl_volumetric_letters_v2` | `product_templates` (letters + premount + volum alum), `product_blueprint_dossier`, module links, inventory/workcenter pricing | YES (upsert) | Partial alone — misses ACM + scope |
| `seeds/seed_tpl_acm_boxed_mounting_support_v1.py` | `python -m seeds.seed_tpl_acm_boxed_mounting_support_v1` | ACM template + dossier + letters module link | YES | Requires letters v2 first |
| `scripts/seed_commercial_e2e_fixture.py` | `python scripts/seed_commercial_e2e_fixture.py` | intake, quotes, orders (legacy), execution — **legacy `TPL-VOLUMETRIC-LETTERS`** | YES (E2E scoped) | **REJECT** for V2 pilot |
| `scripts/seed_canonical_order_for_e2e.py` | `python scripts/seed_canonical_order_for_e2e.py` | one `orders` row, legacy `snapshot_line_items` | YES | **REJECT** for V2 snapshot chain |
| `scripts/seed_active_template_scope.py` / seed module | via sync_all | activates owner-valid templates, deactivates others | YES | Included in sync_all |
| `scripts/cleanup_retired_product_templates.py` | via sync_all | deletes legacy `TPL-VOLUMETRIC-LETTERS` if unreferenced | conditional | Included in sync_all |
| Test-only `_seed_v2_order_with_snapshot` | pytest internal | `quote_snapshots_v2`, `orders.snapshot_v2_json` | n/a | **Not a production seed** |

## 6. Recommended Product System seed (do not execute)

**Canonical command:**

```powershell
$env:APP_ENV='development'
$env:ENVIRONMENT='development'
$env:DATABASE_URL='sqlite+aiosqlite:///C:/w/psiso/backend/dev.db'
$env:JWT_SECRET_KEY='local-dev-secret-not-for-production'
cd C:\w\psiso\backend
C:\Users\offic\workos_app_vs\backend\.venv\Scripts\python.exe -m scripts.seed_sync_all
```

Alternative if worktree venv exists: `.\.venv\Scripts\python.exe -m scripts.seed_sync_all`

## 7. Template coverage (after recommended seed)

| Template code | Covered by seed | Canonical stored code | Usage mode compatible |
|---------------|-----------------|----------------------|------------------------|
| `TPL-VOLUMETRIC-LETTERS_v2` | YES (`seed_tpl_volumetric_letters_v2`) | YES | YES (`root_offerable=true`) |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | YES (same seed module) | YES | YES (`root_offerable=true`, linked child) |
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | YES (`seed_tpl_acm_boxed_mounting_support_v1` in pipeline) | YES | YES (`root_offerable=true`, linked child) |

Also seeds linked module rows (letters ↔ premount, letters ↔ volum aluminum, letters ↔ ACM boxed mounting).

## 8. Dossier boundary compatibility

- Seeds **do write** `product_blueprint_dossier` rows (approved status, sections/task_rules metadata).
- Seeds **also write** compiler authority on `product_templates.components_json` / operations / materials — this is the canonical contract surface.
- Current branch implementation (`dossier_consumption_policy.py` + consumer gates) treats dossier as **metadata/provenance** at runtime; pytest subset (**40 passed**) proves approved dossier cannot independently drive compile when policy rejects.
- **Seeded dossier must not be treated as parallel compiler** under V2 isolation — consumption is gated; template JSON + canonical contract services remain authority.

## 9. Pricing and Intake impact

| Area | Impact from `seed_sync_all` |
|------|----------------------------|
| Pricing registries | **YES** — upserts `inventory_materials`, `workcenter_rates`, owner-confirmed price snapshots (volumetric + ACM) |
| Intake workspaces | **NO** — no intake_v3/v4/v5/v6 workspace rows |
| Quotes / Orders | **NO** — no commercial quote/order rows |
| Repricing | **NO** — registry seed only, no quote orchestration |
| Legacy alias | **Removes** `TPL-VOLUMETRIC-LETTERS` template row when cleanup finds no blocking refs |

## 10. Snapshot fixture availability

| Chain step | Production seed | Notes |
|------------|-----------------|-------|
| Quote Snapshot V2 | **NO** | Created via Intake V6 / API services at runtime; test helper only |
| Order Snapshot V2 | **NO** | `orders.snapshot_v2_json` populated in tests via `_seed_v2_order_with_snapshot` |
| ExecutionPlan V2 | **NO** | Preview/materialize from order snapshot; no dedicated seed script |
| Legacy execution smoke | `seed_canonical_order_for_e2e.py` | Legacy `snapshot_line_items` only — not V2 |

**Snapshot fixture:** **PARTIAL** (schema/columns exist; no repo-owned activation command for V2 chain)

## 11. Linked-child proof availability

After Product System seed: **YES** via `product_template_module_links` (letters → premount, letters → ACM).  
After snapshot seed alone: **NO** — snapshot fixtures do not exist separately.

## 12. Minimum safe activation sequence (commands only — not executed)

### Phase A — Product System catalog (owner GO required)

1. Verify `DATABASE_URL` points to `C:\w\psiso\backend\dev.db` (not main workspace).
2. Run `python -m scripts.seed_sync_all` with dev env vars (see §6).
3. Read-only verify: `product_templates` contains three canonical codes; catalog API count > 0.

### Phase B — Snapshot chain (blocked)

No safe existing command. Options for owner (outside this audit):

- Document `PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA` in next runtime proof, **or**
- Authorize a future dedicated build for V2 snapshot fixture seed (not inventing here).

### Phase C — Re-run runtime proof

Single `npm run dev:stack` → `/ce-debug` FINAL RETRY (third attempt).

## 13. Required questions — explicit answers

| # | Question | Answer |
|---|----------|--------|
| 1 | Existing canonical Product System seed? | **YES** — `scripts/seed_sync_all.py` |
| 2 | Exact command? | `python -m scripts.seed_sync_all` (with dev env + worktree `DATABASE_URL`) |
| 3 | DB target? | `DATABASE_URL` env → `C:\w\psiso\backend\dev.db` when set per worktree |
| 4 | Idempotent? | **YES** (`test_seed_integrity_guard.py`) |
| 5 | Writes three required template codes? | **YES** |
| 6 | Writes Dossier rows? | **YES** (metadata/provenance) |
| 7 | Can seeded Dossier become compiler authority? | **NO** under current V2 consumption gates (template JSON + canonical contracts authority) |
| 8 | Alters pricing? | **YES** — registry/pricing rows (dev owner rates), not live quote repricing |
| 9 | Alters Intake? | **NO** workspace rows |
| 10 | Alters Quote/Order/Execution? | **NO** |
| 11 | Deletes/overwrites unrelated runtime data? | **Conditional** — deletes legacy `TPL-VOLUMETRIC-LETTERS` template if unreferenced; upserts template/pricing registries |
| 12 | Safe for `C:\w\psiso\backend\dev.db`? | **YES** when `DATABASE_URL` explicitly set to worktree path |
| 13 | Separate snapshot fixture command? | **NO** |
| 14 | Linked ACM/Premount via existing fixtures? | **YES** after catalog seed (module links); **NO** via snapshot fixtures |
| 15 | Minimum activation sequence? | §12 Phase A only for catalog; snapshot remains blocked |

## 14. Scope compliance

**PASS** — read-only audit; no seed execution, no DB mutation, no application changes.

## 15. Owner decisions required

1. **GO** for Phase A `seed_sync_all` against worktree `dev.db` with explicit `DATABASE_URL`.
2. Accept **pricing registry writes** and legacy template cleanup side effects on empty dev DB.
3. Decide snapshot proof strategy: accept `PARTIAL_BLOCKED_BY_SNAPSHOT_RUNTIME_DATA` or schedule separate V2 snapshot fixture build.

## 16. Ready for controlled fixture activation

**YES** — for Product System catalog seed only, pending explicit owner GO and DATABASE_URL confirmation.

## 17. Recommended next shortcut

**`STOP_FOR_OWNER_GO`** → run §6 command → re-run V2 runtime proof.

## 18. Roadmap checkpoint

- Roadmap awareness: **9/10**
- Direction: **92/100%**
- Forbidden scope respected: **YES**

## Delivery footer

| Field | Value |
|-------|--------|
| Runtime stopped | **YES** |
| Ports free | **PARTIAL** (:3000 yes; :8000 ghost entry) |
| DB mutated | **NO** |
| Application code changed | **NO** |
| Seed created | **NO** |
| Existing canonical seed found | **YES** |
| Snapshot fixture found | **PARTIAL** |
| Ready for owner GO | **YES** (catalog only) |
| **Verdict** | **`PARTIAL_SEED_FOUND_SNAPSHOT_FIXTURE_MISSING`** |

---

## Phase 2 — Controlled activation (2026-07-14)

**Task:** `PRODUCT_SYSTEM_V2_RUNTIME_FIXTURE_ACTIVATION_V1`  
**Verdict:** **`FIXTURE_ACTIVATION_PASS`**

| Field | Value |
|-------|--------|
| Target DB | `C:\w\psiso\backend\dev.db` |
| DATABASE_URL | `sqlite+aiosqlite:///C:/w/psiso/backend/dev.db` |
| Backup | `C:\w\psiso\backend\dev.pre-product-system-v2-seed.db` (843776 bytes) |
| Seed runs | **1** |
| Seed exit | **0** |
| Command | `python -m scripts.seed_sync_all` from `backend/` |

### Post-seed canonical templates

| Template | Present | Casing | Active | root_offerable | linked_child |
|----------|---------|--------|--------|----------------|--------------|
| `TPL-VOLUMETRIC-LETTERS_v2` | YES | exact | 1 | true | false (root policy) |
| `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` | YES | exact | 1 | true | true |
| `TPL-METAL-PREMOUNT-STRUCTURE_v1` | YES | exact | 1 | true | true |

### Count deltas (pre → post)

| Table | Pre | Post |
|-------|-----|------|
| product_templates | 0 | 8 |
| product_blueprint_dossier | 0 | 4 |
| product_template_module_links | 0 | 3 |
| product_families | 0 | 14 |
| inventory_materials | 0 | 63 |
| workcenter_rates | 0 | 28 |
| intake_* / quotes / orders / quote_snapshots_v2 / execution_plan | 0 | 0 |

### Legacy cleanup

- `TPL-VOLUMETRIC-LETTERS`: inserted by BUILD4, **deleted** by `cleanup_retired_product_templates` (no blocking refs) — expected.

### Forbidden mutations

- Intake: **unchanged** (0)
- Quotes/Orders/Snapshots/Execution: **unchanged** (0)
- Application source: **unchanged by seed**
- Main workspace DB: **untouched**

**Ready for Phase 3 verification:** YES  
**Ready for final `/ce-debug`:** YES
