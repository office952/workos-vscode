# FIX_SAFE_SVG_DOCTYPE_SANITIZATION_FOR_OWNER_FILES

## Purpose

Allow real owner SVG exports (CorelDRAW with standard W3C SVG DOCTYPE) to produce `path_geometry_summary` for Operator Workspace geometry → lighting chain, without relaxing XML parser security.

## Problem

Validated chain worked with `frontend/e2e/fixtures/volumetric-multilayer.svg`, but owner file `blueprints/volumetric-letter-svg-test/litere-volumetrice.svg` failed path geometry with:

| Field | Value |
|-------|-------|
| `path_geometry_summary.parse_status` | `failed` |
| `error_code` | `xml_unsafe_construct` |

Raw SVG analysis could still succeed (separate code path), but layer roles, perimeter classification, and lighting module suggestion remained blocked.

## Root cause

| Layer | Behavior before fix |
|-------|---------------------|
| Raw analysis (`SvgLayerAnalysisService`) | Already sanitized standard DOCTYPE via `sanitize_svg_for_analysis()` |
| Path geometry (`build_path_geometry_summary_from_svg_text`) | Called `SvgMetricsService.parse_svg_metrics()` on **raw** SVG text → fail-closed on DOCTYPE |

Gap: sanitization existed but was **not wired** into path geometry upload pipeline.

Owner SVG contains only standard single-line DOCTYPE — no `<!ENTITY` declarations:

```xml
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
```

## Security decision

- **Do not** switch to an unsafe XML parser
- **Do not** disable `SvgMetricsService` DOCTYPE/ENTITY fail-closed guard
- **Do not** allow entity expansion, external fetch, or internal DTD subsets
- **Do** reuse existing `svg_sanitization_service.py` with stricter ENTITY blocking
- **Do** sanitize only by stripping standard DOCTYPE declarations before safe parse
- **Do** fail closed with explicit codes:
  - `svg_unsafe_entity_declaration`
  - `svg_unsafe_dtd_declaration`
- **Do** expose operator-friendly `operator_message` on blocked/failed path geometry

Parser used: **`xml.etree.ElementTree`** (stdlib) with pre-parse text guards — not `defusedxml`, not `lxml` network fetch.

## Implementation

### `svg_sanitization_service.py`

- Added `prepare_svg_text_for_safe_geometry_parsing()`
- ENTITY declarations → block (`svg_unsafe_entity_declaration`)
- Internal DTD subset (`<!DOCTYPE ... [`) → block (`svg_unsafe_dtd_declaration`)
- Standard DOCTYPE only → strip via existing regex, continue parse
- Metadata: `doctype_removed_for_safe_parse`, `sanitization` dict, warning `svg_sanitized_doctype_removed`
- Updated `sanitize_svg_for_analysis()` to **stop stripping ENTITY** — fail closed instead

### `intake_v3_geometry_metrics_snapshot_service.py`

- `build_path_geometry_summary_from_svg_text()` now calls `prepare_svg_text_for_safe_geometry_parsing()` before metrics + layer path geometry
- Parses sanitized copy only; original upload bytes unchanged in storage flow

### `intake_v3_workspace_service.py`

- Passes `source_file_name` into path geometry builder on SVG upload

### `svg_layer_analysis_service.py`

- Explicit ENTITY / internal DTD errors before generic `xml_unsafe_construct` fallback

## Security tests

| Case | Expected |
|------|----------|
| SVG without DOCTYPE | Unchanged parse |
| Standard DOCTYPE SVG | DOCTYPE removed, parsed |
| `<!ENTITY ...>` | Blocked |
| XXE pattern (`SYSTEM "file://..."`) | Blocked |
| Owner `litere-volumetrice.svg` | `parse_status=parsed`, no `xml_unsafe_construct` |
| `volumetric-multilayer.svg` | Still parsed |

## Owner SVG test result

File: `blueprints/volumetric-letter-svg-test/litere-volumetrice.svg` (not committed — already in repo blueprint folder)

| | Before | After |
|-|--------|-------|
| `path_geometry_summary.parse_status` | `failed` | **`parsed`** |
| `error_code` | `xml_unsafe_construct` | **absent** |
| `doctype_removed_for_safe_parse` | — | **`true`** |
| Detected groups (raw analysis) | Spate, sanfren, volum, fata_x0020_plexiglas, autocolant | unchanged |

Path geometry layers derive from `<path>` elements grouped by `<g id>` — owner file uses mostly `<polygon>` in non-face layers; layer metrics reflect path-based parser scope (unchanged geometry logic).

## Tests run

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest `
  tests/test_intake_v3_path_geometry_svg_sanitization.py `
  tests/test_svg_sanitization.py `
  tests/test_intake_v3_lighting_plan.py `
  tests/test_intake_v3_operator_workspace_e2e_hardening.py -q
```

**Result:** 58 passed

## Boundary confirmations

- No CostEngine / Inventory / StockMovement / ExecutionTask / ExecutionPlan / PO / SupplierOrder
- No Lighting / PSU / reserve logic changes
- No Atoms recomposition
- No unsafe XML parser
- No XXE / entity expansion enabled
- Original uploaded SVG not overwritten
- Owner SVG not added as new committed fixture (uses existing blueprint path in tests only)

## What remains

1. Runtime re-upload owner SVG via Operator file drop → confirm UI shows layers + geometry + lighting suggestion end-to-end
2. Raw analysis path (`analyze_svg_content`) still uses direct `ET.fromstring` — separate hardening if we want unified sanitization warnings on raw analysis payload
3. Path geometry layer metrics for owner file may under-count polygon-only layers until polygon→path geometry support exists (pre-existing scope)
4. Multi-line non-standard DOCTYPE — fail closed unless safely removable

## Verdict

**PASS — owner SVG DOCTYPE safely sanitized and parsed** (path geometry pipeline)
