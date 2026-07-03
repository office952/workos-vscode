# BUILD QA — Migration Hygiene Fix

**Title:** Migration Hygiene Fix — SQLite Clean Upgrade + dev.db Alembic Reconciliation  
**Date:** 2026-06-07  
**Branch:** `master`  
**Fix commit:** `83396d6` — fix: repair sqlite migration chain and ignore generated documents  
**Related:** `c80e616` — fix: persist intake readiness and quote handoff context  
**Verdict:** **PASS**

---

## Scope

Migration and local artifact hygiene only:

- No pricing changes
- No CostEngine changes
- No readiness policy changes
- No quote/order creation during validation
- No Reference Catalogs work started
- No business logic changes

---

## Problem

After `c80e616`, migration hygiene validation **failed** for three reasons:

1. **`backend/dev.db`** had `intake_requests` s42 columns (`confirmed_template_code`, `confirmed_template_name`, `site_audit_json`) but **`alembic_version` was empty** (schema ahead of metadata).
2. **Clean SQLite `alembic upgrade head`** failed at **`s29_stock_movements`** with `NotImplementedError` (SQLite constraint ALTER unsupported).
3. **`backend/generated_documents/`** was untracked generated output (PDF exports) and not ignored.

---

## Root cause

In `s29_stock_movements.py`, uniqueness was added via:

```python
op.create_unique_constraint("uq_stock_movements_idempotency", "stock_movements", ["idempotency_key"])
```

after `op.create_table(...)`.

On SQLite this requires an **ALTER TABLE** constraint operation, which the dialect does not support → clean DB migration chain broke before reaching s42.

---

## Fix implemented (`83396d6`)

| Change | Detail |
|--------|--------|
| **s29 SQLite compatibility** | `sa.UniqueConstraint("idempotency_key", name="uq_stock_movements_idempotency")` moved **inside** `create_table` (same pattern as s20/s21/s25) |
| **`.gitignore`** | `backend/generated_documents/` added — generated PDFs stay local, not versioned |
| **Business logic** | Unchanged |

---

## Clean DB validation

| Check | Result |
|-------|--------|
| Temp DB | `backend/_migration_validate_clean.db` (validation only; removed before commit) |
| `alembic upgrade head` | **PASS** — full chain to head |
| Final head | `s42_intake_persistence_handoff` |
| `alembic_version` | Exactly **one** row: `s42_intake_persistence_handoff` |
| `intake_requests` s42 columns | `confirmed_template_code`, `confirmed_template_name`, `site_audit_json` — present |
| `stock_movements` uniqueness | `CONSTRAINT uq_stock_movements_idempotency UNIQUE (idempotency_key)` |

---

## dev.db reconciliation

| Step | Result |
|------|--------|
| Schema before stamp | s42 columns present; `stock_movements` uniqueness present; **no missing tables** vs clean head |
| `alembic_version` before stamp | Table exists, **0 rows** (out-of-sync metadata) |
| Action | `alembic stamp s42_intake_persistence_handoff` on `backend/dev.db` only — **no upgrade** on dev.db |
| Proof before stamp | Clean upgrade path PASS; dev.db schema superset of head |
| After stamp | `alembic current` = `s42_intake_persistence_handoff (head)` |
| Schema after stamp | **Unchanged** — stamp wrote metadata only |

**Caveat:** `dev.db` has **4 extra tables** vs clean head (`users`, `oidc_states`, `order_output_snapshot_references`, `inventory_sheet_remediation_audit_events`) from `create_all` / local history. This is a **superset**, not a migration hygiene blocker.

---

## Post-stamp validation

| Check | Result |
|-------|--------|
| Entity counts | intakes=**11**, quotes=**7**, orders=**8** (unchanged) |
| `POST simulate-cost` | **844.41 EUR**, `status=simulated`, **`persisted=false`** |
| Quote/order created | **No** |

---

## Tests

| Suite | Result |
|-------|--------|
| `py_compile` — `s29_stock_movements.py` | OK |
| `tests.test_intake_persistence_handoff` | 4/4 OK |
| `test_simulate_cost_unchanged_after_dossier` | OK (844.41 EUR baseline) |
| Direct s29 migration test in repo | **None** (indirect model/inventory tests only) |

---

## Local artifacts

| Path | Disposition |
|------|-------------|
| `backend/_migration_validate_clean.db` | Removed (temp validation) |
| `backend/scripts/_migration_evidence.py` | Removed (temp validation) |
| `backend/scripts/_migration_validate.py` | Removed (temp validation) |
| `backend/generated_documents/` | **Gitignored** — not committed |
| `.git_cmd_out.txt` | Remains **untracked** local |
| `docs/architecture/PRICING_RATE_BASIS_AND_CURRENCY_AUDIT.md` | Remains **untracked** draft |

---

## Result

**PASS** — SQLite clean upgrade works to s42; `dev.db` Alembic metadata reconciled; generated documents ignored; runtime persistence and CostEngine baseline unchanged.

---

## Next safe step

**Reference Catalogs / Material & Color Catalogs** may be planned next from a **migration hygiene** perspective. Resolve any new schema via Alembic on a clean SQLite path before adding catalog tables.
