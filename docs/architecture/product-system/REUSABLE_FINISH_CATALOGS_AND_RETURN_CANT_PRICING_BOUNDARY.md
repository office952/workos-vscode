# Reusable Finish Catalogs And Return Cant Pricing Boundary

## 1. Purpose

Acest document defineste boundary-ul reutilizabil pentru cataloagele de finisaje si boundary-ul final de Pricing pentru `return_cant`, fara schimbari runtime.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
component_scope = return_cant
catalog_scope = reusable finish catalogs
mode = reusable_finish_catalogs_and_return_cant_pricing_boundary_audit
```

Acest document nu implementeaza:

- UI nou de catalog;
- CRUD de catalog;
- modificari Pricing;
- modificari adapter runtime;
- Product Truth writes;
- preview;
- calcul componenta;
- DB / migration / seed;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan.

## 2. Final Decision

Decizia pentru acest task este:

```text
REUSABLE_FINISH_CATALOGS_BOUNDARY_READY
```

Semnificatie exacta:

1. boundary-ul conceptual dintre catalog si Pricing este suficient de clar pentru pasii urmatori;
2. `return_cant` poate consuma cataloage reutilizabile fara sa le privatizeze;
3. Pricing ramane singura sursa pentru costuri si tarife;
4. runtime-ul curent nu este inca complet aliniat la aceasta directie, dar discrepantele ramase sunt follow-up de mapping/alignment, nu blocker pentru contract.

## 3. Core Owner Decision

Finisajele reutilizabile trebuie tratate in 3 familii user-facing si 3 familii tehnice:

### 3.1 User-facing labels obligatorii

- `Culoare Stoc`
- `Folie autocolanta`
- `Vopsit RAL`

### 3.2 Technical variants recomandate

- `stock_color`
- `vinyl_application`
- `paint_application`

### 3.3 Interpretare

1. `Culoare Stoc` nu este extra finish cost.
2. `Folie autocolanta` nu este privata pentru `return_cant`; este o familie reutilizabila pentru Oracal 641 / 651 si alte aplicatii viitoare.
3. `Vopsit RAL` nu este privat pentru `return_cant`; este o familie reutilizabila de paint/process.
4. cataloagele pastreaza doar identitate si metadata tehnica.
5. Pricing pastreaza costurile si tarifele.

## 4. Catalog Boundary

### 4.1 Ce trebuie sa tina catalogul

Catalogul reutilizabil poate tine:

1. cod
2. nume
3. culoare vizibila pentru UI
4. serie
5. sistem
6. status activ / inactiv
7. metadata tehnica de compatibilitate
8. family / series / application hints

### 4.2 Ce NU trebuie sa tina catalogul

Catalogul nu trebuie sa tina:

1. pret
2. cost material
3. cost manopera
4. tarif final
5. adaos comercial

### 4.3 Reusable catalog entities

Boundary-ul minim recomandat este:

#### A. `stock_color_catalog`

- operational labels pentru atelier
- exemple initiale:
  - `Alb`
  - `Negru`
  - `Auriu`
  - `Argintiu`
- metadata posibila:
  - `active`
  - `display_label`
  - `surface_hint`
  - `supplier_hint`

#### B. `vinyl_color_catalog`

- reutilizabil pentru Oracal 641 / 651 / 8500 si alte serii viitoare
- campuri minime:
  - `material_family`
  - `series`
  - `color_code`
  - `color_name`
  - `visual_swatch`
  - `active`

#### C. `paint_color_catalog`

- reutilizabil pentru RAL si alte sisteme viitoare
- campuri minime:
  - `system`
  - `ral_code`
  - `color_name`
  - `visual_swatch`
  - `active`

## 5. Catalog Boundary Summary By Family

### 5.1 `Culoare Stoc`

- semantic family: `stock_color`
- current examples: `Alb`, `Negru`, `Auriu`, `Argintiu`
- catalog role: operational workshop reference
- pricing role: none direct beyond profile width + normal operations
- extra finish cost: `false`

### 5.2 `Folie autocolanta`

- technical family: `vinyl_application`
- reusable material series accepted by owner:
  - `Oracal 641`
  - `Oracal 651`
- catalog role:
  - material family
  - series
  - code
  - visual color
  - active state
- pricing role:
  - material price in Pricing per `mp`
  - labor in Pricing per `ml`

### 5.3 `Vopsit RAL`

- technical family: `paint_application`
- reusable color system: `RAL`
- catalog role:
  - system
  - RAL code
  - visual color
  - active state
- pricing role:
  - material price in Pricing by width
  - labor in Pricing per `ml`

## 6. Mandatory Matrix

| ui_label | technical_variant | catalog_reference | required_ui_control | pricing_material_basis | pricing_labor_basis | width_affects_material | width_affects_labor | component_truth_fields | blockers |
|---|---|---|---|---|---|---|---|---|---|
| `Culoare Stoc` | `stock_color` | `stock_color_catalog` | list or typeahead with workshop-visible label | `MAT-PROFIL-LATERAL-LITERE-{30|60|80|100}MM` | `RETURN_PROFILE_MACHINE_FORMING` + `RETURN_PROFILE_FACE_BONDING` | `true` | `false` | `finish_variant.type`, `finish_variant.stock_color_label`, `pricing_keys.material_profile_width` | no canonical catalog entity yet |
| `Folie autocolanta — Oracal 641` | `vinyl_application` | `vinyl_color_catalog(series=641)` | structured selector with code + visible color | `MAT-ORACAL-641`, quantity = `perimetru_ml x latime_cant_m` | `return_cant_vinyl_application_labor` target 1 EUR/ml | `true` | `false` | `finish_variant.type`, `finish_variant.vinyl.material_family`, `finish_variant.vinyl.series`, `finish_variant.vinyl.color_code`, `finish_variant.vinyl.catalog_reference`, `pricing_keys.vinyl_material`, `pricing_keys.vinyl_application_labor` | current return_cant UI/adapter only models 651 |
| `Folie autocolanta — Oracal 651` | `vinyl_application` | `vinyl_color_catalog(series=651)` | structured selector with code + visible color | `MAT-ORACAL-651`, quantity = `perimetru_ml x latime_cant_m` | `return_cant_vinyl_application_labor` target 1 EUR/ml | `true` | `false` | `finish_variant.type`, `finish_variant.vinyl.material_family`, `finish_variant.vinyl.series`, `finish_variant.vinyl.color_code`, `finish_variant.vinyl.catalog_reference`, `pricing_keys.vinyl_material`, `pricing_keys.vinyl_application_labor` | current live cant runtime still mixes registry material and preview-only labor alignment |
| `Vopsit RAL` | `paint_application` | `paint_color_catalog(system=RAL)` | structured selector with RAL code + visible color | by width: `ral_paint_material_{30|60|80|100}mm` target keys | `ral_paint_application_labor` target 1 EUR/ml | `true` | `false` | `finish_variant.type`, `finish_variant.paint.system`, `finish_variant.paint.ral_code`, `finish_variant.paint.catalog_reference`, `pricing_keys.ral_paint_material_by_width`, `pricing_keys.ral_paint_labor` | current runtime still uses tube-based `MAT-VOPSEA-RAL` and lacks `paint_target` |

## 7. Pricing Boundary

### 7.1 Return profile by width

Owner target confirmed for profile material:

| width | required Pricing entry | target value | unit |
|---|---|---|---|
| `30 mm` | `MAT-PROFIL-LATERAL-LITERE-30MM` | `2 EUR/ml` | `ml` |
| `60 mm` | `MAT-PROFIL-LATERAL-LITERE-60MM` | `3 EUR/ml` | `ml` |
| `80 mm` | `MAT-PROFIL-LATERAL-LITERE-80MM` | `4 EUR/ml` | `ml` |
| `100 mm` | `MAT-PROFIL-LATERAL-LITERE-100MM` | `5 EUR/ml` | `ml` |

Audit result:

- aceste entry-uri exista deja in seed/dev evidence si in Pricing surface ca family de varianti;
- raman in Pricing, nu in componenta si nu in catalog.

### 7.2 Return profile operations

Entry-uri operation/workcenter care trebuie sa ramana in Pricing:

- `RETURN_PROFILE_MACHINE_FORMING`
- `RETURN_PROFILE_FACE_BONDING`

Boundary obligatoriu:

1. `/utilaje` poate descrie capabilitate, capacitate si workcenter mapping;
2. `/utilaje` nu este sursa finala de pret client;
3. named workcenter rate ramane in Pricing Registry.

### 7.3 `Culoare Stoc`

Pentru `Culoare Stoc`:

1. nu exista extra finish cost;
2. costul vine din profilul de cant pe latime;
3. plus operatiile normale de formare/lipire;
4. catalogul retine doar eticheta operationala de culoare.

### 7.4 `Folie autocolanta`

Boundary final dorit pentru `Folie autocolanta`:

#### Material

- `MAT-ORACAL-641` in Pricing la `EUR/mp`
- `MAT-ORACAL-651` in Pricing la `EUR/mp`
- quantity basis = `perimetru_ml x latime_cant_m`

#### Labor

- `vinyl_application_labor` pentru cant = `1 EUR/ml`
- laborul NU depinde de latime
- materialul depinde de latime doar prin consumul de suprafata

Audit result:

1. materialele `MAT-ORACAL-641` si `MAT-ORACAL-651` exista in repo / seed evidence;
2. runtime-ul actual de `return_cant` expune doar `Oracal 651`, nu si `641`;
3. laborul dedicat de `1 EUR/ml` pentru cant nu este inca confirmat ca row live dedicat in Pricing Registry curent;
4. regula trebuie tratata ca target Pricing contract, nu ca existenta runtime deja dovedita.

### 7.5 `Vopsit RAL`

Boundary final dorit pentru `Vopsit RAL`:

#### Material by width

| width | target Pricing material | target value | unit |
|---|---|---|---|
| `30 mm` | `ral_paint_material_30mm` target key | `2 EUR/ml` | `ml` |
| `60 mm` | `ral_paint_material_60mm` target key | `2.5 EUR/ml` | `ml` |
| `80 mm` | `ral_paint_material_80mm` target key | `3 EUR/ml` | `ml` |
| `100 mm` | `ral_paint_material_100mm` target key | `4 EUR/ml` | `ml` |

#### Labor

- `ral_paint_application_labor` target = `1 EUR/ml`
- laborul NU depinde de latime

Audit result:

1. runtime-ul curent are `MAT-VOPSEA-RAL` ca tub whole-material legacy path si `PAINTING` service legacy evidence;
2. asta NU este aceeasi semantica ca material-by-width plus labor fix per ml;
3. boundary-ul final este clar, dar live Pricing needs follow-up alignment pentru a-l exprima curat pe `return_cant`.

## 8. Pricing Gap Classification

### 8.1 Confirmed today

- profile width material variants `30/60/80/100`
- generic return operations `RETURN_PROFILE_MACHINE_FORMING`, `RETURN_PROFILE_FACE_BONDING`
- material rows `MAT-ORACAL-641`, `MAT-ORACAL-651`
- material row `MAT-VOPSEA-RAL` in legacy/tube semantics

### 8.2 Not yet cleanly confirmed as live return_cant Pricing rows

- dedicated `vinyl_application_labor = 1 EUR/ml` for cant
- width-aware RAL material rows for `return_cant`
- dedicated `ral_paint_labor = 1 EUR/ml` for cant

Consecinta:

- boundary-ul este `READY` la nivel de contract;
- pricing alignment runtime ramane follow-up explicit.

## 9. Product Truth Target Proposal

Fara implementare runtime, targetul recomandat devine:

```text
components.return_cant.instances.<instance_key>.finish_variant.type =
  stock_color | vinyl_application | paint_application

components.return_cant.instances.<instance_key>.finish_variant.stock_color_label

components.return_cant.instances.<instance_key>.finish_variant.vinyl.material_family
components.return_cant.instances.<instance_key>.finish_variant.vinyl.series
components.return_cant.instances.<instance_key>.finish_variant.vinyl.color_code
components.return_cant.instances.<instance_key>.finish_variant.vinyl.catalog_reference

components.return_cant.instances.<instance_key>.finish_variant.paint.system
components.return_cant.instances.<instance_key>.finish_variant.paint.ral_code
components.return_cant.instances.<instance_key>.finish_variant.paint.catalog_reference

components.return_cant.instances.<instance_key>.pricing_keys.material_profile_width
components.return_cant.instances.<instance_key>.pricing_keys.vinyl_material
components.return_cant.instances.<instance_key>.pricing_keys.vinyl_application_labor
components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_material_by_width
components.return_cant.instances.<instance_key>.pricing_keys.ral_paint_labor
```

Clarificari obligatorii:

1. `pricing_keys.*` sunt referinte, nu valori;
2. Product Truth nu stocheaza pret/cost;
3. `catalog_reference` nu stocheaza pret/cost;
4. `vinyl_application` si `paint_application` sunt termeni universali, nu private aliases pentru `return_cant`.

## 10. UI Preservation Rules

Reguli obligatorii pentru pasii urmatori:

1. UI user-facing trebuie sa scrie `Culoare Stoc`, nu `Culoare Stock`.
2. Pentru `Culoare Stoc`, operatorul poate alege sau tasta culoarea pentru atelier.
3. Pentru `Folie autocolanta`, selectorul trebuie sa afiseze cod + culoare vizibila.
4. Pentru `Vopsit RAL`, selectorul trebuie sa afiseze cod RAL + culoare vizibila.
5. Culorile vizibile in UI sunt obligatorii.
6. Selectorul Oracal/RAL nu trebuie inlocuit cu text simplu.
7. `Folie autocolanta` trebuie sa ramana termen universal user-facing chiar daca intern exista `641` si `651`.

## 11. Adapter Impact

Adapterul curent din `returnCantTruthFieldCaptureReadonlyAdapter.ts` este:

```text
valid as first pass
```

Motive:

1. separa corect `Vector Litere` de `Vector Logo`;
2. nu stocheaza cost sau pret;
3. tine Pricing ca sursa de valori;
4. pastreaza referinte de catalog read-only.

Dar boundary-ul nou cere un update ulterior:

1. `oracal` -> `vinyl_application`
2. `ral_paint` -> `paint_application`
3. suport pentru `Oracal 641` in afara cazului actual `651`-only
4. UI labels romanesti explicite pentru `Culoare Stoc`
5. split mai clar intre catalog reference si pricing key families

Aceasta NU este o discrepanta critica pentru taskul curent si NU cere STOP.

## 12. Analyzer Boundary Confirmation

Analyzer-ul poate furniza:

- perimeter suggestion
- layer/group evidence
- geometry provenance

Analyzer-ul nu poate furniza:

- truth confirmation
- cost material
- cost manopera
- price final

Consecinta:

- cataloagele si Pricing-ul raman separate de analyzer;
- Product Truth este singurul loc care poate confirma campurile component-owned si dependency-owned.

## 13. Forbidden Scope Confirmation

Acest document NU face:

- code change
- UI change
- Pricing change
- DB / seed / migration
- Quote / Order / Execution change
- ProductAggregate / TaskGraph / ExecutionPlan change

## 14. Next Recommended Prompt

Dupa acest boundary, prompt-ul recomandat este:

```text
RETURN_CANT_READONLY_ADAPTER_UNIVERSAL_FINISH_TERMS_UPDATE_V1
```

Cu instructiunea:

```text
Keep the adapter read-only, migrate semantic labels from oracal/ral_paint to vinyl_application/paint_application, preserve stock_color, and add reusable series-aware catalog references for Oracal 641/651 without introducing pricing values in component truth.
```