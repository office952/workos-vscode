# Sistem LED — display lock

**Date:** 2026-07-23  
**Status:** complete (display / structure association)

## Rule

Structure step: **Sistem LED — montaj pe spate Forex**.

| Role | Display | Code | Evidence |
|---|---|---|---|
| Standard | Modul LED 12V | `MAT-LED-MODULE` | 0.5 EUR/buc |
| Alternative | Bandă LED 12V | `MAT-LED-STRIP` | 2.0 EUR/ml |
| PSU selector | Sursă LED 12V — alege puterea (60/100/160/200 W) | `MAT-LED-PSU-12V` | no single price |
| PSU variants | Sursă LED 12V {W}W | `MAT-LED-PSU-12V-{60\|100\|160\|200}W` | 12 / 16 / 20 / 40 EUR/buc |

## Processes (chips)

1. Montaj module pe spate  
2. Alegere sursă (W)  
3. Cabluri / colet (no shared support → surse în colet)

## Anti-confusion

- Do **not** multiply PSU price by watt value  
- Bandă LED is alternative, not letters standard  
- Codes stay stable

## Surfaces

| Surface | Mechanism |
|---|---|
| Product System structure | `LettersLedSystemPanel` on Sistem LED step |
| Pricing / Inventory | `normalizePricingDisplayName` + notes |
| Seeds / canonical naming | same display strings |
| Material Registry | subcategories Module LED / Surse LED 12V |
