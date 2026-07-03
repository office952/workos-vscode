# TPL-VOLUMETRIC-LETTERS — Pricing Input Adapter

**Service:** `backend/services/intake_v3_pricing_input_adapter.py`  
**Status:** ✅ implemented (in-memory) — **nu** modifică pricing runtime  
**E2E:** consumat de `intake_v3_workspace_preview_service` (preview shell)

---

## Rol

```text
IntakeV3Workspace → build_pricing_input_candidate() → PricingInputAdapterResult
```

**Regulă critică:**

```text
PricingInput Adapter maps facts. CostEngine calculates prices.
```

---

## Implementat

| Funcție | Rol |
|---------|-----|
| `build_pricing_input_candidate()` | map workspace → candidate + quote_input_payload |
| `validate_pricing_input_candidate()` | fără chei preț, fără inventory mutation |
| `summarize_pricing_input()` | summary pentru docs/tests |

---

## Ce include candidate

- template + support mode (`no_shared_support` / `shared_support_pending`)
- production counts (18/27/9)
- dimensions
- finish summary
- material summary (estimate only)
- operation flags
- finish variation notes (`finish_variation_notes`, `requires_grouped_finish_review`) — preview only, no formulas
- readiness summary (blockers/warnings)
- quote readiness gate surfaces pricing preview summary in pre-quote review (no final price)
- dry-run contract references pricing input candidate without invoking CostEngine
- guard policy keeps real quote creation disabled-by-default (dry-run allowed)
- commercial quote bridge maps pricing input candidate as preview_only — no CostEngine, no final price
- quote creation enablement policy marks `FINAL_PRICE_NOT_CALCULATED` as real-creation blocker only — not invented at preview stage
- snapshot policy v1 requires `pricing_input_candidate_snapshot` as reference only until CostEngine enablement build
- guarded draft quote creation stores pricing candidate in snapshot but sets `requires_pricing_review=true` — no CostEngine call
- draft quote review GET exposes pricing handoff checklist and blocked accept/convert — still no CostEngine
- pricing review completion POST records manual totals in Quote + `pricing_review` audit — priced draft only; accept/convert still blocked
- accept/convert readiness GET evaluates separate accept vs convert preview
- guarded accept POST (`draft→priced→accepted`) records `accept_decision` — convert via separate guarded POST
- guarded convert POST (`accepted→Order locked`) records `convert_decision` — production still separate

---

## Boundary

| Nu face | Detaliu |
|---------|---------|
| Calculează preț | fără total_price, unit_price, margin, tva |
| CostEngine | neatins |
| Endpoint quote | neatins |
| DB / Quote / Order | neatins |
| Material Price Registry | neatins |
| Inventory mutation | `inventory_mutation_allowed=false` |

---

## Build viitor

Mapping final către endpoint quote real = integrare separată după review owner.
