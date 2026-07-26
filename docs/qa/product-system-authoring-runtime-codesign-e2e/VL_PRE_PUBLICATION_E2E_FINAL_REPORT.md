# VOLUMETRIC LETTERS — Pre-Publication E2E Proof Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-21 |
| Repo | `C:\w\psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `520f3f01` (**reconfirmed**) |
| Subject | `TPL-VOLUMETRIC-LETTERS_v2` parent — **KEEP UNPUBLISHED** |
| Child | `TPL-VOLUM-ALUMINIU_v1` active=true, published=false |
| Mode | Pre-publication E2E proof — close six NOT_TESTED |
| Shared map | `VL_PRE_PUBLICATION_E2E_SHARED_MAP.md` |
| Allowlist | `VL_PRE_PUBLICATION_E2E_ALLOWLIST.md` |
| Evidence | `runtime/vl_pre_publication_*` |
| Worklog | `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md` |

---

## 1. Kickoff confirmation

| Item | Result |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `520f3f01` reconfirmed |
| Dirty tree | Preserved; allowlist-only commits |
| Prior state | Parent `PASS_WITH_WARNINGS_NOT_PUBLISHED`; 6 NOT_TESTED |
| Owner GO | Pre-publication E2E verification only — **no publish** |

## 2. Absolute boundaries (honored)

Parent unpublished. Logo return untouched. No relationship/pricing/formula redesign. No SVG/DWG/DXF parse. No Build 2. No Execution materialization. No employee assignment. No live customer Quote/Order. Dirty tree untouched outside allowlist. No push/PR.

## 3. Executive truth (română)

Cele șase stări `NOT_TESTED` din System Link Check (Product Truth, CPP, EIC, Quote Snapshot, Order Snapshot, Execution Preview) se **închid la PASS pe `runtime_dry_run`** cu fixture izolat `VL_PREPUB_E2E_FIXTURE_v1` (perimetru confirmat 12.5 m). Modul **static** păstrează onest `NOT_TESTED` (fără claim de runtime). Verdict runtime: **PARTIAL** din warning-uri Aggregate deja cunoscute (nu din cele șase). Părintele VL **rămâne unpublished**. Recomandare: **GO_WITH_CONDITIONS** — nu executată.

## 4. CP0 freeze

Shared map + allowlist authored before behavior writes. Engine: native inline (no `.compound-engineering/config.local.yaml`).

## 5. Fixture lineage

| Key | Value |
|-----|--------|
| Label | `VL_PREPUB_E2E_FIXTURE_v1` |
| Perimeter | 12.5 m operator_confirmed |
| Depth | 60 mm |
| Finish | `white_aluminum` |
| Groups | `pseudo:maria` |
| Persistence | isolated `IV6-VL-PREPUB-*` pytest / proof script memory DB |
| SVG/DWG/DXF | **not used** |

## 6–12. Per-system verdicts (Catalog→EP)

| System | Static | Runtime dry-run | Verdict |
|--------|--------|-----------------|---------|
| catalog | PASS | PASS | **PASS** |
| components | PASS_WITH_WARNINGS | PASS_WITH_WARNINGS | **PASS_WITH_WARNINGS** (premount trigger / dossier metadata) |
| intake | PASS | PASS | **PASS** |
| product_truth | NOT_TESTED | PASS | **PASS** (runtime) |
| product_definition | PASS | PASS | **PASS** |
| aggregate | PASS | PASS | **PASS** |
| quantity | PASS | PASS | **PASS** |
| cpp | NOT_TESTED | PASS | **PASS** (runtime ml preview↔total) |
| eic | NOT_TESTED | PASS | **PASS** (runtime INT_VOL_V2_RETURN_ML) |
| quote_snapshot | NOT_TESTED | PASS | **PASS** (freeze gate) |
| order_snapshot | NOT_TESTED | PASS | **PASS** (provenance; no order create) |
| execution_preview | NOT_TESTED | PASS | **PASS** (frozen preview; no materialization) |

## 13. Six NOT_TESTED disposition table

| # | System | Before (static) | After (runtime) | Disposition | Evidence |
|---|--------|-----------------|-----------------|-------------|----------|
| 1 | product_truth | NOT_TESTED | PASS | **CLOSED→PASS** | confirmed job revision + freeze allowed |
| 2 | cpp | NOT_TESTED | PASS | **CLOSED→PASS** | separate-calc ml qty == product-total 12.5 |
| 3 | eic | NOT_TESTED | PASS | **CLOSED→PASS** | `INT_VOL_V2_RETURN_ML` aligned |
| 4 | quote_snapshot | NOT_TESTED | PASS | **CLOSED→PASS** | freeze gate would allow Snapshot V2 |
| 5 | order_snapshot | NOT_TESTED | PASS | **CLOSED→PASS** | provenance pass-through; `order_created=false` |
| 6 | execution_preview | NOT_TESTED | PASS | **CLOSED→PASS** | frozen preview safety flags all true |

Static mode **still reports NOT_TESTED** for these six by design — not stale reuse; not greenwashed.

## 14. CP1 Intake + Product Truth

**PASS** — confirm pins revision 1, `commercial_freeze_allowed=true`, content_hash `sha256:…`.

## 15. CP2 Product Definition

**PASS** — PD preview shares confirmed revision/hash from workspace.

## 16. CP3 Aggregate + Quantity

**PASS** — Aggregate provenance + commercial quantities share same revision/hash; face area 0.25 m² from instances.

## 17. CP4 CPP + EIC

**PASS** — preview qty 12.5 m; basis `ml`; anti-hourly; line `modelare_cant_aluminiu`; internal `INT_VOL_V2_RETURN_ML`. Negative: evidence≠confirmed → fail-closed.

## 18. CP5 Quote Snapshot V2

**PASS** (freeze-gate assessment only) — no customer-facing live Quote created.

## 19. CP6 Order Snapshot

**PASS** (boundary) — provenance copies PT revision/hash with `no_live_workspace_reread`; **no Order row created**.

## 20. CP7 Execution Preview

**PASS** (preview-only) — `no_write`, `no_materialization`, `no_live_recompile`.

## 21. Identities preserved

Canonical aluminiu BOM `comp_volum_aluminiu_module` → `modelare_cant` once; pricing stub alias only; logo return untouched; parent code `TPL-VOLUMETRIC-LETTERS_v2`.

## 22. Perimeter / materials / finishes / ops

Confirmed perimeter authority; depth 60; white_aluminum; no SVG-derived perimeter.

## 23. Pricing / snapshot provenance

No double calc; quote_geometry bridge when aligned; demoted/fail-closed otherwise. Snapshots assessed via freeze helpers + frozen EP — not live commercial authority rewrite.

## 24. Fresh readiness before/after

| Axis | Before (activation report) | After (this proof) |
|------|---------------------------|--------------------|
| Static verdict | STATIC_READY_WITH_WARNINGS | STATIC_READY_WITH_WARNINGS |
| Six NOT_TESTED (static) | 6 | 6 preserved |
| Runtime six systems | NOT_TESTED / unexercised | **all PASS** |
| Runtime verdict | n/a | **PARTIAL** (aggregate warnings) |
| e2e_ready | false | false (PARTIAL ≠ RUNTIME_READY) |
| template_publication_status | PASS (axis after activation) / warnings | NOT_READY under PARTIAL |
| Parent published | false | **false** |
| write_performed | false | false |

Evidence JSON:

- `runtime/vl_pre_publication_static_readiness.json`
- `runtime/vl_pre_publication_runtime_readiness.json`
- `runtime/vl_pre_publication_disposition_summary.json`

## 25. Remaining warnings (not the six)

- `TRIGGER_FIELD_MISMATCH` premount optional
- `DOSSIER_METADATA_ONLY` / process-map defaults / identity traces

These keep runtime verdict **PARTIAL** — honest, non-blocking for the six closures.

## 26. Negative tests

| Case | Result |
|------|--------|
| Perimeter divergence (12.5 vs 18.5) | fail-closed qty |
| Static NOT_TESTED ≠ PASS | asserted |
| Missing workspace runtime | prior readiness suite BLOCKED |
| Order create | not performed |
| EP materialization | not performed |

## 27. Full test matrix

```text
pytest tests/test_vl_pre_publication_e2e_proof_v1.py \
  tests/test_product_e2e_readiness_v1.py -q
→ 15 passed

pytest tests/test_volum_aluminiu_separate_calc_preview.py \
  tests/test_volum_aluminiu_identity_geometry_convergence.py \
  tests/test_product_truth_revision_quantity_convergence_v1.py \
  tests/test_vl_real_product_configuration_v1.py -q
→ 23 passed
```

## 28. Screenshots 1–17

| Status | Note |
|--------|------|
| **NOT_CAPTURED** | FE/BE stack not confirmed live in this run (probe hung / unavailable). Prior activation pack remains under `volum-aluminiu-activation/`. UI polish not in scope. |

Inventory stub: `vl-pre-publication-e2e/SCREENSHOT_INVENTORY.md`.

## 29. Stop conditions

| Condition | Triggered? |
|-----------|------------|
| Publication required to exercise flow | **NO** |
| Schema/pricing redesign | **NO** |
| Snap/Order needs live customer data | **NO** (boundaries used) |
| EP needs materialization | **NO** |
| Conflicting PT authority | **NO** |
| Double-count | **NO** |
| quote_geometry independent again | **NO** (bridge/fail-closed) |
| Inseparable dirty tree | **NO** |

## 30. PARENT PUBLICATION RECOMMENDATION

### **GO_WITH_CONDITIONS** — **NOT EXECUTED**

Conditions:

1. Owner explicit publication GO (separate decision).
2. Accept remaining Aggregate `PASS_WITH_WARNINGS` (premount trigger / dossier metadata) or close them in a dedicated pass.
3. Prefer runtime_dry_run evidence over static-only for publication readiness narrative.
4. Keep child `publication_status` unpublished unless separately tasked.
5. Do not treat UI `publish_allowed` as “already published”.

**`publication_status` left unpublished.**

## 31. Recommendation alternatives rejected

| Option | Why not |
|--------|---------|
| GO (unconditional) | Aggregate warnings → PARTIAL; e2e_ready false |
| NO-GO | Six runtime closures PASS; no hard blocker from inactive aluminiu |
| INSUFFICIENT_EVIDENCE | Fresh pytest + proof script evidence present |

## 32. Direction scores (0–100)

| Dimension | Score | Note |
|-----------|------:|------|
| Identity clarity | 96 | unchanged |
| Activation honesty | 94 | child active ≠ published |
| Parent publication honesty | 98 | unpublished held |
| Separate calculability | 95 | 12.5 ml path |
| Quantity truth | 95 | confirmed perimeter |
| Commercial-hourly | 93 | ml / anti-hourly |
| Runtime completeness | 88 | six closed at runtime |
| Static honesty | 92 | NOT_TESTED preserved statically |
| Snapshot/Order safety | 90 | no live customer writes |
| EP preview safety | 92 | no materialization |
| Operator readiness clarity | 84 | static vs runtime must be taught |

## 33. Forbidden confirmation

- Parent **not** published
- Child **not** published
- Logo return **not** changed
- Pricing/links/formulas **not** redesigned
- No live customer Quote/Order
- No Execution materialization

## 34. Files changed (allowlist)

- `backend/services/product_e2e_readiness_service.py`
- `backend/tests/test_vl_pre_publication_e2e_proof_v1.py`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/VL_PRE_PUBLICATION_E2E_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/runtime/vl_pre_publication_*`
- `docs/qa/product-system-authoring-runtime-codesign-e2e/vl-pre-publication-e2e/`
- `docs/worklog/realignment/2026-07-20_product_system_authoring_runtime_codesign_e2e_build.md`

## 35. Commits (planned allowlist sequence)

1. `test: intake through quantity` (+ readiness runtime commercial/EP checks needed for CP4–7)
2. `test: CPP EIC snapshot` — may fold into (1) if single test module
3. `test: order EP preview boundaries` — may fold into (1)
4. `fix: evidence-backed E2E defects only` — readiness runtime checkers
5. `docs(qa): finalize pre-publication proof`

## 36. Agents A–G rollup

| Agent | Result |
|-------|--------|
| A Fixture/Intake | PASS |
| B PT+PD | PASS |
| C Agg+Qty | PASS |
| D CPP+EIC | PASS |
| E Snapshot+Order | PASS (boundaries) |
| F EP Preview | PASS (preview-only) |
| G Readiness/UI/QA | PASS readiness; screenshots NOT_CAPTURED |

## 37. Architecture reopen

**None.** No Build 2, no CT table, no PI/CI.

## 38. PAREREA MEA SINCERA

Cele șase `NOT_TESTED` erau oneste în static — readiness refuza să pretindă CPP/EIC/Order/EP fără exercițiu. Cu fixture de 12.5 m și `runtime_dry_run`, traseul e credibil până la preview de EP **fără** a publica părintele. Nu aș da GO necondiționat: rămân warning-uri Aggregate (premount trigger) și `e2e_ready=false` sub PARTIAL. Publicarea tot cere un buton/GO separat — nu o deduceți din închiderea NOT_TESTED.

## 39. Next owner decision

1. Accept **GO_WITH_CONDITIONS** and keep unpublished, **or**
2. Issue dedicated **parent publication GO**, **or**
3. Close Aggregate warning hygiene first, then re-run runtime readiness.

## 40. Rollback note

Readiness runtime checkers are additive. Revert `product_e2e_readiness_service.py` commercial/handoff runtime branches to restore prior static-only NOT_TESTED behavior. Fixture/tests are isolated — no production template mutation beyond prior aluminiu activation.
