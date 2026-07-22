# TEMPLATE_ACTIVATION_V1 — Final Report

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Kickoff HEAD | `c5a7ffea` |
| Final HEAD | `1f8d8e0b` |
| Verdict | **PASS_WITH_WARNINGS** |
| Evidence | `docs/qa/template-activation-v1/` |
| Migration | **none** |
| Push / PR | **none** |

## 1. Verdict by axis

| Axis | Result |
|------|--------|
| Lifecycle contract | PASS — reuse DRAFT…PUBLISHED; active ≠ published |
| Activation | PASS — AI defaults accepted as operational truth |
| Publication | PASS — VL + ACM shell published with evidence |
| AI-default policy | PASS — provenance on state + transition evidence |
| Warnings | PASS — known_conflicts demoted to warnings |
| True blockers | PASS — Logo/Aluminiu root PD missing retained |
| Optional capabilities | PASS — ACM logo honesty scoped; treatments false |
| Product Truth | PASS — no hash rewrite; snapshots pin code+truth |
| Snapshots | PASS — no retroactive recalculation path touched |
| CPP / EIC | PASS — identical line/rule codes vs AI defaults dumps |
| UI | PASS_WITH_WARNINGS — publish chips fixed; list badges still noisy |
| Sidebar navigation | PASS — Inventar exact / Pricing exact |
| Regression | PASS — Logo publish rejected 409 |

## 2. Executive truth (RO)

Template-urile utilizabile nu mai stau suspendate doar pentru că au default-uri AI sau conflicte cunoscute non-structurale. VL și shell-ul ACM sunt **PUBLISHED**. Logo și Volum Aluminiu rămân nepublicate ca root (PD lipsă / rol copil). Tratamentele ACM rămân blocate comercial. Snapshot-urile vechi nu se recalculează.

## 3. Repo / branch / HEADs

- Repo `C:\w\psiso`
- Branch `feature/product-system-active-path-isolation-v1`
- Kickoff `c5a7ffea`
- Dirty tree: unrelated paths protected

## 4. Accepted AI Operational Defaults

schema 1.2.0 · ACTIVE_WITH_AI_DEFAULTS / WARNINGS · no time-primary · packaging demotion preserved

## 5. Runtime

Proof `:8020`. `:8000` ghost 404. FE `:3000`.

## 6–14. Plan / map / CP0 / eligibility / matrix

See CP0 freeze, allowlist, transition matrix, compound map in this folder.

## 15–20. Template decisions

| Template | Decision |
|----------|----------|
| VL | **PUBLISHED** v1 · AI 4 decisions · STATIC_READY_WITH_WARNINGS |
| Logo | **not published** · BLOCKED PD missing · candidate_only |
| Volum Aluminiu | **active child, not root-published** |
| ACM shell | **PUBLISHED** v1 · ACTIVE_WITH_WARNINGS · treatments `false` · 5/0 |
| PREPRESS | OPERATION_ONLY · non-blocking |

## 21–26. Truth / service / snapshots / CPP / EIC / execution

- Publication service: structural blockers only; AI evidence on publish
- Idempotent: second VL publish → `publication_transition_not_allowed`
- Logo invalid publish → 409
- CPP/EIC unchanged vs `ai-operational-defaults-v1/runtime`
- Execution: preview-only untouched

## 27–29. UI / sidebar / screenshots

Publicare panel shows readiness + AI defaults + eligibility. Sidebar ownership fixed. Screenshots 01–04.

## 30–35. Tests / evidence / files / commits / worklog / dirty tree

```text
pytest test_template_activation_eligibility + publication + acm composition → 21 passed
vitest productSystemPublicationGate.test.ts → 5 passed
```

## 36. Remaining warnings

- Catalog “Blocat (pregătire)” chips lag publication truth
- Logo / Aluminiu root PD still missing
- Calibration samples absent
- `:8000` environment ghost

## 37–38. Published / blocked

**Published:** VL, ACM shell  
**Blocked/unpublished:** Logo (PD), Volum Aluminiu (child), ACM treatments (commercial)

## 39. Next recommended build

**PRODUCT_PRICE_BREAKDOWN_V1** — calibration surface for AI defaults vs measured reality.

Alternates: `TEMPLATE_ACTIVATION_V1_CLOSURE`, `ACM_CAPABILITY_PRICING_V1`, `CNC_MACHINE_SERVICE_MATRIX_V1`.

## 40–42. Dead pieces / method / sincere opinion

No dual lifecycle engine. Method: freeze → demote artificial gates → publish evidence-approved only → UI/sidebar.  
Activated real templates? Yes. Blind publish? No. Snapshots safe? Yes. ACM shell unfairly blocked by optional logo? Fixed. Navigation correct? Yes. Fragile: catalog badge lag; Logo PD.

## 43. Roadmap awareness

Inventory live · catalogs rate authority · Product System owns recipes+lifecycle · AI configurable truth · ACM controlled · no Execution · no artwork · no Build 2 · mobile final-final.

## 44. Direction score

| Axis | Score |
|------|------:|
| Lifecycle | 88% |
| Activation | 85% |
| AI-default acceptance | 90% |
| Blocker quality | 82% |
| Snapshot safety | 92% |
| CPP/EIC | 90% |
| UI | 78% |
| Navigation | 95% |
| Operational readiness | 86% |
| **Overall** | **86/100%** |
