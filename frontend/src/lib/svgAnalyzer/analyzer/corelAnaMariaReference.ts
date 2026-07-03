/** CorelDRAW curve-length reference for Ana Maria Grădiniță (owner measurement). */
export const COREL_ANA_MARIA_REFERENCE = {
  volumetricLettersPerimeterM: 26.747203,
  logoPerimeterM: 4.89101,
  totalPerimeterM: 31.638213,
  tolerancePercent: 5,
  warningTolerancePercent: 10,
} as const;

export type CorelPerimeterMismatchReason =
  | "unit_conversion_mismatch"
  | "corel_cm_to_mm_mapping_error"
  | "pseudo_layer_grouping_mismatch"
  | "production_geometry_missing"
  | "logo_excluded_as_artwork"
  | "artwork_included_in_production_geometry"
  | "subpaths_included_by_corel_excluded_by_app"
  | "corel_curve_length_includes_internal_paths"
  | "app_uses_exterior_perimeter_only"
  | "app_uses_cnc_perimeter_not_total_curve_length"
  | "raster_or_clippath_ignored"
  | "path_flattening_tolerance_difference"
  | "logo_perimeter_not_computed_for_raster_artwork";

export interface CorelPerimeterComparison {
  lettersDeltaPercent: number | null;
  logoDeltaPercent: number | null;
  totalDeltaPercent: number | null;
  passApproximate: boolean;
  passWithWarning: boolean;
  reasonIfMismatch: CorelPerimeterMismatchReason[];
  operatorMessage: string | null;
}

export function deltaPercent(
  applicationM: number | null | undefined,
  referenceM: number,
): number | null {
  if (applicationM == null || !Number.isFinite(applicationM) || applicationM <= 0) return null;
  return ((applicationM - referenceM) / referenceM) * 100;
}

export function withinTolerance(
  deltaPercent: number | null,
  tolerancePercent: number,
): boolean {
  if (deltaPercent == null) return false;
  return Math.abs(deltaPercent) <= tolerancePercent;
}

export function compareCorelAnaMariaPerimeters(args: {
  volumetricLettersPerimeterM: number | null;
  artworkLogoPerimeterM: number | null;
  totalVectorPerimeterM: number | null;
  ledExteriorPerimeterM: number | null;
  cncFacePerimeterM: number | null;
  geometrySource: string;
  productionGeometryLayerCount: number;
  artworkLayerCount: number;
}): CorelPerimeterComparison {
  const ref = COREL_ANA_MARIA_REFERENCE;
  const lettersDelta = deltaPercent(args.volumetricLettersPerimeterM, ref.volumetricLettersPerimeterM);
  const logoDelta =
    args.artworkLogoPerimeterM != null && args.artworkLogoPerimeterM > 0
      ? deltaPercent(args.artworkLogoPerimeterM, ref.logoPerimeterM)
      : null;
  const totalDelta =
    args.totalVectorPerimeterM != null && args.totalVectorPerimeterM > 0
      ? deltaPercent(args.totalVectorPerimeterM, ref.totalPerimeterM)
      : null;

  const reasons: CorelPerimeterMismatchReason[] = [];

  if (args.productionGeometryLayerCount < 4) {
    reasons.push("pseudo_layer_grouping_mismatch");
  }
  if (args.volumetricLettersPerimeterM == null || args.volumetricLettersPerimeterM <= 0) {
    reasons.push("production_geometry_missing");
  }
  if (args.artworkLogoPerimeterM == null || args.artworkLogoPerimeterM <= 0) {
    reasons.push("logo_excluded_as_artwork");
    reasons.push("logo_perimeter_not_computed_for_raster_artwork");
    reasons.push("raster_or_clippath_ignored");
  }
  if (
    args.ledExteriorPerimeterM != null &&
    args.volumetricLettersPerimeterM != null &&
    Math.abs(args.ledExteriorPerimeterM - args.volumetricLettersPerimeterM) < 0.01
  ) {
    reasons.push("app_uses_exterior_perimeter_only");
  }
  if (
    args.cncFacePerimeterM != null &&
    args.volumetricLettersPerimeterM != null &&
    args.cncFacePerimeterM > args.volumetricLettersPerimeterM + 0.5
  ) {
    reasons.push("app_uses_cnc_perimeter_not_total_curve_length");
    reasons.push("corel_curve_length_includes_internal_paths");
  }
  if (lettersDelta != null && Math.abs(lettersDelta) > ref.tolerancePercent) {
    reasons.push("subpaths_included_by_corel_excluded_by_app");
    reasons.push("path_flattening_tolerance_difference");
  }

  const lettersPass = withinTolerance(lettersDelta, ref.tolerancePercent);
  const lettersWarning =
    lettersDelta != null && Math.abs(lettersDelta) <= ref.warningTolerancePercent;
  const logoComparable = logoDelta != null;
  const logoPass = logoComparable
    ? withinTolerance(logoDelta, ref.tolerancePercent)
    : true;

  const passApproximate = lettersPass && logoPass;
  const passWithWarning = passApproximate || (lettersWarning && !logoComparable);

  let operatorMessage: string | null = null;
  if (!passApproximate) {
    const appLetters = args.volumetricLettersPerimeterM?.toFixed(2) ?? "—";
    const corelLetters = ref.volumetricLettersPerimeterM.toFixed(3);
    const deltaStr = lettersDelta != null ? `${lettersDelta.toFixed(1)}%` : "n/a";
    operatorMessage = `Corel măsoară ${corelLetters} m pentru litere volumetrice. Aplicația raportează ${appLetters} m. Diferență ${deltaStr}.`;
    if (reasons.includes("app_uses_exterior_perimeter_only")) {
      operatorMessage +=
        " Cauză probabilă: aplicația folosește contur exterior (LED), iar Corel include sub-paths în lungimea curbei selectată.";
    }
    if (reasons.includes("logo_perimeter_not_computed_for_raster_artwork")) {
      operatorMessage +=
        " Logo perimeter not compared because logo layers are classified as printed_artwork and excluded from volumetric vector perimeter.";
    }
  }

  return {
    lettersDeltaPercent: lettersDelta,
    logoDeltaPercent: logoDelta,
    totalDeltaPercent: totalDelta,
    passApproximate,
    passWithWarning,
    reasonIfMismatch: [...new Set(reasons)],
    operatorMessage,
  };
}
