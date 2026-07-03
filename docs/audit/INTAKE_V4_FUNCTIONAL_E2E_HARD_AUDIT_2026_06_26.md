# Intake V4 Operator - Functional E2E Hard Audit

Data: 2026-06-26  
Workspace: `9fe22974-1f65-4bce-847d-02d74bb16e05` / `IV4-4C8EA27B`  
Fisier verificat: `gradi-curat.svg`  
Template: `TPL-VOLUMETRIC-LETTERS`

## Verdict

Fluxul este utilizabil si baza vectoriala este corecta, dar nu este inca "adevar unic" end-to-end. Exista diferente functionale intre totalul live, randurile detaliate, statusul de tarife lipsa si contractul ProductSystem.

## Findings

### P1 - Detaliile din Calcul live nu insumeaza totalul afisat

Backend live returneaza `estimated_cost_total = 713.68 EUR`, iar dupa reload UI afiseaza acelasi total. Totusi suma randurilor vizibile din lista live este `675.94 EUR`.

Diferenta vine din doua cauze:

- `CNC spate Forex` include in UI doar `cnc_backing_cutting_forex_10mm = 184.87 EUR`; randul backend `cnc_backing_bevel_forex_10mm = 36.97 EUR` intra in total, dar nu apare in lista live.
- Consumabilele afiseaza cost recalculat din `unit_price` rotunjit, nu `estimated_cost` backend:
  - Adeziv cant: UI `5.35 EUR`, backend `6.29 EUR`
  - Adeziv LED: UI `2.90 EUR`, backend `3.41 EUR`
  - Cablu 2x0.75: UI `7.60 EUR`, backend `7.08 EUR`
  - Cablu 2x1.5: UI `4.00 EUR`, backend `3.82 EUR`

Cod relevant:

- `frontend/src/lib/intakeV4/intakeV4LiveMaterialsUsedDisplay.ts:35` recalculare cost din `unit_price * pricedQuantity`.
- `frontend/src/lib/intakeV4/intakeV4LiveMaterialsUsedDisplay.ts:333` include doar `cnc_backing_cutting_forex_10mm`, nu si bevel spate.

### P1 - Operatiile de cant au tarif lipsa, dar totalul nu marcheaza lipsa de pret

Backend marcheaza doua operatii cu `missing_rate`:

- `edge_cant_oracal_wrap` / Aplicare Oracal 651 pe cant: `32.0967 m`, tarif lipsa.
- `edge_cant_bond_to_face` / Lipire cant pe fata litere: `26.7472 m`, tarif lipsa.

UI le afiseaza corect ca `tarif lipsa`, dar `material_breakdown.totals.contains_missing_prices` este `false`, iar totalul intern pare final. Asta este periculos pentru ofertare: o operatie reala de finisaj exista, dar nu afecteaza statusul totalului.

Cod relevant:

- `backend/services/intake_v4_material_breakdown_service.py:2097` verifica missing prices doar in `material_rows`, `consumable_rows` si `operation_rows`.
- `edge_cant_operation_rows` sunt returnate separat, dar nu intra in missing-price gate si nici in total.

### P1 - ProductSystem nu este inca autoritatea completa pentru formular

Contractul de template este `partial`, nu canonical. Warnings live:

- `oracal_8500` este descoperit in formular, dar contractul il mapeaza partial catre `oracal_651`, nefiind allowed value canonic in dossier.
- `ral_paint` cere `paint_tube_count` in `quote_input`, dar Intake V4 nu il auto-completeaza.

Asta inseamna ca formularul inca dicteaza o parte din adevar, iar ProductSystem nu domina complet variantele.

### P2 - Plexiglasul este impartit corect in UI, dar backend row-ul ramane semantic gresit

Backend are un singur rand `plexiglas_face` cu label `Plexiglas 3 mm / fata litere`, cantitate `2.5238 m2`. UI il imparte in:

- `Plexiglas 3 mm / fata litere`: `1.545 m2`, `24.72 EUR`
- `Plexiglas 3 mm / embleme/logo`: `0.979 m2`, `15.66 EUR`

Impartirea UI este utila, dar adevarul backend nu este separat pe litere/embleme. Pentru productie si audit ar trebui fie randuri backend separate, fie label backend neutru si campuri de alocare explicite.

### P2 - Confirm are o fereastra de incarcare in care poate afisa geometria incompleta

Stabil, dupa incarcare API, Confirm afiseaza corect:

- Perimetru total vectorial: `31.638 m`
- Perimetru cant total: `31.64 m`
- Cant pentru pret: `37.97 m` cu `+20%`

Inainte ca `material_breakdown` sa fie incarcat, Confirm poate afisa temporar `29.54 m` din geometria persistata. Nu e valoarea finala, dar poate induce operatorul in eroare daca citeste ecranul in loading.

## Confirmari Corecte

- Vector/layers: 6 layere confirmate, 4 litere volumetrice + 2 artwork/logo.
- Dimensiune: `5087 x 600 mm`.
- Perimetru total vectorial: `31.638 m`, aliniat cu referinta Corel.
- Roll width Oracal: `1000 mm` pentru 651/8500.
- Oracal fata este separat pe serii: `651` si `8500`.
- Oracal cant este separat: `Oracal 651 / cant volum`.
- Print:
  - Autocolant print: `1.5 EUR/m2`
  - Serviciu print: `8.5 EUR/m2`
  - Laminare: `5 EUR/m2`
  - Suprafata print este `0.8005 m2`, iar pretul foloseste suprafata cu waste `0.9606 m2`.
- LED:
  - Default activ.
  - Module LED.
  - Lumina `neutral`.
  - Putere modul `0.75 W`.
  - Litere: `85` module.
  - Embleme: `60` module.
  - Total: `145` module, `108.75 W`, PSU necesar `141.38 W`, sursa selectata `160 W`.
- Regula emblema module LED este depth-aware:
  - 60 mm: 60 module pentru cele doua logo-uri.
  - 80 mm: 50 module.
  - 100 mm: 40 module.
- Backing:
  - Nu exista optiune `Fara spate`.
  - Selectul are doar `Forex 10 mm fara sanfren` si `Forex 10 mm cu sanfren`.
- UI Review/Confirm nu mai afiseaza `goluri/interioare`.
- Sablon montaj: aria este `3.0523 m2`, coerenta cu bbox total lucrare.

## Probe

Capturi salvate:

- `C:\Users\offic\Desktop\intake-v4-e2e-audit-layers-2026-06-26.png`
- `C:\Users\offic\Desktop\intake-v4-e2e-audit-review-after-reload-2026-06-26.png`
- `C:\Users\offic\Desktop\intake-v4-e2e-audit-confirm-stable-2026-06-26.png`

Teste:

- Frontend targeted Vitest: 49/49 passed.
- Backend pytest nu a putut rula: venv-ul backend si Python-ul bundled nu au `pytest` instalat.
- Verificarile backend s-au facut prin API live `127.0.0.1:8000` si import direct de servicii pentru regula LED.

## Plan De Aliniere

1. Calcul live trebuie sa foloseasca `estimated_cost` backend pentru randuri si sa includa toate operatiile care intra in total, inclusiv `cnc_backing_bevel_forex_10mm`.
2. `edge_cant_operation_rows` trebuie incluse in missing-price gate. Daca au `missing_rate`, totalul trebuie sa afiseze status incomplet sau sa fie blocat pentru quote final.
3. Configurare tarife lipsa:
   - Aplicare Oracal 651 pe cant / volum, EUR/m.
   - Lipire cant / volum pe fata litere, EUR/m.
4. ProductSystem trebuie actualizat sa aiba allowed values canonice pentru `oracal_8500` si regula de pret pentru `ral_paint` / `paint_tube_count`.
5. Backend material breakdown trebuie sa separe explicit plexiglas litere vs plexiglas embleme, sau sa expuna allocation rows oficiale.
6. Confirm trebuie sa ascunda/perceapa ca loading valorile de cant pana cand `material_breakdown` este incarcat, ca sa nu apara temporar `29.54 m`.
7. Adaugat test de regresie: suma randurilor vizibile din Calcul live trebuie sa fie egala cu totalul intern sau sa arate explicit randurile excluse.
8. Adaugat test de regresie: orice `edge_cant_operation_rows.pricing_status = missing_rate` trebuie sa seteze `contains_missing_prices = true`.
