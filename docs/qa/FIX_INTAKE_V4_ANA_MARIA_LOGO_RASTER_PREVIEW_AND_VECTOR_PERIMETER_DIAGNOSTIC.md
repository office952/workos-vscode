# FIX — Intake V4 Ana Maria logo raster preview and vector perimeter diagnostic

## Purpose

Clarify why Ana Maria kindergarten logos appear broken in SVG preview, why artwork logo perimeter can be `n/a`, and how Corel-measured logo curve length relates to raster vs vector SVG export — **without** changing volumetric production geometry, CostEngine, or quote/order paths.

## Context

For `ana-maria-gradinita.svg` / `ana-maria-gradinita-fara-layere.svg`:

- Logos are exported from Corel as **external PNG** references (`xlink:href="…_Images\…png"`), not embedded base64.
- Each logo group also includes a **stroke-only vector outline** path (`fill="none" stroke="#2B2A29"`) used for Corel curve measurement (~**4.891 m** total for both logos).
- Browser SVG preview uses `dangerouslySetInnerHTML` — relative external PNG paths do not resolve → broken/pixelated logo icons.
- Production role remains **`printed_artwork`** / print overlay; raster logos are **not** volumetric child parts, LED, CNC, or cant geometry.

## Why logo perimeter is n/a (raster-only uploads)

If the SVG contains only raster `<image>` artwork with **no** stroke outline paths assigned to logo layers, the app cannot compute true vector curve length. Perimeter from image bounding box is **not** used (would falsely imply CNC/cant readiness).

UI shows:

`Artwork logo perimeter: n/a — artwork raster, no vector perimeter`

If Corel reference exists but SVG has no vector outline:

`Corel logo reference requires vector outline, but current SVG logo is raster artwork. App cannot compute true vector curve length from raster.`

## Raster artwork vs vector outline

| Aspect | Raster `<image>` | Vector stroke outline |
|--------|------------------|------------------------|
| Production role | `printed_artwork` | Diagnostic only when co-located with raster |
| Preview | Needs embedded asset or `*_Images` folder | Renders in browser |
| Perimeter | Not computed from pixels | Summed from path geometry (diagnostic) |
| Volumetric / LED / CNC / cant | Excluded | Excluded from production totals |

## Export recommendations

1. **Complete preview in WorkOS:** re-export SVG with **embedded/base64 images**, or upload SVG together with the `*_Images` folder (same relative paths).
2. **Vector perimeter required for operator QA:** export logo **outline as vector** (stroke path on logo layer) — Corel already does this in the Ana Maria source files.
3. **Print/sticker production:** keep logo as raster artwork; use Artwork card recommendation (print + laminare) — no volumetric conversion.

## Files changed

- `frontend/src/lib/svgAnalyzer/analyzer/semanticAndPseudoLayerExpansion.ts` — assign sibling stroke outline paths to logo pseudo-layers (unlayered fixture parity with layered).
- `frontend/src/lib/intakeV4/intakeV4ArtworkLogoDiagnostic.ts` — warnings and Corel mismatch messaging.
- `frontend/src/lib/intakeV4/intakeV4GeometryMetricDisplay.ts` — diagnostic vs production artwork perimeter fields.
- `frontend/src/components/workos/intake-v4/IntakeV4GeometryPanel.tsx` — artwork warnings + diagnostic perimeter label.
- `frontend/src/components/workos/intake-v4/IntakeV4ArtworkComplexityCard.tsx` — human-readable external raster warning.
- Tests: `intakeV4ArtworkLogoDiagnostic.test.ts`, updated geometry/artwork panel tests.

## Commands + results

```powershell
cd frontend
npx --yes pnpm@8.10.0 exec vitest run src/lib/intakeV4/intakeV4ArtworkLogoDiagnostic.test.ts src/lib/intakeV4/intakeV4GeometryMetricDisplay.test.ts src/lib/svgAnalyzer/analyzer/rasterOverVectorArtwork.test.ts src/lib/svgAnalyzer/svgAnalyzerRegressionGate.test.ts
```

## Boundary

- No quote/order/task creation, ExecutionPlan, `tasks_json`, stock consumption.
- No Pricing Registry, Color Registry, CostEngine, or employee assignment changes.
- No vector tracing or automatic logo reconstruction.
- Letter/soare volumetric geometry unchanged; PBL regression gate must remain PASS.

## Next steps

- Optional: preview-time fetch of sibling `*_Images` when operator uploads a folder (out of scope for this diagnostic build).
