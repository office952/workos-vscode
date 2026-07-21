# VOLUM ALUMINIU — CP0 Shared Contract Map (FROZEN)

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `6608cdc5` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Subject | `TPL-VOLUM-ALUMINIU_v1` |
| Mode | Contract completion for **separate calculation** — **no activation / no publish** |
| Accepted audit | `VOLUM_ALUMINIU_COMPONENT_CONTRACT_AUDIT.md` (PARTIAL / NO-GO / keep blocked) |

---

## Absolute locks (reconfirmed)

- Do **not** activate or publish `TPL-VOLUM-ALUMINIU_v1`
- Keep VL publication BLOCKED via required inactive child until separate owner GO
- No ComponentTemplate table / PI / CI / parallel calc architecture / Pricing Registry redesign
- No SVG/DWG/DXF parse; no desktop transport; no Build 2; no EP materialization; no mobile
- No logo consolidation with `TPL-VOLUMETRIC-LOGO-RETURN_v1` (appendix only)
- Preserve `modelare_cant` **ml** commercial basis; anti-hourly invariant
- Dirty tree unrelated untouched; allowlist-only commits; no push/PR

---

## Identity (frozen)

| Axis | Canonical value |
|------|-----------------|
| Template code | `TPL-VOLUM-ALUMINIU_v1` |
| Role | child Product Template / `component_only` / required return-cant |
| Mini-module | `modelare_cant` |
| Shared contract key | `volumetric_return_side` |
| Instance schema id | `letter_group_instances.sidewall` |
| PT container | `product_truth.components.return_cant` |
| BOM component_id | `comp_volum_aluminiu_module` |
| Pricing/EIC component_code (legacy stub) | `comp_lateral_litere` |
| Parent | `TPL-VOLUMETRIC-LETTERS_v2` only (`required_module`, `linked_child`, `separate_quote_line`) |
| Admin label (recommend) | **Cant / volum din aluminiu** |
| Role label | Return / cant (sidewall) |
| Implementation | aluminiu |

**Dual-id policy (frozen):** BOM owner = `comp_volum_aluminiu_module`; commercial/EIC rule key remains `comp_lateral_litere` until a dedicated id-unification GO. Documented coupling, not two BOM owners.

---

## Ownership boundary (frozen)

```text
operator/manual OR future external analysis (observe/propose only)
  → operator confirm
  → confirmed Product Truth (components.return_cant)
  → Volum Aluminiu component qty/calc
```

| Concern | Owner |
|---------|-------|
| Observed/proposed perimeter | Source (manual or external analysis provenance) |
| Confirmation action | Operator |
| Confirmed perimeter truth | Product Truth `return_cant.instances[].geometry.confirmed_perimeter_m` |
| Perimeter requirement / unit / validators / transform to qtys | Component contract |
| Materials / finishes / ops / internal cost refs | Child PT + `modelare_cant` |
| File parsing | **Forbidden** in WorkOS |

---

## Canonical input bag (reuse — no parallel names)

| Field | Path | Unit | Notes |
|-------|------|------|-------|
| Evidence perimeter | `geometry.evidence_perimeter_m` (from `quote_geometry.letter_perimeter_m`) | **m** | Observe/propose only; **never** drives separate calc |
| Confirmed perimeter | `geometry.confirmed_perimeter_m` | **m** | Required for separate calc / CPP-EIC component slice |
| Perimeter source | `geometry.perimeter_source` | enum | `missing` \| `evidence_only` \| `operator_confirmed` \| `imported_verified_truth` \| `system_migration_verified` |
| Confirmed source | `geometry.confirmed_perimeter_source` | enum | subset of confirmed sources only |
| Confirmation state | `instances[].confirmation_state` | enum | `missing` \| `draft` \| `blocked` \| `confirmed` |
| Confirmation source | `instances[].confirmation_source` | enum | `operator_component_confirmation` \| `imported_verified_truth` \| `system_migration_verified` |
| Depth / material profile | `material_profile.width_mm` | **mm** | Gates **30 / 60 / 80 / 100** only |
| Finish | `finish_variant` + pricing_keys | — | stock / Oracal / RAL |
| Layer mapping | `layer_group_ids` + `source_ref` | — | required for confirmed |

Upstream evidence bags (not confirmation SoT):

- `quote_geometry.letter_perimeter_m` → evidence only
- `finish_setup.letter_group_instances[].geometry.perimeter_m` → per-group evidence / instance geometry
- Row confirm / finish_setup.confirmed / Step1 → **forbidden** as component confirmation alone

Operator confirm input (typed bag, not new parallel top-level):

```text
finish_setup.return_cant_component_confirmation.instances.<instance_key> = {
  confirmed_perimeter_m: number (>0),
  confirmed_perimeter_source: "operator_confirmed" | "imported_verified_truth" | "system_migration_verified",
  confirmation_source: "operator_component_confirmation" | ...,
  confirmed_by?: string,
  confirmed_at?: ISO-8601
}
```

Bridge projects this into `product_truth.components.return_cant`.

---

## Unit freeze + trace

**Canonical linear unit for aluminium return qty:** **metre (`m`)**.  
Commercial display synonym for ml line: **1 ml = 1 m** (no conversion; same magnitude).

| Stage | Field | Unit | Conversion owner |
|-------|-------|------|------------------|
| Intake evidence | `quote_geometry.letter_perimeter_m` | m | External/manual observe |
| PT confirmed | `confirmed_perimeter_m` | m | Operator confirm → PT |
| Component qty | `return_profile_linear_meter` / commercial qty | m (= ml basis) | Component |
| CPP | `modelare_cant_aluminiu` / `VOL_V2_RETURN_PROFILE_ML` | ml (= m) | Commercial rules (no redesign) |
| EIC | `INT_VOL_V2_RETURN_ML` | ml (= m) | Internal rules |
| Depth | `return_depth_mm` / `material_profile.width_mm` | mm | Component gate |
| Wrap/paint area | formula outputs | m² | Child formulas |

**Rounding:** qty to **6 decimal places** (match letter_group authority); depth must be exact integer gate value.  
**Fail closed:** unknown unit, non-positive perimeter, missing confirmation → no separate calc.

---

## Depth gate freeze

| Surface | Allowed |
|---------|---------|
| Material / bridge / FE `ALLOWED_RETURN_DEPTH_MM` | **30, 60, 80, 100** |
| Form contract `return_depth_mm` options | Align to **30, 60, 80, 100** (remove 40/120 mismatch) |

---

## Quantity / materials / finishes / ops (component-owned)

| Output | Owner | Evidence |
|--------|-------|----------|
| Profile linear m | Child mats `return_profile_linear_meter` | seed child PT |
| Adhesive | `MAT-ADEZIV-CANT-LITERE` | child |
| Oracal wrap | `MAT-ORACAL-*` + wrap formula | child + finish gate |
| RAL paint | `MAT-VOPSEA-RAL*` + `PAINTING` | child + finish gate |
| Forming op | `RETURN_PROFILE_MACHINE_FORMING` | child |
| Face bonding | `RETURN_PROFILE_FACE_BONDING` → Aggregate `modelare_cant` | child |
| Commercial ref | `modelare_cant_aluminiu` ml | commercial_rules_v2 |
| Internal cost | `INT_VOL_V2_RETURN_ML` ml | internal_cost_rules_v2 |

Parent VL materials/ops for cant remain **0** (handoff already done).

---

## Separate calculation preview (frozen)

| Item | Value |
|------|-------|
| Endpoint | `POST /api/v1/product-system/templates/{template_code}/separate-calculation-preview` |
| Allowed template | `TPL-VOLUM-ALUMINIU_v1` only (this build) |
| Persist | **None** — no PT / Quote / Order / EP write |
| Idempotent | Same input → same output |
| Calc driver | **Only** confirmed perimeter (+ depth/finish gates) |
| Commercial line filter | `modelare_cant` / `modelare_cant_aluminiu` |
| Activation required? | **No** — inactive child may still preview contract-complete inputs |

If architecture cannot host this via existing product-system preview patterns → **STOP**.

---

## Readiness / publication (frozen)

| Gate | Behavior |
|------|----------|
| Publication / activation | Remains **BLOCKED** (`KNOWN_REQUIRED_INACTIVE_CHILD`) |
| Contract completeness | New honesty findings for perimeter confirmation / depth / separate-calc readiness |
| Auto-activate | **Forbidden** |

---

## UI (minimal)

| Surface | Change allowed |
|---------|----------------|
| Admin human name | Prefer **Cant / volum din aluminiu** |
| Ownership card | Surface confirmation + separate-calc status honestly |
| Intake return fields | Depth options already FE-gated; no general polish |
| Screenshots | Required for any UI change |

---

## Logo appendix (no consolidation)

| Letters | Logo |
|---------|------|
| `TPL-VOLUM-ALUMINIU_v1` | `TPL-VOLUMETRIC-LOGO-RETURN_v1` (separate active template) |
| Shared concept `volumetric_return_side` | Different runtime module path |

---

## Forbidden field inventories

Do **not** invent parallel:

- `aluminiu_perimeter_m` / `cant_ml` / `sidewall_length_m` as new SoT names
- Hourly commercial basis for `modelare_cant`
- Auto-copy evidence → confirmed without operator/verified source
- Silent fallback to unconfirmed parent perimeter for **separate** calc

---

## Allowlist (this build)

1. `feat(product-system): complete aluminium return input and provenance contract`
2. `feat(product-system): close aluminium return quantity and operation ownership`
3. `feat(product-system): add safe separate calculation preview and readiness`
4. `fix(product-system-ui): clarify aluminium return contract and confirmation`
5. `test(product-system): prove aluminium return separate calculation boundaries`
6. `docs(qa): commit audit and completion evidence`

---

## Agents (after freeze)

| Agent | Scope |
|-------|-------|
| A | Input + PT confirmation honesty |
| B | Quantity ownership |
| C | Materials / finishes / ops evidence |
| D | CPP/EIC boundary (ml, no redesign) |
| E | Separate calc preview (read-only) |
| F | Minimal UI |
| G | QA / readiness / report |

## Checkpoints

| CP | Meaning |
|----|---------|
| CP0 | This map frozen |
| CP1 | Input/provenance/confirmation + depth align |
| CP2 | Qty + ops ownership |
| CP3 | Separate preview + readiness (publication still blocked) |
| CP4 | UI + tests green for allowlisted scope |
| CP5 | Final report + worklog + docs commit |

**CP0 STATUS: FROZEN**
