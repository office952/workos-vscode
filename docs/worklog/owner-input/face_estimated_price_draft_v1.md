# FACE Estimated Material and CNC Price Draft v1

> **Authority:** `OWNER_ESTIMATE_DRAFT` — not Pricing Registry, not active pricing, editable by owner.

**Date:** 2026-07-09
**HEAD:** `df49462` — Record FACE price registry alignment owner decision
**Owner:** Alex / P-Media
**3 mm alignment:** Previous draft **15 EUR/mp** superseded by `face_price_registry_alignment_owner_decision_v1.md`. Current readonly draft **16 EUR/mp** (MAT-ACP-FATA-LITERE registry authority). Still owner estimate / not active pricing.

---

## Material FACE — Plexiglas / acrylic

| Grosime | Pret estimativ | Unitate | Status |
|--------:|---------------:|---------|--------|
| 3 mm | 16 EUR | mp | owner_estimate_draft (aligned to MAT-ACP-FATA-LITERE) |
| 5 mm | 25 EUR | mp | owner_estimate_draft (optional) |
| 10 mm | 50 EUR | mp | owner_estimate_draft (optional) |

## Debitare CNC FACE — pe contur

| Grosime | Proces | Pret estimativ | Unitate |
|--------:|--------|---------------:|---------|
| 3 mm | CNC router | 1.00 EUR | ml contur |
| 5 mm | CNC router | 1.50 EUR | ml contur |
| 10 mm | CNC router | 2.50 EUR | ml contur |

## Minim CNC

| Regula | Valoare | Tip |
|--------|--------:|-----|
| Minim debitare CNC FACE / lucrare | 50 lei | owner commercial policy (NOT Pricing Registry) |

Setup simplu inclus în minim. Dacă debitarea calculată depășește minimul → ml contur.

## Reguli calcul

```
Material FACE = bounding/out-of-box per piece × pret material EUR/mp
Debitare CNC FACE = face_perimeter_length_m × pret CNC EUR/ml
Minim CNC = max(debitare calculata, 50 lei)
```

Nu arie vectorială exactă. Găuri = negative holes.

## Inventory cross-reference (readonly)

- `plexiglas_face` → `MAT-ACP-FATA-LITERE` (3 mm evidence in Intake V4)
- Registry rate may differ from draft — **no write**, **no activation**

## Forbidden

- No `/inventory/pricing` write
- No pricing activation
- No Product Truth live write
