# Agent B — Commercial Finish Price Path Trace (F7D)

Repo: `C:\w\psiso` · HEAD `43d7a3c5` · Scope: Intake V6 / ACM finish selections, read-only.

Fixture used for live UI trace: workspace `5a5ce742-f50f-47b0-985b-32cc6f2fb6a4` (`IV6-9C5D9538`, "Litere volumetrice", SVG `REMUS`, 2 layers: Alucobond casetat panel + volumetric letters). Fixture used for API probes: synthetic quote_input held-constant geometry, `vector_file: "test-bond-litere.svg"` (coordination fixture per Lead instructions — Agent A confirmed no conflicting write in this workspace).

## 1. End-to-end path (as implemented today)

```
UI combobox (IntakeV6ReturnCantFields.tsx / face finish selects)
   │  values: white | black | gold | silver | ral_paint | oracal_wrapped (cant)
   │          none | oracal_641 | oracal_651 | oracal_8500 | print_laminate (face)
   ▼
Workspace payload (finish_setup.letter_group_finishes[])
   │  face_finish_type, face_oracal_code, return_finish_type, return_oracal_code, confirmed
   ▼
Form contract (schemas/intake_v4.py — FinishSetup-like models)
   │  return_finish_type: str | None = "white_aluminum"   ← UNCONSTRAINED string, no Literal/enum
   │  face_finish_type / face_oracal_code: str | None      ← UNCONSTRAINED string
   ▼
ProductDefinition (product_definition_builder_service.py: build_preview)
   │  read_only=true, workspace_id=none for synthetic probes; workspace_id set for live UI
   ▼
ProductAggregate / active_modules resolution
   │  module "finisaje" gates on presence of any face/return finish selection (on/off only)
   ▼
CommercialPriceProposalService.build_preview()
   │  iterates VOLUMETRIC_V2_COMMERCIAL_RULES (backend/data/commercial_rules_volumetric_v2.py)
   ▼
CommercialRuleDefinition line_code="finisaje_colantare_vopsire"
   │  pricing_rule_code = "VOL_V2_FINISH_M2_OR_MINIMUM"
   │  basis_type = "m2"
   │  quantity_paths = ("quote_geometry.letter_face_area_m2", "letter_face_area_m2")   ← AREA ONLY
   │  documented_unit_price = DEV_BRIDGE_FINISH_RON_M2 = 35.0                          ← FLAT CONSTANT
   │  material_gate_path = None   material_gate_value = None                          ← NO BRANCHING
   ▼
commercial_price_lines[] → subtotal_commercial → commercial_total (RON, VAT separate)
   ▼
UI "Ofertă client" summary panel + Step 3 "Confirmare finală" → "Creaza oferta pretuita"
```

Confirmed via source: `backend/data/commercial_rules_volumetric_v2.py:142-156` and capture `docs/qa/workos-f7d-intake-v6-acm-commercial-integrity-audit-v1/captures/A_face_finish__A1_face_oracal_651_code021.json`.

## 2. Per-surface trace detail

### 2a. Face finish (`face_finish_type`, `face_oracal_code`) — Oracal 641 / 651 / 8500 / print_laminate / none

| Stage | Detail |
|---|---|
| Storage | `finish_setup.letter_group_finishes[].face_finish_type` / `.face_oracal_code` (workspace payload JSON) |
| Form contract | `schemas/intake_v4.py` — no `Literal[...]` constraint; free string |
| PD | Passed through `product_definition_builder_service.py` unchanged into `finish_setup` echo |
| Component ownership | Per `frontend/src/features/product-system/canonicalFinishEnumMap.ts`: face vinyl = **FINISH** component (`face_oracal_641/651/8500`), `activationStatus: "blocked"` in the (separate, not-yet-runtime-wired) Product System governance model — see §4 |
| Aggregate | `active_modules` includes `"finisaje"` once any face finish ≠ absent is set (on/off gate only, no value-sensitivity) |
| CPP rule | Single rule `finisaje_colantare_vopsire` / `VOL_V2_FINISH_M2_OR_MINIMUM`, keyed only on `letter_face_area_m2`. **No `material_gate_path` on `face_finish_type` or `face_oracal_code` exists in the rule table.** |
| EIC separate | Yes — `intake_v4_oracal_face_pricing_service.py` computes real differentiated **internal** material cost per Oracal series (641: 6.5 EUR/m², 651: 9.0 EUR/m², 8500: 20.0 EUR/m²) but this is marked `informational_only` and is never read by the CPP. |
| Snapshot boundary | `QuoteSnapshotV2Service` freezes whatever `commercial_price_lines` the CPP produced at freeze time — it does not re-derive or validate finish-sensitivity; a frozen quote will carry the same flat 87.5 RON finish line regardless of which face finish was chosen. |
| UI total source | `Ofertă client` summary card, sourced from `commercial_total` (CPP), not from `Estimări pe produs` sidebar (which is explicitly labeled informational — see `Nu înlocuiește deciziile de produs. Oferta client rămâne în rezumatul de mai sus.`). |

Live proof: switching Element 1 face finish from **"Fără finisaj — plexiglas brut"** to **"Oracal 8500 · 070 Black"** left the `Ofertă client` total at **2.288,75 RON** in both states (screenshots `agent-b-01-*` and `agent-b-02-*`).

### 2b. Return/cant finish (`return_finish_type`, `return_oracal_code`) — stock (Alb/Negru/Auriu/Argintiu) / Vopsit RAL / Oracal 651 wrap

| Stage | Detail |
|---|---|
| Storage | `finish_setup.letter_group_finishes[].return_finish_type` / `.return_oracal_code` |
| Form contract | `schemas/intake_v4.py:104,139` — `return_finish_type: str | None = "white_aluminum"` (unconstrained; default value does not match any live UI combobox value — see terminology doc) |
| Component ownership | RETURN-CANT component per canonical map: `cant_stock_color` (owner_confirmed, **no additional tariff by design**), `cant_oracal_wrap` (owner_confirmed **ownership**, real material+labor pricing keys declared: `MAT-ORACAL-641/651` + `RETURN_CANT_VINYL_APPLICATION_LABOR`), `cant_ral_paint` (owner_confirmed ownership, `MAT-VOPSEA-RAL-CANT-*` + `RETURN_CANT_RAL_PAINT_LABOR`), `cant_ral_minimum_policy` (documented "100 lei pe culoare RAL" commercial minimum) |
| Aggregate | Same single `"finisaje"` module gate as face — return finish selection does not add a separate module/line |
| CPP rule | **Same** single flat `finisaje_colantare_vopsire` line as face finish. No cant-specific rule exists in `commercial_rules_volumetric_v2.py` at all — no rule keys off `return_finish_type`, `return_oracal_code`, or cant depth for a finish tariff (cant depth does drive `modelare_cant_aluminiu`, a separate physical-forming line, unaffected by finish type). |
| EIC separate | Yes — `intake_v4_ral_paint_rules_service.py` computes real RAL paint tube material cost (50 RON / tube / 15 linear meters), marked informational only, never reaches CPP. |
| Snapshot boundary | Same as face — frozen as-is. |
| UI total source | Same `Ofertă client` card. |

Live proof: cant finish switched Alb → Vopsit RAL (color selection blocked mid-flow pending RAL code pick — see §5); API probe confirms stock (white/black/gold/silver), `ral_paint` (codes 9016, 3020), and `oracal_wrapped` all produce **identical** `commercial_total = 577.5` and identical finish line (`unit_price=35.0`, `subtotal=87.5`).

### 2c. ACM shell finish (`acm_panel_instance.shell_finish`)

| Stage | Detail |
|---|---|
| Storage | `finish_setup.acm_panel_instance.shell_finish` (`schema: acm_shell_finish_v1`, `face`/`volume` sub-objects) |
| Form contract | `backend/services/acm_quote_input_helpers.py` derivation helpers expect ACM-specific geometry merge |
| PD | `product_definition_builder_service.py` builds PD for `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` |
| CPP rule | Never reached in isolated-template probe — **blocked** by `CRITICAL_GEOMETRY_MISSING` before any finish-sensitive rule executes (see Finding P1, geometry validator expects letter-oriented fields even for a pure-ACM template) |
| Live composite workspace | In the real two-layer workspace (Litere + Alucobond casetat), the ACM panel geometry IS present (from the layer/panel step) and produces itemized "Estimări pe produs" lines (Debitare panou ACM, Material ACM față panou, Material ACM cant, etc. — screenshot `step2-panou-carcasa-acm-priced-lines.png`) but the panel-level offer is gated `blocked` (1 blocant) pending panel confirmation, so a finish-vs-total comparison could not be completed live within this audit's time budget. |

## 3. Field-by-field terminology / ownership summary

See `agent-b-terminology.md` for full E2E term-mismatch table.

## 4. Important scope clarification — "Product System" canonical map is NOT the live pricing path

`frontend/src/features/product-system/canonicalFinishEnumMap.ts` and its source decision `docs/worklog/owner-input/canonical_finish_enum_map_owner_decision_v1.md` (2026-07-09, HEAD `0a4a346`) are **explicitly disclaimed** as non-runtime, non-pricing-activating ("Nu activează pricing", "Pricing activation from Product System contracts" listed under "Still forbidden"). They describe a **future, separate Product System component-ownership architecture**, not the currently-live Intake V6 → `CommercialPriceProposalService` path audited here.

However, they are directly useful **corroborating evidence** for this audit because:
- They confirm the owner has *already anticipated* differentiated material/labor pricing for cant Oracal wrap and RAL paint (validating this is a real, planned capability — not an invented expectation).
- They confirm stock cant colors are *intentionally* zero-tariff ("Fără tarif finish suplimentar").
- `commercial_rules_volumetric_v2.py`'s own module docstring and `DEV_BRIDGE_*` comments self-disclose that today's flat rates are "Step 8 dev bridge — interim RON commercial unit prices for live V6 QA only... Owner must replace before official rollout" — i.e., the code itself agrees this is incomplete.

The severity finding in this audit is that this **admittedly-interim** pricing table is nonetheless the **live** path generating real "Ofertă client" totals and feeding the "Creaza oferta pretuita" (create priced offer) action today — there is no gate preventing an operator from creating a real commercial offer priced by the flat/interim rule.

## 5. Live UI trace log (this session)

1. Navigated to `http://localhost:3000/intake-v6/5a5ce742-f50f-47b0-985b-32cc6f2fb6a4/operator`, Step 2 "Configurare" → tab "Finisaje".
2. Baseline: Element 1 face = "Fără finisaj — plexiglas brut", cant = "Alb · 60 mm". `Ofertă client` = **2.288,75 RON**. (`agent-b-01-before-fara-finisaj-total-228875RON.png`)
3. Changed face finish combobox to "Oracal 8500" → color picker required → selected "Oracal 8500-070 Black". After sync settled, `Ofertă client` = **2.288,75 RON** (unchanged). (`agent-b-02-after-oracal8500-black-total-228875RON.png`)
4. Cross-checked Step 3 "Confirmare finală" independently shows the same **2.288,75 RON** total under "Ofertă client — total" (`agent-b-03-confirmare-finala-total-228875RON.png`), confirming the zero-delta is not a Step-2-only display artifact.
5. Attempted to change cant finish to "Vopsit RAL" + pick a RAL code to get a second live pair; blocked by a UI overlay/z-index issue on the RAL swatch grid after 2 click attempts (browser tooling limitation, not a product defect) — abandoned per anti-rabbit-hole guidance since the API probe already covers this scenario numerically (see delta matrix rows B5/B6).
6. Noted incidental discovery unrelated to finish pricing: Step-1 "Straturi" screen shows the Alucobond casetat layer's Product-System component card labeled "Opțional · Selectat" while a system warning simultaneously states the same layer is "standby, nu intră în quote litere volumetrice" (`step1-p0-standby-vs-included-contradiction.png`) — flagged as a separate finding (F-005), out of primary finish-pricing scope.
