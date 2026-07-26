# RETURN-CANT Owner Answers

> **Notă:** Acest document este pentru workshop.  
> **Nu** este sursă runtime. **Nu** activează pricing. **Nu** scrie Product Truth live.

Completarea coloanei **Owner answer** este singura cale prin care valorile pot trece în contractul readonly la task-ul de apply.

## Status legend

| Status | Meaning |
|--------|---------|
| `pending` | Fără răspuns owner — nu se aplică în contract |
| `answered` | Răspuns complet — eligibil pentru apply readonly |
| `partial` | Răspuns incomplet — rămâne OWNER INPUT REQUIRED pentru părțile lipsă |
| `blocked` | Necesită decizie owner înainte de orice apply |

---

## A. Oracal

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 1 | Oracal selector | Selector cu listă coduri uzuale + „alt cod”? Listă completă? Text liber? | **B — listă completă** | answered | Mod selector confirmat. Catalog efectiv (`oracal_code_list`) încă pending. No pricing activation. |
| 2 | Oracal pricing | Preț unic sau preț pe cod/familie? | **B — preț pe cod/familie** | answered | Mod confirmat. Tabel prețuri pe cod/familie încă pending. |

## B. RAL

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 3 | RAL mode | Text liber? Selector standard? Selector + text liber? | **B — selector standard** | answered | Mod confirmat. Sursă/listă RAL efectivă încă pending. |

## C. Adâncimi cant

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 4 | Depths | 30 mm? 60 mm? 80 mm? 100 mm? altele? | **30 / 60 / 80 / 100 mm** | answered | Adâncimi standard confirmate. |

## D. Material cant

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 5 | Material | Aluminiu? PVC? plexiglas/acryl? alt material? | **Aluminiu 0.6 mm** | answered | Material + grosime confirmate. |
| 6 | Material vs depth | Același material pentru 30/60 mm sau diferit? | **Același material (aluminiu 0.6 mm)** | answered | Inclus în răspunsul material. |

## E. Unități calcul

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 7 | Material unit | Material pe ml / mp / buc / set? Perimetru cant ca bază? | **ml** | answered | Perimetru/contur confirmat separat (#12). |
| 8 | Labor unit | Manoperă pe ml / mp / buc / set? | **ml** | answered | Manoperă pe ml confirmată. |

## F. RAL material

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 9 | RAL material price | Preț material 30 / 60 / 80 mm? Unitate? | **Unitate ml confirmată — preț neconfirmat** | partial | Unitate aplicată. Valori preț rămân OWNER INPUT REQUIRED. |

## G. RAL manoperă

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 10 | RAL labor | Pe ml? set? piesă/literă? mp? minim + ml? Preț minim? | **Unitate ml confirmată — preț/minim neconfirmat** | partial | Unitate aplicată. Preț și minim rămân OWNER INPUT REQUIRED. |

## H. Culoare Stock

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 11 | Stock pricing | Culoarea tastată influențează prețul sau doar info atelier? | **NU — doar informație atelier** | answered | Clarificare owner: punctul 10 din lista task. |

## I. Perimetru / geometrie

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 12 | Perimeter source | Perimetrul literelor? bounding/nesting/contur? Path Product Truth? | **DA — perimetru/contur real al literelor** | answered | Cerință ProductDefinition înregistrată. Algoritm ne modificat. |
| 13 | Compatibility | Combinații valide material ↔ adâncime? | | pending | Contract key: `material_depth_compatibility` |

---

## J. Oracal catalog source

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 14 | Oracal catalog source | Sursă listă completă? Catalog intern / import / administrabil? | **Intake V6 colorRegistry — oracal651.ts + oracal8500.ts (641 reutilizează paleta 651)** | answered | Cross-ref readonly — fără catalog duplicat în Product System |
| 15 | Oracal calculation | Model consum Oracal? | **lățime rolă × lungime folosită = mp** | answered | Nu se calculează simplu pe ml |
| 16 | Oracal roll widths | Lățimi rolă? | **100 cm · 126 cm** | answered | Confirmat owner |

## K. Oracal price table

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 17 | Oracal price unit | Preț pe ml cant / mp folie / altă unitate? | **mp (din lățime rolă × lungime)** | answered | Confirmat via calculation model |
| 18 | Oracal series prices | Prețuri pe serie 651 / 641 / 8500? | **Pricing Registry: MAT-ORACAL-641 · MAT-ORACAL-651 · MAT-ORACAL-8500 — edit in /inventory/pricing** (supersedes prior chat literals 8/5/13) | answered | Owner confirmat — fără activare pricing; Product System keys only |
| 19 | Oracal price table complete | Valori preț pe toate codurile/seriile? | **Serii 651/641/8500 confirmate — restul pending** | partial | Fără valori inventate în afara celor confirmate |

## L. RAL selector source/list

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 20 | RAL list source | RAL Classic / Design / Effect / altă listă? | **Intake V6 ralColors.ts — RAL Classic (213 culori)** | answered | Cross-ref readonly colorRegistry/ralColors.ts |
| 21 | RAL catalog shape | Cod simplu vs cod + nume culoare? | **RAL Classic structurat în color registry Intake V6** | answered | Fără coduri RAL inventate |

## M. RAL material price by depth

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 21 | RAL material 30 mm | Preț material/ml la 30 mm? | **2.00 EUR/ml (MAT-VOPSEA-RAL-CANT-30MM)** | answered | Owner confirmat |
| 22 | RAL material 60 mm | Preț material/ml la 60 mm? | **2.50 EUR/ml (MAT-VOPSEA-RAL-CANT-60MM)** | answered | Owner confirmat |
| 23 | RAL material 80 mm | Preț material/ml la 80 mm? | **3.00 EUR/ml (MAT-VOPSEA-RAL-CANT-80MM)** | answered | Owner confirmat |
| 24 | RAL material 100 mm | Preț material/ml la 100 mm? | **4.00 EUR/ml (MAT-VOPSEA-RAL-CANT-100MM)** | answered | Owner confirmat |

## N. RAL labor price by depth

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 25 | RAL labor all depths | Preț manoperă/ml? | **1.00 EUR/ml — același preț toate adâncimile** | answered | Owner confirmat |

## O. RAL minimum rule

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 27 | RAL minimum | Există minim? Valoare? Scope? Material / manoperă / total? | **100 lei, pe culoare RAL, aplicat la total material + manoperă** | answered | Fără conversie automată lei→EUR · fără activare pricing · fără formulă runtime |

---

## P. Material-depth compatibility

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 28 | Compatibility | Aluminiu 0.6 mm valid pentru 30/60/80/100 mm? Excepții? | **DA — valid pentru toate** | answered | Owner confirmat |

---

## Confirmat deja (workshop — nu necesită răspuns în tabel)

- Variante finisaj: **Culoare Stock · Oracal · Vopsit RAL**
- Vopsit RAL: material + manoperă **separate** (model, fără prețuri)
- Calcul separat: component-owned truth pe path componentă
- Fără activare: no Product Truth write · no Pricing · no Work Intake

## Încă pending (catalog / prețuri — nu inventa)

| Item | Contract key | Status |
|------|--------------|--------|
| Tabel prețuri Oracal complet (coduri/serii în afara 651/641/8500) | `oracal_price_table` | partial |
| Formă catalog Oracal stocat separat în Product System | `oracal_catalog_shape` | pending |
| Extragere modul catalog shared stabil | cross-ref only | pending |
| Pricing activation | — | blocked |
| Product Truth live write | — | blocked |

## Ce NU se completează fără confirmare owner explicită

- Coduri Oracal individuale inventate
- Valori tabel Oracal inventate
- Coduri RAL inventate în product system catalog
- Conversie automată lei→EUR
- Formule pricing runtime

## Următorul pas

Task: **RETURN-CANT Oracal remaining series/code prices apply** — owner furnizează prețuri pe cod/familie în afara seriilor 651/641/8500, dacă e nevoie.
