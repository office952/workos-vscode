# Wave 2 — TECHNICAL_MODEL_LEAK_TO_UI

Classify only. Bevel lesson: commercial grain ≠ execution grain.

| # | route | element | internal truth | user need | severity | disposition |
|---|-------|---------|----------------|-----------|----------|-------------|
| 1 | `/intake` | FLUX Cereri→**Produse**→Oferte | Product System catalog | Next request to open | HIGH | SIMPLIFY / MOVE Produse out of this strip |
| 2 | `/intake` | `IR-*` as primary label + `NORMAL` + `email` | request id / enum / channel | client + what to do | MED | SIMPLIFY |
| 3 | V6 | URL `IR-MSRB28PU` vs header `IV6-F823AA06` | two identity schemes | one work identity | HIGH | MERGE identity display |
| 4 | V6 Configurare | “Element 1”, Față/Cant/Spate as cards | component/layer model | finish confirmation | MED | KEEP with plainer labels |
| 5 | V6 | “25 linii” / “7 linii” | CPP line count | whether offer is ready | MED | HIDE_BY_ROLE or disclosure |
| 6 | V6 | “Detalii tehnice despre finisaj — mapări interne” | mappings | operator confirm | LOW | ADMIN_ONLY / disclosure |
| 7 | `/orders` | `ORD-IV6-V2-…` + Înghețat | snapshot/lock codes | which job / paid? | MED | RENAME |
| 8 | `/orders` | dual FLUX (commercial + execution) | two system spines | one next step | HIGH | SIMPLIFY |
| 9 | `/orders` | Vezi produse | Product System | not needed to understand an accepted order | MED | HIDE_BY_ROLE |
| 10 | `/clients` | “1 în registrul entități” vs 19 cards | two client stores | who is a real client | HIGH | MERGE / clarify |
| 11 | `/quotes` observe | client as text | no entity link | open client | MED | MOVE add link (later GO) |
| 12 | V6 / quotes | EUR vs orders/clients RON | two money projections | one commercial number | HIGH | see contradictions |

Count for report: **12** leaks logged (not 12 unique root causes).
