# Mounting Fixing System Contract

| Field | Value |
|-------|-------|
| Date | 2026-07-18 |
| GO | `GO_DECOUPLE_ACP_FROM_COMMERCIAL_MOUNTING_AND_ADD_VERTICAL_STEEL_FIXING_SYSTEM` |
| Contract | `mounting_fixing_system/v1` |
| Code | `backend/data/product_system/mounting_fixing_system_v1.py` |

## Separation of concepts

| Concept | Authority | Gated by commercial `mounting_scope`? |
|---------|-----------|----------------------------------------|
| Panou ACP casetat | Product component | **No** |
| Cadru interior ACP | Nested ACP product config | **No** (profile gate separate) |
| Sistem de prindere | Technical wall attachment | **No** |
| Pregătire / montaj comercial | Commercial service | **Yes** |

## V1 type — Brat otel vertical

| Field | Value |
|-------|-------|
| `type_code` | `FIXING-SYSTEM-VERTICAL-STEEL-BRACKET` |
| Main profile | `PROFILE-SHS-20X20X1_5` (steel SHS 20×20×1.5) |
| Material | `MAT-STRUCT-STEEL` |
| Top angle | `STEEL_ANGLE` · `MANUAL_CONFIRMATION_REQUIRED` · `length_mm: null` |
| Bottom bar | steel · `MANUAL_CONFIRMATION_REQUIRED` · `length_mm: null` |
| Lower fastener | self-drilling hex head 4.5×60 mm |

**Dimensiunile cornierului superior și barei inferioare sunt manual-confirmed per lucrare.**  
Nu există default sau formulă automată.

## Persist / project

| Layer | Location |
|-------|----------|
| FinishSetup | `mounting_fixing_system` |
| ProductDefinition | `canonical_values.mounting_configuration.fixing_system` (+ flat `mounting_fixing_system`) |
| Aggregate | `mounting_fixing_aggregate_projection` — semantic only; no fake BOM |
| Lifecycle | Step 2 evidence; frame profile gate remains separate |

## Out of scope

CPP · tasking · Execution · schema/migration · pricing · automatic structural calc
