# Quote & Order — Snapshot Contract

**Version:** 1.0.4  
**Status:** Target architecture + **Step 8 VALIDATED_WITH_GUARDS** + **Step 9 persist draft VALIDATED_WITH_GUARDS** (sync 2026-06-30)  
**Services (read context):** `quote_orchestrator.py`, intake quote-to-order flow, `order_immutability_service.py`, `profitability_analysis_service.py`, `quote_snapshot_v2_service.py`, `quote_snapshot_v2_accept_gate_service.py`, `order_snapshot_v2_convert_service.py`  
**Step:** 8 — **VALIDATED_WITH_GUARDS** (live freeze → pricing review → owner approval → accept → convert **VALIDATED**); **10.1** — **IMPLEMENTED**; **10.2+10.3** — **VALIDATED**

---

## 1. Rolul sistemului

Quote înghețează **propunerea comercială** și **costul intern estimativ** side-by-side. Order înghețează **configurația acceptată**, **prețul acceptat**, **costul estimat la acceptare**, promisiunea clientului și inputul pentru execuție.

---

## 2. Ce detine

### Quote (target snapshot)

| Categorie | Conținut |
|-----------|----------|
| **commercial_price** | CommercialPriceProposal frozen copy |
| **estimated_internal_cost** | EstimatedInternalCost frozen copy |
| **margin_preview / warnings** | Confidence, marjă estimată |
| **configuration snapshot** | product_definition, quote_input, finish summary |
| **commercial rules applied** | rule_provenance[] |
| **owner_decisions** | Approvals, acknowledgements |
| **revision versioning** | Priced revisions — not silent overwrite |
| **status lifecycle** | draft → priced → accepted |

### Order (target snapshot)

| Categorie | Conținut |
|-----------|----------|
| **Accepted configuration** | Frozen product_definition |
| **Accepted commercial price** | What client agreed |
| **Estimated cost at acceptance** | Internal estimate at moment |
| **Client promise** | Scope frozen |
| **snapshot_line_items** | For ExecutionPlan input |
| **Linkage** | quote_id, intake workspace ref |

---

## 3. Ce NU detine

| Exclus |
|--------|
| Minute reale inexistente ca basis |
| Modificare preț comercial după ExecutionActuals |
| Taskuri din catalog paralel |
| Recalcul comercial retroactiv |
| ProfitabilityAnalysis (downstream) |
| Live registry prices post-freeze |
| `final = total_cost × margin` ca singură formulă (target) |

---

## 4. Inputuri

| Sursă | Date |
|-------|------|
| Intake V6 | Draft quote creation, gates |
| CommercialPriceProposal | commercial lines (7G) |
| EstimatedInternalCost | internal lines (7H) |
| ProductDefinition | Structure at price time |
| Owner approval flow | complete-pricing-review, owner-approval |
| Priced line_items | Today via `/price` — **FROZEN path** |

---

## 5. Outputuri

| Output | Consumator |
|--------|------------|
| Quote PDF / client comms | commercial_price section |
| Order | convert-to-order |
| ExecutionPlan | snapshot_line_items processes |
| ProfitabilityAnalysis | quoted baseline |
| Audit trail | revisions, approval hash |

---

## 6. Source of truth

| Aspect | Status |
|--------|--------|
| Official client offer | **Quote snapshot post-Step 8** — not Intake preview |
| Today deviated | grand_total from cost-plus; draft grand_total=0 |
| Order commercial promise | **Frozen at convert** |
| Internal estimate at offer | Side B snapshot — today mixed |

---

## 7. Conexiuni cu celelalte sisteme

```
Intake V6 → draft quote (notes, grand_total=0)
    ↓
CommercialPriceProposal + EstimatedInternalCost (previews 7G/7H)
    ↓
Quote Snapshot (Step 8) — dual field
    ↓ accept + owner gates
Order frozen snapshot
    ↓
ExecutionPlan (from snapshot product_definition — NOT re-price)
    ↓
ExecutionActuals (does NOT modify quote/order price)
    ↓
ProfitabilityAnalysis
```

**Frozen paths today:** `POST /api/v1/entities/quotes/price`, `POST .../quotes/{id}/price`, `QuoteOrchestrator._apply_commercial`.

---

## 8. Reguli owner obligatorii

1. Draft quote **intentionally** unpriced until proper snapshot path.
2. No Quote 4 reprice until 7G→8 aligned.
3. Accept requires priced snapshot + gates — not live Intake calc.
4. Order convert requires priced line_items with product_definition.
5. ExecutionActuals never retrochanges accepted commercial price.

---

## 9. Riscuri actuale din audit

| Risk | Detail | Tag |
|------|--------|-----|
| grand_total=0 draft | By design — confusing with preview 6324 | `MISLEADING_UI` |
| /price mixed model | Single write commercial+internal | `FROZEN_UNTIL_REALIGNED` |
| cost-plus final | _apply_commercial | `HIGH_RISK_WRONG_DIRECTION` |
| Notes-only draft | No product_definition until /price | Partial |
| Order without execution_plan | Convert OK; plan separate | OK — documented |
| Reprice in-place | Quote 4 risk | `FROZEN_UNTIL_REALIGNED` |

---

## 10. Target state (Step 8)

**Quote snapshot schema (conceptual):**

```json
{
  "commercial_price": { "lines": [], "subtotal": 0, "total": 0, "currency": "RON", "provenance": [] },
  "estimated_internal_cost": { "material": 0, "operation": 0, "total": 0, "completeness": 1.0, "warnings": [] },
  "margin_preview": { "estimated_margin_pct": null, "warnings": [] },
  "product_definition": {},
  "owner_decisions": {},
  "frozen_at": "ISO8601"
}
```

| Aspect | Țintă |
|--------|-------|
| Dual fields mandatory | Never single total_cost×margin alone |
| Official label | Only post-snapshot = „ofertă oficială” |
| Revision discipline | New revision — not silent mutate |
| Order immutability | Commercial frozen |
| PUT financial guard (Slice 10.1 + batch) | **IMPLEMENTED + VALIDATED** — individual (`90ba918`) + batch (`453932f`); see §13 |

---

## 13. Runtime — Order financial immutability guard (Slice 10.1 + batch)

**Status:** **IMPLEMENTED + VALIDATED** — individual PUT (`90ba918`); batch PUT (`453932f`, branch `feature/step-7g-commercial-price-proposal`)

| Item | Detail |
|------|--------|
| Service | `backend/services/order_immutability_service.py` — shared by individual and batch |
| Individual router hook | `PUT /api/v1/entities/orders/{id}` — `update_orders` calls `assert_order_financial_fields_mutable` **before** `OrdersService.update` |
| Batch router hook | `PUT /api/v1/entities/orders/batch` — `update_orderss_batch` pre-validates **all** items via `assert_order_financial_fields_mutable` **before** any `OrdersService.update` (fail-closed) |
| Blocked fields | `total_amount`, `snapshot_line_items`, `snapshot_version` |
| Order protected when | `locked_at` set **OR** non-empty `snapshot_v2_json` **OR** status ∈ `{locked, in_execution, completed}` |
| HTTP response | **422** — `error: ORDER_FINANCIAL_FIELDS_IMMUTABLE`, `blocked_fields[]`, `order_id`, `order_status` |
| Allowed updates | `notes`, `promised_delivery`, `payment_status`, `job_id`, `contact_person`, status transitions per lifecycle |
| Preserved behavior | Unlocked legacy order + `total_amount` update remains **allowed** (individual and batch) |
| Not in scope | `snapshot_v2_json` is **not** in `OrdersUpdateData` — not PATCH-able via generic PUT |
| Out of scope | CostEngine, QuoteOrchestrator, `/price` — guard only; no reprice |
| **Was WATCH** | Batch `PUT /orders/batch` bypassed individual guard after Slice 10.1 — **MITIGATED** in `453932f` |

**Why:** ProfitabilityAnalysis and Step 10 read paths require stable `accepted_commercial_total` (inside `snapshot_v2_json`) and legacy financial fields. Silent PUT (individual or batch) undermined frozen commercial promise.

**Tests:** `backend/tests/test_orders_update_immutability.py` — **16** contract tests (individual + batch).

---

## 14. Runtime — ProfitabilityAnalysis read consumer (Slice 10.2 + 10.3)

**Status:** **IMPLEMENTED + VALIDATED** (commit `45255a1`)

| Item | Detail |
|------|--------|
| Endpoint | `GET /api/v1/profitability-analysis/order/{order_id}` |
| Service | `backend/services/profitability_analysis_service.py` — **read-only** |
| Reads from snapshot | `snapshot_v2_json.accepted_commercial_total`, `estimated_internal_total` |
| Legacy fallback | `order.total_amount` when no V2 — emits `legacy_order_without_snapshot_v2` warning |
| ExecutionActuals | Reads ExecutionReality when present — does **not** mutate |
| Writes | **None** — `retroactive_change_allowed: false`, `write_back_performed: false` |
| Why stable snapshot matters | Analysis compares frozen commercial/internal at accept vs actuals post-job |

**Dependency on §13:** Slice 10.1 PUT guard keeps `accepted_commercial_total` stable for profitability reads.

**Tests:** `backend/tests/test_profitability_analysis.py`. **Doc:** [16_PROFITABILITY_ANALYSIS.md](./16_PROFITABILITY_ANALYSIS.md) §10.

---

## 15. Runtime — Dual Quote Snapshot V2 preview/freeze (Step 8)

**Status:** **VALIDATED_WITH_GUARDS** — preview and live freeze persist **VALIDATED** on safe IV6 path (paper QA payload + dev registry bridge)

| Item | Detail |
|------|--------|
| Preview endpoint | `POST /api/v1/product-system/quote-snapshot-v2/preview/{template_code}` — **no persist** |
| Freeze endpoint | `POST /api/v1/product-system/quote-snapshot-v2/freeze/{template_code}` |
| Template (QA) | `TPL-VOLUMETRIC-LETTERS_v2` |
| Schema | `quote_snapshots_v2` table **present** in dev DB (s53–s56 equivalent via `create_all`) |
| Preview runtime | **VALIDATED** — HTTP 200, `readiness=partial_with_owner_decisions` (paper QA), dual snapshots returned, commercial/internal **separate** |
| Freeze runtime (live dev) | **VALIDATED** — HTTP 200, `persist_status=persisted`, snapshot `QSN2-2026-0003`, `status=frozen`, `readiness=partial_with_owner_decisions` |
| Freeze persist (pytest) | **VALIDATED** — `test_quote_snapshot_v2.py`, `test_step8_snapshot_acceptability.py` (**126 pytest** total scoped suite) |
| Fail-closed rule | Freeze must persist **only** when readiness permits; hard-blocked readiness must **not** write `quote_snapshots_v2` — still validated for `blocked_snapshot_conflict` |
| Side effects | **No** order, execution_plan, or task creation on freeze |
| Forbidden paths | **No** `/price`, CostEngine, QuoteOrchestrator on freeze path |

**Guarded status:** `partial_with_owner_decisions` remains valid only with explicit owner decision acknowledgement on accept; freeze persist sets `status=frozen` while readiness stays partial.

**Not claimed:** Step 9; ExecutionPlan creation; tasks; `/price`/CE/QO replacement; 7I complete; full production on all payloads without owner decisions.

**Worklogs:** `2026-06-30_step8_snapshot_acceptability_build.md`, `2026-06-30_step8_live_freeze_accept_convert_qa.md`

---

## 16. Runtime — Quote Snapshot V2 accept gate (Step 8.3)

**Status:** **VALIDATED_WITH_GUARDS** — **126 pytest PASS** + live accept API **VALIDATED** on quote 1 / snapshot 3

| Item | Detail |
|------|--------|
| Accept API | `POST /api/v1/intake-v6/quotes/{quote_id}/accept` → `accept_v6_quote` |
| Service | `quote_snapshot_v2_accept_gate_service.py` — `validate_snapshot_for_accept`, `resolve_snapshot_for_accept` |
| Linkage field | `quotes.accepted_snapshot_v2_id` → FK `quote_snapshots_v2.id` |
| Live accept | **VALIDATED** — quote 1 `accepted_snapshot_v2_id=3` after `confirm_owner_decisions_acknowledged=true` |
| Order convert guard | `convert_accepted_quote_snapshot_v2_to_order` requires `accepted_snapshot_v2_id`; missing → `MISSING_ACCEPTED_SNAPSHOT_V2` |
| Accept side effects | **No** order, execution_plan, or task creation on accept (live + tested) |
| Forbidden paths | **No** `/price`, CostEngine, QuoteOrchestrator on accept path |

### Acceptable snapshot readiness

| Readiness | Accept |
|-----------|--------|
| `ready_for_owner_review` | **Yes** — `snapshot_ready_for_acceptance` |
| `partial_with_owner_decisions` | **Yes** only when `confirm_owner_decisions_acknowledged=true` |

### Blocked snapshot readiness

`blocked_snapshot_conflict`, `blocked_missing_commercial`, `blocked_missing_internal`, `blocked_forbidden_path`, `blocked_schema_missing`

### `blocked_snapshot_conflict`

Both **7G** CommercialPriceProposal **and** **7H** EstimatedInternalCost are `status=blocked` at the same time (`compute_readiness`). In this state, freeze/accept must **fail closed** and must **not** persist an accepted snapshot.

### `allow_freeze_readiness` (test only)

Pytest fixture / monkeypatch used to validate persistence mechanics under controlled conditions. **Not** production behavior — must **not** be documented or used as a runtime bypass.

**Tests:** `test_quote_snapshot_v2_accept_gate.py`, `test_order_snapshot_v2_convert.py`, `test_step8_snapshot_acceptability.py`

---

## 17. Runtime — Live accept/convert chain (Step 8 live validation)

**Status:** **VALIDATED_WITH_GUARDS** — full Intake V6 chain validated on safe dev data (commit `acf5a28`)

Step 8 dual quote snapshot flow is **VALIDATED_WITH_GUARDS**.

**Validated live chain:**

freeze snapshot V2 → complete pricing review from snapshot V2 commercial total → owner approval → accept quote → convert to order snapshot V2.

| Step | Endpoint | Live result |
|------|----------|-------------|
| Freeze | `POST .../quote-snapshot-v2/freeze/TPL-VOLUMETRIC-LETTERS_v2` | **VALIDATED** — snapshot `QSN2-2026-0003` (`id=3`), `status=frozen`, `readiness=partial_with_owner_decisions` |
| Pricing review | `POST .../intake-v6/quotes/1/complete-pricing-review` | **VALIDATED** — `pricing_totals_source=quote_snapshot_v2`; **no** `/price`/CE/QO |
| Owner approval | `POST .../intake-v6/quotes/1/owner-approval` | **VALIDATED** |
| Accept | `POST .../intake-v6/quotes/1/accept` | **VALIDATED** — `quotes.accepted_snapshot_v2_id=3`; `confirm_owner_decisions_acknowledged=true` |
| Convert | `POST .../intake-v6/quotes/1/convert-to-order` | **VALIDATED** — order `88002` (`ORD-IV6-V2-1782815703-1`); `orders.quote_snapshot_v2_id=3` |

**Runtime evidence:**

- snapshot `QSN2-2026-0003` persisted as **frozen**;
- quote 1 accepted with `accepted_snapshot_v2_id=3`;
- order **88002** created with `quote_snapshot_v2_id=3`;
- `orders.snapshot_v2_json` contains **commercial_price_proposal_snapshot** and **estimated_internal_cost_snapshot**;
- `execution_plan` count unchanged (`1 → 1`);
- **no** execution_tasks created;
- **no** `/price`, CostEngine, or QuoteOrchestrator path used.

**Guarded status:**

- `partial_with_owner_decisions` requires explicit owner decision acknowledgement on accept;
- Step 8 does **not** imply Step 9;
- convert-to-order creates **order snapshot V2 only**, not execution_plan or tasks;
- Step 9 requires **separate owner GO**.

**Backup (live QA):** `backend/dev.backup-before-step8-3-runtime-20260630-133442.db`

**Tests:** **126 pytest PASS** (scoped Step 8 suite including `test_step8_snapshot_acceptability.py`)

**Step 9:** Step 8 convert creates **order snapshot V2 only** — persist draft is a **separate** Step 9 action with owner GO. As of `b12889c`, order `88002` has execution plan draft `id=2` (`source_quote_snapshot_v2_id=3`); **no** execution_tasks or sessions.

---

## 18. Runtime — Step 9 persist draft from Order snapshot V2

**Status:** **VALIDATED_WITH_GUARDS** (commit `b12889c`)

| Step | Endpoint | Result |
|------|----------|--------|
| Preview | `POST .../execution/plan-v2/preview/88002` | **VALIDATED** — `partial_missing_planning_minutes`; 12 task candidates; `no_write=true` |
| Persist draft | `POST .../execution/plan-v2/from-order/88002` | **VALIDATED_WITH_GUARDS** — plan `id=2`; service-level QA **PASS**; HTTP **pending backend restart** |

**Persist evidence:**

- `execution_plan.id=2`, `order_id=88002`, `plan_source=order_snapshot_v2`
- `source_quote_snapshot_v2_id=3` (snapshot `QSN2-2026-0003`)
- `tasks_json` contains **12** `planned_tasks`, **17** `planned_operations`
- Idempotency: second call → `already_exists`, no duplicate row
- **No** execution_tasks; **no** sessions; **no** Employee Mobile; **no** `/price`/CE/QO

**Backup (persist QA):** `backend/dev.backup-before-step9-plan-persist-20260630-140648.db`

**Blocked next:** `materialize-tasks` — **NEEDS OWNER GO**

---

## 11. Forbidden behavior

| Interzis |
|----------|
| Intake live offer → official quote without snapshot |
| /price as permanent fix without realignment |
| Reprice Quote 4 |
| Modify accepted order commercial from actuals |
| PUT financial fields on locked/V2 order | Slice 10.1 guard — use dedicated flows only |
| Task catalog bypassing snapshot product_definition |
| Single-field grand_total without commercial/internal split |

---

## 12. Acceptance criteria

| Criteriu | OK când |
|----------|---------|
| Snapshot has both prices | commercial + internal |
| Order freeze complete | product_definition + commercial |
| No retroactive commercial change | Policy enforced — Slice 10.1 PUT guard |
| Gates documented | pricing-review → owner → accept → convert |
| Misleading UI fixed | Labels Step 11 |
