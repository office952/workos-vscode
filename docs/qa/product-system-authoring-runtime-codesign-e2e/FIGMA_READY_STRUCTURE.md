# Figma structure — Product System authoring (FINAL CLOSURE)

| Field | Value |
|-------|--------|
| File | `0CDPIuqoaZ1OQgNnvNyl1F` |
| Date | 2026-07-20 |
| Write access | **YES** (Full seat) — frames created with real IDs |
| Rule | Do not invent IDs. Owner promotes PROPOSED → FINAL. |

## Existing Intake frames (verified)

| Frame | Node ID | Role |
|-------|---------|------|
| FINAL — Confirmare 1440×900 | `66:2` | Operator confirm |
| Configurare | `64:2` | Config / Finisaje |
| Iluminare | `65:2` | Lighting |
| Montaj | `65:106` | Mounting |
| PinFooter | `67:18` | Sticky footer pattern |

## Page: PS — Authoring Studio (`91:2`)

| Frame | Node ID | Status | Runtime mapping |
|-------|---------|--------|-----------------|
| PS Template Authoring Shell | `91:3` | PROPOSED | `/product-system/products/:code` |
| Component Contract + Used-by | `91:12` | PROPOSED | `ComponentContractUsedByPanel` |
| Blueprint Dossier Studio split | `91:21` | PROPOSED | `/product-system/blueprint-dossier` |
| Publication states | `91:36` | PROPOSED | `ProductTemplatePublicationPanel` |
| Readiness PASS / BLOCKED | `91:60` | PROPOSED | `ProductE2EReadinessPanel` |
| 01 Product System Landing | `91:76` | PROPOSED shell | `/product-system/products` |
| 02 Product Template Overview | `91:79` | PROPOSED shell | template overview |
| 03 Composition / Components | `91:82` | PROPOSED shell | composition tab |
| 06 Validation Rail | `91:85` | PROPOSED shell | dossier rail |
| 07 E2E Readiness Collapsed | `91:88` | PROPOSED shell | readiness collapsed |
| 08 E2E Readiness Expanded | `91:91` | PROPOSED shell | readiness expanded |
| 10 Publication Ready | `91:94` | PROPOSED shell | only when truly publishable |
| 11 Version Status | `91:97` | PROPOSED shell | publication_version |
| 12 Runtime Preview | `91:100` | PROPOSED shell | runtime preview tab |

Screenshots: `screenshots/figma_*.png`.

## Honesty

- `active ≠ published`
- aluminiu inactive → TEMPLATE PUBLICATION BLOCKED (never fake PASS)
- BUILD closure may PASS_WITH_WARNINGS while template publication stays BLOCKED
