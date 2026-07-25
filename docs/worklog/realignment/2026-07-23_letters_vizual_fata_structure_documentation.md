# Vizual față — document explicativ + direcțional (Product System)

**Date:** 2026-07-23  
**Status:** ACTIVE (operator documentation on structure detail page)  
**Route:** `/product-system/products/:templateCode/structure/vizual-fata`  
**FE model:** `frontend/src/features/product-system/lettersFaceStructureDocumentation.ts`

---

## Rol

Pasul **1 / 5** din Structură produs (Litere volumetrice): substratul vizibil al literei — material + prelucrare CNC + finisaj față după asamblare.

Conturul feței autorizează lungimea de cant (Volum aluminiu). Nu este panou ACM, nu este spate Forex, nu este pasul Finisaj (asamblare/QC).

---

## Material standard

| Câmp | Valoare |
|------|---------|
| Display | `plexiglas 3mm PMMA - opal` |
| Cod | `MAT-ACP-FATA-LITERE` (legacy ACP în cod — nu ACM) |
| Familie permisă | plexiglas / acrylic |
| Grosime standard | 3 mm opal |
| Opțional (owner) | 5 mm / 10 mm — confirmare înainte de pricing |
| Nu FACE standard | Forex, ACM / Bond / Dibond |
| Nesting | bounding / out-of-box pe piesă |

---

## Prelucrare CNC

| Câmp | Valoare |
|------|---------|
| Badge UI | `CNC` |
| Cod capacitate | `BADGE-CNC-PROCESSABLE` |
| Material carrier | `MAT-ACP-FATA-LITERE` |
| Utilaj carrier | `MCH-CNC-4020` (CNC 4020) |
| Proces 1 | Debitare (obligatoriu pe calea standard) |
| Proces 2 | Șanfren / Canal (pentru lipire volum–față) |

Finisajele Oracal / print **nu** sunt procese CNC pe plexi.

---

## Cum calculăm (carduri primare pe pagină)

### Consum material

```
consum mp = sumă (bounding / out-of-box pe piesă)
cost = consum mp × preț registry (€/mp)   ← verifică în Pricing
```

- Nu arie vectorială exactă; găuri = negative holes  
- Ieșiri: `face_piece_boxes`, `face_material_usage_area_m2`, `mp_face_area` (finisaj)

### Debitare CNC

```
debitare = face_perimeter_length_m × tarif CNC (€/ml contur)
```

- Contur real — nu aria bounding box  
- Același perimetru alimentează și Volum aluminiu (cant)  
- Model intern pe treceri (pass) ≠ tarif comercial pe contur  
- Tariful: Pricing / politică owner — link pe card, fără EUR hardcodat în PS

---

## Finisaj față (după asamblare)

Identitate = etichetă + `MAT-*`. Fără `BADGE-FACE-*`.

| Label | Cod | Preț |
|-------|-----|------|
| Oracal 8500 | `MAT-ORACAL-8500` | Verifică în `/inventory/pricing?code=…` |
| Oracal 641 | `MAT-ORACAL-641` | idem |
| Oracal 651 | `MAT-ORACAL-651` | idem |
| Printat / Laminat | `MAT-VINYL-PRINT-LAMINATED` | idem |

Substrat față: `/inventory/pricing?code=MAT-ACP-FATA-LITERE`.

Manoperă comună: Aplicare față · Decupare contur.

**Nu duplicăm EUR/mp în Product System** — link UI: «Verifică preț material».

Vizual față **nu** deține vopsirea cantului, RAL minim sau prețuri comerciale.

---

## Ce nu este aici

- Panou ACM / Dibond (alt template + contract ulterior)
- Capac spate Forex 10 mm
- Finisaj produs (pasul 5 — asamblare / QC)
- Redenumire coduri CostEngine / activare ofertă / Execution
- Scriere Product Truth fără confirmare operator

---

## Direcție în sistem

1. **Structură produs** = hartă scurtă 1→5  
2. **Pagina componentei** = documentul explicativ (acest tip de pagină)  
3. Pattern de repetat: Volum aluminiu → Capac spate → Sistem LED → Finisaj  
4. **Litere UI** se închide înainte de contract ACM / Composer  
5. Finish line laborator = **EIC / cost producție**

---

## Surse (owner / lock)

- `docs/worklog/owner-input/face_component_truth_owner_decision_v1.md`
- `docs/worklog/realignment/2026-07-23_letters_face_plexi_display_name_lock.md`
- `docs/worklog/realignment/2026-07-23_cnc_processable_badge_identifier.md`
- `docs/worklog/realignment/2026-07-23_letters_face_finish_meaning.md`
- `docs/worklog/realignment/decision__letters_acm_compatibility_composer_direction_v1.md`
