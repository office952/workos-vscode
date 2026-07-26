# Manual Material Fill Checklist (no Supplier Import)

Policy API: `GET /api/v1/product-system/reference-finish-line/critical-materials`

## Classification policy

| Class | Meaning |
|-------|---------|
| ACTIVE_TEMPLATE_CRITICAL | Active template path + missing unit_cost + distorts production cost |
| ACTIVE_TEMPLATE_OPTIONAL | Active path optional / alternate; warn only |
| UNUSED_ACTIVE | Active inventory, unused by templates |
| LEGACY | History only |
| DUPLICATE_ALIAS | Alias of canonical code |
| FUTURE_ONLY | Reserved |
| UNKNOWN | Insufficient evidence |

## Seed checklist (owner fill — do not invent)

1. **MAT-LED-PSU-12V** — VARIANT_SELECTOR (closed in ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1; do not price)
2. **MAT-ADEZIV-CANT-LITERE** — OPTIONAL if missing
3. **MAT-CABLU-MYYUP-2X075** — OPTIONAL if missing
4. **MAT-CABLU-MYYUP-2X15** — OPTIONAL if missing
5. **SVC-LAMINATION-SERVICE** — OPTIONAL if missing

## Rules

- Do **not** invent prices in this build
- Do **not** run Supplier Import
- Follow-up build: `ACTIVE_TEMPLATE_CRITICAL_MATERIAL_FILL_V1` (owner GO)
