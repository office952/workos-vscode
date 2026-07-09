# FACE Price Registry Alignment — Owner Decision v1

> **Notă:** Decizie owner pentru alinierea conceptuală FACE draft ↔ Inventory/Pricing Registry.  
> **Nu** activează pricing. **Nu** scrie în Pricing Registry. **Nu** modifică cod runtime.

**Date:** 2026-07-09  
**HEAD la semnare:** `e87f043` — Add FACE estimated material and CNC price draft  
**Owner:** Alex / P-Media  
**Decision source:** Owner chat decision after `FACE_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1`

---

## 1. Status

| Field | Value |
|---|---|
| Decision status | **OWNER_ACCEPTED** |
| Scope | FACE pricing alignment decision only |
| Runtime activation | **NO** |
| Pricing Registry write | **NO** |
| `/inventory/pricing` write | **NO** |
| Product Truth live write | **NO** |
| ProductDefinition bridge | **NO** |
| FINISH workshop | **NO** (blocked until owner accepts moving forward after this doc) |
| Seed / migration / DB | **NO** |

---

## 2. Audit basis

Findings from `FACE_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1` (audit only, PASS):

| Finding | Detail |
|---|---|
| FACE draft authority | Values stored as `OWNER_ESTIMATE_DRAFT`; `readyForPricing: false`; `pricingActive: false` |
| Plexiglas 3 mm registry | `MAT-ACP-FATA-LITERE` = **16 EUR/mp** — registry authority for volumetric letter face material |
| FACE draft 3 mm | **15 EUR/mp** — owner estimate draft (superseded conceptually by this decision) |
| Plexiglas 5 / 10 mm | No active volumetric registry keys; `MAT-PLEXI-*` naming/stubs only |
| CNC registry model | `CNC_ROUTER` = **1.5 EUR/ml per pass** — workcenter/internal/runtime evidence |
| FACE draft CNC | Contour commercial rates: 3 mm **1.00**, 5 mm **1.50**, 10 mm **2.50** EUR/ml contur |
| FACE CNC minimum | **50 lei/lucrare** — owner estimate/policy only; not Pricing Registry rate |
| Audit readiness | `NEED_OWNER_DECISION` — resolved by this document |

**Note on 15 vs 16:** Seed source notes on `MAT-ACP-FATA-LITERE` mention 15 EUR/mp in a **separate premount/ACM context** — not as the plexi face registry rate. Registry authority for face Plexiglas 3 mm remains **16 EUR/mp**.

---

## 3. Owner decisions table

| Area | Decision | Status | Future action |
|---|---|---|---|
| **A. Plexiglas 3 mm material** | `MAT-ACP-FATA-LITERE` at **16 EUR/mp** is registry authority. FACE draft **15 EUR/mp** is superseded **conceptually** by 16 EUR/mp for future alignment. | `owner_confirmed` | Future apply slice may update readonly draft display/value to 16 — **no activation now**. |
| **B. Plexiglas 5 mm** | Keep **25 EUR/mp** as draft-only estimate. No registry key now. | `owner_estimate_draft` | Future owner GO required for key creation or registry alignment. |
| **C. Plexiglas 10 mm** | Keep **50 EUR/mp** as draft-only estimate. No registry key now. | `owner_estimate_draft` | Future owner GO required for key creation or registry alignment. |
| **D. CNC commercial model** | Commercial offer model for FACE CNC uses **contour EUR/ml**, not direct pass model: 3 mm **1.00**, 5 mm **1.50**, 10 mm **2.50** EUR/ml contur. | `owner_confirmed_as_commercial_draft` | Future alignment slice may encode readonly policy draft references — **no registry write now**. |
| **E. CNC_ROUTER workcenter model** | `CNC_ROUTER` **1.5 EUR/ml/pass** remains internal/workcenter/runtime evidence. Does **not** automatically become commercial offer price. | `owner_confirmed_boundary` | Future routing/runtime may use pass model for production/time/internal calculation, separate from commercial contour rates. |
| **F. FACE CNC minimum** | **50 lei/lucrare** remains owner commercial policy. Not Pricing Registry material/service rate. | `owner_confirmed_policy` | Future commercial policy layer may consume it — **no registry write now**. Similar category to RETURN-CANT RAL 100 lei minimum. |
| **G. Pricing activation** | FACE remains **not ready** for active pricing. | `blocked_until_future_GO` | Future explicit owner GO required for any pricing activation. |

---

## 4. Commercial vs internal model boundary

### Commercial offer model (FACE — future, not active)

- Material charged by **bounding/out-of-box** material usage (`face_material_usage_area_m2` from piece boxes).
- CNC charged by **`face_perimeter_length_m` × contour EUR/ml** (thickness-specific commercial rates in §3D).
- **Minimum 50 lei** applied as owner commercial policy when calculated CNC debitare is below threshold.

### Internal / workcenter model (separate — not client-facing price)

- Pass count, pass depth, machine speed.
- **`CNC_ROUTER` 1.5 EUR/ml/pass** — production/routing/time evidence (`intake_v4_cnc_router_pass_policy_service`, workcenter registry).
- **Not** automatically mapped to final commercial offer price.
- **Not** used as direct commercial quote model without owner-approved contour rate layer.

---

## 5. Registry alignment implications

- Future draft apply **may** update Plexiglas 3 mm FACE draft from **15 → 16 EUR/mp** (readonly display/value only).
- **5 / 10 mm** stay draft-only until owner GO.
- **No MAT-\*** keys for 5/10 mm in this decision.
- **No** seed changes, **no** registry write, **no** pricing activation in slices gated by this doc alone.

Cross-reference (readonly):

| Key / model | Role after decision |
|---|---|
| `MAT-ACP-FATA-LITERE` | Registry authority for Plexiglas 3 mm face material |
| `CNC_ROUTER` 1.5 EUR/ml/pass | Internal/workcenter evidence only |
| FACE contour rates (1.00 / 1.50 / 2.50) | Commercial draft policy — not registry |
| 50 lei minimum | Owner commercial policy — not registry |

---

## 6. What remains blocked

- FACE pricing activation
- Pricing Registry write
- Product Truth live write
- ProductDefinition bridge
- Runtime Intake V6 → FACE handoff
- **FINISH workshop** until owner accepts moving forward after alignment doc
- New **MAT-\*** keys for Plexiglas 5/10 mm
- Automatic use of **pass model** for commercial quote
- Quote / Order / Execution changes
- Work Intake exposure

---

## 7. Future allowed slices after this doc

| Slice | Purpose | Registry write? |
|---|---|---|
| `FACE_PRICE_DRAFT_ALIGN_3MM_TO_REGISTRY_V1` | Update readonly FACE draft 15 → 16 EUR/mp | **NO** |
| `FACE_CNC_COMMERCIAL_POLICY_DRAFT_APPLY_V1` | Encode commercial contour model as readonly policy draft | **NO** |
| `FACE_PLEXI_5_10_REGISTRY_KEYS_PLAN_V1` | Plan key names only; no creation without GO | **NO** |
| `FINISH_COMPONENT_TRUTH_WORKSHOP_V1` | Allowed only after owner accepts FACE alignment uncertainty is documented enough | **NO** (FINISH scope separate) |

Any slice that writes Pricing Registry or sets `pricingActive: true` requires **separate explicit owner GO**.

---

## 8. Owner signature

| Field | Value |
|---|---|
| Owner decision | **ACCEPTED** |
| Date | 2026-07-09 |
| Owner | Alex / P-Media |
| Decision source | Owner chat after `FACE_SOURCE_INVENTORY_CROSS_REFERENCE_AUDIT_V1` |
| Signed by | Owner (Alex / P-Media) |

---

## Related documents

- `docs/worklog/owner-input/face_estimated_price_draft_v1.md` — current draft values (15 EUR/mp 3 mm until apply slice)
- `docs/worklog/owner-input/face_component_truth_owner_decision_v1.md` — FACE substrate/geometry boundary
- `docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md` — FINISH vs RETURN-CANT vs FACE finish split
