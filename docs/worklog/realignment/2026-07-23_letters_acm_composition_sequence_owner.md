# Letters↔ACM composition sequence — owner lock (2026-07-23)

**Status:** OWNER_CONFIRMED → folded into **`LETTERS_ACM_COMPATIBILITY_CONTRACT_V1_ACCEPTED`** (2026-07-23)  
**Boundary:** docs + Product System teaching SoT. Not CostEngine wiring. Not Composer UI.

## Sequence

```text
A. Alucobond casetat final (taskuri ACM 1–9) — FĂRĂ pack
B. Proces șablon pe bond
C. Forex + electrică pe bond
D. Corp plexi+volum pe Forex
E. Pack ansamblu
```

| # | Pas |
|---|-----|
| A | ArtCAM → V-groove → debitare → pliere → cadru → prindere → colant XOR vopsire șuruburi → accesorii montaj |
| B | Șablon: material + cutter/plotter + transfer + aplicare (**un proces comercial**) |
| C1 | Prindere Forex pe bond (autoforante); LED+jumpers deja pe Forex |
| C2 | Electrică în carcasa bond + legare transformator |
| C3 | Cablu 5 m 220V |
| C4 | Test lumină |
| D | Corp pe Forex — autoforante fine vopsite la cant/volum |
| E | Impachetare ansamblu |

## Șablon commercial (LOCKED)

| Câmp | Valoare |
|------|---------|
| Proces | Bundle: material + cutter/plotter + transfer + aplicare |
| Tarif | **20 EUR / mp** |
| Baza mp | **Outbox al literelor volumetrice ca layer integral** — nu sumă piesă cu piesă |
| Reguli | Nu orar; nu linii separate material/cutter/transfer/aplicare |

Code SoT:

- `frontend/src/features/product-system/lettersAcmCompositionSablonProcess.ts`
- `frontend/src/features/product-system/lettersAcmCompositionTaskOrder.ts`

## Connection price sheet (complete — owner verified coherent)

SoT UI: `structure/conexiune-litere-acm-preturi` · code `lettersAcmCompositionConnectionPrices.ts`

| Linie | Tarif | Decizie |
|-------|-------|---------|
| Șablon process | 20 EUR/mp | OWNER_LOCKED |
| Prindere Forex pe bond | 8 EUR/mp | OWNER_VERIFIED_COHERENT |
| Electrică + traf în carcasă | 35 EUR/buc | OWNER_VERIFIED_COHERENT |
| Cablu 5 m 220V + atasare | 6 EUR/buc | OWNER_VERIFIED_COHERENT |
| Test lumină | 8 EUR/buc | OWNER_VERIFIED_COHERENT |
| Prindere corp pe Forex | 12 EUR/mp | OWNER_VERIFIED_COHERENT |
| Pack ansamblu | 10 EUR/mp (min 15) | OWNER_VERIFIED_COHERENT |

## Intake gap (wiring only)

| Linie | Intake / CostEngine azi | Gap |
|-------|-------------------------|-----|
| Toate liniile de mai sus | `sablon_montaj` split; restul fără linii composition | **Wiring GO** |

**Next GO (separate):** wire CostEngine/Intake; Finish Contract ACM finishes.

## Artefacts

- Decision amend: `decision__letters_acm_compatibility_composer_direction_v1.md` §4.2 / §8 Q1 / §9
- MIXED §13
- Contract: `docs/architecture/product-system/LETTERS_ACM_COMPATIBILITY_CONTRACT_V1.md`
