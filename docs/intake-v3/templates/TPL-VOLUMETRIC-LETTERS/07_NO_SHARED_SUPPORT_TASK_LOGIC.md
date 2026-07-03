# TPL-VOLUMETRIC-LETTERS — No Shared Support Task Logic (Index)

**Variantă:** litere volumetrice luminoase **fără suport comun pe spate**

---

## Document detaliat

Logica operațională completă este în:

**[TASK_LOGIC_NO_SHARED_SUPPORT.md](./TASK_LOGIC_NO_SHARED_SUPPORT.md)**

Acest fișier (`07_…`) este **index / summary** — nu înlocuiește documentul sursă.

---

## Rezumat reguli cheie

| Regulă | Valoare |
|--------|---------|
| Suport comun | absent (bare, ACM, casetă, structură) |
| Surse calculate | **în colet** la task final infoliere |
| Task cablare/surse pe suport | **nu** se generează |
| LED | montaj + cablare + test per literă pe Forex |
| Colantare cant | la banc, **înainte** de modelare (dacă cant colantat) |
| Colantare fețe | **după** asamblare; după vopsire cant dacă e cazul |
| Task final | infoliere stretch + pregătire colet livrare/montaj |

---

## Flux scurt (11 pași conceptuali)

1. Verificare grafică / vectorizare  
2. Confirmare model producție  
3. Pregătire fișiere CNC  
4. Pregătire traseu cant  
5. Debitare față + spate CNC  
6. Colantare cant la banc *(dacă colantat)*  
7. Modelare cant  
8. Lipire cant pe fețe  
9. Montaj LED + cablare + test  
10. Asamblare pe Forex  
11. Colantare fețe *(dacă în comandă)* / vopsire cant *(dacă vopsit)* → colet final  

Ordinea exactă = Operation Catalog cu `active_if`, nu listă fixă.

---

## Când să citești documentul detaliat

- checklist operator per task;
- ramificări cant colantat / necolantat / vopsit;
- task generation rules (`return_vinyl`, `face_vinyl`, `electrical_source_mounting`);
- opțiune `paint_recessed_screw_heads_to_return_color`.

---

## Suport comun

Pentru varianta **cu** suport comun → [08_SHARED_SUPPORT_PENDING_MODEL.md](./08_SHARED_SUPPORT_PENDING_MODEL.md)
