# Volum aluminiu — display lock (anti-confusion)

**Date:** 2026-07-23  
**Status:** complete after interrupt recovery

## Rule

Operator label everywhere: **Volum aluminiu XX mm** (30/60/80/100).  
Selector: **Volum aluminiu — alege lățimea (30/60/80/100)** (`MAT-PROFIL-LATERAL-LITERE`).

Not these (different materials):
- ACM / Dibond panels
- Premount aluminum tube (`MAT-PREMOUNT-BAR-ALUMINUM`)
- Caseta profile (`MAT-PROFIL-ALU-BOX`)

## Surfaces

| Surface | Mechanism |
|---|---|
| Product System structure | chips on Volum aluminiu step |
| Pricing | `normalizePricingDisplayName` + note |
| Inventory | same display helper + note |
| Seeds / canonical naming | `Volum aluminiu *` |
| Material registry subcategory | `Volum aluminiu (litere)` |

Codes `MAT-PROFIL-LATERAL-LITERE-*` stay stable.
