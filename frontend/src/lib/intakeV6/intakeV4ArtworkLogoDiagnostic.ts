/**
 * Read-only artwork logo diagnostics — raster preview warnings and vector outline perimeter
 * for operator display only. Does not alter production geometry roles or volumetric paths.
 */

import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";

export const INTAKE_V4_LOGO_RASTER_EXTERNAL_MISSING_WARNING =
  "Logo/artwork raster extern lipsă sau neîncorporat. Preview-ul poate fi incomplet. Pentru reproducere completă, exportă SVG cu imagini embedded/base64 sau atașează folderul *_Images.";

export const INTAKE_V4_COREL_LOGO_VECTOR_REFERENCE_MISMATCH =
  "Corel logo reference requires vector outline, but current SVG logo is raster artwork. App cannot compute true vector curve length from raster.";

export const INTAKE_V4_ARTWORK_LOGO_PERIMETER_DIAGNOSTIC_NOTE =
  "diagnostic — exclus din volumetric / CNC / LED / cant";

/** Corel operator reference for Ana Maria logo stroke outline (m). */
export const ANA_MARIA_COREL_LOGO_VECTOR_REFERENCE_M = 4.891;

export interface IntakeV4ArtworkLogoDiagnostic {
  hasRasterArtwork: boolean;
  hasMissingExternalRasterAsset: boolean;
  hasExternalRasterHref: boolean;
  artworkLogoWarnings: string[];
  showCorelReferenceMismatch: boolean;
}

export function buildIntakeV4ArtworkLogoDiagnostic(
  report: SvgAnalysisCoreReport | null | undefined,
  options?: {
    artworkVectorPerimeterDiagnosticM?: number | null;
    artworkPerimeterIsRasterNa?: boolean;
  },
): IntakeV4ArtworkLogoDiagnostic {
  const assessments = report?.artworkComplexity?.assessments ?? [];
  const rasterRows = assessments.filter((row) => row.has_raster_image)
  const hasRasterArtwork = rasterRows.length > 0
  const hasMissingExternalRasterAsset = rasterRows.some(
    (row) => row.missing_external_image_asset,
  )
  const hasExternalRasterHref = rasterRows.some((row) => row.has_external_image)

  const artworkLogoWarnings: string[] = []
  if (hasMissingExternalRasterAsset || hasExternalRasterHref) {
    artworkLogoWarnings.push(INTAKE_V4_LOGO_RASTER_EXTERNAL_MISSING_WARNING)
  }

  const diagnosticM = options?.artworkVectorPerimeterDiagnosticM ?? 0
  const rasterNa = options?.artworkPerimeterIsRasterNa ?? false
  const showCorelReferenceMismatch =
    hasRasterArtwork &&
    rasterNa &&
    (diagnosticM == null || diagnosticM <= 0)

  if (showCorelReferenceMismatch) {
    artworkLogoWarnings.push(INTAKE_V4_COREL_LOGO_VECTOR_REFERENCE_MISMATCH)
  }

  return {
    hasRasterArtwork,
    hasMissingExternalRasterAsset,
    hasExternalRasterHref,
    artworkLogoWarnings,
    showCorelReferenceMismatch,
  }
}

export function formatArtworkComplexityWarning(warning: string): string {
  if (warning === "missing_external_image_asset") {
    return INTAKE_V4_LOGO_RASTER_EXTERNAL_MISSING_WARNING
  }
  if (warning === "raster_image_not_attached_to_production_geometry") {
    return "Imagine raster artwork — nu este atașată la geometrie volumetrică de producție."
  }
  return warning.replace(/_/g, " ")
}
