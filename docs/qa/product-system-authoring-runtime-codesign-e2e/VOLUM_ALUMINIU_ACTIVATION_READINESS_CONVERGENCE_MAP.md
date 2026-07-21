# VOLUM ALUMINIU — Activation Readiness Convergence Map (FROZEN)

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Kickoff HEAD | `a385f156` (reconfirmed) |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Subject | `TPL-VOLUM-ALUMINIU_v1` |
| Mode | Activation readiness closure — **no activation / no publish** |
| Prior CP0 | `VOLUM_ALUMINIU_COMPONENT_CONTRACT_CP0_SHARED_MAP.md` |
| Prior report | `VOLUM_ALUMINIU_COMPONENT_CONTRACT_COMPLETION_FINAL_REPORT.md` |

---

## Absolute locks (reconfirmed)

- Do **not** activate or publish `TPL-VOLUM-ALUMINIU_v1`
- VL publication remains **BLOCKED** (`KNOWN_REQUIRED_INACTIVE_CHILD`)
- No ComponentTemplate table / PI / CI / Pricing redesign / schema migration
- No SVG/DWG/DXF parse; no desktop transport; no EP materialization; no mobile
- Dirty tree unrelated untouched; allowlist-only commits; no push/PR

---

## 1. Canonical identity (one)

| Axis | Canonical value | Lookup |
|------|-----------------|--------|
| Template code | `TPL-VOLUM-ALUMINIU_v1` | by code |
| BOM component_id | `comp_volum_aluminiu_module` | by id |
| Aggregate / mini-module | `modelare_cant` | by module_code |
| PT container | `product_truth.components.return_cant` | by path |
| Instance schema | `letter_group_instances.sidewall` | by schema id |
| Shared contract key | `volumetric_return_side` | by key |
| Commercial line | `modelare_cant_aluminiu` | by line_code |
| Commercial rule | `VOL_V2_RETURN_PROFILE_ML` | by rule_code |
| EIC rule | `INT_VOL_V2_RETURN_ML` | by rule_code |
| Parent | `TPL-VOLUMETRIC-LETTERS_v2` | by code |

**Canonical identity token for runtime mapping:** `TPL-VOLUM-ALUMINIU_v1` + `comp_volum_aluminiu_module` (BOM owner).

---

## 2. Explicit aliases (not parallel owners)

| Alias | Role | Maps to |
|-------|------|---------|
| `comp_lateral_litere` | Pricing / EIC / dossier stub (legacy commercial key) | Aggregate `modelare_cant` + commercial/EIC lines |
| `sidewall` / `return_cant` / `return_profile` | Role / PT / produced-role labels | same component |
| `volumetric_return_side` | PS ownership / shared contract key | same component |
| `RETURN-CANT` / `CANT` | Process / offer-scope alias | process graph only — **not** BOM id |
| `TPL-COMP-LETTER-RETURN-CANT_v1` | Aspirational component-first label | future readonly map — **not** active runtime |
| Admin UI: Cant / volum din aluminiu | Display only | template code |

**Policy:** one BOM owner (`comp_volum_aluminiu_module`). Pricing stub is an **explicit alias**, resolved only via `IDENTITY_MAP` / `resolve_*` helpers — **never** name-based fuzzy lookup. No double-counting: Aggregate keys by `modelare_cant` once.

**Resolver module:** `backend/services/volum_aluminiu_component_contract.py` (`IDENTITY_MAP`, `resolve_identity_*`).

---

## 3. Canonical perimeter authority

```text
operator/manual OR external observation (evidence)
  → operator confirm
  → confirmed Product Truth perimeter (m)
  → component quantity (m = ml 1:1)
  → Aggregate modelare_cant
  → CPP modelare_cant_aluminiu / EIC INT_VOL_V2_RETURN_ML
```

| Stage | Field | Unit | Authority |
|-------|-------|------|-----------|
| Evidence | `quote_geometry.letter_perimeter_m` | m | Observe only |
| Confirmed PT | `…return_cant.instances[].geometry.confirmed_perimeter_m` | m | **Canonical** |
| Component qty | `return_profile_linear_meter` / preview qty | m (= ml) | Derived from confirmed |
| CPP / EIC | `modelare_cant*` lines | ml (= m) | Must match confirmed when present |

**Rounding:** 6 decimal places. **Fail closed** on unknown unit / non-positive / missing confirmation (separate calc) / confirmed↔evidence divergence (product-total).

---

## 4. `quote_geometry` classification (frozen)

| Classification | Meaning |
|----------------|---------|
| **Compatibility bridge (controlled)** | When confirmed PT exists: product-total may **project** confirmed → `quote_geometry.letter_perimeter_m` with provenance metadata so legacy CPP/EIC path readers stay compatible. Read-only for persistence; not a second authority. |
| **Legacy fallback (demoted)** | When confirmed PT is absent: `quote_geometry` may still supply VL product-total qty with explicit warning `quote_geometry_legacy_fallback` — demoted from silent dual-authority. Separate-calc never uses it. |
| **Not canonical** | Never confirmation SoT; never auto-promote to confirmed. |
| **Divergence** | Confirmed present and `|confirmed − quote_geometry| > 0` after 6dp round → **fail closed** (no silent pick). |

---

## 5. Readers (must use map)

| Surface | Identity reader | Perimeter reader |
|---------|-----------------|------------------|
| Separate-calc preview | template + BOM map | confirmed only |
| Quantity ownership | BOM + pricing alias map | confirmed only |
| Aggregate | `CHILD_TEMPLATE_MINI_MODULE` + dossier aliases incl. BOM id | module `modelare_cant` |
| CPP product-total | pricing stub via alias map | confirmed prefer → bridge; else named legacy fallback |
| EIC product-total | same | same |
| Readiness | identity + geometry convergence findings | fail-closed signals; never auto-activate |
| UI / diagnostics | admin label by template code | honesty copy only |

---

## 6. Publication / activation

| Gate | Behavior |
|------|----------|
| Publication | **BLOCKED** even if warnings close |
| Activation | Recommendation only — **do not execute** |
| Auto-activate | **Forbidden** |

---

## 7. Allowlist (this closure)

1. `feat(product-system): converge aluminium return canonical identity mappings`
2. `feat(product-system): converge CPP product-total on confirmed perimeter / control quote_geometry bridge`
3. `test(product-system): prove identity and geometry equivalence`
4. `docs(qa): activation readiness closure evidence`

Allowed paths: prior completion allowlist union + this map + readiness closure report + targeted CPP/EIC/Aggregate/measurement seams listed in the final report.

---

## Agents (after freeze)

| Agent | Scope |
|-------|--------|
| A | Identity map |
| B | Product Truth + Aggregate alias |
| C | Quantity + Preview honesty |
| D | CPP/EIC perimeter convergence |
| E | Readiness + publication stay blocked |
| F | UI/diagnostics only if needed |
| G | QA equivalence |

**CP0 STATUS: FROZEN** — all agents use this map.
