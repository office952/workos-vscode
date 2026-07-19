# Pricing Trace — Montaj-related

## Runtime ACM dry-run (`acm_priced_quote_dry_run.json`)

Commercial line items observed (7): debitare_fata, modelare_cant_aluminiu, debitare_spate, sistem_led_module, sursa_led, finisaje_colantare_vopsire, ambalare.

- **No** `montaj` site line (`mounting_scope=none` → expected).
- **sablon_montaj_***: string present in payload (`sablon: true` in summarizer) but **not** an applicable commercial line with totals under prep-inactive gate (`_sablon_enabled` requires preparation active).
- **Accesorii montaj**: **not** present in dry-run commercial_line_items / internal_cost_trace keys walked — yet **UI shows** `Tarife lipsă — Accesorii montaj / conectori`.

## Accesorii montaj / conectori — exact source

| Question | Finding |
|----------|---------|
| Exact source | `backend/services/intake_v4_material_breakdown_service.py` `_build_mounting_accessories_percent_row` — `mounting_accessories_percent`, 5% of manufacturing subtotal, `price_source=cost_formula_mounting_accessories_5pct` |
| Logical list | `gradi_logical_list_read_model_service.py` line `material.mounting_accessories`, formula `MATERIAL_MOUNTING_ACCESSORIES_BY_COST_PERCENT_V1`, gap `COMMERCIAL_FORMULA_UNVERSIONED` |
| UI banner | `IntakeV6LiveCalculationSummary.tsx` missing-rates banner when live calc / logical rows mark missing |
| Why missing | Formula is unversioned commercial; registry_code null; live calc can flag missing prices / diagnostic rows even when dry-run commercial lines omit the row |
| Should it block? | Soft commercial warning in operator rail — **not** the same as Confirmare composition blockers; does **not** require Montaj scope |
| Generic or scenario-specific? | **Generic** whenever manufacturing subtotal > 0 |
| Appear when irrelevant? | **Yes** — appears with `mounting_scope=none` (runtime screenshot/probe) |
| Belongs to Montaj or production consumables? | **Production/commercial consumable estimate**, not an operator Montaj decision field |

## Other Montaj pricing lines

| Line | Source field | Formula/unit | When | Operator visible |
|------|--------------|--------------|------|------------------|
| sablon_montaj_forex/hartie | template enable+material+area + prep scope | CPP rules | prep-active | via commercial proposal |
| montaj (site) | site scope / installation_template | CPP `montaj` | site required | commercial |
| ACM boxed lines | ACM solution config | `acm_*` rules | ACM payload | commercial |
| Cable | mains_cable_length_m | wire consumable | illuminated/process | materials |
| Segmented / electrical | segmented_* | **pricing: False** | confirmed still unpriced | should not price |
| Premount metal | metal solution | module gates | selected | commercial/module |
| Accesorii 5% | manufacturing subtotal | percent job | always (subtotal>0) | Tarife lipsă banner |

## Investigation verdict

`Tarife lipsă — Accesorii montaj / conectori` is a **pricing-rail consumable warning**, not proof that commercial Montaj scope is incomplete. Naming couples it to Montaj psychologically while code couples it to manufacturing cost percent.
