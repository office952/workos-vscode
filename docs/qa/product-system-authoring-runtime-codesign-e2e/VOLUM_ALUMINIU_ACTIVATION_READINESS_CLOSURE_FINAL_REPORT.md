# VOLUM ALUMINIU — Activation Readiness Closure Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `a385f156` (reconfirmed) |
| Subject | `TPL-VOLUM-ALUMINIU_v1` |
| Mode | Activation readiness closure — **no activation / no publish** |
| Convergence map | `VOLUM_ALUMINIU_ACTIVATION_READINESS_CONVERGENCE_MAP.md` |
| Allowlist | `VOLUM_ALUMINIU_ACTIVATION_READINESS_ALLOWLIST.md` |
| Prior completion | `VOLUM_ALUMINIU_COMPONENT_CONTRACT_COMPLETION_FINAL_REPORT.md` |

---

## 1. Kickoff confirmation

| Item | Result |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `a385f156` reconfirmed |
| Dirty tree | Preserved; allowlist-only commits |
| Prior state | Separate calc **PASS_WITH_WARNINGS**; Activation **NO-GO**; Publication **BLOCKED** |

## 2. Absolute boundaries (honored)

Not activated / not published. No CT table, PI/CI, SVG parse, Pricing redesign, schema migration, push/PR, or dirty-tree clean.

## 3. Executive truth (română)

Cele două warning-uri rămase pe contractul de calcul separat sunt **închise prin mapping și demotion controlat**, nu prin activare: un singur ID canonic de BOM cu alias explicit de pricing; product-total CPP/EIC preferă perimetrul confirmat din Product Truth; `quote_geometry` este bridge de compatibilitate sau legacy fallback denumit — divergența eșuează închis. **Publicarea VL rămâne blocată. Nu activa.**

## 4. Identity verdict

### **PASS**

| Criterion | Result |
|-----------|--------|
| One canonical BOM id | `comp_volum_aluminiu_module` |
| Documented aliases | `IDENTITY_MAP` + `resolve_identity_token` / `map_component_ref_to_module` |
| Explicit readers | Aggregate dossier maps both BOM + stub → `modelare_cant` once |
| No duplicate active BOM owners | PASS |
| No name-based lookup | PASS (`Cant din aluminiu` / labels → `None`) |
| No double qty | Aggregate keys once by `modelare_cant` |
| used_by complete | identity convergence view |
| Preview + product-total same component | same template + module + commercial line |

## 5. Geometry verdict

### **PASS**

| Criterion | Result |
|-----------|--------|
| One confirmed perimeter authority | PT `confirmed_perimeter_m` |
| Unit m explicit; ml 1:1 | PASS |
| quote_geometry controlled | compatibility bridge when confirmed; demoted legacy fallback when not |
| No unconfirmed silent authority | separate-calc unchanged; product-total names legacy |
| Divergence fail-closed | clears `letter_perimeter_m`; extractors return None |
| Preview ↔ CPP equivalent basis | same confirmed qty within 6dp when aligned |

## 6. quote_geometry classification (accepted)

| Role | Classification |
|------|----------------|
| With confirmed PT (aligned) | **Compatibility bridge** — derived projection + provenance |
| Without confirmed PT | **Legacy fallback (demoted)** — explicit warning |
| Confirmed ≠ evidence | **Diverged fail-closed** — not parallel authority |

Not deleted (unrelated VL surfaces still use workspace geometry evidence). Not canonical confirmation SoT.

## 7–12. Identity surfaces (closed)

PT / composition link / Aggregate / preview / readiness / CPP/EIC / UI all resolve through `IDENTITY_MAP`. Pricing stub `comp_lateral_litere` remains commercial key without becoming a second BOM owner.

## 13–18. Perimeter path (closed)

```text
confirm → PT confirmed_perimeter_m (m)
  → resolve_product_total_perimeter_authority
  → apply_confirmed_perimeter_quote_geometry_bridge (read-only)
  → CPP modelare_cant_aluminiu / EIC INT_VOL_V2_RETURN_ML / measurements
```

## 19. Preview / CPP equivalence

| Case | Preview qty | Product-total / CPP path |
|------|-------------|--------------------------|
| Confirmed = evidence | confirmed | confirmed (bridge) |
| Confirmed only | confirmed | confirmed (bridge) |
| Evidence only | blocked (separate) | legacy fallback named |
| Diverged | confirmed (separate) | fail-closed (no qty) |

## 20. Commercial-hourly

**PASS** — ml basis preserved; no hourly redesign.

## 21–24. Readiness / publication

| Finding | Status | Blocking |
|---------|--------|----------|
| `components.required_inactive.TPL-VOLUM-ALUMINIU_v1` | BLOCKED | Yes (publication) |
| `components.volum_aluminiu.separate_calc_contract` | PASS | No |
| `components.volum_aluminiu.identity_convergence` | PASS | No |
| `components.volum_aluminiu.geometry_convergence` | PASS | No |

Publication **still BLOCKED**. Auto-activate **forbidden**.

## 25–28. UI / logo / legacy

UI not required for this closure (honesty already present). Logo return not consolidated. Process aliases remain non-BOM.

## 29. Runtime fixture

Synthetic VL payload with known confirmed perimeter **12.5 m**, evidence aligned, depth 60, finish `white_aluminum` — exercised via unit/measurement resolvers (read-only; no Quote/Order writes).

## 30. Separate calculation test (updated)

### **PASS** (warnings closed)

Prior **PASS_WITH_WARNINGS** dual-id + quote_geometry product-total deps → closed by mapping + bridge demotion.

## 31–32. Stop conditions

| Condition | Triggered? |
|-----------|------------|
| Schema migration required | NO |
| Duplicate active DB records unsafe | NO |
| quote_geometry required by unrelated products | NO (kept as demoted/bridge; not deleted) |
| CPP needs pricing redesign | NO |
| Unit conversion differs across products | NO (m=ml 1:1) |
| Removing fallback breaks accepted runtime | NO (legacy named fallback retained) |
| Activation required to test | NO |
| Inseparable dirty tree | NO |

## 33. Missing for activation (still — intentional)

Owner commercial/ops GO; child `active=true` decision; logo reuse; dossier quote_readiness text cleanup. **Not in this closure.**

## 34. Activation recommendation

### **NO-GO**

Do **not** execute activation. Warnings closed ≠ activation GO. Publication remains BLOCKED.

Optional future: **GO_WITH_CONDITIONS** only after owner GO on activation + publication unblock — out of scope here.

## 35. Naming

Internal codes kept. Admin label unchanged (Cant / volum din aluminiu).

## 36. Forbidden confirmation

Activation not executed. Publication blocker not removed.

## 37. Tests / commands

```text
pytest tests/test_volum_aluminiu_identity_geometry_convergence.py \
  tests/test_volum_aluminiu_quantity_ownership.py \
  tests/test_volum_aluminiu_separate_calc_preview.py \
  tests/test_return_cant_product_truth_bridge.py \
  tests/test_product_template_component_contracts_v1.py \
  tests/test_product_e2e_readiness_v1.py \
  tests/test_product_truth_revision_quantity_convergence_v1.py \
  tests/test_letter_group_instance_authority_v1.py -q
→ 55 passed
```

## 38. Owner decision

### **keep blocked** (publication + activation)

---

## Direction scores (0–100)

| Dimension | Score | Note |
|-----------|------:|------|
| Identity clarity | 96 | IDENTITY_MAP + resolvers |
| Operator label clarity | 82 | Unchanged |
| Composition correctness | 92 | Alias → one module |
| BOM/ops ownership | 94 | Dual-id closed as mapping |
| Separate calculability | 94 | Prior PASS + warnings closed |
| Quantity truth | 95 | Confirmed drives preview + product-total |
| Geometry convergence | 94 | Bridge / legacy / diverge |
| Commercial-hourly | 92 | ml |
| Activation readiness | 35 | Still NO-GO (intentional) |
| Publication honesty | 96 | Still blocked |

---

## PAREREA MEA SINCERA

Warning-urile erau oneste, nu cosmetice: dual-id-ul era cuplare documentată, iar product-total-ul încă trăia pe `quote_geometry`. Le-am închis prin **hartă și bridge**, fără să mintim că VL e activabil. Dacă cineva cere „activează acum că warning-urile au dispărut”, răspunsul corect rămâne **nu** — blockerul de publicare e feature, nu bug.

---

## Files changed (this closure)

- `backend/services/volum_aluminiu_component_contract.py`
- `backend/services/volum_aluminiu_quantity_ownership.py`
- `backend/services/volum_aluminiu_separate_calc_preview_service.py`
- `backend/services/commercial_price_proposal_service.py`
- `backend/services/estimated_internal_cost_service.py`
- `backend/services/letters_commercial_measurement_service.py`
- `backend/services/product_aggregate_service.py`
- `backend/services/product_e2e_readiness_service.py`
- `backend/data/mini_module_registry_volumetric_v2.py`
- `backend/tests/test_volum_aluminiu_identity_geometry_convergence.py`
- Docs under `docs/qa/product-system-authoring-runtime-codesign-e2e/VOLUM_ALUMINIU_ACTIVATION_READINESS_*`
- Worklog section **VOLUM ALUMINIU ACTIVATION READINESS CLOSURE**

## Commit SHAs

| # | SHA | Message |
|---|-----|---------|
| 1 | `a7cb015f` | feat(product-system): converge aluminium return canonical identity mappings |
| 2 | `5b2daca4` | feat(product-system): converge CPP product-total on confirmed perimeter / control quote_geometry bridge |
| 3 | `ca835156` | test(product-system): prove identity and geometry equivalence |
| 4 | (docs commit) | docs(qa): activation readiness closure evidence |

Closure HEAD: see `git rev-parse HEAD` after docs commit.
