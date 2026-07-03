# BUILD — Post DB Rebuild Stability + Commercial Document Fix

## 1. Context

After Option B fresh `dev.db` + controlled reseed, Employee Payments and ProductSystem were restored, but owner reported:

- Work Intake / QuoteWizard / layer-tablet layout feeling “dated back”
- Commercial offer document: client line items did not sum to displayed subtotal

This build stabilizes without new features, global polish, or large refactors.

## 2. What was already OK

- Alembic head: `s50_employee_payment_records`
- Employee Payments live wiring (commits `a4d909f`, `d9157a1`)
- Chirila `cost_lunar_firma` = 7000 → slots 3500/3500 in UI logic
- Andrei 500 / Vali 300 confirmed payments; Calin accidental payment cancelled (not deleted)
- ProductSystem: `TPL-VOLUMETRIC-LETTERS` active (`active=1`)
- Orders empty state (`6401cd5`)

## 3. FAZA 0 — Precheck

| Check | Result |
|-------|--------|
| Branch | `local/integration-pr4-plus-svg-path` |
| HEAD | `6401cd5` |
| Alembic | `s50_employee_payment_records (head)` |
| Git status at start | **NOT clean** — WIP commercial document fix files (expected continuation) |

## 4. FAZA 1 — DB baseline (read-only)

### Employees / Payments

| Item | Value |
|------|-------|
| employees | 8 |
| payment records confirmed | 2 (Andrei emp 7 slot 15: 500; Vali emp 5 slot 15: 300) |
| payment records cancelled | 1 (Calin emp 1 slot 15: 4250) |
| Chirila `cost_lunar_firma` | 7000 |

Note: payment `status` column uses `confirmed` / `cancelled`, not `active`.

### ProductSystem / Pricing

| Item | Count / state |
|------|----------------|
| product_families | 14 |
| product_templates | 9 (1 active: TPL-VOLUMETRIC-LETTERS) |
| product_blueprint_dossiers | present (seeded) |
| inventory_materials | present |
| workcenter_rates | present |
| commercial_markup_policies | present |

### Commercial flow

| Item | Value |
|------|-------|
| intake_requests | 3 |
| quotes | 3 |
| orders | 0 |
| Fixtures | WI-E2E-COMMERCIAL-001, WI-E2E-COMMERCIAL-WARN-001, WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001 |
| Quote fixtures | QT-E2E-COMMERCIAL-001, QT-E2E-COMMERCIAL-WARN-001 |
| Manual priced quote | `Q-1781196429` — 934.79 EUR subtotal, 1131.09 EUR total, margin 25% |

### Work Intake data (seed vs manual)

| Intake | Template | Layers in `product_spec_json` | Primary layer |
|--------|----------|-------------------------------|---------------|
| WI-E2E-COMMERCIAL-001 | TPL-VOLUMETRIC-LETTERS | 0 (file only: e2e-volumetric-letters.svg) | — |
| WI-E2E-COMMERCIAL-WARN-001 | TPL-VOLUMETRIC-LETTERS | 3 (Cadru, Litere volumetrice, Emblema) | — |
| WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001 | TPL-VOLUMETRIC-LETTERS | 1 (L1 Letters) | L1 |

**Verdict:** DB coherent with canonical E2E seeds. Owner’s manual session (`Q-1781196429` / richer SVG state) is **not** fully replicated in minimal E2E fixture rows.

## 5. FAZA 2 — Code audit (HEAD~3)

Recent commits touched only:

- Employee payments (`a4d909f`, `d9157a1`)
- Orders empty state (`6401cd5`)

**WorkIntake / QuoteWizard / tablet / SVG / volumetric layout files: NOT modified.**

Conclusion: observed Work Intake “tablets misaligned” is **data/fixture/viewport/content**, not code regression from recent commits.

## 6. FAZA 3 — Work Intake / tablet layout diagnosis

| Question | Answer |
|----------|--------|
| Code regression? | **No** — no relevant file changes in recent commits |
| Root cause class | **B** fixture differs from old manual state; **C** minimal E2E seed (e.g. WI-E2E-COMMERCIAL-001 has 0 parsed layers) |
| Layout bug? | **No fix applied** — `V2LayersGeometryStage` grid (`grid-cols-2 md:grid-cols-3`) unchanged; tests in `WorkIntakeV2Flow.test.tsx` cover SVG+layers card |
| Action | Re-open intake with full SVG parse (WARN fixture) or recreate manual spec; do **not** reseed blindly |

## 7. FAZA 4 — Commercial document fix

### Cause

- Subtotal from quote columns (priced with ~25% margin)
- Lines from `component_breakdown` internal costs (no markup) → sum ~238 EUR vs ~934 EUR

### Strategy

`_finalize_client_line_items()` in `quote_document_service.py`:

- Hide zero lines and internal labels
- If sum ≠ `total_before_vat` → single line: *Litere volumetrice luminoase conform specificațiilor*
- `validity_display` without em-dash
- Volumetric client text sanitized (no CNC/laser)
- `component_breakdown` removed from client DTO

### Before / after (`Q-1781196429` — owner screenshot quote)

| Field | Before | After |
|-------|--------|-------|
| Visible lines | 6 (~238,43 EUR) | **1** |
| Line sum | 238,43 EUR | **934,79 EUR** |
| Subtotal ex-VAT | 934,79 EUR | 934,79 EUR |
| TVA | 196,31 EUR | 196,31 EUR |
| Total | 1.131,09 EUR | **1.131,09 EUR** |
| 0,00 line | yes | **no** |
| CNC/laser | yes | **no** |
| până la — | yes | **no** (15 zile de la emitere or real date) |

E2E fixture `QT-E2E-COMMERCIAL-001`: 928,01 RON / 1.104,33 RON — single coherent line, sums match.

## 8. Files changed

- `backend/services/quote_document_service.py`
- `backend/routers/quote_documents.py`
- `backend/tests/test_quote_commercial_document.py`
- `frontend/src/api/quoteDocuments.ts`
- `frontend/src/components/workos/QuoteCommercialDocument.tsx`
- `frontend/src/components/workos/QuoteCommercialDocument.test.tsx`
- `docs/qa/BUILD_COMMERCIAL_OFFER_DOCUMENT_CONSISTENCY_FIX.md` (prior slice doc)
- `docs/qa/BUILD_WORKOS_POST_DB_REBUILD_STABILITY_AND_COMMERCIAL_DOCUMENT_FIX.md` (this doc)

## 9. Tests run

| Suite | Result |
|-------|--------|
| `tests/test_quote_commercial_document.py` | 38 passed |
| `tests/test_employee_payments_live.py` | passed |
| `tests/test_employee_internal_pay_base.py` | passed |
| `Orders.empty.test.tsx` | 3 passed |
| `Orders.executionDispatch.test.tsx` | 3 passed |
| `EmployeePayments.test.tsx` | 9 passed |
| `QuoteCommercialDocument.test.tsx` | 5 passed |

## 10. Runtime smoke (service-level + DB)

- Commercial doc `Q-1781196429`: line sum = subtotal, total unchanged
- Employee payments DB: Andrei/Vali confirmed; Calin cancelled excluded
- ProductSystem: volumetric template active
- Orders: 0 rows (empty state path)
- Work Intake: seed data differs per fixture (see table above)

## 11. Boundaries confirmed

- No schema / migrations / alembic stamp
- No seed rerun
- No CostEngine / pricing registry / ProductSystem template mutation
- No Employee Payments code changes
- No Orders code changes
- No global CSS / App shell changes
- No commit

## 12. Remaining risks / next candidates

1. **Work Intake visual parity** — owner manual SVG/layer state not in minimal E2E seed; consider canonical “rich SVG” fixture if UI parity required without manual re-entry.
2. **EUR vs RON presentation** — E2E quotes in RON with FX; manual quote `Q-1781196429` in EUR — both valid if quote columns match snapshot currency.
3. **`frontend/test_placeholder.db`** — test artifact; do not commit.
4. Full `validate:frontend` still blocked by unrelated TS debt (~85 errors).
