# Step 8 Persistent Snapshot DB Schema Plan + Backup Gate — 2026-06-30

## Status

**PASS** (plan/audit only)

## Scope

PLAN / AUDIT ONLY — no code, no DB writes, no migration apply, no commit of runtime changes.

Prepare owner decision for Step 8 persistence: schema audit, backup gate, migration apply plan, test plan, exact GO phrase.

**Forbidden (confirmed):** code, backend runtime, frontend, UI, DB writes, migration create/apply, seed, `/price`, CostEngine, QuoteOrchestrator, order/execution_plan/task creation, push, work in `C:\Users\offic\workos`.

---

## Architecture readback summary

### Docs read

| Doc | Relevance |
|-----|-----------|
| `README.md` | Step 8 PARTIAL; batch PUT closed; next = Step 8 schema owner decision |
| `00_WORKOS_TARGET_ARCHITECTURE_OVERVIEW.md` | Dual snapshot target; no single total; commercial/internal separate |
| `05_COMMERCIAL_PRICE_PROPOSAL.md` | 7G preview — no hourly basis; frozen copy in snapshot |
| `06_ESTIMATED_INTERNAL_COST.md` | 7H preview — supports commercial, does not dictate price |
| `08_PRICING_REGISTRY_SEPARATION.md` | 7I NOT STARTED — registry separation deferred |
| `09_QUOTE_ORDER_SNAPSHOT_CONTRACT.md` | Quote/order freeze contract; immutability guards validated |
| `10_EXECUTION_PLAN_TASK_GRAPH.md` | Plan reads order snapshot; no reprice from actuals |
| `11_EXECUTION_ACTUALS_AND_TASK_SESSIONS.md` | Actuals read-only for profitability |
| `16_PROFITABILITY_ANALYSIS.md` | Step 10 PARTIAL; stable snapshot dependency |
| `18_GOVERNANCE_SETTINGS_POLICY.md` | Owner GO gates |
| `20_ROADMAP_STEPS_7G_TO_12.md` | Step 8 NEEDS OWNER GO; Step 10 partial |

### Commit context reviewed

| Commit | Role |
|--------|------|
| `62ba581` | Step 7G CommercialPriceProposal preview |
| `f73f4ce` | Step 7H EstimatedInternalCost preview |
| `d7c3afb` | Step 8 dry-run dual snapshot — `PERSISTENCE_AVAILABLE = False`, `blocked_schema_missing` |
| `2ad5607` | Step 8.2 persist — `quote_snapshots_v2` table + model + freeze write path |
| `c1c5e5a` | Accept gate on snapshot v2 |
| `2c94a2d` | Order convert from accepted snapshot v2 |
| `453932f` | Batch order financial immutability |
| `1090731` | Docs sync batch guard |

### Owner rules applied

- Commercial and internal snapshots **frozen separately** — never merged into one universal price.
- No `/price`, CostEngine, QuoteOrchestrator on freeze path.
- No order / execution_plan / task creation on freeze.
- Accepted quote/order snapshot remains frozen post-accept.
- Step 10 reads stable sources — immutability guards validated.
- Step 8 full persist requires explicit owner GO before migration apply on target DB.

### Systems affected (future apply)

| System | Impact |
|--------|--------|
| `quote_snapshots_v2` table | Primary persistence |
| `quotes.accepted_snapshot_v2_id` | Accept linkage |
| `orders.quote_snapshot_v2_id` + `snapshot_v2_json` | Convert linkage |
| `execution_plan.source_quote_snapshot_v2_id` | Plan provenance |
| Freeze / accept / convert services | Read persisted rows |
| Alembic s53–s56 | Schema apply on non-create_all DBs |

### Alignment verdict

**ALIGNED** with owner architecture — with **PARTIAL_ALIGNMENT** on documentation: architecture docs still mark Step 8 as NEEDS OWNER GO while code+migrations already exist on branch (`2ad5607`+).

---

## Git preflight

| Check | Result |
|-------|--------|
| Branch | `feature/step-7g-commercial-price-proposal` |
| HEAD | `1090731` — docs(realignment): mark batch order guard validated |
| Working tree | Clean except older untracked worklogs — **OK** |
| Unexpected backend/frontend changes | **None** |

---

## Current Step 8 state (code audit)

### Dry-run endpoint — **IMPLEMENTED**

`POST /api/v1/product-system/quote-snapshot-v2/preview/{template_code}`

- Composes 7G + 7H via `QuoteSnapshotV2Service.build_preview`
- `persist_status = not_persisted`
- No DB write, no `/price`, no QO/CE

### Freeze endpoint — **IMPLEMENTED** (code path); **apply GO pending** on some DBs

`POST /api/v1/product-system/quote-snapshot-v2/freeze/{template_code}`

| Phase | Behavior |
|-------|----------|
| `d7c3afb` | `PERSISTENCE_AVAILABLE = False` → `blocked_schema_missing` |
| `2ad5607`+ | `PERSISTENCE_AVAILABLE = True` → `_persist_snapshot` writes `quote_snapshots_v2` |

Current service (`quote_snapshot_v2_service.py`):

- `PERSISTENCE_AVAILABLE = True`
- Fail-closed on: missing identity (`quote_id`/`workspace_id`), hard-blocked readiness, non-allowed readiness
- Allowed readiness for persist: `ready_for_owner_review`, `partial_with_owner_decisions`
- Returns `persist_status: persisted` with `snapshot_code`, `snapshot_id`

### Files audited

| Path | Role |
|------|------|
| `backend/schemas/quote_snapshot_v2.py` | Dual snapshot Pydantic contract |
| `backend/services/quote_snapshot_v2_service.py` | Preview + freeze + persist |
| `backend/routers/quote_snapshot_v2.py` | Preview/freeze/get endpoints |
| `backend/models/quote_snapshot_v2.py` | `QuoteSnapshotV2Record` ORM |
| `backend/models/quotes.py` | `accepted_snapshot_v2_id` FK |
| `backend/models/orders.py` | `quote_snapshot_v2_id`, `snapshot_v2_json` |
| `backend/services/quote_snapshot_v2_accept_gate_service.py` | Accept validation |
| `backend/services/order_snapshot_v2_convert_service.py` | Quote → order convert |
| `backend/tests/test_quote_snapshot_v2.py` | Step 8/8.2 contract tests |
| `backend/tests/test_quote_snapshot_v2_accept_gate.py` | Accept gate |
| `backend/tests/test_order_snapshot_v2_convert.py` | Order convert |
| `backend/alembic/versions/s53`–`s56` | Migrations chain |

### Tests existing

`test_quote_snapshot_v2.py` covers: preview, freeze persist, no order/plan side effects, forbidden imports, commercial/internal separation, versioning, provenance, migration additive-only check.

---

## Current DB / model audit

### Safe persistence in repo?

**YES — already designed and implemented** as dedicated table `quote_snapshots_v2` (Option A variant).

| Artifact | Status |
|----------|--------|
| ORM model | `QuoteSnapshotV2Record` — imported in `models/__init__.py` |
| Dev bootstrap | `Base.metadata.create_all` in `core/database.py` — creates table when model imported |
| Alembic | `s53_create_quote_snapshots_v2` → `s54` (quotes FK) → `s55` (orders) → `s56` (execution_plan) |
| JSON strategy | Full dual snapshot in `snapshot_json` Text column (commercial + internal nested) |
| Denormalized totals | Inside JSON only — no merged column on quotes |

### Gap vs owner context

Owner context cites `blocked_schema_missing` — accurate for **`d7c3afb` dry-run only**. Current branch has persistence code; risk is **environments without s53–s56 applied** or **stale DB** without `quote_snapshots_v2`, not missing design.

**Recommendation:** Do **not** invent `quote_pricing_snapshots` — use existing `quote_snapshots_v2`.

---

## Mandatory questions (22)

| # | Answer |
|---|--------|
| 1 | New table vs JSON? **Dedicated table already exists** (`quote_snapshots_v2`). Single JSON blob column stores full dual snapshot. |
| 2 | `quote_pricing_snapshots` vs JSON on quotes? **Use existing `quote_snapshots_v2`** — not quotes JSON columns. |
| 3 | Why? Versioning, FK linkage, avoids bloating `quotes`, accept/order/plan FKs already wired, tests exist. |
| 4 | Min fields to persist | `snapshot_json` (full `QuoteSnapshotV2`), `template_code`, `quote_id`/`workspace_id`, `readiness`, `status`, `version`, `frozen_at`, `frozen_by`, `content_hash`, `snapshot_code` |
| 5 | Indexes | Existing: `snapshot_code` (unique), `quote_id`, `workspace_id`, `status`, `(quote_id, version)`, `(workspace_id, version)` |
| 6 | Link to quote | `quote_snapshots_v2.quote_id`; `quotes.accepted_snapshot_v2_id` → active accepted row |
| 7 | Link to order | `orders.quote_snapshot_v2_id` FK + `snapshot_v2_json` copy at convert (s55) |
| 8 | Quote modified after snapshot | New freeze → new `version`; prior rows remain; accept gate validates active snapshot hash |
| 9 | Prevent reprice | Freeze path never calls `/price`/QO; accept gate blocks legacy reprice path for V2 quotes |
| 10 | Prevent live registry pointer | Frozen JSON copies 7G/7H at freeze time — provenance records sources |
| 11 | Frozen 7G/7H copies | Stored inside `snapshot_json.commercial_price_proposal_snapshot` + `estimated_internal_cost_snapshot` |
| 12 | Owner decisions | `owner_decisions_snapshot[]` in JSON |
| 13 | Blockers/warnings | `blockers_snapshot[]`, `warnings_snapshot[]` in JSON |
| 14 | Provenance | `provenance[]` in JSON + `content_hash` on row |
| 15 | Freeze must do | Build preview, validate readiness/identity, insert `quote_snapshots_v2`, return snapshot id/code |
| 16 | Freeze must NOT | Call `/price`, CE, QO; create order/plan/task; merge totals; mutate quote unless separate accept flow |
| 17 | Migration needed | **Apply existing** `s53`→`s56` — **no new migration design** unless schema drift found |
| 18 | Backup before apply | Copy `dev.db`; git clean; record alembic head; no push |
| 19 | Rollback | Alembic downgrade s56→s53 in reverse; restore DB file from backup |
| 20 | Mandatory tests | Existing suite + post-apply smoke: freeze persist, accept gate, convert, immutability regression |
| 21 | Missing owner decisions | Apply GO; repeated-freeze policy; `frozen_by` identity; prod vs dev; whether to add runtime table-exists check |
| 22 | GO for apply | See § Exact GO phrase below |

---

## Schema options

### Option A — dedicated table `quote_snapshots_v2` (**EXISTS**)

| | |
|-|-|
| **Pros** | Versioned rows; FK to quotes/orders/plan; large JSON isolated; tests + migrations done |
| **Risks** | Alembic not applied on some DBs; `PERSISTENCE_AVAILABLE` is compile-time flag not runtime probe |
| **Migration** | s53–s56 already authored |
| **Tests** | `test_quote_snapshot_v2.py`, accept gate, order convert |
| **Order convert** | Already expects `quote_snapshot_v2_id` |
| **Alignment** | **95/100** — matches architecture |

### Option B — JSON columns on `quotes`

| | |
|-|-|
| **Pros** | Fewer joins |
| **Risks** | No multi-version history; bloats quotes; conflicts with `accepted_snapshot_v2_id` FK design |
| **Alignment** | **40/100** — contradicts existing s54 |

### Option C — dry-run only

| | |
|-|-|
| **Pros** | Zero migration risk |
| **Risks** | Blocks accept/convert V2 path; contradicts `2ad5607`+ implementation |
| **Alignment** | **20/100** — superseded |

### **Recommendation**

**Option A — adopt existing `quote_snapshots_v2` table.** Do not create duplicate `quote_pricing_snapshots`.

---

## Recommended schema (existing — reference)

Table: `quote_snapshots_v2`

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | |
| `snapshot_code` | String unique | `QSN2-YYYY-####` |
| `snapshot_version` | String | schema version `1.0.0` |
| `version` | Integer | per quote_id or workspace_id |
| `quote_id` | Integer nullable indexed | |
| `workspace_id` | String(36) nullable indexed | |
| `template_code` | String | |
| `status` | String | draft/frozen/superseded/archived/rejected |
| `readiness` | String | includes blocked states |
| `frozen_at` | DateTime TZ | |
| `frozen_by` | String | **OWNER_DECISION** on auth binding |
| `snapshot_json` | Text | full `QuoteSnapshotV2` JSON |
| `content_hash` | String | SHA256 prefix |
| `superseded_by_id` | Integer nullable | future supersede chain |
| `notes` | Text | |
| `created_at` / `updated_at` | DateTime TZ | |

Related FKs (s54–s56):

- `quotes.accepted_snapshot_v2_id` → `quote_snapshots_v2.id`
- `orders.quote_snapshot_v2_id` → `quote_snapshots_v2.id`
- `execution_plan.source_quote_snapshot_v2_id` → `quote_snapshots_v2.id`

**Versioning:** `_get_next_version` increments per `quote_id` or `workspace_id` — **new version on each successful freeze** (owner may later want “block if active frozen exists”).

---

## Backup gate (proposed — NOT executed)

### Pre-apply checklist

1. `git status --short` — clean or docs-only
2. `git branch --show-current` — expected feature branch
3. `git log -3 --oneline` — confirm s53–s56 present
4. Record current alembic head: `cd backend; .\.venv\Scripts\python.exe -m alembic current`
5. **No push / no remote actions**

### DB backup (SQLite dev)

```powershell
cd C:\Users\offic\Desktop\workos-active\backend
Copy-Item .\dev.db ".\dev.backup-before-step8-apply-$(Get-Date -Format yyyyMMdd-HHmmss).db"
```

If `DATABASE_URL` points elsewhere, use equivalent dump (pg_dump, etc.) — **OWNER_DECISION** on non-SQLite.

### Apply (future GO only)

```powershell
cd C:\Users\offic\Desktop\workos-active\backend
.\.venv\Scripts\python.exe -m alembic upgrade s56_add_execution_plan_source_metadata
```

### Rollback

```powershell
.\.venv\Scripts\python.exe -m alembic downgrade s52_add_intake_v3_workspaces
# or restore dev.db backup file
```

---

## Migration plan (apply existing — do not author new unless drift)

| Migration | Action |
|-----------|--------|
| `s53_create_quote_snapshots_v2` | Create table + indexes |
| `s54_add_quotes_accepted_snapshot_v2_id` | FK on quotes |
| `s55_add_orders_quote_snapshot_v2_fields` | `quote_snapshot_v2_id`, `snapshot_v2_json` on orders |
| `s56_add_execution_plan_source_metadata` | `source_quote_snapshot_v2_id` on execution_plan |

**Downgrade:** reverse order s56 → s53.

**Optional future hardening (separate GO):** replace `PERSISTENCE_AVAILABLE = True` with runtime `inspect` / try-select on `quote_snapshots_v2` so freeze fails closed with `blocked_schema_missing` when table missing.

---

## Service / endpoint plan (future apply)

| Endpoint | After apply |
|----------|-------------|
| Preview | **Unchanged** — no persist |
| Freeze | **Functional** when table exists + readiness allows |
| GET by snapshot_code | Reads persisted row |

Freeze after apply must still:

- NOT call `/price`, CE, QO
- NOT create order / execution_plan / tasks
- NOT merge commercial + internal totals
- Return `snapshot_id`, `snapshot_code`, frozen JSON copies

---

## Test plan (apply validation)

Run after migration apply:

```powershell
cd C:\Users\offic\Desktop\workos-active\backend
.\.venv\Scripts\python.exe -m pytest tests/test_quote_snapshot_v2.py tests/test_quote_snapshot_v2_accept_gate.py tests/test_order_snapshot_v2_schema.py tests/test_order_snapshot_v2_convert.py tests/test_orders_update_immutability.py -q
```

Covers: migration additive, dry-run no-write, freeze persist, dual snapshots, forbidden paths, accept gate, convert FK, immutability regression.

---

## Risks

| Risk | Mitigation |
|------|------------|
| DB without s53–s56 | Backup + alembic upgrade |
| Duplicate table proposal | Use `quote_snapshots_v2` only |
| `create_all` vs Alembic drift | Document single source of truth per environment |
| Repeated freeze ambiguity | Owner decision: allow multi-version vs block active frozen |
| Docs stale (Step 8 NOT STARTED) | Separate docs sync after apply GO |
| Prod apply | Separate GO + backup policy |

---

## Owner decisions needed

1. Approve **existing `quote_snapshots_v2`** (not new table name, not quotes JSON columns)
2. Approve **Alembic apply s53–s56** on target DB
3. Approve **backup execution** before apply
4. **Repeated freeze:** new version each time (current) vs block if active frozen exists
5. **`frozen_by`:** accept string vs bind to auth user id
6. **Quote accept flow:** when to set `quotes.accepted_snapshot_v2_id`
7. **Order conversion boundary:** separate GO already partially implemented
8. **Can Step 8 schema apply run now?** — only after backup + pytest on target DB

---

## Exact GO phrase for next step

```
GO: Step 8 persistent snapshot schema APPLY — use existing quote_snapshots_v2 table and Alembic migrations s53 through s56 (do not create quote_pricing_snapshots), backup backend/dev.db first, run alembic upgrade to s56, verify freeze persist on dev stack, run pytest test_quote_snapshot_v2.py test_quote_snapshot_v2_accept_gate.py test_order_snapshot_v2_convert.py test_orders_update_immutability.py, no /price, no CostEngine, no QuoteOrchestrator, no order/execution_plan creation in freeze path, no UI, no push.
```

---

## What was not changed

No code, backend runtime, frontend, UI, DB, migrations applied, seed, push, or work in `C:\Users\offic\workos`.

---

## Owner verification (this task)

**No browser UI.** Verify:

- Worklog: this file
- Audited code paths listed above
- Commit referenced for persistence: `2ad5607` (not modified)
- HEAD at audit start: `1090731`

---

## Next recommended step

**Owner decision + backup + Alembic apply s53–s56** — not greenfield schema design.

---

## Roadmap awareness

| Item | Status |
|------|--------|
| Position | After Step 8 dry-run (`d7c3afb`); persistence code exists (`2ad5607`); before Step 9 expansion |
| Why not Step 9 | Schema/accept linkage is prerequisite for stable order/plan V2 |
| Why not Step 10 | Step 10 MVP done; actual margin deferred |
| Why not 7I full | Registry separation independent; NOT STARTED |
| **Cât sunt în direcția stabilită** | **75/100%** — design+code ahead of docs; apply GO remains |
