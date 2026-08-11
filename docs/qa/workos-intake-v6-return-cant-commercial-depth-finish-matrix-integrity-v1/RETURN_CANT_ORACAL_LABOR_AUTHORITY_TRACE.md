# RETURN_CANT_ORACAL_LABOR_AUTHORITY_TRACE

GO continuation: close Oracal labor authority mismatch after `fa3437a8`.

## What is F7F?

**Owner commercial law activation (2026-08-03)** documented in `backend/data/commercial_rules_volumetric_v2.py` under `# --- F7F Owner commercial law activation ---`.

Among other letter commercial rates, F7F defines:

| Constant | Value | Scope |
|---|---|---|
| `VINYL_APPLICATION_EUR_M2` | **3.0 EUR/m²** | Face vinyl application (`finisaje_aplicare_autocolant_fata`, rule `VOL_V2_FACE_VINYL_APPLICATION_M2`) |

F7F also owns Oracal material series rates, print+laminate, ACM sheet variants, etc. It is **not** a single line item — it is the owner commercial-law package for volumetric/ACM presentation.

## Is F7F generic or RETURN-CANT specific?

**Generic / face-scoped for the 3 EUR/m² application rate.**

- Canonical face key/line: `finisaje_aplicare_autocolant_fata` / `VOL_V2_FACE_VINYL_APPLICATION_M2`
- Kind: **service/labor** (application), area-based
- Not RETURN-CANT-specific

Before this repair, CPP incorrectly reused `VINYL_APPLICATION_EUR_M2` on `finisaje_cant_oracal_labor` with `basis_type=m2` and developed wrap area qty — treating cant application as the same F7F face law on a “distinct surface.”

## Canonical RETURN-CANT Oracal labor authority

| Field | Value |
|---|---|
| Pricing Registry / workcenter code | `RETURN_CANT_VINYL_APPLICATION_LABOR` |
| Rate | **1.0 EUR/ml** |
| Rate basis | `per_linear_meter` |
| Seed | `backend/seeds/seed_volumetric_workcenter_rates.py` |
| Also seeded | `backend/seeds/seed_intake_v5_volumetric_letters_pricing.py` |
| Product Truth bridge | `return_cant_product_truth_bridge.py` → `vinyl_application_labor` |
| Formula truth qty | `template_labor_formula_truth.py` → `letter_perimeter_m` |
| Typed catalog | `pricing_typed_catalog.py` lists the code |
| CPP line | `finisaje_cant_oracal_labor` |
| CPP rule code (after repair) | `VOL_V2_CANT_VINYL_APPLICATION_ML` |
| Documented fallback | `RETURN_CANT_VINYL_APPLICATION_LABOR_EUR_ML = 1.0` |

**PRICING_REGISTRY_VALUE_CHANGES = 0** — key and 1 EUR/ml already existed; wiring was wrong.

## Why CPP previously used F7F for cant

`finisaje_cant_oracal_labor` was authored under F7F with:

- `documented_unit_price=VINYL_APPLICATION_EUR_M2` (3.0)
- `basis_type="m2"`
- quantity = same developed wrap area as material (`perimeter × depth`)

A prior preview test asserted that seeded `RETURN_CANT_VINYL_APPLICATION_LABOR` must **not** displace that F7F 3 EUR/m² rate — creating duplicate authority where registry key existed but CPP ignored it for Oracal cant labor.

## Duplicate authority?

| Authority | Status before repair | Status after |
|---|---|---|
| F7F `VINYL_APPLICATION_EUR_M2` on cant labor | Active (wrong for RETURN-CANT) | Removed from cant labor |
| `RETURN_CANT_VINYL_APPLICATION_LABOR` @ 1 EUR/ml | Present in registry / seeds / bridge; unused by CPP Oracal cant labor | Bound as CPP registry authority |
| Face `finisaje_aplicare_autocolant_fata` @ 3 EUR/m² | Unchanged | Unchanged |

## Precedence rule (owner-confirmed)

`return_cant + Oracal` →

1. **Material** = perimeter × depth → m² × Oracal material catalog rate  
2. **Application labor** = real return perimeter × **1 EUR/ml** (`RETURN_CANT_VINYL_APPLICATION_LABOR`)

Generic face application 3 EUR/m² remains valid for face vinyl only.

## Components

| Component | Quantity | Unit | Rate authority |
|---|---|---|---|
| Oracal material | perimeter × depth | m² | series catalog (641/651) |
| Oracal application labor | real return perimeter | ml | `RETURN_CANT_VINYL_APPLICATION_LABOR` @ 1 EUR/ml |
| Face vinyl application | face area | m² | F7F `VINYL_APPLICATION_EUR_M2` @ 3 EUR/m² |
