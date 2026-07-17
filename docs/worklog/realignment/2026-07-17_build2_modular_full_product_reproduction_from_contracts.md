# Build 2 — Modular Full-Product Reproduction from Contracts

| Field | Value |
|-------|--------|
| Task | BUILD2_FULL_PRODUCT_REPRODUCTION |
| Date | 2026-07-17 |
| Repo | `C:/w/psiso` |
| Branch | `feature/product-system-active-path-isolation-v1` |
| Start HEAD | `1764f0f` |
| End HEAD | `e07afb3` |
| Commit | `e07afb3` |
| Verdict | `BUILD2_FULL_PRODUCT_REPRODUCTION_COMPLETE_WITH_GUARDS` |

## Objective

Compose Intake V6 full-product Configurare from Product System modular form contracts while preserving golden behavior. No subset activation.

## Chosen architecture

```text
IntakeV6ModularFormContractService (single writer)
  → render_sections + full_product_composition
  → FE resolveReviewTabsFromModularContract
  → IntakeV6ReviewTabNav (contract authority)
  → specialized adapters (letter groups / lighting / montaj) keep golden UI
```

**Rejected:** second Intake, parallel catalog, generic rewrite of letter-group cards, subset UI, adhesive ownership move, formula/price edits, schema/migration.

## Contracts consumed

- `GET /api/v1/intake-v6/form-contract/TPL-VOLUMETRIC-LETTERS_v2` → v`1.3.0-full-product-composition`
- `composition_authority=true`, `subset_activation_enabled=false`
- Tabs: `finisaje` · `iluminare` · `montaj`
- Metadata sections: geometry_svg, packaging_logistics, interface_face_cant, montaj_system

## UI sections composed

| Tab | Renderer | Owners |
|-----|----------|--------|
| Finisaje | specialized_letter_groups | FACE, CANT, BACK, SURFACE_FINISH |
| Iluminare | specialized_lighting | LIGHTING, ELECTRICAL |
| Montaj | generic_fields + specialized_montaj | INSTALLATION_TEMPLATE, MOUNTING, STRUCTURE_SUPPORT |

## Remaining hardcoding

- Specialized JSX for letter groups / lighting / montaj still renders golden controls (by design)
- Plugin tabs remain fallback when composition_authority absent
- Offer-scope chips / soft defaults unchanged (Gates A–D deferred)

## Parity / guards

| Guard | Status |
|-------|--------|
| Historical CPP full-set fingerprint | Authority kept (`debitare_fata=20.9727`) |
| Fixture geometry rebuild `21.1675` | Preserved in Build 1 harness |
| Fresh UI disposable perimeter | Matches live historical `20.9727` |
| Thin Aggregate seed | Still non-authority |
| Adhesive ownership | Metadata only; not moved |
| Build 1 tests | Green |

## Fresh UI E2E

| Item | Value |
|------|--------|
| Workspace | `ce44f3f2-1018-4b8c-9011-92a1c402daaf` |
| Evidence | `docs/audits/_evidence/2026-07-17_intake_v6_build2_full_product/` |
| Composition UI | `data-composition-authority=contract`, tabs finisaje/iluminare/montaj |
| Save / return / hard refresh | OK |
| Responsive 1440 / 1280 / 768 | no horizontal scroll |

## Tests

```text
pytest modular_form + build2 + golden_parity → 39 passed, 1 skipped
vitest resolveReviewTabs + goldenSvg + productPlugin → pass
```

## Adversarial findings → fix pass

1. First E2E runs never reached Review step → fixed via `intake-v6-footer-next` / wait for `data-intake-v6-step=review`
2. Return URL missing `/operator` → fixed
3. Composition markers null until Configurare mounted → fixed

## Explicit exclusions honored

No Build 3, no cant-only, no Gates A–D, no formula/price/schema/seed, no historical mutation, no second Intake.

## Next safe step

Owner reviews fresh E2E + guards → separate GO for Build 3 subset isolation only.

**Cat sunt in directia stabilita: 90/100%**
