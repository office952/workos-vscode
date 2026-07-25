# Capac spate — Forex 10 mm display lock

**Date:** 2026-07-23  
**Status:** complete (display / structure association)

## Rule

Operator label: **Forex 10 mm**.  
Structure step: **Capac spate — Forex 10 mm**.  
Stable code: `MAT-SPATE-PVC-LITERE` (legacy PVC in code only).

Not these:
- Panou ACM / Dibond
- Șablon montaj Forex 3 mm (`MAT-SABLON-MONTAJ`)
- Face plexi (`MAT-ACP-FATA-LITERE`) — CNC badge stays on face + 4020 only

## Processes (chips, not BADGE-CNC-PROCESSABLE)

1. **Debitare CNC** — required (`back_cut`)
2. **Șanfren spate** — optional (owner default: without)

## Surfaces

| Surface | Mechanism |
|---|---|
| Product System structure | `LettersBackForexMaterialPanel` on Capac spate step |
| Pricing / Inventory | `normalizePricingDisplayName` + note |
| Seeds / canonical naming | `Forex 10 mm` |
| Material registry catalog | same canonical name |

## Also closed in this pass

Volum aluminiu process strip (Formare / Oracal before / RAL after) wired into width badges.
