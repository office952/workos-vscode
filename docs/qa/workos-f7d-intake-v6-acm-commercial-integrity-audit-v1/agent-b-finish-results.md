# Agent B — Finish Zero-Delta Classification (F7D)

Classification key: **included** (zero-delta is correct — cost already folded into another line or genuinely free), **informational** (a real cost difference exists and is computed somewhere, but by design does not affect the customer commercial price), **missing rule** (a differential rule is planned/anticipated but not implemented — interim/dev-bridge state), **defect** (behaves against a specific, checkable expectation), **OWNER_DECISION_REQUIRED** (no documented policy exists either way).

## Stock finishes (return/cant: Alb, Negru, Auriu, Argintiu)

**Classification: `included` — zero-delta is correct by owner design.**

Evidence: `frontend/src/features/product-system/canonicalFinishEnumMap.ts` entry `cant_stock_color`, `activationStatus: "owner_confirmed"`, `notesRo: "Fără tarif finish suplimentar — cost din profil cant pe adâncime + operații formare/lipire."` (No additional finish tariff — cost comes from the cant profile-by-depth + forming/bonding operations, which ARE separately priced via `modelare_cant_aluminiu` / `VOL_V2_RETURN_PROFILE_ML`, keyed on `return_depth_mm`, unaffected by color). API probe confirms: white/black/gold/silver all → `commercial_total = 577.50`, identical to each other. This is the one finish family where zero-delta is the *documented, intended* behavior, not a gap.

## Oracal (face: 641/651/8500; cant: Oracal 651 wrap)

**Classification: `missing rule` (interim/dev-bridge, self-disclosed) for cant wrap; `missing rule` / borderline `defect` for face.**

Evidence:
- Cant Oracal wrap (`cant_oracal_wrap`) is `owner_confirmed` for **ownership** with explicit planned pricing keys `MAT-ORACAL-641`, `MAT-ORACAL-651`, `RETURN_CANT_VINYL_APPLICATION_LABOR`, `quantityBasis: "ml_perimeter_x_width"` — none of this is wired into the live `commercial_rules_volumetric_v2.py`.
- Face Oracal variants are marked `activationStatus: "blocked"` in the same governance doc ("FINISH workshop blocked până la FACE boundary workshop") — meaning face-vinyl commercial pricing is **not yet owner-authorized to activate at all**, yet the live CPP silently charges a flat 35 RON/m² for it under the generic `finisaje_colantare_vopsire` line regardless of which Oracal series (or none) is chosen. Internal (EIC) material cost IS correctly differentiated 6.5/9.0/20.0 EUR/m² per series in `intake_v4_oracal_face_pricing_service.py` but is explicitly `informational_only` and never consulted by the CPP.
- API probe: all Oracal face series (641/651/8500) and both cant-wrap colors tested → identical `commercial_total = 577.50`.

This is the highest-value P0 pair: the business already knows the material cost spreads >3× between Oracal series, but the customer never sees any of that reflected in the offer.

## Vopsit RAL (return/cant paint)

**Classification: `missing rule` (a specific, documented commercial policy exists and is unimplemented).**

Evidence: `cant_ral_paint` (owner_confirmed ownership, planned keys `MAT-VOPSEA-RAL-CANT-{30,60,80,100}MM` + `RETURN_CANT_RAL_PAINT_LABOR`) and a separate, explicitly commercial (not just internal-cost) policy `cant_ral_minimum_policy`: **documented "100 lei pe culoare RAL"** commercial minimum, `commercialPolicySource: "cpp_owner_policy"`. Internal (EIC) tube-cost model exists (`intake_v4_ral_paint_rules_service.py`, 50 RON/tube per 15 linear meters) but is informational only. API probe: RAL 9016 and RAL 3020 both → `commercial_total = 577.50`, identical to stock and to no-finish. **No 100 RON RAL surcharge of any kind is applied** — this is the clearest, most concrete "missing rule" case since a specific RON figure is already owner-documented and simply not coded into `commercial_rules_volumetric_v2.py`.

## ACM mass color (panel/shell face and volume finish)

**Classification: could not be fully evaluated — blocked by an unrelated geometry-validation defect (P1), not a finish-pricing defect per se.**

Evidence: standalone `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` preview calls with valid ACM geometry (`panel_width_mm`, `panel_height_mm`, `acm_thickness_mm`, `return_depth_mm`) uniformly return `status: "blocked"`, `commercial_blockers: ["CRITICAL_GEOMETRY_MISSING"]` across all four shell-finish variants tested (stock_plate, oracal_651 × 2 colors, print_laminate) — the blocker fires identically regardless of finish, meaning the geometry validator (written for letter-oriented fields) rejects the payload before any finish-sensitive rule can execute. In the live composite workspace, ACM panel material/operation lines DO appear itemized in the "Estimări pe produs" sidebar, but that panel remains gated "1 blocant" (not ready), so no clean live before/after total pair was captured for ACM finish in the time available. Recommend a dedicated follow-up once the geometry-validation gap (P1, see findings) is fixed.

## Mirror (mirror_silver)

**Classification: `OWNER_DECISION_REQUIRED` + a contract-hygiene concern.**

Evidence: `mirror_silver` is listed as a valid `intakeTokens` entry in `canonicalFinishEnumMap.ts` (`cant_stock_color` family) and the backend schema field accepts it without validation error (`return_finish_type: str | None`, no enum constraint) — but the **live UI combobox for cant finish does not offer "mirror" as a selectable option at all** (observed live options: Alb / Negru / Auriu / Argintiu / Vopsit RAL / Oracal 651). It is unclear whether mirror is (a) intentionally deferred to a future UI slice, (b) accessible via some other flow not exercised in this audit, or (c) dead/vestigial. API probe shows it prices identically to stock colors (`commercial_total = 577.50`), consistent with the "no additional tariff" stock-color policy if it is indeed meant to be a stock-family finish — but since it's not reachable from the live UI, this is a UI/contract completeness gap rather than a pricing defect, and is flagged `OWNER_DECISION_REQUIRED` on whether mirror should be exposed as a selectable option.

## Other (print/laminate face; confirmation state; empty/absent finish groups)

**Classification: mixed — `missing rule` (print/laminate) and `defect` (warning theater on confirmation state).**

- `print_laminate` face finish: no dedicated commercial rule exists at all in `commercial_rules_volumetric_v2.py`; it falls through to the same flat `finisaje_colantare_vopsire` line. `missing rule`.
- Confirmation state (`confirmed: true/false`, empty list, absent field): all four variants produce `status: "ready"` with an **identical numeric total** (577.50) and an identical or near-identical warning ("Unconfirmed finish groups may require owner review before numeric pricing."). The warning text itself implies pricing *should* be deferred/gated for unconfirmed groups, but the actual numeric behavior never changes. Classified `defect` — the system is not honest about what "unconfirmed" means for the number the customer will see.

## Summary table

| Family | Classification | P-level | Root evidence |
|---|---|---|---|
| Stock cant colors (Alb/Negru/Auriu/Argintiu) | included (correct) | — | `canonicalFinishEnumMap.ts:cant_stock_color` |
| Oracal face (641/651/8500) | missing rule / borderline defect | P0 | `commercial_rules_volumetric_v2.py:142-156`; `intake_v4_oracal_face_pricing_service.py` |
| Oracal cant wrap | missing rule | P0 | `canonicalFinishEnumMap.ts:cant_oracal_wrap` |
| Vopsit RAL (cant) | missing rule (documented 100 RON policy unimplemented) | P0 | `canonicalFinishEnumMap.ts:cant_ral_minimum_policy`; `intake_v4_ral_paint_rules_service.py` |
| ACM mass color / shell finish | blocked / not evaluable | P1 (separate bug) | ACM probe captures `E_acm_shell__*.json` |
| Mirror (mirror_silver) | OWNER_DECISION_REQUIRED | P2 | `canonicalFinishEnumMap.ts` vs live UI combobox options |
| Print/laminate (face) | missing rule | P2 | no rule entry in `commercial_rules_volumetric_v2.py` |
| Confirmation state | defect (warning theater) | P2 | scenario set C (delta matrix) |
