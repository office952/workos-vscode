# WORKOS_ACM_PANEL_PRICING_PREVIEW_AND_AUTHORITY_GATES_V1 — Worklog

| Field | Value |
|-------|--------|
| Date | 2026-07-20 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD before | `e9a502fb1e26f6cd85b65f3da12c2ad2076d8ace` |
| Feature commit | `ab514f32d54af219787bfb4d049242cecfa0c8b1` (`ab514f3`) |
| Docs commit | `446fce38f87ba1823676822a52ec373ca141620a` (`446fce3`) |
| HEAD after | `446fce3` |
| Plan | `docs/plans/2026-07-20_WORKOS_ACM_PANEL_PRICING_PREVIEW_AND_AUTHORITY_GATES_V1.md` |
| Fixture | `IV6-DB2F86B7` / `a7b0162b-dc91-467f-aa24-c1279fb3a073` |
| Verdict | **PASS** (provisional preview + authority gates; no final/Offer/Exec) |

---

## 1. Plan Mode source

Owner GO accepted plan verdict **A**: Pricing Preview AcmPanel in an isolated build with explicit commercial geometry contract.

No re-audit. No Plan Mode redo. Binding owner decisions unchanged.

---

## 2. Owner decisions

| Decision | Binding |
|----------|---------|
| Placement | `IntakeV6LiveCalculationSummary` in Review + Confirm continuity |
| No new route / no inventory-pricing operator preview / no inspector money | Honored |
| Face area | Assembly `2000×350` → `0.700 mp` |
| Cut / V-groove | Sum of panel perimeters → `5.4 ml` |
| Assembly exterior | `4.7 ml` observability only — not cut/V-groove |
| No remap | `panel_*` stays envelope; commercial aliases `panel_area_m2` / `panel_perimeter_m` |
| 6 `acm_*` rates | Unchanged values; no hourly; no new joint rate |
| Material | `MAT-ACM-BOND-3MM` preferred; `MAT-ACP-3MM` legacy alias, no duplicate line |
| Fixture state | `provisional_with_warnings`; final/Offer/Exec blocked |

---

## 3. Pricing trace

```text
acm_panel_instance (+ segmented panels / assembly_dimensions)
  → ProductDefinition canonical_values (assembly_* inject; panel_* may remain envelope)
  → V6 quote_input_payload (+ mounting_solution.configuration)
  → merge_acm_boxed_mounting_derived_fields
       → derive_acm_casetted_quote_input(panel_*)   # envelope dims preserved
       → apply_acm_commercial_geometry              # Slice C
  → CommercialPriceProposalService.build_preview (7G / CPP)
  → dry-run acm_panel_commercial_preview
  → IntakeV6LiveCalculationSummary / AcmPanelProvisionalPricingBlock
```

| Stage | Input | Output | Source | Authority | Fallback | Warnings | Tests |
|-------|-------|--------|--------|-----------|----------|----------|-------|
| Instance | finish_setup.acm_panel_instance | coalesced instance | AcmPanel SoT | instance | mounting_solution.configuration | — | geometry unit |
| Assembly keys | panels + assembly_dimensions | assembly_width/height_mm | A+B extent | geometry | envelope ignore | envelope ignored | A+B + Slice C |
| Commercial geom | assembly + panels | face/cut/fold/return aliases | `acm_commercial_geometry` | pricing consumer only | assembly exterior cut | joints gap, envelope | `test_acm_commercial_geometry_v1` |
| CPP | aliased qty keys | 6 acm lines | registry rates | Pricing Registry | — | quantity_source | `test_acm_panel_pricing_preview_cpp_v1` |
| Dry-run preview | lines + authority | provisional contract | dry-run service | gates projection | unavailable | tech/seg/comp/catalog | probe + HTTP :8011 |
| UI | preview | Review/Confirm block | live-calc | display only | hidden if unavailable | RO copy | vitest + capture |

---

## 4. Commercial geometry contract

| Quantity | Formula (fixture) | Value |
|----------|-------------------|-------|
| Face area | `assembly_w × assembly_h / 1e6` | **0.700 mp** |
| Panel perimeter sum | `Σ 2×(pw+ph)/1000` | **5.4 ml** |
| Cut length | = panel perimeter sum | **5.4 ml** |
| V-groove / fold | = fold_sides=all → same as perimeter sum | **5.4 ml** |
| Assembly exterior | `2×(aw+ah)/1000` | **4.7 ml** (not used for cut/V-groove) |
| Return strip area | fold_m × (return_depth_mm/1000) | fixture-dependent (runtime ~0.4482 mp) |

**Forbidden:** treating envelope `1000×350` as commercial overall; remapping `panel_width_mm ← assembly_width_mm`.

---

## 5. Rate inventory (6 acm_* — unchanged)

| Code | Label (runtime) | Unit | Rate | Qty formula | Min policy | Source (rule) |
|------|-----------------|------|------|-------------|------------|---------------|
| `acm_panel_cut` | Debitare panou ACM | ml | **1.5** | commercial_cut = Σ panel perimeters | none | `acm_panel_cut_owner_eur_lm` |
| `acm_v_groove` | Frezare V-groove ACM | ml | **3.0** | commercial_fold (all sides) | none | `acm_v_groove_owner_eur_lm` |
| `acm_panel_face_material` | Material ACM față panou | m2 | **15.0** | commercial_face_area | none | `acm_mat_face_owner_eur_m2` |
| `acm_return_strip_material` | Material ACM canturi | m2 | **15.0** | fold_m × depth_m | none | `acm_mat_return_owner_eur_m2` |
| `acm_boxed_assembly` | Asamblare suport ACM casetat | m2 | **15.0** | face area | **min 20 EUR** | `acm_assembly_owner_eur_m2_min` |
| `acm_fasteners` | Șuruburi / prinderi standard ACM | set | **5.0** | 1 set | none | `acm_suruburi_owner_eur_set` |

- Consumer: CPP 7G → dry-run preview → live-calc UI  
- Version marker: `acm_commercial_geometry_v1`  
- Hourly commercial: **0** lines (`basis_type` ml/m2/set only)

Fixture estimated ACM total (runtime): **66.523 EUR** (assembly min 20 applied).

---

## 6. Material binding

- Preferred SKU: `MAT-ACM-BOND-3MM`
- Legacy alias: `MAT-ACP-3MM` — excluded from duplicate commercial line
- No inventory write, no migration, no historical rewrite
- Stock null remains unknown (not zero)

---

## 7. Authority gates (fixture)

| Gate | State |
|------|-------|
| Preview provisional | **PERMIS** → `provisional_with_warnings` |
| Final price | **BLOCAT** |
| Offer ferm | **BLOCAT** |
| Order | **BLOCAT** (out of scope) |
| Execution | **BLOCAT** |

Visible warnings include: technical unconfirmed, construction catalog_default, segmentation PROPOSED, composition inconsistent/unconfirmed, joints without commercial rate, envelope not used for face area.

No auto-promotion catalog_default → operator_confirmed, PROPOSED → CONFIRMED, estimate → Offer/Exec.

---

## 8. Preview contract

Exposed on dry-run as `acm_panel_commercial_preview`:

`status`, `currency`, `estimated_total`, `lines[]`, `geometry_summary`, `material_reference`, `rate_version`, `authority_summary`, `warnings[]`, `blockers[]`, `final_eligibility`, `offer_eligibility`, `execution_eligibility`.

UI copy (RO): header **Estimare provizorie AcmPanel**; summary with assembly + panel count + registry rates; warning that price is estimative / not firm-offer eligible.

---

## 9. UI placement

- Primary: `AcmPanelProvisionalPricingBlock` inside `IntakeV6LiveCalculationSummary` (rightPanel + sidebar + **bar** for Confirm)
- Confirm: bar layout now includes provisional block; CTA card branch also mounts block for continuity
- Inspector: no money UI added
- `/inventory`, `/inventory/pricing`: read-only proof only; not operator preview

---

## 10. Tests

| Suite | Result |
|-------|--------|
| `tests/test_acm_commercial_geometry_v1.py` | PASS |
| `tests/test_acm_panel_pricing_preview_cpp_v1.py` | PASS |
| `tests/test_acm_boxed_mounting_standalone_offer_v1.py` (subset with rates) | PASS (prior run) |
| FE `acmPanelCommercialPreviewDisplay.test.ts` | PASS |
| FE `AcmPanelProvisionalPricingBlock.test.tsx` | PASS |

---

## 11. Runtime proof

| Check | Result |
|-------|--------|
| Local service probe + TestClient | face 0.7, cut/fold 5.4, 6 lines, provisional_with_warnings |
| HTTP `http://127.0.0.1:8011/.../priced-quote-dry-run` | same (fresh uvicorn; stale :8001/:8003 processes were wrong) |
| UI capture `PW_BASE_URL=http://127.0.0.1:3011` | **PASS** (`ui-proof.json`) |
| Expand/collapse writes | **0** mutating requests |
| Inventory/Pricing page writes during proof | **0** |

Evidence: `docs/audits/_evidence/2026-07-20_acm-panel-pricing-preview-authority/`

---

## 12. Screenshot matrix (minimum)

| # | Shot | Verdict |
|---|------|---------|
| 1 | `01-review-full.png` | PASS |
| 2–5 | sticky / header / assembly / face | PASS (0.7 / 2000×350) |
| 6–10 | expanded breakdown + acm lines | PASS (6 lines) |
| 11–15 | warnings + final/offer unavailable | PASS |
| 16 | Confirm continuity | PASS |
| 17 | inspector region | PASS (no dedicated money UI in inspector) |
| 18–19 | inventory / pricing registry | PASS read-only |
| 20–21 | mobile + full page | PASS |

---

## 13. Risks / dead pieces

- Stale uvicorn workers on :8001/:8003 can serve old CPP quantities without `acm_panel_commercial_preview` — restart required after deploy.
- Confirm previously used `layout="bar"` without AcmPanel block — fixed this slice.
- Joint / segmentation handling remains informational gap (no invented rate).
- Finish commercial rates (Oracal/print/RAL) not invented; MIXED operation SoT unchanged.
- Component card still shows envelope `1000×350` as technical detail — intentional separation from commercial assembly.

---

## 14. Roadmap (not this slice)

1. Operator confirmation path → allow `official_ready` only after technical + segmentation + composition gates
2. Optional joint / handling rate when owner defines registry codes
3. Finish-factor commercial lines when rates exist
4. Frontend Typecheck Debt Audit (repo-wide)

---

## 15. Commit

See git commit on this branch (feature + optional docs/evidence). No migrations. No seeds. No Inventory writes. No rate value changes.
