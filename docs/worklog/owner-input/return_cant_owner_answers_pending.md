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
| 14 | Oracal catalog source | Sursă listă completă? Catalog intern / import / administrabil? | | partial | Mod listă completă confirmat (#1). Sursă + format + ownership lipsă. |

## K. Oracal price table

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 15 | Oracal price unit | Preț pe ml cant / mp folie / altă unitate? | | pending | Mod preț pe cod/familie confirmat (#2). Unitate neconfirmată. |
| 16 | Oracal price table | Valori preț pe cod/familie? | | pending | Fără tabel inventat. Monedă + unitate + dată efectivă lipsă. |

## L. RAL selector source/list

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 17 | RAL list source | RAL Classic / Design / Effect / altă listă? | | partial | Mod selector standard confirmat (#3). Sursă/listă efectivă lipsă. |
| 18 | RAL catalog shape | Cod simplu vs cod + nume culoare? | | pending | Doar structură propusă — fără listă inventată. |

## M. RAL material price by depth

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 19 | RAL material 30 mm | Preț material/ml la 30 mm? | | pending | Unitate ml confirmată (#9). |
| 20 | RAL material 60 mm | Preț material/ml la 60 mm? | | pending | Idem. |
| 21 | RAL material 80 mm | Preț material/ml la 80 mm? | | pending | Idem. |
| 22 | RAL material 100 mm | Preț material/ml la 100 mm? | | pending | Idem. |

## N. RAL labor price by depth

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 23 | RAL labor 30 mm | Preț manoperă/ml la 30 mm? | | pending | Unitate ml confirmată (#10). |
| 24 | RAL labor 60 mm | Preț manoperă/ml la 60 mm? | | pending | Idem. |
| 25 | RAL labor 80 mm | Preț manoperă/ml la 80 mm? | | pending | Idem. |
| 26 | RAL labor 100 mm | Preț manoperă/ml la 100 mm? | | pending | Idem. |

## O. RAL minimum rule

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 27 | RAL minimum | Există minim? Valoare? Material / manoperă / total? | | pending | Fără minim inventat. |

## P. Material-depth compatibility

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 28 | Compatibility | Aluminiu 0.6 mm valid pentru 30/60/80/100 mm? Excepții? | | pending | Material + adâncimi confirmate — combinații neconfirmate. |

---

## Confirmat deja (workshop — nu necesită răspuns în tabel)

- Variante finisaj: **Culoare Stock · Oracal · Vopsit RAL**
- Vopsit RAL: material + manoperă **separate** (model, fără prețuri)
- Calcul separat: component-owned truth pe path componentă
- Fără activare: no Product Truth write · no Pricing · no Work Intake

## Încă pending (catalog / prețuri — nu inventa)

| Item | Contract key | Status |
|------|--------------|--------|
| Catalog coduri Oracal efectiv | `oracal_code_list` | pending |
| Tabel prețuri Oracal pe cod/familie | (catalog pricing) | pending |
| Sursă/listă selector RAL standard | `ral_selector_source` | pending |
| Valori preț material Vopsit RAL | `ral_material_price_rule` (preț) | partial |
| Valori preț/minim manoperă Vopsit RAL | `ral_labor_price_rule`, `minimum_price_rule` | partial/pending |
| Compatibilitate material ↔ adâncime | `material_depth_compatibility` | pending |

## Ce NU se completează fără confirmare owner explicită

- Liste Oracal sau coduri
- Tabele / liste RAL
- Prețuri material sau manoperă
- Formule pricing
- Reguli compatibilitate material/adâncime

## Următorul pas

Task: **RETURN-CANT catalog and price data apply** — owner furnizează sursă catalog Oracal, tabel prețuri, sursă/listă RAL, valori preț RAL pe adâncime, minim, compatibilitate material/adâncime.

Contract workshop: `componentFirstReturnCantCatalogPriceInputs.ts`
