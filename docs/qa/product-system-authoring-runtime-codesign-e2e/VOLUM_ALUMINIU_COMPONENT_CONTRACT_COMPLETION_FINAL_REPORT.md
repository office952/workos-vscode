# VOLUM ALUMINIU — Component Contract Completion Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `6608cdc5` |
| Subject | `TPL-VOLUM-ALUMINIU_v1` |
| Mode | Contract completion — **no activation / no publish** |
| CP0 map | `VOLUM_ALUMINIU_COMPONENT_CONTRACT_CP0_SHARED_MAP.md` |
| Allowlist | `VOLUM_ALUMINIU_CONTRACT_COMPLETION_ALLOWLIST.md` |
| Audit (accepted) | `VOLUM_ALUMINIU_COMPONENT_CONTRACT_AUDIT.md` |
| Evidence | `volum-aluminiu-completion/` |

---

## 1. Kickoff confirmation

| Item | Result |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `6608cdc5` reconfirmed |
| Dirty tree | Preserved; allowlist-only commits |
| Audit | Accepted; gaps closed without reopening legitimacy |

## 2. Absolute boundaries (honored)

Not activated / not published. No CT table, PI/CI, SVG parse, Build 2, EP materialization, Pricing redesign, logo consolidation, push/PR, or dirty-tree clean.

## 3. Executive truth (română)

**Cant / volum din aluminiu** are acum contract de calcul separat onest: perimetrul confirmat (m) conduce qty; evidența din `quote_geometry` nu mai poate marca componenta confirmată; preview read-only pe endpoint dedicat; baza comercială rămâne **ml**; publicarea VL rămâne **blocată**. Nu activa — contractul e gata de preview, nu de GO activare.

## 4–10. Identity / role / parents / usage

Unchanged from audit: child PT `component_only`, required on VL via `linked_child` / `letter_group_instances.sidewall` / `modelare_cant`. Admin label now **Cant / volum din aluminiu**.

## 11. Instance schema

`letter_group_instances.sidewall` + PT bag `product_truth.components.return_cant`.

## 12. Inputs (closed)

| Input | Unit | Ownership |
|-------|------|-----------|
| `confirmed_perimeter_m` | m | Operator → PT (drives separate calc) |
| `evidence_perimeter_m` | m | Observe only from `quote_geometry.letter_perimeter_m` |
| `return_depth_mm` / `material_profile.width_mm` | mm | Component gate 30/60/80/100 |
| `finish_variant` | enum | Component |
| `confirmation_state` | enum | Component (requires confirmed perimeter) |

Confirm bag: `finish_setup.return_cant_component_confirmation.instances.*`.

## 13. Validators / gates

Depth form options aligned to **30/60/80/100**. Unknown unit / non-positive / missing confirmation → fail closed. Evidence cannot auto-promote.

## 14–19. Materials / finishes / ops / pricing / cost

Child-owned (unchanged ownership); dual-id documented (`comp_volum_aluminiu_module` BOM vs `comp_lateral_litere` pricing stub). Commercial `modelare_cant_aluminiu` / EIC `INT_VOL_V2_RETURN_ML` — **ml**.

## 20. Commercial-hourly

**PASS** — ml + anti-hourly preserved.

## 21–22. Parent duplication / formulas

Root mats/ops remain 0. Formulas stay on child. No blind bridge deletion.

## 23. Readers

Contract view enrichment + separate-calc preview; Aggregate/CPP/EIC unchanged architecture.

## 24. Dossier

Still metadata-only; not activation SoT.

## 25. UI labels

Admin: **Cant / volum din aluminiu**. Ownership card: confirmation + preview honesty. Publication still blocked messaging.

## 26–27. Logo / legacy

Logo appendix only — `TPL-VOLUMETRIC-LOGO-RETURN_v1` not consolidated. RETURN-CANT naming aspirational; runtime remains Aluminiu code.

## 28. Runtime path

```text
Confirm bag / prior PT
  → return_cant bridge (honesty)
  → separate-calculation-preview (read-only)
  → qty m (= ml) + commercial/internal rule projection
Publication gate still BLOCKED (inactive required child)
```

## 29. SoT matrix

Confirmed perimeter SoT = `components.return_cant.instances[].geometry.confirmed_perimeter_m`. Evidence SoT = `quote_geometry.letter_perimeter_m` (non-driving for separate calc).

## 30. Separate calculation test

### **PASS_WITH_WARNINGS**

| Criterion | Result |
|-----------|--------|
| Child PT + schema | PASS |
| Validators / depth align | PASS |
| Qty ownership (confirmed) | PASS |
| Ops + materials refs | PASS |
| Pricing/EIC ml refs | PASS |
| Confirmation honesty | PASS |
| Independent preview | PASS |
| Live product-total CPP path still may use quote_geometry | WARNING (documented remaining parent dep) |
| Dual id | WARNING (documented) |
| Activation / publication | BLOCKED (intentional) |

## 31–32. Readiness / blockers

`KNOWN_REQUIRED_INACTIVE_CHILD` unchanged. New non-blocking finding `components.volum_aluminiu.separate_calc_contract`. Flipping `active=true` still **not** recommended.

## 33. Missing for activation (still)

Owner commercial/ops GO; live product-total path prefer confirmed qty; id unification GO; logo reuse decision; dossier quote_readiness text cleanup.

## 34. Activation recommendation

### **NO-GO**

Do not execute. Keep blocked.

## 35. Naming

Internal codes kept. Admin label updated to Cant / volum din aluminiu.

## 36. Stop conditions

| Condition | Triggered? |
|-----------|------------|
| Schema migration required | NO |
| Perimeter can't fit typed bags | NO |
| Unsafe formula split | NO |
| modelare_cant pricing architecture change | NO |
| Logo/letter identity collision | NO |
| Activation required to test preview | NO |
| Inseparable dirty tree | NO |

## 37. Screenshots

`volum-aluminiu-completion/`:

1. `01_separate_calc_evidence_board.png`
2. `02_unit_confirmation_trace.png`

Plus JSON: `01_input_contract.json`, `02_preview_blocked_evidence_only.json`, `03_preview_pass_confirmed.json`.

Audit screenshots (3) remain under `volum-aluminiu-audit/`.

## 38. Tests / commands

```text
pytest tests/test_return_cant_product_truth_bridge.py \
  tests/test_volum_aluminiu_quantity_ownership.py \
  tests/test_volum_aluminiu_separate_calc_preview.py \
  tests/test_product_template_component_contracts_v1.py \
  tests/test_product_e2e_readiness_v1.py -q
→ 28 passed

vitest productSystemAdminDisplay.test.ts → 4 passed
```

## 39. Owner decision

### **keep blocked**

## 40. Roadmap awareness

Aligned with component-owned calculation boundary; external artwork consume-only; no CT table; product-root quote remains.

## 41. Direction scores (0–100)

| Dimension | Score | Note |
|-----------|------:|------|
| Identity clarity | 88 | Real cant/return child |
| Operator label clarity | 82 | Cant / volum din aluminiu |
| Composition correctness | 90 | Required linked_child |
| BOM/ops ownership | 86 | Dual-id warn |
| Separate calculability | 84 | PASS_WITH_WARNINGS |
| Quantity truth | 86 | Confirmed m drives preview |
| Commercial-hourly | 92 | ml |
| Activation readiness | 28 | NO-GO |
| Logo reuse readiness | 40 | Appendix only |
| Publication honesty | 94 | Still blocked |

## 42. Preview endpoint

`POST /api/v1/product-system/templates/TPL-VOLUM-ALUMINIU_v1/separate-calculation-preview`

## 43. Unit freeze

Canonical **m**; commercial synonym **ml** (1:1); rounding 6 dp.

## 44. Forbidden confirmation

No activation. No publish. No auto-activate from readiness.

## 45. Commit SHAs

Recorded in worklog after allowlisted commits.

---

## PAREREA MEA SINCERA

Contractul era deja „pe jumătate adevărat”: bridge-ul marca `confirmed` fără perimetru confirmat — asta era minciuna care bloca separate calc. Am închis gap-ul pe bag-urile existente, fără arhitectură nouă de pricing și fără activare. Preview-ul separat e util și onest; **nu** înseamnă că VL e gata de Publică. Dual-id-ul și fallback-ul product-total pe `quote_geometry` rămân warning-uri reale pentru un GO ulterior.

## Verdict final (return-to-parent)

| Item | Verdict |
|------|---------|
| Separate calculability | **PASS_WITH_WARNINGS** |
| Activation recommendation | **NO-GO** (not executed) |
| Publication | **still BLOCKED** |
| Commercial-hourly | **PASS** |
| Unit freeze | **m** (ml synonym) |
| Preview endpoint | `.../TPL-VOLUM-ALUMINIU_v1/separate-calculation-preview` |
| Stop conditions | None hard-triggered |
| Kickoff HEAD | `6608cdc5` |
