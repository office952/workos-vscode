# 15 — Form System Modularization Plan

**Version:** 1.0.0  
**Date:** 2026-06-30  
**Current status:** PARTIAL

---

## 1. Purpose

Form System must **not** be a separate hardcoded form per product. It must be:

- composed from **reusable mini-modules** aligned with ProductSystem;
- the Intake-facing layer that maps operator input → workspace paths → ProductDefinition properties;
- driven by **template activation** (which modules apply), not duplicate UI code per SKU.

**Role in chain:** Intake V6 UI → **Form System contract** → ProductDefinition compiler → ProductAggregate expand.

---

## 2. Current status

**PARTIAL** — read-only `form-contract` API + mini-module registry for `TPL-VOLUMETRIC-LETTERS_v2`; `VOLUMETRIC_FIELD_BINDINGS` still hardcoded in `intake_v6_modular_form_contract_service.py`; Intake UI only partly generated from contract.

---

## 3. Current implementation audit

| Area | File/route | Current behavior | Hardcoded? | Reusable? | Risk |
| ---- | ---------- | ---------------- | ---------- | --------- | ---- |
| Form contract API | `GET /api/v1/intake-v6/form-contract/{template}` | Returns modules + field_bindings | Partial | Pilot only | New templates need manual bindings |
| Mini-module registry | `data/mini_module_registry_volumetric_v2.py` | 8 module contracts | Data-driven | Yes for v2 | Not all modules have form fields |
| Field bindings | `VOLUMETRIC_FIELD_BINDINGS` in contract service | Static list ~20+ fields | **Yes** | No | Drift from registry |
| Intake UI steps | `frontend/.../intake-v6/*` | Step components | **Yes** | No | Duplicate per product risk |
| Template binding | workspace `template_code` | Single pilot | — | — | — |
| Payload mapping | workspace reducer | Paths in bindings | Partial | — | — |
| Conditional sections | activation_rules in registry + UI logic | Mixed | Partial | — | Trigger mismatches documented |

---

## 4. Target modular model

```
Form System =
  product family base fields (client, job meta)
+ geometry module (dimensions, SVG, letter metrics)
+ file/SVG module (upload, layer roles)
+ face/front finish module
+ side/return/cant module
+ back/support module
+ lighting/LED module (+ electrical when active)
+ mounting/premount module
+ finish module (paint/vinyl/RAL)
+ commercial constraints module (operator inputs — not commercial truth)
+ readiness/dossier acknowledgment module (gates, not pricing)
```

Each module is a **FormModule** with: `module_code`, `fields[]`, `activation_rules[]`, `product_definition_keys[]`, `product_system_module_code`.

---

## 5. Module contract (target)

| Module | Purpose | Inputs | Outputs | ProductSystem link | ProductDefinition output | Required/optional | Reusable |
| ------ | ------- | ------ | ------- | ------------------ | ------------------------ | ----------------- | -------- |
| geometry_svg | SVG + base geometry | file, layer roles | quote_geometry | geometry_svg mini-module | dimensions, letter_count | **Required** | Yes — all letter products |
| face_front | Face finish, CNC face | face_finish_type | finish_setup | debitare_fata | face processes | Required | Yes |
| side_return | Return depth, cant | return_depth_mm, finishes | finish_setup | modelare_cant | lateral/return | Required (volumetric) | Yes |
| back_support | Backing, spate | backing_mode | finish_setup | debitare_spate, structura_suport | back/support | Conditional | Yes |
| lighting_led | LED, PSU | lighting fields | finish_setup | sistem_led, electrica_logo | LED modules | Conditional | Yes |
| mounting | Bars, template | mounting_system | finish_setup | structura_suport, sablon | mounting ops | Conditional | Yes |
| finish_paint_vinyl | RAL, vinyl | finish fields | finish_setup | finisaje, colantare | finish ops | Conditional | Yes |
| commercial_inputs | markup, discount | operator numbers | commercial_inputs | — | **not** price truth | Optional | Yes |
| readiness | confirmations | gates | readiness flags | dossier gates | validation | Required at handoff | Yes |

---

## 6. Field-to-product mapping (pilot excerpts)

| Field | Form module | Workspace path | ProductDefinition property | ProductSystem module | Required? | Risk |
| ----- | ----------- | -------------- | -------------------------- | -------------------- | --------- | ---- |
| vector_file | geometry_svg | svg_source.file_name | vector_file | geometry_svg | Yes | Gate for geometry |
| letter_count | geometry_svg | quote_geometry.letter_count | letter_count | geometry_svg, debitare_fata | Yes | CPP/EIC key |
| return_depth_mm | side_return | finish_setup.return_depth_mm | return depth | modelare_cant | Yes | Activates lateral module |
| illuminated | lighting_led | finish_setup.illuminated | LED active | sistem_led | Conditional | — |
| mounting_system | mounting | finish_setup.mounting_system | mounting | structura_suport | Conditional | DEC-002 premount |

Full binding list: `intake_v6_modular_form_contract_service.py` — **hardcoded today**.

---

## 7. Conditional logic

| Condition | Form effect | ProductDefinition effect |
| --------- | ----------- | ------------------------ |
| SVG uploaded + layer roles | geometry module complete | geometry_svg active |
| `illuminated` / lighting type ≠ none | LED fields visible | activates sistem_led (+ electrica when wired) |
| return depth selected | cant fields active | modelare_cant + linked TPL-VOLUM-ALUMINIU |
| mounting bars / premount | mounting fields | structura_suport (DEC-002 if fab task needed) |
| face finish paint vs vinyl | finish subfields | finisaje / colantare paths |
| readiness confirmations | handoff enabled | validation READY / blockers |

**Rule:** conditions live in **registry activation_rules** + single evaluator — not copy-pasted per product form.

---

## 8. Avoid duplicate forms

1. **One FormModule library** — shared across templates (geometry_svg, lighting_led, …).
2. **Template manifest** — lists which FormModules activate for `TPL-VOLUMETRIC-LETTERS_v2` vs future ACM.
3. **Intake UI renders from contract** — sections = modules; fields = bindings (target).
4. **ProductDefinition** composes activated modules into one technical solution.
5. **ProductSystem dossier** holds technical ops/task_rules — not duplicate Intake fields.

**Forbidden:** new full-page form fork per product; duplicate field paths in Intake and dossier without binding registry.

---

## 9. Status of volumetric pilot

| Aspect | Status |
| ------ | ------ |
| Registry modules (8) | VALIDATED — `mini_module_registry_volumetric_v2.py` |
| Form contract route | VALIDATED — read-only |
| Hardcoded bindings | PARTIAL — must generalize |
| UI from contract | PARTIAL — many custom step components |
| Maps to ProductDefinition | STRONG — builder uses same triggers |
| Reusable for next template | NOT_STARTED — needs module library extraction |

See [16_VOLUMETRIC_LETTERS_TEMPLATE_MODULARIZATION.md](./16_VOLUMETRIC_LETTERS_TEMPLATE_MODULARIZATION.md).

---

## 10. Gaps

| Gap | Severity |
| --- | -------- |
| Hardcoded `VOLUMETRIC_FIELD_BINDINGS` | HIGH |
| UI not contract-driven | HIGH |
| No universal FormModule schema in DB | MEDIUM |
| Trigger field mismatches (`metal_support_required` vs `mounting_system`) | MEDIUM |
| commercial_inputs in form vs CPP rules separation unclear in UI | MEDIUM |

---

## 11. Next safe step

**Audit current volumetric letters template modules** (doc 16) and **owner DEC-003/004/005** before implementing dynamic form generation — avoid encoding wrong lateral/paint semantics into new form modules.
