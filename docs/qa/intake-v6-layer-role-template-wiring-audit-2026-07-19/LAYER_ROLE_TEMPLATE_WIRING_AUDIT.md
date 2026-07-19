# Intake V6 — Layer Role & Template Wiring Truth Audit

**Mode:** READ-ONLY (docs + runtime inspection; no domain/UI implementation)  
**Date:** 2026-07-19  
**Baseline:** `f39c260`  
**Stack:** FE `:3000` · BE `:8003`

---

## 1. Verdict

**FAIL for “wiring truth ready for next UI polish”** — visual pilot remains accepted, but **physical binding is not yet trustworthy on first paint**.

ACM/support geometry is repeatedly **proposed as Vector Litere (`face`)**; correct ACM shell wiring exists only after **operator correction** (and prior live workspaces prove the happy path). Dual SVG ingest paths diverge. Next presentation build must wait for a targeted wiring repair GO.

---

## 2. Mini decizia agentului

Stop before more Finisaje/Iluminare polish. Document exact failure boundary: **analyzer proposal / role confirmation**, not missing ACM registry.

---

## 3. Git / runtime pre-flight

| Item | Value |
|------|--------|
| Branch | `feature/product-system-active-path-isolation-v1` |
| HEAD | `f39c260` |
| Foreign WIP | Present — untouched |
| FE | `:3000` 200 |
| BE | `:8003` healthy |
| `:3001` | Crash `3221226505` — operational only |
| Implementation | None (docs-only) |

---

## 4. Served commit

Acceptance evidence collected with repo HEAD `f39c260` on the `:3000` proxy stack. No claim that `:3001` served this commit.

---

## 5. Fixture inventory

See `runtime-evidence.md`. Mandatory fixtures found and exercised.

---

## 6. SVG detection trace

### Client analyzer (Page 1 file chooser) — truth for operator UI

Fixture `litere-cu-fundal-acm-segmentat.svg`:

| Detected element | Layer key | Proposal (auto) | Display label |
|------------------|-----------|-----------------|---------------|
| Grey panel fill | `pseudo:fill-c5c6c6` | `face` (high) | **Vector Litere** |
| Red letter fill | `pseudo:fill-e31e24` | `face` (high) | **Vector Litere** |

Root cause in code: `guessLayerAutoRole` short-circuits **all** `pseudo:*` layers to `face` (`frontend/src/lib/svgAnalyzer/analyzer/guessLayerAutoRole.ts` ~96–104). Support is **not** inferred from fill-pseudo layers; Contur suport comes from **closed-contour** association when operator picks `support_panel`.

### Server upload API

Produces named layers (`gravare-cnc-135gr`, `decupare-cnc-outside`) with `auto_role=unknown`, composition `blocked` / `NO_PRODUCT_COMPONENT_DETECTED`. **Does not** populate Page 1 client analyzer state (UI still empty upload). Detection truth ≠ UI truth on this path.

### Separation

| Stage | ACM segmented client path |
|-------|---------------------------|
| Detection | 2 pseudo fills + closed contours metadata |
| Proposal | Both → Vector Litere |
| Operator confirmation | Required; grey must become Contur suport |
| Confirmed truth | Only after role + FinishSetup support binding persist |

---

## 7–8. Role proposal & confirmation

- Labels **Vector Litere / Vector Logo / Fundal…** are **operator display labels** for geometry roles (`intakeV6LayerRoleOptions` + bindable `owner_label` “Vector litere”), not Product Templates.
- Selecting a role updates local confirmation via `updateLayerRole` / `applyLayerRoleSelection` — **does not** silently confirm a different role in the handler itself.
- Live: changing `face` → `printed_artwork` stayed on Straturi (`jumpedToConfirm=false`).
- Known wired workspace proves reload persistence of confirmed roles (`support_panel` + `face`) and bindings.

---

## 9. Navigation behavior

| Claim | Finding |
|-------|---------|
| Role select navigates to Confirmare | **Not observed** — handler has no `setStep` |
| Progress bar can open Confirmare early | **Yes** — `canAccessIntakeV6Step` allows `review` **and** `confirm` once analysis ready (`intakeV6Readiness.ts`) |
| Continue disabled until roles confirmed | Observed on client upload screenshots |

---

## 10. Component binding trace

Chain (active):

```text
confirmedRole face → LETTER_VECTOR_SET binding
  component_template_code from bindables LETTER_VECTOR_SET
  (contract FACE_COMPONENT = TPL-VOLUMETRIC-FACE_v1)

confirmedRole support_panel + closed contour associate
  → SUPPORT_CONTOUR binding
  component_template_code = TPL-ACM-BOXED-MOUNTING-SUPPORT_v1
  (svgComponentBindings.bindingFromSupportSelection / associate patch)
```

UI **displays/consumes** bindables from Product System availability projection; it **creates** FinishSetup bindings from role confirmation + contour association (`buildLayerRoleComponentBindings`, `IntakeV6SvgAnalyzerStep.handleUpdateLayerRole`).

---

## 11. `TPL-VOLUMETRIC-FACE_v1`

| Question | Answer |
|----------|--------|
| Origin | Static Product System SVG binding contract `FACE_COMPONENT` in `backend/data/product_system/svg_component_binding_contract.py` |
| Condition | LETTER_VECTOR_SET when layers confirmed as `face` |
| Hardcoded? | **Yes — code-owned registry constant**, not invented ad hoc in a random React card; also mirrored in FE bindable display switches |
| Can it attach to ACM support layer? | **If that layer remains confirmed as `face`**, yes — binding follows confirmed role, not physical intent. Proposal currently pushes ACM grey into `face`. |

---

## 12. ACM shell template wiring

| Question | Answer |
|----------|--------|
| Registered? | **Yes** — `SVG_BINDABLE_BY_PRODUCT_TEMPLATE[LETTERS]` + standalone ACM product entry |
| Selectable? | Via Contur suport / support_panel + closed contour (not as default layer proposal) |
| Produced for real ACM fixture? | **After operator correction** — proven on `bd26e3d5-…` CONFIRMED SUPPORT_CONTOUR |
| Reaches PD? | PD GET ACM template 200 with components |
| Reaches Aggregate/dry-run? | production-task-dry-run 200 |
| Page 2 config? | Montaj shows Fundal/carcasă IA + composition authority notice for ACM; Oracal-on-shell not shown as Finisaje letter fields (expected location = Montaj/support, not Finisaje letter cards) |

Live friction: client upload showed **“Salvarea Contur suport / ACP a eșuat (FinishSetup)”** when association attempted — wiring path exists but persistence can fail (classify as binding/FinishSetup reliability, not missing template).

---

## 13–14. ProductDefinition / Aggregate

- Letters PD 200 for workspace context; ACM PD 200.
- Composition recommendation on wired workspace: `letters_plus_support` with both template codes.
- Inactive-zero rule: not violated in inspected confirmed bindings (ACM present only when support binding CONFIRMED). No compiler changes made.
- Aggregate proxy: task dry-run preview only; no production mutation flags asserted true in summary keys inspected.

---

## 15. Page 2 rendering truth

| Surface | When ACM+letters confirmed (known wired) | Fresh client upload (roles incomplete) |
|---------|------------------------------------------|----------------------------------------|
| Finisaje | Letter/logo finish cards from letter bindings | Blocked / incomplete — no letter cluster until roles persisted |
| Iluminare | Letter LED path | Not reached |
| Montaj | Fundal/carcasă + ACM authority copy | Text may mention Alucobond from guidance; full panel after access |
| Confirmare | Accessible via progress once analysis ready | Not until ready |

Why operator sees Vector Litere on ACM grey: **proposal label**, not confirmed component truth. Why ACM config “missing”: roles not corrected / composition not confirmed / Finisaje is wrong place for shell Oracal/folds.

---

## 16. Segmented background

Known wired: `segmented_background.status=CONFIRMED` nested under FinishSetup with ACM host. Client guidance explicitly instructs Contur suport for exterior ACP panel. Proposal does not auto-confirm segmented (code comment: never auto-confirm).

---

## 17–18. Hardcoded / dead pieces

| Finding | Class |
|---------|-------|
| `FACE_COMPONENT = TPL-VOLUMETRIC-FACE_v1` in svg_component_binding_contract | **Active** registry constant |
| `ACM_BOXED_SUPPORT` same file | **Active** |
| `LEGACY_INTAKE_SVG_ROLE_ADAPTER` | Adapter marker — active guardrail |
| `TPL-BOND-CASETAT` | **Legacy/deprecated** string; UI warns live authority is ACM shell |
| `IntakeV6ReviewFaceLettersSection` / Cant split | **Legacy unused** in ReviewStep (tests only) — not revived |
| Pseudo→face short-circuit | **Active dangerous proposal heuristic** |
| Server vs client SVG paths | **Active dual path** — dangerous inconsistency |
| Progress bar confirm==review gate | **Active UX footgun** |

---

## 19. Screenshots

Indexed in `runtime-evidence.md` under `screenshots/`.

---

## 20. Root cause classification

| Symptom | Class |
|---------|-------|
| ACM shown as Vector Litere | **1 analyzer proposal** (+ display label) |
| FACE template on letter binding | **3/4 binding + registry** (correct when role=face) |
| ACM shell absent until Contur suport | **2 role confirmation** + contour associate |
| Page 2 omits ACM until confirmed | **7 frontend rendering condition** (access + tab content) gated by confirmation |
| Jump to Confirmare via progress | **7 frontend** readiness gate (not role handler) |
| Empty UI after server upload | **7 frontend / ingest path split** |

**Not** “missing ACM template registration”.

---

## 21. Smallest correct repair boundary (STOP — do not implement)

1. **Analyzer proposal:** do not force all `pseudo:fill-*` to `face` when closed-contour support candidates identify a panel envelope; propose `support_panel` / Contur suport for the support fill (or leave unknown + force Contur suport card).  
2. **Optional UX:** keep Confirmare progress locked until composition confirmed (separate from role select).  
3. **Ingest:** unify server upload hydration with client analyzer so Page 1 is not empty after API SVG.  

Out of bounds for that repair: Montaj IA redesign, pricing, PD schema, visual DS expansion.

---

## 22. Frozen

Backend domain compilers (unless dedicated GO), Montaj IA redesign, letter visual pilot scope creep, pricing, seeds/migrations, analyzer “quick hacks” without tests.

---

## 23. Tests/evidence

Runtime JSON + screenshots + static code references above. No new domain tests added (forbidden mutation). Existing contract tests already assert FACE/ACM bindables on LETTERS product.

---

## 24–25. Files modified / not

**Modified:** this QA pack + letter-pilot runtime closure docs + worklog.  
**Not modified:** frontend behavior, backend, analyzer, schemas, templates, DB.

---

## 26–27. Worklog / commit

Worklog: `docs/worklog/realignment/2026-07-19_intake_v6_layer_role_template_wiring_audit.md`  
Commit: `docs(intake-v6): audit layer role and template wiring`

---

## Core answers (explicit)

1. **ACM misclassified?** Yes at **proposal** time (both fills → Vector Litere). Correctable; known wired shows confirmed support.  
2. **Vector Litere/Logo?** Display/proposal label for roles — becomes binding truth only after confirmation.  
3. **FACE hardcoded?** Code-owned contract constant — yes; not a fake UI card.  
4. **ACM shell wired?** Yes when Contur suport confirmed; PD/dry-run/Montaj evidence.  
5. **Page 1 role select navigates wrong?** Role handler no; progress bar can open Confirmare early.  
6. **Page 2 omits ACM?** Omits until support/composition path complete; Finisaje is not shell home.  
7. **Presentation vs domain?** Primarily **proposal/confirmation wiring**, not cosmetic.  
8. **Smallest repair?** Pseudo-layer role proposal + Contur suport reliability (+ optional confirm step gate).  
9. **Frozen?** Montaj redesign, pricing, broader DS polish, domain compilers.  
10. **Next UI build safe?** **NU.**
