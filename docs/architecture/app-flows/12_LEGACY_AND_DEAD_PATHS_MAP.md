# Legacy and Dead Paths Map

**Current status:** DEAD_LEGACY_RISK

---

## 1. Purpose

Classify **frozen, legacy, misleading, and dead** paths so operators and agents do not use them as canonical V2 truth. Step 12 cleanup **NOT_STARTED** — label first, delete only with per-piece owner GO.

---

## 2. Current status

**DEAD_LEGACY_RISK** — parallel intakes, `/price`, CE/QO commercial misuse, V3/V4 task dry-run, and unified pricing registry remain callable or visible.

---

## 3. Pages / UI surfaces

| Route/Page | Component/File | Role | Reads | Writes | Status | Risk |
| ---------- | -------------- | ---- | ----- | ------ | ------ | ---- |
| `/intake/:id` | `IntakeLegacyRoute` | Legacy intake | old intake | — | DEAD_LEGACY_RISK | Parallel |
| `/inventory/pricing` | `Pricing` | Registry hub | mixed registry | admin | DEAD_LEGACY_RISK | Hourly rates |
| `/quotes` + price actions | `Quotes` | Legacy price | CE | quote lines | FROZEN | cost-plus |
| Intake task-preview | IV6/IV4 panels | Catalog dry-run | V3/V4 catalog | — | DEAD_LEGACY_RISK | ≠ Step 9 |

---

## 4. Backend routes

| Method | Route | Router/File | Purpose | Status | Risk |
| ------ | ----- | ----------- | ------- | ------ | ---- |
| POST | `/api/v1/entities/quotes/price` | `quotes.py` | Legacy universal price | **FROZEN** | HIGH_RISK_MINUTES_AS_PRICE |
| POST | `/api/v1/entities/quotes/{id}/price` | `quotes.py` | Legacy reprice | **FROZEN** | Reprice risk |
| * | `/api/v1/intake-v3/*` | `intake_v3_*` | V3 workspace | **LEGACY** | Parallel intake |
| * | `/api/v1/intake-v4/*` | `intake_v4_*` | V4 workspace | **LEGACY** | Task dry-run source |
| * | `/api/v1/intake-v5/*` | `intake_v5` | V5 projects | **LEGACY** | — |
| POST | `/api/v1/product-system/simulate-cost` | cost simulation | CE sim | **ANALYTICS_ONLY** | Not commercial |
| GET | `/api/v1/product_system/preview/{order_id}` | execution output | Old preview | **LEGACY_RISK** | Parallel to plan-v2 |

---

## 5. Services / schemas / models

| File | Role | Status | Notes |
| ---- | ---- | ------ | ----- |
| `quote_orchestrator.py` | Legacy quote pricing | **FROZEN** | `_apply_commercial` cost-plus |
| Cost Engine services | Internal cost | **FROZEN** for commercial | per_hour pre-quote risk |
| `intake_v4_task_generation_dry_run_service.py` | Catalog tasks | **DEAD_LEGACY_RISK** | IV6 wraps V4 |
| `pricing_registry_service.py` | Unified hub | **DEAD_LEGACY_RISK** | 7I separation pending |
| `product_system_execution_output_service.py` | Old execution preview | **LEGACY_RISK** | Forbidden on V2 plan path |

---

## 6. Data contract

**Legacy quote after `/price`:** `line_items`, `grand_total` from CE — **not** dual snapshot V2.

**Frozen intent list (doc 20):** no Quote 4 reprice; no `/price` fix; no CE rewrite ad-hoc.

---

## 7. Links to previous and next systems

| Path | Canonical replacement | Strength of replacement |
| ---- | --------------------- | --------------------- |
| `/price` | Quote Snapshot V2 freeze | STRONG on pilot |
| IV3/IV4 task preview | ExecutionPlan V2 from order snapshot | STRONG when plan exists |
| CE commercial | CPP + EIC previews | IMPLEMENTED_PREVIEW_ONLY |
| Pricing registry hub | 7I separated tabs | NOT_STARTED |

---

## 8. Source of truth

**Canonical V2 volumetric:** Intake V6 → Snapshot V2 → Order Snapshot V2 → ExecutionPlan V2.

**Everything in section 4 table is NOT canonical** for new production quotes unless explicitly labeled legacy compat.

---

## 9. What must not happen

- Delete legacy routes before Step 12 owner GO per piece.
- Extend `/price` or CE as commercial fix.
- Reprice Quote 4.
- Route new volumetric quotes through legacy price.
- Auto-cleanup dossier/V3 catalog without canonical proof.

---

## 10. Gaps / risks

| Gap | Severity | Evidence | Blocks what | Recommended action |
| --- | -------- | -------- | ----------- | ------------------ |
| `/price` callable | HIGH | quotes router | Wrong commercial model | Block new quotes; Step 11 label |
| V3/V4 intakes live | MEDIUM | routers exist | Fragmentation | Step 12 classify |
| Misleading UI on pricing page | HIGH | unified registry | Operator trust | 7I + Step 11 |
| Mock/simulated data in tests only | LOW | test fixtures | — | Keep out of prod path |

---

## 11. Owner decisions

Step 12: **per-piece** delete/archive — all **PENDING_OWNER**.

Feature flag for `/price` during transition — **PENDING_OWNER** (roadmap UNKNOWN).

---

## 12. Verification checklist

```powershell
Select-String -Path backend\routers\quotes.py -Pattern "/price"
Get-ChildItem backend\routers\intake_v*.py
Select-String -Path docs\architecture\realignment\20_ROADMAP_STEPS_7G_TO_12.md -Pattern "Frozen"
```

---

## 13. Next safe step

Label legacy paths in UI (Step 11); do not delete until canonical route stable (Doc 21 Faza 9).

---

## Classification table

| Piece | Tag | Action now |
| ----- | --- | ---------- |
| POST `/quotes/price` | FROZEN | Do not use for V2; label |
| QuoteOrchestrator commercial | FROZEN | No V2 snapshot imports |
| Cost Engine per_hour pre-quote | HIGH_RISK_WRONG_DIRECTION | Internal only target |
| Intake V3/V4/V5 routers | LEGACY_COMPATIBILITY | Route volumetric to V6 |
| IV6 task dry-run (V4) | MISLEADING_UI | Label non-authoritative |
| Employee Mobile on empty plan | FROZEN | final-final only |
| product_system_execution_output | LEGACY_RISK | Do not use vs plan-v2 |
| Step 12 deletion | NOT_STARTED | Owner GO per piece |
