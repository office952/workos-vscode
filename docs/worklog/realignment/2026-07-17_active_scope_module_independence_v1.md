# Active Scope Module Independence V1 — Letters Slice 1

**Date:** 2026-07-17  
**Owner GO:** `GO: ACTIVE_SCOPE_MODULE_INDEPENDENCE_V1`  
**Branch:** `feature/product-system-active-path-isolation-v1`  
**Gate HEAD before work:** `1bc6a02`  
**Source audit:** `docs/audits/2026-07-17_product_system_module_independence_e2e_audit.md`  
**Acceptance case:** RETURN-CANT ONLY  

---

## Outcome

Canonical active-scope compiler (`active_scope_resolver_service`) is the single Letters Slice 1 authority from Intake `offer_scope` through ProductDefinition → Aggregate selected graph → commercial measurements / CPP → ExecutionPlan preview (frozen sold scope).

Modeled return sold alone no longer inherits full-template face/back/LED/finish/bonding pollution.

---

## Active-scope contract

- Schema: `backend/schemas/active_scope.py` (`ActiveScopeResult`)
- Resolver: `backend/services/active_scope_resolver_service.py` (`compile_active_scope`)
- Dependency classes: hard_technical · conditional · composition_only · commercial · execution
- Composition-only for RETURN-CANT alone: `return_face_bonding` / `RETURN_PROFILE_FACE_BONDING`

### Sold → runtime (Slice 1)

| Sold | Runtime |
|------|---------|
| FACE | debitare_fata |
| RETURN-CANT | modelare_cant |
| BACK | debitare_spate |
| LIGHTING / ELECTRICAL | sistem_led |
| Calc | geometry_svg (not priced) |

---

## ProductDefinition

- Consumes `compile_active_scope`
- Unselected modules → `inactive` (not pending blockers)
- In-scope pending stays selected (missing fields block readiness, not scope membership)
- Subset readiness skips inactive bindings; suppresses full-template warning noise

---

## ProductAggregate

- `filter_aggregate_by_active_scope` before consumers
- Identity dossier components enriched for sold modules without `components_json` rows
- RETURN-CANT forces aluminum child when `volum_aluminum_module_template_code` absent
- Composition child `mini_module_code` maps via `CHILD_TEMPLATE_TO_MODULE` (not composition role)
- Commercial measurements gated by `module_gate or module_code`

---

## Pricing path unification

- `resolve_pricing_active_modules` → `resolve_pricing_active_modules_from_scope`
- Graph cost path uses sold commercial set (not PD always_on ∩ sold)
- Linked-logo commercial lines suppressed in `component_subset`
- Live-calc offer-scope tests green for FACE / RETURN-CANT / BACK / FACE+RETURN

---

## Snapshots / Execution

- Quote/Order freeze of `offer_scope_snapshot` preserved (no retroactive mutation)
- Execution reader excludes bonding when canonical sold == `{RETURN-CANT}`
- Preview-only; no task materialization

---

## Tests (targeted)

```text
backend: test_active_scope_resolver_service
         test_product_definition_active_scope
         test_product_aggregate_active_scope_filter
         test_execution_sold_scope_reader
         test_intake_v6_live_calc_offer_scope
         test_intake_v6_offer_scope_persistence (FACE subset)
         + related composition / logo commercial

frontend: activeScopeGovernanceTruth · ModuleChain · Governance · currentTruthControlCenter
```

Known residual (out of slice / fixture debt): some template-only BOM dossier-component expectations; two V6 official snapshot fixture dry-run blockers (`PRINT_REQUIRED_UNKNOWN` / invalid payload schema).

---

## Control Center

`/modules` + `/governance` updated only after runtime proof:

- ACTIVE SCOPE SYSTEM = PROVEN FOR LETTERS SLICE 1 (status still PARTIAL — not global)
- MODELED RETURN STANDALONE = READY
- LOGO = BLOCKED
- ACM = PARTIAL
- G14 = PARTIAL APLICAT

---

## Explicit exclusions

No new templates · no `component_templates` table · no migrations/seeds · no Pricing Registry 7I · no Logo/ACM activation · no live task materialization · no minute→price · no `validate:frontend` green claim.
