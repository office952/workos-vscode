# F7I — Commercial pricing truth & tariff registry closure

| Field | Value |
| ----- | ----- |
| Date | 2026-08-03 |
| Branch | `feat/f7i-commercial-tariff-registry-closure` |
| Starting HEAD | `6f6e7efa` (F7H publish baseline) |
| Final HEAD | branch tip after F7I commit (see `git rev-parse HEAD`) |
| Mini decision | Owner GO: close Catalog → template references → CPP → Snapshot V2 without inventing rates |
| Verdict | `BUILD_COMPLETE_WITH_OWNER_RATE_GAPS` |

## Mini decision (Owner)

Authorized structural closure of commercial ownership: Pricing Catalog owns values; Product Template holds references/applicability; CPP resolves published rates or fail-closed blockers; Snapshot V2 remains frozen. Forbidden: inventing tariffs, hourly client rates, FX, CPP↔EIC coupling, reprice accepted, materialization/scheduling/HR/Employee Mobile/SVG parsers, DB migration.

## Audit findings (Etapa A)

| Problemă | Adevăr actual | Owner corect | Impact | Acțiune în build |
| -------- | ------------- | ------------ | ------ | ---------------- |
| Registry `/pricing/registry` aggregates materials+WC | 50/50 typed; not sell authority | Catalog + commercial_rules_v2 | Misleading if treated as sole CPP source | Keep; clarify template references + commercial_rules ownership |
| Sell authority in `commercial_rules_volumetric_v2.py` | Documented EUR + unpublished gaps | commercial_rules catalog | Four Owner gaps fail-closed | Publication classification + template honesty |
| AI packaging demoted ambalare readiness | False commercial_ready | CPP / Owner rate | Hidden gap | Stop demotion; warn only |
| Template tab naming | Admin tab was opaque | Product Template UI | Operator confusion | Label `Prețuri template` + reference statuses |
| ACM treatment | shell 5/0; treatment blocked | Policy | Must not invent treatment sell | Preserve `ACM_TREATMENT_COMMERCIAL_BLOCKED` |
| STOP_DB_EXPANSION | No schema needed for F7I | — | Migration risk | No migration |

## Architecture chosen

```text
commercial_rules_volumetric_v2 (catalog owner values + publication honesty)
        ↓ classify_commercial_rule_publication / inventory
Product Template pricing recipe (references + readiness; editable=false)
        ↓
CPP (existing F7H fail-closed path; no invent)
        ↓
Quote Snapshot V2 (frozen; unchanged)
```

EIC / inventory `unit_cost` / `rate_per_hour` remain non-commercial.

## Commercial rules inventory (pilot VL)

Publication via `inventory_commercial_rules_for_template(TPL-VOLUMETRIC-LETTERS_v2)`:

- **ACTIVE_PUBLISHED** — Owner F7F EUR material/labor lines + ACM shell lines present in RULES_BY_TEMPLATE
- **ACTIVE_PROVISIONAL** — `debitare_fata` (1.5 EUR/ml), `modelare_cant_aluminiu` (5.0 EUR/ml) WC reuse (honest provisional)
- **ACTIVE_MISSING_RATE** — Owner gaps below (+ `montaj` until SITE_INSTALLATION_STANDARD binds in registry)
- **LEGACY_NOT_USED** — RON DEV_BRIDGE finish / forex sablon lines

## Rate gaps before / after

| Code | Before F7I | After F7I |
| ---- | ---------- | --------- |
| `ambalare` | unpublished fail-closed | same; explicit `ACTIVE_MISSING_RATE` on template + `COMMERCIAL_RATE_MISSING` |
| `debitare_spate` | unpublished fail-closed | same; template honesty |
| `sistem_led_module` | unpublished fail-closed | same; never LED_ASSEMBLY sell |
| `sursa_led` | unpublished fail-closed | same |
| Invented rates | none | none |

## Owner Rate Decision Pack

| Rule code | Modul/operație | Unitate | Monedă | Sursă actuală | Stare | Întrebare exactă |
| --------- | -------------- | ------- | ------ | ------------- | ----- | ---------------- |
| `debitare_spate` | Debitare spate litere | m² | EUR | unpublished catalog | MISSING_OWNER_RATE | Care este tariful comercial publicat pentru `debitare_spate`, în EUR/m2, fără TVA? |
| `sistem_led_module` | Sistem LED — module | buc | EUR | unpublished (not LED_ASSEMBLY) | MISSING_OWNER_RATE | Care este tariful comercial publicat pentru `sistem_led_module`, în EUR/buc, fără TVA? |
| `sursa_led` | Sursă LED (PSU) | buc | EUR | unpublished | MISSING_OWNER_RATE | Care este tariful comercial publicat pentru `sursa_led`, în EUR/buc, fără TVA? |
| `ambalare` | Ambalare | set | EUR | unpublished | MISSING_OWNER_RATE | Care este tariful comercial publicat pentru `ambalare`, în EUR/set, fără TVA? |

Note: `montaj` resolves from Pricing Registry `SITE_INSTALLATION_STANDARD` when present (template bind). Live DB may show missing until that registry row exists — not an invented rate.

## Files changed

- `backend/data/commercial_rules_volumetric_v2.py` — publication classifier + inventory
- `backend/schemas/template_pricing_recipe.py` — v1.3.0 reference status fields
- `backend/services/template_pricing_recipe_service.py` — wire honesty; no invent fill; AI pack warn-only; montaj registry bind
- `backend/tests/test_f7i_commercial_tariff_registry_closure.py` — new
- `frontend/src/api/templatePricingRecipe.ts` — types
- `frontend/src/features/product-system/ProductSystemTemplateDetailPanel.tsx` — tab label
- `frontend/src/features/product-system/TemplatePricingStudioPanel.tsx` — ownership UI
- `frontend/src/features/product-system/templatePricingCommercialReference.ts` (+ test)
- `frontend/scripts/ci-unit-tests.txt` — allowlist
- this worklog

## Tests

- Backend: `test_f7i_commercial_tariff_registry_closure.py`, `test_template_pricing_recipe.py`, `test_f7h_*`, `test_commercial_price_proposal_preview.py` — green targeted
- Frontend: `templatePricingCommercialReference.test.ts` — green; `pnpm run lint` — green

## Runtime

- `GET /api/v1/pricing/registry` — 50 items typed (material 33 / labor 9 / machine_operation 5 / service 3)
- `GET /api/v1/product-system/templates/TPL-VOLUMETRIC-LETTERS_v2/pricing` — 5 `ACTIVE_MISSING_RATE` (4 Owner gaps + montaj unbound); values null
- ACM recipe — shell 5/0, `treatment_commercial_lines_allowed=false`, blocker retained

## UI proof

| Element | Result |
| ------- | ------ |
| URL | `http://127.0.0.1:3000/product-system/products/TPL-VOLUMETRIC-LETTERS_v2?ps_legacy=1` |
| Tab | Administrare → **Prețuri template** |
| Visible | `Lipsă tarif Owner` / `Tarif lipsă`; value `—` (not 0) for ambalare, debitare_spate, LED, PSU |
| Catalog | `http://127.0.0.1:3000/inventory/pricing?template=TPL-VOLUMETRIC-LETTERS_v2` — Registru prețuri ownership zones |
| Light/day | Verified on staging dark shell (app default); no separate day theme required beyond existing toggle |

## Protected baselines (read-only)

| Order | accepted_commercial_total | snapshot sha256 prefix |
| ----- | ------------------------- | ---------------------- |
| 880811 | 1847.5 | `a59b6c44` |
| 973019 | 847.5 | `2d412e6e` |

No accept/convert/reprice/materialize executed.

## DB / schema / migration

- No reset, reseed, or migration
- `STOP_DB_EXPANSION` respected

## Forbidden scope confirmation

Materialization CLOSED · Scheduling HOLD · Employee Mobile FROZEN · no HR/utilaje commercial hourly · no SVG/DWG/DXF · no push/PR

## Commit

`feat(pricing): close commercial registry and template rate references` on `feat/f7i-commercial-tariff-registry-closure` (no push).

## What remains

1. Owner publishes the four EUR sell rates (Decision Pack)
2. Optional: ensure `SITE_INSTALLATION_STANDARD` present in live registry for montaj bind
3. Small activation/regression pass after Owner values
4. DISPLAY_RECONCILIATION 0.01 EUR polish remains non-blocking

## Exact next step

```text
The structural commercial pricing path is complete.
The remaining action is limited to Owner publication of the exact missing
commercial values listed in the Owner Rate Decision Pack.
No architectural redesign is required.
After those values are supplied, run one small dedicated activation and
regression pass.
Materialization remains CLOSED.
Scheduling remains HOLD.
```

## Direction score

**88/100** — structural path closed and honest; commercial tariff publication still Owner-gated for four codes.
