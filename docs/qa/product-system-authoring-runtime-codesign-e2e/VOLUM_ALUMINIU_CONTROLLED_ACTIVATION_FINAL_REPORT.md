# VOLUM ALUMINIU — Controlled Activation Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `6dcf7bc1` (reconfirmed) |
| Subject | `TPL-VOLUM-ALUMINIU_v1` |
| Mode | Controlled **activate-only** — **no parent publish** |
| Prior readiness | `VOLUM_ALUMINIU_ACTIVATION_READINESS_CLOSURE_FINAL_REPORT.md` |
| Convergence map | `VOLUM_ALUMINIU_ACTIVATION_READINESS_CONVERGENCE_MAP.md` |
| Allowlist | `VOLUM_ALUMINIU_CONTROLLED_ACTIVATION_ALLOWLIST.md` |
| Evidence | `volum-aluminiu-activation/` |

---

## 1. Kickoff confirmation

| Item | Result |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `6dcf7bc1` reconfirmed |
| Dirty tree | Preserved; allowlist-only commits |
| Owner GO | **ACTIVATION GO** (child only) |
| Prior state | Identity/geometry PASS; publication BLOCKED by inactive child |

## 2. Absolute boundaries (honored)

Not published parent. Not activated logo return. No CT table / PI / CI. No pricing/formula/link edits. No Quote/Order/Execution. No schema migration. No SVG parse. No push/PR. Dirty tree untouched outside allowlist.

## 3. Executive truth (română)

Child-ul canonic `TPL-VOLUM-ALUMINIU_v1` este acum **activ** (`product_templates.active=true`, row id 10). Nu este publicat. Părintele VL **nu** a fost publicat. Blockerul de inactivitate s-a închis; rămân warning-uri / `NOT_TESTED`. Active ≠ published ≠ parent ready ≠ parent published.

## 4. Pre-activation gate

| Gate | Verdict |
|------|---------|
| Unique canonical identity | **PASS** (1 row) |
| Explicit aliases | **PASS** (`IDENTITY_MAP`) |
| No duplicate active aluminiu | **PASS** |
| Separate calc PASS | **PASS** (37+ tests pre-write) |
| Preview/CPP equivalence | **PASS** (prior + regression) |
| Perimeter authority | **PASS** |
| Anti-hourly | **PASS** (ml) |
| Expected relationship | **PASS** (`required_module` VL) |
| Known write path | **PASS** (script + seed durability) |
| Known audit | **PASS** (receipt JSON + logger) |
| No migration/pricing write | **PASS** |

**Lead approval:** GO for Agent B activate-only write.

## 5. Canonical DB/API record

| Field | Value |
|-------|--------|
| Table | `product_templates` |
| Row id | `10` |
| `template_code` | `TPL-VOLUM-ALUMINIU_v1` |
| BOM id | `comp_volum_aluminiu_module` |
| Module link | parent `TPL-VOLUMETRIC-LETTERS_v2`, `required_module`, link `active=true` (unchanged) |

## 6. Aliases (not activated)

| Alias | Action |
|-------|--------|
| `comp_lateral_litere` | mapping only |
| `TPL-COMP-LETTER-RETURN-CANT_v1` | absent from DB |
| `TPL-VOLUMETRIC-LOGO-RETURN_v1` | untouched (already active elsewhere) |

## 7. Activation write path

| Item | Value |
|------|--------|
| Mechanism | `backend/scripts/activate_tpl_volum_aluminiu_v1.py` |
| Actor | `product_system_activation_controller` |
| Timestamp UTC | `2026-07-21T11:50:35.197342+00:00` |
| Dry-run | executed first — PASS |
| Atomic field | `active` only |
| Idempotent re-run | noop (`mutated=false`) |

## 8. Exact fields mutated

| Entity | Field | Before | After |
|--------|-------|--------|-------|
| `product_templates` id=10 | `active` | `false` | `true` |
| same row | `publication_status` | `null` | `null` (untouched) |
| same row | `published_at` / `published_by` | `null` | `null` (untouched) |
| Parent VL id=8 | any | — | **not touched** |
| Module links | any | — | **not touched** |

## 9. Seed durability (code)

- `seed_tpl_volumetric_letters_v2`: default `active=True`; no longer force-deactivates on reseed
- `seed_tpl_volumetric_letters_component_modules_v1`: no longer force-deactivates aluminiu; dossier publication_policy updated (`do_not_auto_publish`)

## 10. Contract flags

| Flag | Value |
|------|-------|
| `ACTIVATION_FORBIDDEN_IN_THIS_BUILD` | `False` |
| `PUBLICATION_REMAINS_BLOCKED` | `True` (parent publish separate GO) |

## 11. Audit

Receipt: `volum-aluminiu-activation/activation_write_receipt.json`  
Logger event: `component_template_activate_only`.

## 12. Rollback procedure (documented — not executed)

1. Set `product_templates.active=false` for row id 10 / `TPL-VOLUM-ALUMINIU_v1` only.
2. Do not touch `publication_status`.
3. Re-run static readiness — expect `components.required_inactive.TPL-VOLUM-ALUMINIU_v1` BLOCKED again.
4. Revert seed defaults only if owner revokes GO.

## 13. Identity table (post)

| Layer | Identifier | Active target | Verdict |
|-------|------------|---------------|---------|
| Template code | `TPL-VOLUM-ALUMINIU_v1` | true | **PASS** |
| BOM | `comp_volum_aluminiu_module` | `modelare_cant` | **PASS** |
| Pricing stub | `comp_lateral_litere` | `modelare_cant` | **PASS** |
| Aspirational | `TPL-COMP-LETTER-RETURN-CANT_v1` | — | **PASS** |
| Logo return | `TPL-VOLUMETRIC-LOGO-RETURN_v1` | true untouched | **PASS_UNTOUCHED** |
| Parent VL | `TPL-VOLUMETRIC-LETTERS_v2` | active / not published | **PASS_NOT_PUBLISHED** |
| Duplicate rows | count=1 | 1 active | **PASS** |

## 14. Separate preview regression

Fixture perimeter **12.5 m**, depth 60, `white_aluminum` → `separate_calculation=PASS`, qty 12.5, commercial basis `ml`, `persist=false`.

## 15. Fresh readiness

| Axis | Result |
|------|--------|
| Verdict | `STATIC_READY_WITH_WARNINGS` |
| Build | `PASS_WITH_WARNINGS` |
| Template publication axis | `PASS` |
| `e2e_ready` | `false` |
| Inactivity blocker | **closed** |
| `required_active` aluminiu | **PASS** |
| NOT_TESTED | **6 preserved** (cpp/eic/quote_snapshot/order_snapshot/execution_preview/product_truth runtime) |

## 16. System Link Check (Catalog→EP)

| System | Status |
|--------|--------|
| catalog | PASS |
| components | PASS_WITH_WARNINGS |
| intake | PASS |
| product_definition | PASS |
| aggregate | PASS |
| quantity | PASS |
| product_truth / cpp / eic / quote_snapshot / order_snapshot / execution_preview | NOT_TESTED |

## 17. Parent VL impact

### **PASS_WITH_WARNINGS_NOT_PUBLISHED**

- Not BLOCKED by inactive aluminiu anymore
- Not auto-published
- `publication_status` remains `null`
- API may report `publish_allowed=true` — **does not mean published**; no publish transition executed

## 18–24. Distinctions (kept separate)

| State | Value |
|-------|-------|
| Component active | **true** |
| Component published | **false** |
| Parent ready (axis) | PASS with warnings / NOT_TESTED remain |
| Parent published | **false** |

## 25. UI screenshots

14 files in `volum-aluminiu-activation/` — see `SCREENSHOT_INVENTORY.md`.

## 26. Test matrix

```text
pytest tests/test_volum_aluminiu_controlled_activation_v1.py \
  tests/test_volum_aluminiu_identity_geometry_convergence.py \
  tests/test_volum_aluminiu_quantity_ownership.py \
  tests/test_volum_aluminiu_separate_calc_preview.py \
  tests/test_product_e2e_readiness_v1.py \
  tests/test_vl_real_product_configuration_v1.py \
  tests/test_product_template_publication_v1.py -q
→ passed (activation + invariants; inactive-child cases still force active=false in-test)
```

## 27. Stop conditions (after)

| Condition | Triggered? |
|-----------|------------|
| Duplicate active aluminiu | NO |
| Preview/CPP diverge | NO |
| PT bypassed | NO |
| Parent auto-published | NO |
| Unrelated product impact | NO (logo untouched) |

## 28. Naming

Internal codes unchanged. Admin label unchanged.

## 29. Commercial-hourly

**PASS** — ml basis preserved.

## 30. Logo return

**NOT GO / untouched.**

## 31. Publication honesty

Parent **not published**. Child **not published**. Activate-only.

## 32. Missing for parent publication (owner)

Runtime NOT_TESTED stages; owner publication GO; remaining aggregate warnings (e.g. trigger_field mismatch premount).

## 33. Activation verdict

### **PASS** (activate-only)

## 34. Next owner decision

### **request parent publication GO** *or* **keep parent unpublished**

Recommended default until runtime stages exercised: **keep parent unpublished**, then request publication GO when warnings/NOT_TESTED accepted.

Alternatives: close remaining readiness warnings first; activation failed — **N/A**.

## 35. Direction scores (0–100)

| Dimension | Score | Note |
|-----------|------:|------|
| Identity clarity | 96 | unchanged map |
| Activation honesty | 94 | activate ≠ publish |
| Parent publication honesty | 97 | not published |
| Separate calculability | 94 | regression PASS |
| Quantity truth | 95 | 12.5 m fixture |
| Commercial-hourly | 92 | ml |
| Readiness closure (inactivity) | 90 | blocker closed |
| Runtime completeness | 55 | NOT_TESTED remain |
| Operator label clarity | 82 | unchanged |

## 36. Forbidden confirmation

- Parent **not** published
- Child **not** published
- Logo return **not** changed
- Pricing/links/formulas **not** changed
- No Quote/Order/Execution

## 37. Files changed

See allowlist. Evidence under `volum-aluminiu-activation/`.

## 38. PAREREA MEA SINCERA

Activarea era pasul corect după closure — blockerul de inactivitate era onest, nu cosmetic. Important: UI/API pot arăta `publish_allowed` după ce child-ul e activ; asta **nu** înseamnă că VL e publicat. Nu apăsați Publică doar pentru că blockerul a dispărut — mai există `NOT_TESTED` pe CPP/EIC/EP. Păstrați părintele unpublished până la un GO dedicat de publicare.

---

## Rollback note

Documented in §12 — **not executed**.
