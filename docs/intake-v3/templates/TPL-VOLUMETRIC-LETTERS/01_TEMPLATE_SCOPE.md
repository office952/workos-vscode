# TPL-VOLUMETRIC-LETTERS — Template Scope

---

## Ce acoperă

Litere volumetrice **luminoase**:

- față plexiglas (CNC, eventual colantare finală);
- cant aluminiu (modelat, lipit);
- spate Forex (LED, asamblare);
- iluminare interioară;
- finisaje variabile pe față și cant.

---

## Pilot de referință (HUB MEDIA PRODUCTION)

| Câmp | Valoare |
|------|---------|
| Dimensiuni | 9250 × 550 mm |
| Litere reale | 18 |
| Contururi CNC | 27 |
| Goluri interioare | 9 |
| Față | plexiglas |
| Cant | aluminiu 60 mm |
| Spate | Forex |
| LED | interior, front-lit |
| Suport comun | **nu** |

---

## Variante template trebuie să suporte

### Finisaj cant

| Variantă | Efect |
|----------|-------|
| Cant colantat (Oracal 651 / folie) | task colantare banc înainte de modelare |
| Cant necolantat | fără task colantare cant |
| Cant vopsit | vopsire după asamblare |

### Finisaj față

| Variantă | Efect |
|----------|-------|
| Față colantată (Oracal 8500 etc.) | task colantare finală fețe după asamblare |
| Față necolantată | fără task fețe |

### Montaj / suport

| Variantă | Efect |
|----------|-------|
| Fără suport comun | surse în colet; fără `electrical_source_mounting` |
| Cu suport comun | **pending** — [08_SHARED_SUPPORT_PENDING_MODEL.md](./08_SHARED_SUPPORT_PENDING_MODEL.md) |

### Electric

| Variantă | Efect |
|----------|-------|
| Fără suport comun | LED + cablare + test; surse calculate la colet |
| Cu suport comun | cablare/surse pe suport — pending |

---

## Ce nu acoperă (pilot)

- ACM casetat ca template separat;
- panouri plate non-volumetrice;
- montaj pe șantier (doar intent în intake, execuție separată).

---

## Legături

- Operation Catalog: [05_OPERATION_CATALOG.md](./05_OPERATION_CATALOG.md)
- Vector model: [02_VECTOR_AND_LETTER_MODEL.md](./02_VECTOR_AND_LETTER_MODEL.md)
