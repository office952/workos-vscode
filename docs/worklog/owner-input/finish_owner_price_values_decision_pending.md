# FINISH owner price values — decision pending

> **Status:** AWAITING OWNER CHAT — questions prepared by `FINISH_OWNER_PRICE_VALUES_DECISION_V1` (QUESTIONS PREP)  
> **HEAD:** `542fff6`  
> **Not a signed owner decision.** Do not treat as runtime authority. Do not activate pricing.

---

## Context

Source inventory cross-reference audit (`542fff6`) returned **PARTIAL** (accepted). Keys are found in seeds and Intake V4; blockers remain on labor mapping, artwork print_only runtime, and Product System geometry handoff.

Prior signed decisions still apply:

- `finish_component_truth_owner_decision_v1.md` — 9/9 variants owner_confirmed, evidence_only catalog refs
- FINISH estimated price draft (`c6b06d7`) — readonly, inactive

---

## Owner questions (A–G)

Answer in owner chat. Rerun `FINISH_OWNER_PRICE_VALUES_DECISION_V1` with `OwnerDecision` block to APPLY.

### A. Face labor key

**Question:** Should FINISH face/artwork application labor use `FACE_VINYL_APPLICATION_LABOR` as readonly evidence/draft source, or should `WC_VINYL_APPLICATION` be treated as the future canonical workcenter labor source?

| Field | Detail |
|-------|--------|
| Current evidence | `FACE_VINYL_APPLICATION_LABOR` — 5.0 EUR/mp, `seed_volumetric_workcenter_rates.py`, label “Manoperă aplicare folie fețe litere” |
| Conflict | Intake V4 artwork print/lam application rows use `WC_VINYL_APPLICATION` workcenter (`intake_v4_material_breakdown_service.py`); legacy fallback 3.0 EUR/mp when registry absent |
| Options | (1) FINISH draft uses `FACE_VINYL_APPLICATION_LABOR` evidence_only; (2) Future canonical = `WC_VINYL_APPLICATION`; (3) Document both as conflicting_evidence until harmonized |
| Recommended | **(1)** for FINISH readonly draft — aligns with prior owner component truth decision; document Intake V4 divergence as legacy_runtime_evidence, activation blocked |
| Activation | Remains **blocked** regardless |

---

### B. Artwork labor

**Question:** Should artwork application labor use the same face labor model, or remain blocked until an artwork-specific labor key exists?

| Field | Detail |
|-------|--------|
| Current evidence | Same conflict as A — draft shows `FACE_VINYL_APPLICATION_LABOR`; Intake artwork uses `WC_VINYL_APPLICATION` |
| Options | same as face evidence_only · require artwork-specific labor key · defer to workcenter model · blocked |
| Recommended | **same as face evidence_only** for readonly draft; no new artwork labor key until owner requests; activation blocked |
| Activation | **blocked** |

---

### C. Artwork print+lam

**Question:** Can artwork print+lam use the same evidence keys as face print+lam for readonly draft?

**Keys:** `MAT-VINYL-PRINT`, `MAT-VINYL-PRINT-LAMINATED`, `LARGE_FORMAT_PRINT`, `LAMINATION`

| Field | Detail |
|-------|--------|
| Current evidence | Intake V4 `_append_artwork_print_rows` resolves to same registry keys as face (`MATERIAL_REGISTRY_CODES`); seed names say “față litere” |
| Draft row | `artwork_print_laminate_draft` — UI still `source_inventory_audit_required`; audit recommends evidence_only for keys |
| Options | accept evidence_only for readonly draft · require artwork-specific keys · keep source_inventory_audit_required |
| Recommended | **accept evidence_only** for material/service keys (same as face); labor + geometry handoff still block activation |
| Activation | **blocked** |

---

### D. Artwork print only

**Question:** Canonical variant `artwork_print_only` exists; Intake V4 `PRINT_ARTWORK_EXECUTION_TYPES` does **not** include `print_only`. What should we do?

| Field | Detail |
|-------|--------|
| Current evidence | `MAT-VINYL-PRINT` + `LARGE_FORMAT_PRINT` exist in seeds; no Intake V4 breakdown path for `execution_type=print_only` |
| Canonical | `canonicalFinishEnumMap.ts`, `svgArtworkContracts.ts` — token exists |
| Options | keep blocked until Intake V4/runtime support · create future implementation task · remove/hide from draft · **keep visible as blocked** |
| Recommended | **keep visible as blocked** + flag future Intake V4 task; do not remove owner-confirmed variant |
| Activation | **blocked** |

---

### E. Artwork quantity handoff

**Question:** `mp_artwork_area` / `artwork_instances` exist in Intake V4 via `quote_geometry.artwork_boxes`, but Product System component-first has no live producer. What next?

| Field | Detail |
|-------|--------|
| Owner rule | `mp_artwork_area` when geometry exists — already owner_confirmed in component truth |
| Intake V4 | Area from `quote_geometry.artwork_boxes|bounding_box_footprint` or fallbacks |
| Product System | `componentFirstFinishTruthWorkshop.ts` blocker: “runtime source missing” |
| Options | blocked until handoff · evidence_only from Intake V4 · create ProductSystem handoff spec next |
| Recommended | **blocked until handoff** + **create ProductSystem handoff spec next** (`FINISH_PRODUCT_TRUTH_HANDOFF_SPEC_V1`); Intake V4 area as reference evidence_only in draft notes |
| Activation | **blocked** |

---

### F. Seed EUR/mp values

**Question:** Can seed values be used as readonly draft evidence only, or do you want to provide owner draft values now?

| Key | Seed evidence (EUR/mp) | Classification today |
|-----|------------------------|----------------------|
| MAT-ORACAL-641 | 6.5 | evidence_only |
| MAT-ORACAL-651 | 9.0 | evidence_only |
| MAT-ORACAL-8500 | 20.0 | evidence_only |
| MAT-VINYL-PRINT-LAMINATED | 10.0 | evidence_only (material only) |
| MAT-VINYL-PRINT | 1.5 | evidence_only (material only) |
| LARGE_FORMAT_PRINT | 8.5 | evidence_only (service) |
| LAMINATION | 5.0 | evidence_only (service) |
| FACE_VINYL_APPLICATION_LABOR | 5.0 | evidence_only |
| RETURN_CANT_VINYL_APPLICATION_LABOR | 1.0 EUR/ml | **excluded** — return_cant_only |

| Options | Use seeds as readonly draft evidence only · provide owner draft values now (OWNER_ESTIMATE_DRAFT like FACE) |
| Recommended | **seeds as readonly draft evidence only** — not owner-confirmed FINISH pricing authority; owner may supply override values in a later slice |
| Activation | **blocked** — seed prices are not `pricingActive` |

---

### G. Boundary reaffirmation

**Question:** Confirm again — no pricing activation, no Product Truth write, no Pricing Registry write, no ProductDefinition bridge, no RETURN-CANT ownership, no FACE base material ownership, no RAL minimum ownership?

| Boundary | Expected answer |
|----------|-----------------|
| pricing activation | NO |
| Product Truth live write | NO |
| Pricing Registry write | NO |
| ProductDefinition bridge | NO |
| RETURN-CANT ownership | NO |
| FACE base material (MAT-ACP-FATA-LITERE) | NO |
| RAL 100 lei minimum | NO |

**Recommended:** **ACCEPT all** — unchanged from prior FINISH owner decisions.

---

## Compact question table

| Question | Decision needed | Current evidence | Recommended answer | Status |
|----------|-----------------|------------------|--------------------|--------|
| A — Face labor key | `FACE_VINYL_APPLICATION_LABOR` vs `WC_VINYL_APPLICATION` | 5 EUR/mp vs Intake WC path | Use `FACE_VINYL_APPLICATION_LABOR` evidence_only in FINISH draft; document WC as legacy intake | pending |
| B — Artwork labor | Same as face or artwork-specific key | Labor conflict | Same as face evidence_only; no new key yet | pending |
| C — Artwork print+lam | Shared keys vs artwork-specific | Keys found in Intake V4 | Accept evidence_only (same keys as face) | pending |
| D — Artwork print only | Block / hide / implement | No Intake V4 `print_only` handler | Keep visible as blocked; future runtime task | pending |
| E — Artwork quantity handoff | When to unblock `mp_artwork_area` | Intake V4 boxes; PS no producer | Blocked until handoff spec | pending |
| F — Seed EUR/mp | Evidence only vs owner draft values | All keys in seeds | Seeds as evidence_only only | pending |
| G — Boundary | Reconfirm all NO | Prior owner decisions | ACCEPT all boundaries | pending |

---

## After owner answers

Rerun with:

```
OwnerDecision:
  A: ...
  B: ...
  ...
```

→ APPLY mode → `finish_owner_price_values_decision_v1.md` + readonly draft metadata updates (still blocked).

---

## References

- `docs/worklog/realignment/2026-07-09_finish_source_inventory_cross_reference_audit_v1.md`
- `docs/worklog/owner-input/finish_component_truth_owner_decision_v1.md`
- `docs/worklog/realignment/2026-07-09_finish_estimated_price_draft_v1.md`
