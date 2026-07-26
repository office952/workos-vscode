# Build — Composer IA mock Litere↔Alucobond v1

| Field | Value |
|-------|-------|
| **Date** | 2026-07-23 |
| **Track** | Dual-track B |
| **Boundary** | PS UI mock only — no CostEngine / Offer / Execution / DB writes |

## Delivered

- Route: `/product-system/products/:templateCode/structure/composer-litere-acm`
- Page: `LettersAcmComposerIaMockPage.tsx`
- Entry from Structură (Letters + ACM) + link from foaia de prețuri
- Flow: root → compatibil v1 → attach → composit (spine + price sheet readonly)

## Out of scope

Live composite freeze · CostEngine · Offer lines
