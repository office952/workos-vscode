# Return Cant Pricing Keys Alignment Plan

## 1. Purpose

Acest document fixeaza planul de aliniere pentru Pricing keys necesare lui `return_cant`, fara schimbari runtime, fara modificari Pricing si fara schimbari UI.

Boundary fix pentru acest slice:

```text
root_template = TPL-VOLUMETRIC-LETTERS_v2
component_scope = return_cant
mode = pricing_keys_alignment_plan
```

Acest document nu implementeaza:

- modificari Pricing Registry;
- insert/update de rows in `inventory_materials` sau `workcenter_rates`;
- seed-uri;
- migratii;
- schimbari UI;
- schimbari adapter runtime;
- Product Truth writes;
- calcul componenta;
- preview;
- Quote / Order / Execution;
- ProductAggregate / TaskGraph / ExecutionPlan.

## 2. Final Decision

Decizia pentru acest task este:

```text
RETURN_CANT_PRICING_KEYS_ALIGNMENT_READY
```

Semnificatie exacta:

1. naming-ul target pentru Pricing keys poate fi blocat fara ambiguitate critica;
2. rows existente si rows lipsa pot fi separate clar;
3. Product Truth / adapter boundary ramane corect: numai referinte la keys, fara valori EUR;
4. implementarea ulterioara de Pricing va necesita row creation/alignment, dar nu mai are blocker de contract.

## 3. Audit Summary

### 3.1 Rows confirmate acum in Pricing evidence

Materiale profil pe latime:

- `MAT-PROFIL-LATERAL-LITERE-30MM`
- `MAT-PROFIL-LATERAL-LITERE-60MM`
- `MAT-PROFIL-LATERAL-LITERE-80MM`
- `MAT-PROFIL-LATERAL-LITERE-100MM`

Materiale folie:

- `MAT-ORACAL-641`
- `MAT-ORACAL-651`

Rates / workcenter rows confirmate:

- `RETURN_PROFILE_MACHINE_FORMING`
- `RETURN_PROFILE_FACE_BONDING`
- `PAINTING`
- `FACE_VINYL_APPLICATION_LABOR`
- `VINYL_APPLICATION` legacy

Legacy material row confirmat:

- `MAT-VOPSEA-RAL`

### 3.2 Rows existente, dar nealiniate la targetul `return_cant`

1. `FACE_VINYL_APPLICATION_LABOR` exista, dar este face-scoped si are unit `EUR/mp`, nu `EUR/ml`.
2. `VINYL_APPLICATION` exista ca legacy rate, dar este tot `EUR/mp` si nu exprima specific cant / return.
3. `PAINTING` exista ca labor generic la `4 EUR/ml`, dar nu exprima targetul owner-confirmed `1 EUR/ml` pentru `return_cant` RAL labor.
4. `MAT-VOPSEA-RAL` exista ca material consumabil pe tub, nu ca family de materiale by-width pentru cant `30/60/80/100 mm`.

### 3.3 Rows lipsa ca target explicit

1. un labor key dedicat pentru aplicare folie pe cant `1 EUR/ml`;
2. patru material keys dedicate pentru `Vopsit RAL` pe latime `30/60/80/100 mm`;
3. un labor key dedicat pentru `Vopsit RAL` pe cant `1 EUR/ml`.

## 4. Current Evidence

### 4.1 Pricing surface / aggregation

`backend/services/pricing_registry_service.py` agrega materialele si ratele active pentru template-urile valide. Pentru `TPL-VOLUMETRIC-LETTERS_v2`, serviciul injecteaza explicit `V6_REQUIRED_MATERIAL_CODES` si `V6_REQUIRED_WORKCENTER_CODES`, deci rows precum `MAT-ORACAL-641`, `MAT-ORACAL-651`, `RETURN_PROFILE_MACHINE_FORMING`, `RETURN_PROFILE_FACE_BONDING`, `PAINTING` si `FACE_VINYL_APPLICATION_LABOR` sunt parte din surface-ul Pricing chiar daca unele nu apar in JSON-ul template-ului curent.

### 4.2 Seed / owner evidence

Repo-ul confirma read-only:

1. `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py`
   - profile `30/60/80/100 mm`
   - `MAT-ORACAL-641`
   - `MAT-ORACAL-651`
   - `MAT-VOPSEA-RAL`
   - `PAINTING`
   - `FACE_VINYL_APPLICATION_LABOR`
2. `backend/seeds/seed_intake_v6_unified_pricing.py`
   - mentine profilele si materialele V5 in surface-ul V6
   - normalizeaza `RETURN_PROFILE_FACE_BONDING` la rata V4 unificata
3. `backend/seeds/seed_volumetric_workcenter_rates.py`
   - confirma pattern-ul actual de naming pentru labor/workcenter codes uppercase cu underscore
4. `backend/seeds/seed_volumetric_owner_confirmed_prices.py`
   - confirma `MAT-VOPSEA-RAL` ca material consumabil separat de `PAINTING`

### 4.3 Runtime / contract evidence

1. adapterul readonly cere acum slots:
   - `pricing_keys.material_profile_width`
   - `pricing_keys.vinyl_material`
   - `pricing_keys.vinyl_application_labor`
   - `pricing_keys.ral_paint_material_by_width`
   - `pricing_keys.ral_paint_labor`
2. `frontend/src/lib/intakeV6/productTruth/returnCantTruthFieldCaptureReadonlyAdapter.ts` trateaza:
   - `MAT-ORACAL-641` / `MAT-ORACAL-651` ca material rows candidate
   - `return_cant_vinyl_application_labor` si `ral_paint_application_labor` doar ca target refs, nu ca rows dovedite live
3. contractul de boundary anterior fixeaza deja valorile owner-confirmed si lipsurile curente.

## 5. Owner Values

### 5.1 Profil cant material

| width | pricing key | owner value | unit |
|---|---|---|---|
| `30 mm` | `MAT-PROFIL-LATERAL-LITERE-30MM` | `2 EUR/ml` | `ml` |
| `60 mm` | `MAT-PROFIL-LATERAL-LITERE-60MM` | `3 EUR/ml` | `ml` |
| `80 mm` | `MAT-PROFIL-LATERAL-LITERE-80MM` | `4 EUR/ml` | `ml` |
| `100 mm` | `MAT-PROFIL-LATERAL-LITERE-100MM` | `5 EUR/ml` | `ml` |

### 5.2 Folie autocolanta material

- `MAT-ORACAL-641` = Pricing material row la `EUR/mp`
- `MAT-ORACAL-651` = Pricing material row la `EUR/mp`
- consum material = `perimetru_ml x latime_cant_m`

### 5.3 Aplicare folie pe cant

- target labor = `1 EUR/ml`
- laborul nu depinde de latime

### 5.4 Vopsit RAL material

| width | target owner value | unit |
|---|---|---|
| `30 mm` | `2 EUR/ml` | `ml` |
| `60 mm` | `2.5 EUR/ml` | `ml` |
| `80 mm` | `3 EUR/ml` | `ml` |
| `100 mm` | `4 EUR/ml` | `ml` |

### 5.5 Vopsit RAL labor

- target labor = `1 EUR/ml`
- laborul nu depinde de latime

## 6. Naming Recommendation

### 6.1 Principles

1. material rows trebuie sa urmeze pattern-ul existent `MAT-*` din `inventory_materials`.
2. labor / workcenter rows trebuie sa urmeze pattern-ul existent uppercase cu underscore din `workcenter_rates`.
3. keys noi nu trebuie sa se prefaca deja existente.
4. naming-ul propus trebuie sa exprime clar scope-ul `return_cant`, dar sa ramana coerent cu naming-ul existent.

### 6.2 Recommended keys

Pentru aplicare folie pe cant, recomandarea este:

```text
RETURN_CANT_VINYL_APPLICATION_LABOR
```

Rationale:

1. se aliniaza cu `FACE_VINYL_APPLICATION_LABOR`;
2. exprima clar ca este labor si nu material;
3. exprima clar ca unit-ul va fi linear, nu area-based;
4. evita pattern-ul nou cu prepozitii de tip `*_ON_*`.

Pentru materialul RAL by width, recomandarea este:

```text
MAT-VOPSEA-RAL-CANT-30MM
MAT-VOPSEA-RAL-CANT-60MM
MAT-VOPSEA-RAL-CANT-80MM
MAT-VOPSEA-RAL-CANT-100MM
```

Rationale:

1. pastreaza radacina existenta `MAT-VOPSEA-RAL`;
2. foloseste pattern-ul real de material codes cu prefix `MAT-` si segmente cu `-`;
3. introduce width-scope fara sa rupa compatibilitatea semantica cu naming-ul deja existent.

Pentru laborul RAL pe cant, recomandarea este:

```text
RETURN_CANT_RAL_PAINT_LABOR
```

Rationale:

1. urmeaza pattern-ul `FACE_VINYL_APPLICATION_LABOR`;
2. separa clar laborul de material;
3. evita reutilizarea incorecta a lui `PAINTING`.

## 7. Mandatory Matrix

| pricing_need | current_key | exists_now | proposed_key | unit | owner_value | width_dependent | used_by_variant | source_of_truth | blocker |
|---|---|---|---|---|---|---|---|---|---|
| profil cant 30 mm | `MAT-PROFIL-LATERAL-LITERE-30MM` | `yes` | `MAT-PROFIL-LATERAL-LITERE-30MM` | `ml` | `2 EUR/ml` | `true` | `stock_color`, `vinyl_application`, `paint_application` | Pricing material row | none |
| profil cant 60 mm | `MAT-PROFIL-LATERAL-LITERE-60MM` | `yes` | `MAT-PROFIL-LATERAL-LITERE-60MM` | `ml` | `3 EUR/ml` | `true` | `stock_color`, `vinyl_application`, `paint_application` | Pricing material row | none |
| profil cant 80 mm | `MAT-PROFIL-LATERAL-LITERE-80MM` | `yes` | `MAT-PROFIL-LATERAL-LITERE-80MM` | `ml` | `4 EUR/ml` | `true` | `stock_color`, `vinyl_application`, `paint_application` | Pricing material row | none |
| profil cant 100 mm | `MAT-PROFIL-LATERAL-LITERE-100MM` | `yes` | `MAT-PROFIL-LATERAL-LITERE-100MM` | `ml` | `5 EUR/ml` | `true` | `stock_color`, `vinyl_application`, `paint_application` | Pricing material row | none |
| Oracal 641 material | `MAT-ORACAL-641` | `yes` | `MAT-ORACAL-641` | `mp` | `6.5 EUR/mp` | `false` | `vinyl_application` | Pricing material row | current cant runtime input is still 651-only |
| Oracal 651 material | `MAT-ORACAL-651` | `yes` | `MAT-ORACAL-651` | `mp` | `9 EUR/mp` | `false` | `vinyl_application` | Pricing material row | none |
| aplicare folie pe cant | `FACE_VINYL_APPLICATION_LABOR` nearest row; `VINYL_APPLICATION` legacy | `no` | `RETURN_CANT_VINYL_APPLICATION_LABOR` | `ml` | `1 EUR/ml` | `false` | `vinyl_application` | Workcenter rate row | current rows are face-scoped or wrong basis `mp` |
| RAL material cant 30 mm | `MAT-VOPSEA-RAL` legacy tube | `no` | `MAT-VOPSEA-RAL-CANT-30MM` | `ml` | `2 EUR/ml` | `true` | `paint_application` | Pricing material row | current row is tube-based, not width-based |
| RAL material cant 60 mm | `MAT-VOPSEA-RAL` legacy tube | `no` | `MAT-VOPSEA-RAL-CANT-60MM` | `ml` | `2.5 EUR/ml` | `true` | `paint_application` | Pricing material row | current row is tube-based, not width-based |
| RAL material cant 80 mm | `MAT-VOPSEA-RAL` legacy tube | `no` | `MAT-VOPSEA-RAL-CANT-80MM` | `ml` | `3 EUR/ml` | `true` | `paint_application` | Pricing material row | current row is tube-based, not width-based |
| RAL material cant 100 mm | `MAT-VOPSEA-RAL` legacy tube | `no` | `MAT-VOPSEA-RAL-CANT-100MM` | `ml` | `4 EUR/ml` | `true` | `paint_application` | Pricing material row | current row is tube-based, not width-based |
| RAL labor | `PAINTING` nearest row | `no` | `RETURN_CANT_RAL_PAINT_LABOR` | `ml` | `1 EUR/ml` | `false` | `paint_application` | Workcenter rate row | current `PAINTING` row is generic and valued at `4 EUR/ml` |

## 8. Product Truth And Component Boundary

Clarificari obligatorii:

1. componenta nu stocheaza valori `EUR`;
2. Product Truth nu stocheaza costuri;
3. adapterul readonly emite doar pricing key references;
4. Pricing ramane singurul owner pentru valori;
5. catalogul ramane owner pentru cod / culoare / swatch, nu cost;
6. formula ramane declarativa.

## 9. Formula Summary

### 9.1 `Culoare Stoc`

```text
material_profile_quantity_ml = confirmed_perimeter_m
extra_finish_cost = none
labor_machine_forming_quantity_ml = confirmed_perimeter_m
labor_face_bonding_quantity_ml = confirmed_perimeter_m
```

### 9.2 `Folie autocolanta`

```text
material_profile_quantity_ml = confirmed_perimeter_m
vinyl_material_quantity_mp = confirmed_perimeter_m x latime_cant_m
vinyl_application_labor_quantity_ml = confirmed_perimeter_m
```

### 9.3 `Vopsit RAL`

```text
material_profile_quantity_ml = confirmed_perimeter_m
ral_paint_material_key = width_selected_row
ral_paint_labor_quantity_ml = confirmed_perimeter_m
```

## 10. Non-Blocking Gaps

1. `frontend/src/lib/pricingRegistry.ts` in `product001ExpectedCodes()` include profile rows si generic return ops, dar nu include inca `MAT-ORACAL-641`, `MAT-ORACAL-651`, `FACE_VINYL_APPLICATION_LABOR`, `PAINTING` sau viitoarele cant-specific keys. Acesta este follow-up de Pricing UI coverage, nu blocker de plan.
2. runtime-ul `return_cant` direct-input ramane `Oracal 651` only, dar acest gap nu blocheaza planul de Pricing keys.
3. `MAT-VOPSEA-RAL` si `PAINTING` trebuie pastrate explicit ca legacy semantics pana la alinierea noului model pe width.

## 11. Next Implementation Slice

Slice-ul urmator recomandat, separat de acest task docs-only, este:

```text
RETURN_CANT_PRICING_KEYS_CREATION_AND_REGISTRY_ALIGNMENT_V1
```

Acest slice viitor trebuie sa:

1. creeze rows lipsa in Pricing;
2. pastreze clar separatia dintre material si labor;
3. nu scrie valori in Product Truth;
4. actualizeze coverage-ul Pricing UI dupa crearea rows.