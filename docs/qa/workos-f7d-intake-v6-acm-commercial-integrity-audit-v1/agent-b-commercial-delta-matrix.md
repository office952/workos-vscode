# Agent B — Commercial Delta Matrix (F7D)

All rows use the read-only preview endpoint `POST /api/v1/product-system/commercial-price-preview/{template_code}` (no `/price`, no CostEngine, no persistence) with a synthetic-but-held-constant geometry (`letter_face_area_m2=2.5`, `letter_perimeter_m=8.0`, 9 letters), currency RON, `TPL-VOLUMETRIC-LETTERS_v2`, **except** row set "Live UI" which is the real workspace `5a5ce742-f50f-47b0-985b-32cc6f2fb6a4`. Full JSON captures under `captures/`. Rule id: `VOL_V2_FINISH_M2_OR_MINIMUM` unless noted. VAT (21%) and adaos comercial (0%) held constant throughout; RON is the CPP-native currency (no conversion).

## A. Face finish type (`face_finish_type` / `face_oracal_code`)

| Field | Initial | Selection | Total before | Total after | Expected Δ | Actual Δ | Pricing line | Persists to snapshot | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| face_finish_type | oracal_651 / 021 | oracal_651 / 032 (diff color) | 577.50 RON | 577.50 RON | Unknown (OWNER_DECISION_REQUIRED — no color-tier policy exists) | 0.00 | finisaje_colantare_vopsire = 35.0 RON/m² flat | Yes (frozen as-is) | **ZERO-DELTA / defect candidate** |
| face_finish_type | oracal_651 | oracal_641 | 577.50 RON | 577.50 RON | Likely > 0 — internal material cost differs 9.0 vs 6.5 EUR/m² (`intake_v4_oracal_face_pricing_service.py`) | 0.00 | same flat line | Yes | **ZERO-DELTA — defect (P0)** |
| face_finish_type | oracal_641 | oracal_8500 | 577.50 RON | 577.50 RON | Likely > 0 — internal material cost 6.5 → 20.0 EUR/m² (>3×) | 0.00 | same flat line | Yes | **ZERO-DELTA — defect (P0)** |
| face_finish_type | oracal_8500 | print_laminate | 577.50 RON | 577.50 RON | Unknown — no print/laminate commercial rule exists at all | 0.00 | same flat line | Yes | **ZERO-DELTA / missing rule** |
| face_finish_type | print_laminate | none (module off→off transition here; module was already on from group entry) | 577.50 RON | 577.50 RON | Expect drop to 0 for finish line if truly "none" | 0.00 (line still charges 35 RON/m²) | same flat line, still charged even for "none" in this harness state | Yes | **ZERO-DELTA — see note below** |

Note on the "none" row: in the live UI (§5 of price-path-trace), moving from the workspace's true initial state (module fully inactive) to "Oracal 8500" **did** move the sidebar informational estimate (+10.92 EUR on the "Litere" line) — this is the module-activation gate switching on, not finish-type-sensitive pricing. Once the module is already active (as in the isolated API-probe harness, which always includes one confirmed finish group), switching between any two non-none values is proven zero-delta.

## B. Return / cant finish type (`return_finish_type` / `return_oracal_code`)

| Field | Initial | Selection | Total before | Total after | Expected Δ | Actual Δ | Pricing line | Persists | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| return_finish_type | white (stock) | black (stock) | 577.50 | 577.50 | 0 — owner-documented "no additional tariff" for stock colors | 0.00 | none dedicated; same flat finisaje line | Yes | **ZERO-DELTA — correct by design** |
| return_finish_type | white (stock) | gold (stock) | 577.50 | 577.50 | 0 (same as above) | 0.00 | — | Yes | **ZERO-DELTA — correct by design** |
| return_finish_type | white (stock) | silver (stock) | 577.50 | 577.50 | 0 (same as above) | 0.00 | — | Yes | **ZERO-DELTA — correct by design** |
| return_finish_type | white (stock) | ral_paint / RAL 9016 | 577.50 | 577.50 | > 0 — owner-declared 100 lei/color minimum + material+labor keys planned (`cant_ral_paint`, `cant_ral_minimum_policy`) | 0.00 | same flat finisaje line; no RAL-specific line, no 100 RON minimum applied | Yes | **ZERO-DELTA — missing rule (P0)** |
| return_finish_type | ral_paint / RAL 9016 | ral_paint / RAL 3020 (different color) | 577.50 | 577.50 | Unknown — RAL color-tier pricing not documented | 0.00 | — | Yes | **ZERO-DELTA / OWNER_DECISION_REQUIRED** |
| return_finish_type | white (stock) | oracal_wrapped / 021 | 577.50 | 577.50 | > 0 — owner-declared `MAT-ORACAL-641/651` + `RETURN_CANT_VINYL_APPLICATION_LABOR` keys planned for `cant_oracal_wrap` | 0.00 | same flat finisaje line | Yes | **ZERO-DELTA — missing rule (P0)** |

**Live UI cross-check:** face finish switch "Fără finisaj" → "Oracal 8500 · 070 Black" → `Ofertă client` total unchanged at **2.288,75 RON** (`agent-b-01-*.png` vs `agent-b-02-*.png`), confirmed a second time on the independent Step-3 "Confirmare finală" total screen (`agent-b-03-*.png`). This is the same live workspace/quote a real operator would use to click "Creaza oferta pretuita."

## C. Confirmation state (`letter_group_finishes[].confirmed`)

| Field | Initial | Selection | Total before | Total after | Expected Δ | Actual Δ | Pricing line | Persists | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| confirmed | true | false | 577.50 | 577.50 | Warning text implies pricing "may require owner review before numeric pricing" — expected either a block or a visibly different (deferred) state | 0.00, `status` stays `"ready"` both times | same flat line + same warning text regardless of true/false | Yes | **Warning theater — P2** |
| letter_group_finishes | [] (empty) | present | 577.50 | 577.50 | Expected block/`owner_decision_required=true` on the finish line when no group is declared at all | 0.00; only an extra warning string added, `status` stays `"ready"` | same flat line | Yes | **Silent pricing on empty finish declaration — P2** |
| letter_group_finishes | absent (`None`) | present | 577.50 | 577.50 | Same as above | 0.00 | same flat line | Yes | **Silent pricing on absent finish declaration — P2** |

## D. Control group — mounting template material (sanity check; NOT a finish field, included to prove the CPP mechanism works when wired correctly)

| Field | Initial | Selection | Total before | Total after | Expected Δ | Actual Δ | Pricing line | Persists | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| mounting_template_material_type | paper | forex | 582.50 | 592.50 | > 0 — different `material_gate_value` rules (`sablon_montaj_hartie` 5 EUR/m² vs `sablon_montaj_forex` 15 RON/m² dev bridge) | **+10.00 RON** | `sablon_montaj_hartie` → `sablon_montaj_forex` (distinct `CommercialRuleDefinition` rows, gated by `material_gate_path`) | Yes | **CORRECT — proves the differential-pricing mechanism exists and works** |

This positive control is the strongest evidence that the zero-delta results in A/B are a **rule-authoring gap**, not a framework limitation: the exact `material_gate_path`/`material_gate_value` pattern used successfully for `sablon_montaj` (paper vs Forex) was simply never applied to `finisaje_colantare_vopsire`.

## E. ACM shell finish (`acm_panel_instance.shell_finish`) — standalone template probe

| Field | Initial | Selection | Total before | Total after | Expected Δ | Actual Δ | Pricing line | Persists | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| shell_finish.face.kind | stock_plate | oracal_651 | N/A (blocked) | N/A (blocked) | Unknown | N/A | none reached | N/A | **BLOCKED — `CRITICAL_GEOMETRY_MISSING` (P1, separate bug)** |
| shell_finish.face.kind | oracal_651 / 021 | oracal_651 / 9016 (diff color) | N/A (blocked) | N/A (blocked) | Unknown | N/A | none reached | N/A | **BLOCKED — same geometry validation bug** |
| shell_finish.face.kind | oracal_651 | print_laminate | N/A (blocked) | N/A (blocked) | Unknown | N/A | none reached | N/A | **BLOCKED — same geometry validation bug** |

All four ACM standalone-template scenarios returned `commercial_total: 34.0` (a fixed pre-blocker structural line) and `commercial_blockers: ["CRITICAL_GEOMETRY_MISSING"]` — the geometry validator requires letter-oriented fields (`letter_count`, etc.) even for a pure ACM-panel template, so no ACM finish-vs-price comparison could be completed via the standalone template. The **composite** workspace (Litere + Alucobond casetat together) does compute itemized ACM material/operation lines (screenshot `step2-panou-carcasa-acm-priced-lines.png`), but that panel remains in a "1 blocant" (not-ready) state pending panel confirmation, so a clean before/after pair for ACM shell finish could not be captured within this audit's scope — recommend a dedicated follow-up.

## Currency / VAT / rule id reference

- Currency: RON throughout (CPP-native, `source_currency: "RON"`, no conversion needed for these rows).
- VAT: 21%, held constant, applied at the total level (not per-line) — not part of the zero-delta finding.
- Rule id for all finisaje rows: `VOL_V2_FINISH_M2_OR_MINIMUM` (`backend/data/commercial_rules_volumetric_v2.py:142-156`).
- Rule id for control group: `VOL_V2_SABLON_HARTIE_EUR_M2` / `VOL_V2_SABLON_FOREX_DEV_BRIDGE` (`:170-204`).
- Warnings present on every finisaje row regardless of scenario: `"Unconfirmed finish groups may require owner review before numeric pricing."`, `"quantity_source=COMPATIBILITY_WORKSPACE_PATH"`.
