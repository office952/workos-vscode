# Pricing and Internal Cost Flow

**Current status:** IMPLEMENTED_PREVIEW_ONLY

---

## 1. Purpose

Separate **commercial price proposal** (client: mp/ml/buc/literă/set) from **estimated internal cost** (materials + internal ops). Compose dual snapshot for Step 8. **Not** legacy cost-plus hourly client pricing.

---

## 2. Current status

**IMPLEMENTED_PREVIEW_ONLY** — CPP + EIC preview services and Step 8 snapshot composition **VALIDATED_WITH_GUARDS** on V2 path. Legacy `/price` + CostEngine remain **DEAD_LEGACY_RISK**. Steps 7I registry separation **NOT_STARTED**.

---

## 3. Pages / UI surfaces

| Route/Page | Component/File | Role | Reads | Writes | Status | Risk |
| ---------- | -------------- | ---- | ----- | ------ | ------ | ---- |
| Intake V6 | pricing preview panels | Live preview | CPP/EIC or pricing-input | — | IMPLEMENTED_PREVIEW_ONLY | MISLEADING_UI |
| `/inventory/pricing` | `Pricing` | Registry admin | pricing_registry | admin CRUD | DEAD_LEGACY_RISK | Unified hub |
| `/quotes` | `Quotes` | Quote list/detail | quotes entity | legacy price | PARTIAL | `/price` path |
| `/demo/commercial-spine` | demo | Step 8 demo | snapshot APIs | — | IMPLEMENTED_PREVIEW_ONLY | Dev only |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Reads | Writes | Status | Risk |
| ------ | ----- | ----------- | ------- | ----- | ------ | ------ | ---- |
| POST | `/api/v1/product-system/commercial-price-preview/{template}` | `commercial_price_proposal.py` | CPP preview | workspace, rules | — | IMPLEMENTED_PREVIEW_ONLY | — |
| POST | `/api/v1/product-system/estimated-internal-cost-preview/{template}` | `estimated_internal_cost.py` | EIC preview | aggregate, inventory | — | IMPLEMENTED_PREVIEW_ONLY | — |
| POST | `/api/v1/product-system/quote-snapshot-v2/preview\|freeze/{template}` | `quote_snapshot_v2.py` | Dual snapshot | CPP+EIC+PD+Agg | freeze row | VALIDATED_WITH_GUARDS | — |
| POST | `/api/v1/entities/quotes/price` | `quotes.py` | Legacy price | CE, QO | quote lines | DEAD_LEGACY_RISK | FROZEN intent |
| POST | `/api/v1/entities/quotes/{id}/price` | `quotes.py` | Legacy reprice | CE, QO | quote | DEAD_LEGACY_RISK | No Quote 4 reprice |

**Forbidden on V2 canonical path:** CostEngine, QuoteOrchestrator, `/price` (enforced in snapshot services via import guards).

---

## 5. Services / schemas / models

| File | Role | Input | Output | Status | Notes |
| ---- | ---- | ----- | ------ | ------ | ----- |
| `commercial_price_proposal_service.py` | CPP builder | workspace, PD | lines, total, blockers | IMPLEMENTED_PREVIEW_ONLY | `commercial_rules_volumetric_v2` |
| `estimated_internal_cost_service.py` | EIC builder | aggregate, PD | internal lines, capacity hints | IMPLEMENTED_PREVIEW_ONLY | No hourly totals as commercial |
| `quote_snapshot_v2_service.py` | Dual compose + freeze | workspace/quote | `QuoteSnapshotV2` | VALIDATED_WITH_GUARDS | No CE/QO |
| `quote_orchestrator.py` | Legacy pricing | quote | cost-plus lines | FROZEN | Not V2 canonical |
| `cost_engine_service` (family) | Internal calc | BOM | per_hour risk | FROZEN | Not commercial generator |

---

## 6. Data contract

**CPP preview keys:** `commercial_lines[]`, `commercial_total`, `currency`, `blockers[]`, `unknown_owner_decisions[]`, `provenance[]`

**EIC preview keys:** `lines[]`, `estimated_total`, `capacity_hints[]`, `completeness`, `warnings[]`

**Quote Snapshot V2 (frozen):**

| Field | Role |
| ----- | ---- |
| `commercial_price_proposal_snapshot` | Client offer side |
| `estimated_internal_cost_snapshot` | Internal estimate side |
| `product_definition_snapshot` | Structure |
| `product_aggregate_snapshot` | Technical graph |
| `owner_decisions_snapshot` | Partial readiness ack |

**Rule:** Commercial basis = product rules (mp/ml/buc). Minutes/workcenter rates = internal/capacity only.

---

## 7. Links to previous and next systems

| Previous | Link | Next | Link | Strength | Gap |
| -------- | ---- | ---- | ---- | -------- | --- |
| ProductAggregate | geometry keys | CPP / EIC | preview builders | STRONG | — |
| CPP + EIC | compose | Quote Snapshot V2 | freeze | STRONG | — |
| Quote Snapshot V2 | accept | Order Snapshot V2 | convert copy | STRONG | — |
| Legacy quotes | `/price` | quote lines | CE+QO | LEGACY_RISK | Parallel path |

---

## 8. Source of truth

| Aspect | Source |
| ------ | ------ |
| Official client commercial (V2) | **Frozen Quote Snapshot V2** → Order Snapshot V2 `accepted_commercial_total` |
| Intake live preview | **NOT official** |
| Legacy priced quote | **`/price` output** — deprecated for new V2 |
| Internal estimate at accept | **EIC side of snapshot** |

---

## 9. What must not happen

- Commercial hourly pricing (`rate_per_hour` as client basis).
- `/price` as canonical path for new volumetric V2 quotes.
- CostEngine or QuoteOrchestrator in Step 8/9 snapshot or execution paths.
- Using internal cost × markup as universal commercial formula.
- Repricing Quote 4 or accepted snapshots.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| Legacy `/price` callable | HIGH | `quotes.py` routes | Wrong commercial model | 7I + Step 11 label; block new quotes |
| Doc says 7G NOT STARTED | MEDIUM | README vs code | Agent confusion | Docs sync |
| Pricing Registry unified hub | HIGH | `/inventory/pricing` | CE rates as commercial | Step 7I |
| WC missing blocks legacy quote | MEDIUM | old NOT_READY gates | Wrong blocker class | Reclassify internal vs commercial |

---

## 11. Owner decisions

None currently known for CPP rules beyond template pilot scope. Registry separation needs **7I owner GO**.

---

## 12. Verification checklist

```powershell
Select-String -Path backend\services\quote_snapshot_v2_service.py -Pattern "FORBIDDEN_IMPORT"
cd backend; .\.venv\Scripts\python.exe -m pytest tests/test_commercial_price_proposal_preview.py tests/test_estimated_internal_cost_preview.py -q
```

---

## 13. Next safe step

Use only Snapshot V2 freeze for new volumetric offers; do not call `/price`; owner GO for 7I registry separation.
