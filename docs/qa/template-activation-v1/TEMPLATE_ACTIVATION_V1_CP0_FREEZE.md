# TEMPLATE_ACTIVATION_V1 — CP0 Lifecycle Freeze

| Field | Value |
|-------|--------|
| Kickoff HEAD | `c5a7ffea` |
| Prior build | AI_OPERATIONAL_DEFAULTS_V1 PASS_WITH_WARNINGS |
| Proof port | `:8020` (`:8000` ghost) |
| Migration | **none** — reuse `publication_status` / existing transition API |

## Activation vs publication (frozen)

| Concept | Meaning | Field |
|---------|---------|-------|
| **Active** | Catalog usable / permitted readers | `product_templates.active` |
| **Published** | Current Product System truth for downstream | `publication_status=PUBLISHED` |
| **Draft / lifecycle** | Authoring pipeline | DRAFT → VALIDATED → E2E_CHECKED → PUBLISHED → DEPRECATED → ARCHIVED |
| Rule | `active=true` ≠ published | `active_is_not_published=True` |

## Operational readiness (additive, from pricing 1.2.0)

`ACTIVE_WITH_CONFIRMED_TRUTH` · `ACTIVE_WITH_AI_DEFAULTS` · `ACTIVE_WITH_WARNINGS` · `BLOCKED`

AI defaults are valid commercial fallback. Provenance must travel with publish evidence.

## Publish hard-gate (frozen)

Publish / mark_e2e_checked allowed only when:

1. E2E verdict ∈ `{STATIC_READY, STATIC_READY_WITH_WARNINGS, RUNTIME_READY}`
2. No **structural** blockers (`blocking=true` findings, inactive template, `required_inactive_child`)
3. Known conflicts are **warnings** unless listed as hard structural codes

Do **not** treat every `known_conflicts[]` entry as a publish blocker.
Do **not** treat `e2e_ready=false` alone as publish denial when verdict is publishable.

## Optional capability (ACM)

| Capability | Scope |
|------------|-------|
| Base shell (panel-only) | May publish when shell truth coherent |
| Logo branch | Optional — honesty warning, not shell BLOCKED |
| Face treatments | Commercially blocked; `treatment_commercial_lines_allowed=false` |

## Snapshot safety

Quote/Order Snapshot V2 pin `template_code` + Product Truth revision/hash — not `publication_version`. Publish must not recalculate historical snapshots.

## Target templates

VL · Logo · Volum Aluminiu · ACM boxed. No ACM cassetted. No dual-select. No Execution materialization.

## Sidebar CP0 UI closure

`/inventory` exact · `/inventory/pricing` Pricing only · `/product-system/*` Product System (nested OK).
