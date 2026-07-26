# Identity Inventory (summary)

| Occurrence area | Was | Now | Action |
|---|---|---|---|
| `semanticAndPseudoLayerExpansion.ts` | TECHNICAL_IDENTITY positional | `logo_instance_NNN` | **FIXED** |
| `eic_workspace_logo_fixtures.py` | TEST_FIXTURE positional | neutral IDs | **FIXED** |
| Backend linked-logo tests | TEST_FIXTURE positional | neutral IDs | **FIXED** |
| `intakeV4OperatorUiDisplay.ts` | DISPLAY_LABEL | Logo 1/2 map | **KEPT** |
| `intakeV6SvgPreviewLayerHighlight.ts` | POSITION_METADATA | left/right hint | **LEGITIMATE** |
| Compound/historical docs | DOCUMENTATION_EXAMPLE positional | correction notes | **UPDATED** |
| Frontend component tests | legacy SVG group names | unchanged | **EXCEPTION** — legacy compat tests |

**Full static gate:** zero positional IDs in production backend services and analyzer synthesis path.
