# RETURN-CANT Owner Answers

> **Notă:** Acest document este pentru workshop.  
> **Nu** este sursă runtime. **Nu** activează pricing. **Nu** scrie Product Truth live.

Completarea coloanei **Owner answer** este singura cale prin care valorile pot trece în contractul readonly la următorul task de apply.

## Status legend

| Status | Meaning |
|--------|---------|
| `pending` | Fără răspuns owner — nu se aplică în contract |
| `answered` | Răspuns complet — eligibil pentru apply readonly |
| `partial` | Răspuns incomplet — rămâne OWNER INPUT REQUIRED |
| `blocked` | Necesită decizie owner înainte de orice apply |

---

## A. Oracal

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 1 | Oracal selector | Selector cu listă coduri uzuale + „alt cod”? Listă completă? Text liber? | | pending | Contract keys: `oracal_code_list` |
| 2 | Oracal pricing | Preț unic sau preț pe cod/familie? | | pending | Contract key: `oracal_pricing_mode` |

## B. RAL

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 3 | RAL mode | Text liber? Selector standard? Selector + text liber? | | pending | Contract key: `ral_input_mode` |

## C. Adâncimi cant

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 4 | Depths | 30 mm? 60 mm? 80 mm? 100 mm? altele? | | pending | Contract key: `return_depths_standard` |

## D. Material cant

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 5 | Material | Aluminiu? PVC? plexiglas/acryl? alt material? | | pending | Contract key: `return_material` |
| 6 | Material vs depth | Același material pentru 30/60 mm sau diferit? | | pending | Poate fi parte din răspunsul material |

## E. Unități calcul

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 7 | Material unit | Material pe ml / mp / buc / set? Perimetru cant ca bază? | | pending | Contract key: `return_material_unit` |
| 8 | Labor unit | Manoperă pe ml / mp / buc / set? | | pending | Contract key: `return_labor_unit` |

## F. RAL material

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 9 | RAL material price | Preț material 30 / 60 / 80 mm? Unitate? | | pending | Contract key: `ral_material_price_rule` |

## G. RAL manoperă

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 10 | RAL labor | Pe ml? set? piesă/literă? mp? minim + ml? Preț minim? | | pending | Contract keys: `ral_labor_price_rule`, `minimum_price_rule` |

## H. Culoare Stock

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 11 | Stock pricing | Culoarea tastată influențează prețul sau doar info atelier? | | pending | Contract key: `stock_color_affects_price` |

## I. Perimetru / geometrie

| Priority | Topic | Question | Owner answer | Status | Notes |
|----------|-------|----------|--------------|--------|-------|
| 12 | Perimeter source | Perimetrul literelor? bounding/nesting/contur? Path Product Truth? | | pending | Contract key: `perimeter_geometry_source` |
| 13 | Compatibility | Combinații valide material ↔ adâncime? | | pending | Contract key: `material_depth_compatibility` |

---

## Confirmat deja (workshop — nu necesită răspuns în tabel)

Aceste reguli sunt deja în contract readonly; **nu** completa prețuri sau liste aici:

- Variante finisaj: **Culoare Stock · Oracal · Vopsit RAL**
- Culoare Stock: operator tastează pentru atelier (mod confirmat; impact preț = întrebarea #11)
- Vopsit RAL: material + manoperă **separate** (model, fără prețuri)
- Calcul separat: component-owned truth pe path componentă
- Fără activare: no Product Truth write · no Pricing · no Work Intake

## Ce NU se completează fără confirmare owner explicită

- Liste Oracal sau coduri
- Tabele / liste RAL
- Prețuri material sau manoperă
- Formule pricing
- Adâncimi sau materiale default
- Unități de calcul presupuse

## Următorul pas (apply)

1. Owner completează coloana **Owner answer** pentru rândurile `pending`.
2. Marchează **Status** = `answered` sau `partial`.
3. Task următor: **RETURN-CANT owner answers apply** — doar rândurile `answered` devin `owner_confirmed` în contract; restul rămân OWNER INPUT REQUIRED.
