# F7E Stage A — Commercial-Law Matrix

Read-only inventory of **existing CANONICAL commercial truth** for finishes (not EIC/internal costs). Sources read in full:

- `backend/data/commercial_rules_volumetric_v2.py` (the live CPP rule table)
- `backend/services/commercial_price_proposal_service.py` (rule evaluation: `_material_gate_matches`, registry lookup, minimum-charge special cases)
- `backend/services/shared_vinyl_material_catalog.py`, `backend/services/intake_v4_oracal_face_pricing_service.py`, `backend/services/intake_v4_ral_paint_rules_service.py` (EIC-side, informational only)
- `backend/seeds/seed_volumetric_owner_confirmed_prices.py`, `backend/seeds/seed_volumetric_workcenter_rates.py`, `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py` (Pricing Registry seed data)
- `frontend/src/features/product-system/canonicalFinishEnumMap.ts` + `docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md` (owner ownership decision, 2026-07-09, HEAD `0a4a346`)
- ACM capture evidence: `docs/qa/workos-f7d-.../captures/E_acm_shell__*.json`

**No rates are invented in this document.** Every rate cited below is quoted from an existing source file with its exact value; anything without a source citation is marked missing.

---

## 0. The proven differential-pricing pattern (positive control)

Two patterns already exist and work correctly in `commercial_rules_volumetric_v2.py`, proven by Agent B's control-group probe (AGENT-B-F009, +10.00 RON delta paper→Forex):

1. **`material_gate_path` + `documented_unit_price`** — e.g. `sablon_montaj_hartie` (`material_gate_path="finish_setup.mounting_template_material_type"`, `material_gate_value="paper"`, flat owner-documented EUR/m²) vs `sablon_montaj_forex` (same gate, `material_gate_value="forex"`, different RON/m² dev-bridge rate). Two `CommercialRuleDefinition` rows, mutually exclusive by gate value.
2. **`registry_pricing_code` lookup** — e.g. `logo_print` → `LARGE_FORMAT_PRINT`, `logo_laminate` → `LAMINATION`, `logo_application` → `FACE_VINYL_APPLICATION_LABOR`, `montaj` → `SITE_INSTALLATION_STANDARD`. `_load_registry_operation_rate(db, registry_pricing_code)` resolves the live Pricing Registry row; `fail-closed` (sets `owner_required=True`, appends `registry_lookup_missed:*` warning) if the registry row is missing.
3. **Minimum-charge floor** — `commercial_price_proposal_service.py:591-601` special-cases `pricing_rule_code in {"ACM_BOXED_ASSEMBLY_M2_MIN", "LETTERS_ACM_PACK_M2_MIN"}` to apply `max(quantity × unit_price, MIN_EUR)`. Proven mechanism for a "commercial minimum" business rule that isn't a simple per-unit rate.

Any finish row below marked **GO for branch** can reuse pattern 1 or 2 without inventing new mechanism. Any row needing a floor (RAL minimum) can reuse pattern 3.

### Legibility note — an existing style debt in the reused pattern

`commercial_price_proposal_service.py:592,598` does `from data.commercial_rules_volumetric_v2 import ACM_BOXED_ASSEMBLY_MIN_EUR` **inside** the function body (inline import), which conflicts with this workspace's `no-inline-imports` rule. This is pre-existing, out of F7E Stage A's read-only scope, but flagged now so G1 (§ implementation) moves those two constants to the top-level import block instead of copying the inline pattern for the new RAL-minimum branch.

---

## 1. The flat `finisaje_colantare_vopsire` line — legitimate scope vs abuse

```python
# commercial_rules_volumetric_v2.py:142-156
CommercialRuleDefinition(
    line_code="finisaje_colantare_vopsire",
    ...
    quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
    documented_unit_price=DEV_BRIDGE_FINISH_RON_M2,   # = 35.0 RON/m² (module docstring line 48-55)
    warnings=("Unconfirmed finish groups may require owner review before numeric pricing.",),
)
```

- **File-level docstring, line 1-5**: *"Temporary local read-only commercial price rules for volumetric letters v2 (Step 7G)... Step 8 dev bridge — interim RON commercial unit prices for live V6 QA only. NOT production Pricing Registry (Step 7I)."*
- **Legitimate scope (by the code's own declared intent):** a single interim placeholder so the CPP preview endpoint returns *some* non-zero, non-blocking finish line for QA/demo purposes while the real differentiated rules are authored. It is explicitly self-documented as temporary and non-production.
- **Actual current abuse:** the rule has `criticality="critical"` and **no `module_gate` and no `material_gate_path` at all** — it fires unconditionally on `letter_face_area_m2` for every workspace with an active finish module, including `face_finish_type="none"` (per Agent B's delta-matrix §A "none" row, the line still charges 35 RON/m² even when the operator picked no finish). It is standing in for at least 4 distinct, already-rated finish families (Oracal face, Oracal cant wrap, RAL cant, print/laminate) that never differentiate from it, and for the "no finish" case that shouldn't be charged at all.
- **Verdict:** this line is a defect in its current unconditional form, not a "GO" rate. It should be narrowed to genuinely uncovered/legacy cases only (or removed once G1 branches are authored) — not treated as a commercial policy in itself.

---

## 2. Finish-by-finish matrix

| Finish | Technical meaning | Commercial policy | Rule/code | Unit | Rate owner | Status |
|---|---|---|---|---|---|---|
| **Fără finisaj** (`face_finish_type=none`) | No face treatment; raw substrate | Should be **zero** finish charge | None dedicated — currently mis-absorbed by `finisaje_colantare_vopsire` (fires anyway, 35 RON/m²) | m² | N/A (should be $0) | **DEFECT, not a rate gap.** Fix = gate the flat line off for `none`, or split it away entirely once G1 branches exist. |
| **Stock cant colors** (Alb/Negru/Auriu/Argintiu — `white_aluminum`/`black_aluminum`/`gold_aluminum`/`standard_aluminum`) | Aluminum cant profile in stock finish, no applied treatment | Zero additional finish tariff — cost is inside the cant-profile-by-depth + forming/bonding line | `modelare_cant_aluminiu` / `VOL_V2_RETURN_PROFILE_ML` (already active, unrelated to finish selection) | ml (perimeter) | N/A by design | **GO — already correct.** `canonicalFinishEnumMap.ts:cant_stock_color`, `activationStatus="owner_confirmed"`. Confirmed zero-delta in probe (AGENT-B-F008), correct-by-design. |
| **Oracal face** (641/651/8500 on letter face) | Vinyl film applied to face | Not yet activated in CPP; material+labor rates exist and are owner-confirmed | Material: `MAT-ORACAL-641`=6.5, `MAT-ORACAL-651`=9.0, `MAT-ORACAL-8500`=20.0 EUR/m² (`seed_volumetric_owner_confirmed_prices.py:205-259`, `shared_vinyl_material_catalog.py:16-18`, `pricing_source=OWNER_CONFIRMED_INTERIM`). Labor: `FACE_VINYL_APPLICATION_LABOR` = 5 EUR/m² (`seed_intake_v5_volumetric_letters_pricing.py:62`, seeded as a workcenter rate `seed_volumetric_workcenter_rates.py:216`) | m² | Material rates: owner-confirmed. Labor rate: owner-confirmed. **CPP consumption:** none exists. | **GO for branch, with one caveat to surface to Owner explicitly:** `canonicalFinishEnumMap.ts` marks `face_oracal_641/651/8500` `activationStatus: "blocked"` with note *"FINISH workshop blocked până la FACE boundary workshop"* — this is a Product System component-ownership gate, not a rate gap, and does not by itself forbid the separate legacy `commercial_rules_volumetric_v2.py` engine (which is pre-Product-System and already wires `registry_pricing_code`/`material_gate_path` for other lines) from consuming the already-confirmed `MAT-ORACAL-*`/`FACE_VINYL_APPLICATION_LABOR` keys the same way `sablon_montaj`/`logo_*` do. **Recommend Owner explicitly confirm this reading before G1 authors face-Oracal rows**, since the "blocked" tag is real and owner-authored even if scoped to a different system layer. |
| **Oracal cant wrap** (`oracal_wrapped`, cant/return) | Vinyl film wrapped around cant/return profile | Not yet activated in CPP; ownership + rates confirmed, no Product-System-layer block | Material: `MAT-ORACAL-641`/`MAT-ORACAL-651` (same rates as above). Labor: `RETURN_CANT_VINYL_APPLICATION_LABOR` = 1 EUR/ml (`seed_volumetric_workcenter_rates.py:34,229-239`, owner-confirmed note at line 237) | ml (perimeter × width, `quantityBasis: "ml_perimeter_x_width"`) | Owner-confirmed (both material and labor) | **GO for branch — clean case.** `canonicalFinishEnumMap.ts:cant_oracal_wrap`, `activationStatus="owner_confirmed"` (unlike face, no "blocked" flag). Matches `sablon_montaj_forex` pattern exactly: gate on `return_finish_type="oracal_wrapped"`. |
| **Oracal series/color** (e.g. same series, different printed color code) | Color-tier pricing within one Oracal series | **No documented policy either way** | None | — | **OWNER_DECISION_REQUIRED.** Delta-matrix row A confirms: switching `face_oracal_code` within the same series (021→032) is zero-delta with *"Unknown (OWNER_DECISION_REQUIRED — no color-tier policy exists)"* as the audit's own expected-value note. Missing field: an owner statement on whether color (not series) ever changes commercial price. Do not invent a color-tier rate. |
| **Vopsit RAL** (cant paint) | RAL-painted cant/return | Ownership + material/labor rates confirmed; separate 100 RON/color commercial-minimum policy also owner-documented | Material: `MAT-VOPSEA-RAL-CANT-30MM`=2.0, `-60MM`=2.5, `-80MM`=3.0, `-100MM`=4.0 EUR/ml (`seed_volumetric_owner_confirmed_prices.py:159-203`). Labor: `RETURN_CANT_RAL_PAINT_LABOR` = 1 EUR/ml (`seed_intake_v5_volumetric_letters_pricing.py:61`, `seed_volumetric_workcenter_rates.py:190`). Minimum: **"100 lei pe culoare RAL"**, `canonicalFinishEnumMap.ts:cant_ral_minimum_policy`, `commercialPolicySource: "cpp_owner_policy"` — explicitly **not** a Pricing Registry rate, a CPP-level commercial floor | ml (perimeter, width-tiered) + owner-policy minimum | Owner-confirmed (material, labor, and the 100 RON floor policy) | **GO for branch — highest-confidence case.** Everything needed (material, labor, floor, and the exact mechanism to implement the floor — §0 pattern 3) already exists and is owner-signed (`canonical_finish_enum_map_owner_decision_v1.md`, decision D, ACCEPT, 2026-07-09). |
| **ACM mass color** (shell face treatment: solid color panel) | Colored ACM sheet as shell face | No canonical entry exists for ACM *finish* differentiation at all (distinct from ACM *construction* materials, which are rated) | None. Existing `acm_panel_face_material` (`ACM_BOXED_MAT_FACE_M2` = 15 EUR/m², `commercial_rules_volumetric_v2.py:287-300`) is a flat base-material rate with **no `material_gate_path`** on any shell-finish kind — confirmed by reading the capture `E_acm_shell__E1_shell_stock_plate.json`: the same 15 EUR/m² line fires with `commercial_unit_price: 15.0` regardless of `shell_finish.face.kind` | m² | Construction material: owner-confirmed (generic ACM sheet). Finish/color differentiation: **not owner-confirmed, not in `canonicalFinishEnumMap.ts` at all.** | **OWNER_COMMERCIAL_RULE_REQUIRED.** Missing: (1) an owner decision on whether ACM mass-color is even a chargeable differentiator vs a stock/no-charge family like cant stock colors, (2) if chargeable, a `canonicalFinishEnumMap.ts` entry + material rate, (3) either way, blocked from live proof today by AGENT-B-F003 (`CRITICAL_GEOMETRY_MISSING` — standalone ACM template preview never reaches rule evaluation). |
| **ACM mirror** | Mirror-finish ACM/aluminum shell face | Not found anywhere in ACM commercial or canonical-enum code | None — no `shell_finish` gate, no canonical entry, no rate reference of any kind for an ACM "mirror" variant (distinct from `mirror_silver`, which is a **cant** stock-color token in `canonicalFinishEnumMap.ts`, not an ACM panel finish) | — | None | **OWNER_COMMERCIAL_RULE_REQUIRED.** Missing everything: no ownership decision, no canonical entry, no rate, no code path. Do not conflate with `mirror_silver` (cant), which is a separate, already-priced (zero-tariff) family. |
| **Other ACM finishes** (`print_laminate`, `oracal_651` as a `shell_finish.face.kind` value per the F7D probe scenarios) | Print/laminate or vinyl-wrapped ACM shell face | Same gap as ACM mass color — no `shell_finish`-gated rule exists in `commercial_rules_volumetric_v2.py` (confirmed: zero matches for `shell_finish` anywhere in `backend/`) | None | — | None | **OWNER_COMMERCIAL_RULE_REQUIRED**, and also blocked live by AGENT-B-F003 same as above. All 4 shell-finish variants probed (`stock_plate`, `oracal_651` ×2 colors, `print_laminate`) returned identical `commercial_total: 34.0` with `status: "blocked"` — no finish-sensitive rule was ever reached, so this row cannot even be scored "zero-delta defect" vs "correct-by-design" yet. |
| **Print/laminate (face, letters)** (`face_finish_type="print_laminate"`) | Printed + laminated face treatment | No CPP rule exists; EIC-side material code exists but uncosted into CPP | `MAT-VINYL-PRINT` = 1.5 EUR/m², `MAT-VINYL-PRINT-LAMINATED` = 10.0 EUR/m² (`seed_intake_v5_volumetric_letters_pricing.py:34-35`) exist as EIC/material-registry rows; no `CommercialRuleDefinition` branch consumes them | m² | Material rate exists in registry; no owner CPP-activation decision found | **OWNER_COMMERCIAL_RULE_REQUIRED** for the CPP branch itself (rate exists, but `canonicalFinishEnumMap.ts:face_print_laminate` is `activationStatus="blocked"` with note *"Chei exacte print/lam în registry — pending confirmare sursă"* — the map's own author was not yet certain which registry keys are authoritative). Falls through to the flat 35 RON/m² line today (§1 abuse). |

---

## 3. Summary — what is genuinely GO vs genuinely blocked on Owner

| Bucket | Finishes | Why |
|---|---|---|
| **GO for branch now** (rate + ownership both proven, mechanism proven) | Oracal cant wrap, Vopsit RAL (cant) | Ownership `owner_confirmed` (not `blocked`) in `canonicalFinishEnumMap.ts`; every material/labor/floor rate cited above traces to an owner-confirmed seed row; the exact `material_gate_path`/registry/minimum mechanisms are already proven elsewhere in the same rule table. |
| **GO for branch, with one Owner confirmation to request first** | Oracal face (641/651/8500) | Rates fully proven (same registry rows as cant, just different `component_code`/`quantityBasis`), but `canonicalFinishEnumMap.ts` explicitly tags face-Oracal `activationStatus="blocked"` pending a Product-System "FACE boundary workshop." The legacy CPP engine is arguably a different layer than that block targets — ask, don't assume. |
| **Already correct, no build needed** | Stock cant colors | Zero-delta is the documented, owner-confirmed design. Confirmed by probe. Keep as reference/regression case. |
| **OWNER_COMMERCIAL_RULE_REQUIRED** | Oracal color-tier (same-series different code), ACM mass color, ACM mirror, other ACM shell finishes, print/laminate face | No owner-confirmed rate and/or no canonical ownership entry exists at all. Do not invent rates for these; return to Owner with the exact missing-field list above per row. |
| **Defect to fix regardless of the above (not a rate question)** | "Fără finisaj" being charged 35 RON/m² anyway | The flat dev-bridge line has no gate; it must stop firing for `none` selections and stop being the silent catch-all for every finish family above once those are branched. |

## 4. Explicit non-invented-rate statement

No numeric rate in this document was authored by this audit. Every EUR/RON figure above is quoted verbatim from an existing seed file, workcenter-rate seed, or `documented_unit_price`/`price_eur_per_sqm` constant already committed to the repository. Where no such figure exists (Oracal color-tier, ACM mass color, ACM mirror, other ACM shell finishes), this document states that explicitly rather than proposing one.
