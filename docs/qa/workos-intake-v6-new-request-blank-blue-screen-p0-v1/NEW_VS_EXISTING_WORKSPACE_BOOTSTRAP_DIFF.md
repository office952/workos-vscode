# NEW_VS_EXISTING_WORKSPACE_BOOTSTRAP_DIFF

## Subjects

| Role | ID | Code |
|------|-----|------|
| Failing (Owner) | `e994927e-aa90-46b0-bde0-dd34e025e44e` | IV6-7DFE073B |
| Working | `03a1da1e-003a-4139-9668-59ac6bcec812` | IV6-362B31FC |
| Synthetic empty QA | `2670859b-bc57-4ac0-b2d7-0cc24567b9ed` | IV6-EC35E0A1 |

## Compare

| Field | Failing | Working |
|-------|---------|---------|
| template_code | TPL-VOLUMETRIC-LETTERS_v2 | TPL-VOLUMETRIC-LETTERS_v2 |
| payload shape | full finish_setup + analysis | full finish_setup + analysis |
| finish_setup | present | present |
| svg_analysis_json.layerRoleConfirmation | present | present |
| product composition | present | present |
| route params | `:workspaceId/operator` | same |
| previewRefresh init | gen 0/0 | gen 0/0 |

## Diff that mattered for blank

Not payload divergence — both parse and price. Blank triggered when Review rendered commercial sliders **before** `eurToRonRate` hydrated (`null`), crashing both new and existing workspaces intermittently.

Synthetic empty workspace correctly lands on Straturi (no crash path until Configurare/review commercial panel).
