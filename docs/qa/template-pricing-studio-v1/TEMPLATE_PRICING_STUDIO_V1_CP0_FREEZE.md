# TEMPLATE_PRICING_STUDIO_V1 — CP0 Freeze

| Field | Value |
|-------|--------|
| Date | 2026-07-22 |
| Kickoff HEAD | `585115da` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| API gate | PASS — see `RUNTIME_API_TRUTH.md` |

## Route freeze

| Layer | Decision |
|-------|----------|
| Operator nav | Product System → detail template → tab **Prețuri template** |
| Frontend path | `/product-system/products/:templateCode` + section `pricing` |
| Deep link | same path; section state local (no second Product System shell) |
| Rejected | `/product-system/templates/{code}/pricing` (frontend shell uses `products`, not `templates`) |
| Rate catalog exit | keep `/inventory/pricing?template=` (reusable rates, not recipe) |
| Backend API | `GET /api/v1/product-system/templates/{template_code}/pricing` |

## Ownership freeze

| Owner | Owns |
|-------|------|
| Inventory | material identity, stock, purchase cost |
| Pricing catalogs | reusable rates / typed_catalog |
| Product Template | recipe, quantity keys, applicability, version |
| CPP | commercial line result (preview only; no formula change) |
| EIC | provenance / internal evidence (preview only) |
| Studio | composition + visibility; **no** rate creation |

## Recipe item kinds

`material` · `machine_operation` · `labor` · `service` · `commercial_line` · `minimum` · `adjustment` · `unknown`

Identity (derived, not DB table):  
`{template_code}::{recipe_kind}::{stable_code}` where `stable_code` is `pricing_code` or CPP `line_code`.

## Editability policy

| Level | V1 |
|-------|-----|
| Read-only | **Default** — all recipe rows |
| Controlled reference selection | **Not enabled** |
| Unsupported editing | Locked with explanation |

## No-migration boundary

- No schema migration
- No seed/price value changes
- No ACM treatment unblock
- No CNC matrix
- No TemplateLaborRecipe table
- No rate-basis auto-fix
- No XOR / dual-select / Execution / artwork

## V1 template scope

- `TPL-ACM-BOXED-MOUNTING-SUPPORT_v1` (+ face-treatment blockers)
- `TPL-VOLUMETRIC-LETTERS_v2`
- `TPL-VOLUMETRIC-LOGO_v1` (linked recipe visibility)
- `TPL-VOLUM-ALUMINIU_v1` (component / identity map visibility)
