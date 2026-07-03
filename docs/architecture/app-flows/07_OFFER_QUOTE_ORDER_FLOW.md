# Offer / Quote / Order Flow

**Current status:** VALIDATED_WITH_GUARDS

---

## 1. Purpose

Move from **draft quote** through **frozen dual snapshot**, owner gates, **accept**, and **order convert** — freezing commercial promise and internal estimate without creating execution plan.

---

## 2. Current status

**VALIDATED_WITH_GUARDS** — live chain on fixture: freeze → pricing review → owner approval → accept → convert; order `88002`, snapshot `QSN2-2026-0003`.

---

## 3. Pages / UI surfaces

| Route/Page | Component/File | Role | Reads | Writes | Status | Risk |
| ---------- | -------------- | ---- | ----- | ------ | ------ | ---- |
| Intake V6 | confirm/handoff cards | Spine UX | commercial-spine-state API | spine POSTs | VALIDATED_WITH_GUARDS | — |
| `/quotes`, `/quotes/:id` | `Quotes` | Quote admin | entities/quotes | status, notes | PARTIAL | Legacy price UI |
| `/orders`, `/orders/:id` | `Orders` | Order admin | orders API | PUT guarded | VALIDATED_WITH_GUARDS | Slice 10.1 immutability |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| POST | `.../quote-snapshot-v2/preview/{template}` | `quote_snapshot_v2.py` | Snapshot preview | CPP+EIC+PD+Agg | — | VALIDATED | — |
| POST | `.../quote-snapshot-v2/freeze/{template}` | same | Persist snapshot | compose | `quote_snapshot_v2` | VALIDATED_WITH_GUARDS | — |
| GET | `.../quote-snapshot-v2/{id}` | same | Load snapshot | DB | — | VALIDATED | — |
| POST | `/api/v1/intake-v6/quotes/{id}/complete-pricing-review` | intake_v6 | Pricing review gate | snapshot commercial total | quote notes | VALIDATED | — |
| POST | `.../owner-approval` | intake_v6 | Owner gate | snapshot | quote notes | VALIDATED | — |
| POST | `.../accept` | intake_v6 + accept gate | Accept quote | snapshot V2 | quote status, `accepted_snapshot_v2_id` | VALIDATED_WITH_GUARDS | partial readiness ack |
| POST | `.../convert-to-order` | `order_snapshot_v2_convert_service` | Create order | accepted snapshot | `orders`, `snapshot_v2_json` | VALIDATED | No plan/tasks |
| POST | `/api/v1/entities/quotes/price` | `quotes.py` | Legacy | CE | quote lines | DEAD_LEGACY_RISK | Not V2 |

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `quote_snapshot_v2_service.py` | Build/freeze | workspace_id | QuoteSnapshotV2 | VALIDATED_WITH_GUARDS | SUPPORTED_TEMPLATES |
| `quote_snapshot_v2_accept_gate_service.py` | Accept validation | snapshot | blockers | VALIDATED | owner_decisions |
| `order_snapshot_v2_convert_service.py` | Order convert | accepted snapshot | OrderSnapshotV2 JSON | VALIDATED | no reprice |
| `intake_v6_quote_to_order_service.py` | IV6 spine orchestration | quote_id | accept/convert | VALIDATED_WITH_GUARDS | — |
| `models/quote_snapshot_v2.py` | Persistence | — | ORM | VALIDATED | — |
| `models/orders.py` | Order row | — | `snapshot_v2_json`, `quote_snapshot_v2_id` | VALIDATED | — |
| `schemas/order_snapshot_v2.py` | Frozen order payload | — | dual snapshots embedded | VALIDATED | `no_reprice_policy` |

---

## 6. Data contract

**Quote accept linkage:** `quotes.accepted_snapshot_v2_id` → row in `quote_snapshot_v2`

**Order Snapshot V2 (`orders.snapshot_v2_json`):**

| Field | Meaning |
| ----- | ------- |
| `accepted_commercial_total` | Frozen client total |
| `estimated_internal_total` | Frozen internal estimate |
| `product_definition_snapshot` | Frozen PD |
| `product_aggregate_snapshot` | Frozen aggregate + task_rules |
| `commercial_price_proposal_snapshot` | Frozen CPP |
| `estimated_internal_cost_snapshot` | Frozen EIC |
| `quote_snapshot_v2_id` | Lineage |
| `no_reprice_policy` | true |

**Convert does NOT create:** `execution_plan`, `operational_tasks`, sessions.

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| Intake V6 + CPP/EIC | freeze input | Quote Snapshot V2 | persist | STRONG | — |
| Quote Snapshot V2 | accept | Quote row | accepted_snapshot_v2_id | STRONG | — |
| Quote Snapshot V2 | convert | Order Snapshot V2 | copy JSON | STRONG | — |
| Order Snapshot V2 | manual/API | ExecutionPlan V2 | separate POST preview/persist | STRONG | Not automatic at convert |

---

## 8. Source of truth

| Stage | Source |
| ----- | ------ |
| Draft quote | `quotes` row — **unpriced by design** (`grand_total=0`) |
| Official offer candidate | **Quote Snapshot V2** after freeze |
| Accepted commercial | **Accepted snapshot** + quote accept metadata |
| Order promise | **Order Snapshot V2** at convert |

---

## 9. What must not happen

- Accept without frozen snapshot V2 (V2 path).
- Convert without accept + pricing review + owner approval gates.
- Reprice accepted snapshot in place.
- Create execution_plan at convert.
- Use `/price` output as V2 canonical commercial truth.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| Draft grand_total=0 vs preview | MEDIUM | by design | UI confusion | Step 11 |
| Legacy quotes on `/price` | HIGH | parallel path | Commercial model drift | Deprecate label |
| Partial readiness accept | MEDIUM | owner_decisions ack | Quality | Document guards |
| Batch order PUT was bypass | LOW | fixed 453932f | — | Monitor |

---

## 11. Owner decisions

None currently known for accept/convert (execution DEC-* are downstream).

---

## 12. Verification checklist

```powershell
# Worklogs: step8 live freeze accept convert qa
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_quote_snapshot_v2*.py -q  # targeted
```

Fixture: quote snapshot `id=3`, order `88002`, `quote_snapshot_v2_id=3`.

---

## 13. Next safe step

New volumetric jobs: complete Step 8 spine only; then ExecutionPlan preview from order (separate step).
