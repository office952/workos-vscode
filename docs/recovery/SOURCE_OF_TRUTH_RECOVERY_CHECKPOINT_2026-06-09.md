# Source of Truth Recovery Checkpoint — 2026-06-09

## 1. Status

**Status: PASS**

Active product base:

* **Folder:** `C:\Users\offic\workos`
* **Branch:** `recovery/frontend-source-of-truth-wip`
* **HEAD:** `b3181d5`
* **Frontend:** http://127.0.0.1:3000
* **Backend:** http://127.0.0.1:8000

**Decision:**

`recovery/frontend-source-of-truth-wip` is the active WorkOS development base.

---

## 2. What Happened

Work existed across three owner-facing workstreams — **Frontend**, **Angajati**, and **Anaf** — without a single agreed repository location. GitHub `origin/main` was treated as product truth during port-phase integration work.

A later audit showed that `origin/main` is a stale, unrelated **app-layout baseline** (post PR #3), not the running product in `C:\Users\offic\workos`. PR #3 was merged into `origin/main` but does **not** overwrite or replace the local product truth.

The real product work — frontend, operational workforce (Angajati), ANAF-related commits, pricing, ProductSystem, Work Intake, and related backend routes — lived in `C:\Users\offic\workos` on the local `master` lineage and operational feature branches.

On 2026-06-09, uncommitted WIP was captured safely into branch `recovery/frontend-source-of-truth-wip`, pushed to origin, and runtime was verified on `:3000/:8000`. A follow-up fix (`b3181d5`) stabilized the operational registry employees endpoint against stale local SQLite schema.

---

## 3. Mapping of Owner Terms

| Owner term | Actual location / meaning | Status |
| ---------- | ------------------------- | ------ |
| **Frontend** | `C:\Users\offic\workos` master lineage (`backend/` + `frontend/`) | **Real product base** |
| **Angajati** | `feat/operational-workforce` / operational workforce modules | **Captured into recovery branch** |
| **Anaf** | Commits on local master lineage (e.g. `anaf_client.py`) | **Captured into recovery branch** |
| **GitHub main** | `origin/main` after PR #3 | **DO NOT USE** as product truth |
| **:3000** | `C:\Users\offic\workos\frontend` | **Product frontend** |
| **:3002** | App-layout / PR #3 port-phase frontend | **DO NOT USE** as product truth |
| **:8000** | `C:\Users\offic\workos\backend` | **Product backend** |
| **:8001** | Previous hybrid/port runtime | **DO NOT USE** as product truth |

---

## 4. Important Commits

| Commit | Description | Role |
| ------ | ----------- | ---- |
| `dbd836d` | chore: capture source-of-truth frontend operational WIP | Recovery capture — 67 source files |
| `afeac01` | chore: capture recovery docs and config WIP | Recovery capture — docs/config |
| `b3181d5` | fix: stabilize operational registry employees endpoint | Dev schema repair for stale `dev.db` |
| `d2d343b` | Merge pull request #3 from integration/workos-port-phase-2-operational-frontend | **Artifact only** on `origin/main` — not active product base |

Recovery branch stack (simplified):

```
b3181d5  fix: stabilize operational registry employees endpoint
afeac01  chore: capture recovery docs and config WIP
dbd836d  chore: capture source-of-truth frontend operational WIP
537bd2c  feat/operational-workforce tip
…        master lineage (ProductSystem, Pricing, Work Intake, ANAF, etc.)
```

---

## 5. Runtime Verification

Verified on 2026-06-09 after recovery capture and employees endpoint fix:

| Check | Result |
| ----- | ------ |
| Frontend `:3000` | **PASS** |
| Backend `:8000` | **PASS** |
| `/health` | **200** |
| `/api/v1/operational-registry/employees` | **200** |
| `/api/v1/operational-reports/summary` | **200** |
| `/api/v1/operational-reality/review` | **200** |
| ProductSystem | **reachable** |
| Pricing | **reachable** |
| Personal / Angajati on `:3000` | **PASS** |
| `:3002` `/personal` | **Not product truth** — wrong lineage |

Backend startup: use `scripts/start-dev.ps1` with local dev env (`APP_ENV=development`, `DATABASE_URL`, `JWT_SECRET_KEY`). Raw uvicorn without dev env blocks on staging safety checks.

---

## 6. Operational Registry Fix

**Symptom:** `GET /api/v1/operational-registry/employees` returned **500 Internal Server Error**.

**Root cause:** Local `dev.db` was at Alembic revision `s42_intake_persistence_handoff` while the ORM model expected columns from `s43_operational_resource_registry` (`user_id`, `salary_currency`, `salary_period`). `create_all()` does not alter existing tables; schema repair was previously disabled in `create_tables()`.

**Fix (`b3181d5`):** Re-enabled `check_and_repair_existing_tables()` on startup, gated to `development` / `local` / `dev` / `test` only. Production and staging safety checks remain separate and unchanged.

**Result:**

* Endpoint returns **200** with employee list payload.
* Related operational tests: **48/48 PASS** (resource registry, reports, reality review, operator selection, workforce capture, field installation).
* Local Alembic stamp may still read `s42` while columns exist via repair — **acceptable for local dev runtime**.
* **Production/staging must still use proper Alembic migrations** — dev repair is not a substitute.

---

## 7. What Not To Do

| Action | Label |
| ------ | ----- |
| Use `origin/main` as product truth right now | **DO NOT USE** |
| Use `:3002` as product truth | **DO NOT USE** |
| Develop from `C:\Users\offic\workos-main-post-merge` | **DO NOT USE** |
| Clean up old worktrees without an explicit plan | **WARNING** |
| Revert PR #3 unless a separate decision is made | **WARNING** — artifact preserved intentionally |
| Migrate to `app/backend` + `app/frontend` as an emergency action | **DO NOT USE** as current base |
| Reset or clean `C:\Users\offic\workos` | **DO NOT USE** |
| Delete scratch files without a cleanup plan | **WARNING** |
| Delete `origin/main` or branches/worktrees as part of this recovery | **DO NOT USE** |

`origin/main` is **not deleted**. PR #3 is **not reverted**. Both remain as historical artifacts until a branch strategy decision is made.

---

## 8. Remaining Local Scratch

Known uncommitted scratch/generated files (local only):

* `.compat-scan.json`
* `.ecut-*`
* `.extract-*`
* `.ledworld-*`
* `annes-quote-result.json`
* `backend/test_placeholder.db`
* `frontend-typecheck-*.txt`
* `frontend-vitest-*.txt`
* `frontend-validate-*.txt`

**Status:**

* Intentionally **not committed**.
* Backed up in `C:\Users\offic\workos-backups\source-truth-wip-20260609-080127`.
* Safe to handle later under a dedicated cleanup plan.

---

## 9. Open Decisions

1. Whether to eventually reconcile the recovery branch with `app/backend` + `app/frontend` layout.
2. Whether to revert, keep, or ignore PR #3 on `origin/main`.
3. Whether to create a new GitHub default branch from `recovery/frontend-source-of-truth-wip`.
4. Whether to clean old worktrees.
5. Whether to add scratch/generated patterns to `.gitignore`.
6. Whether to align local `dev.db` Alembic stamp with head (`s44_field_installation_reporting`).
7. Which product build comes next (integration branch, smoke suite, branch strategy).

App-layout reconciliation is **future work**, not the current base.

---

## 10. Recommended Next Path

1. **Continue development** from `recovery/frontend-source-of-truth-wip`.
2. **Do not touch `origin/main`** until a branch strategy is chosen.
3. **Create a clean integration branch** from recovery:
   `integration/recovered-product-base`
4. **Run final smoke and validations** from that branch (frontend typecheck/lint/build, backend pytest, operational e2e).
5. **Decide later** whether GitHub `main` should be replaced via PR, reset strategy, or new default branch.
6. **Treat app-layout migration** as a separate architecture build — not immediate cleanup.

---

## 11. Current PASS Statement

As of **2026-06-09**, the verified WorkOS product base is **`recovery/frontend-source-of-truth-wip`** at **`b3181d5`**. Local runtime on **`:3000/:8000`** is green for the checked operational endpoints and core product areas (ProductSystem, Pricing, Personal / Angajati).

**`origin/main` is not the product source of truth** until a future branch strategy decision is made.
