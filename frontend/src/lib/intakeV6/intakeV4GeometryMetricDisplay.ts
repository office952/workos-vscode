/**
 * Read-only operator-facing geometry metric labels — does not alter geometry algorithms.
 */

import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import {
  buildIntakeV4ArtworkLogoDiagnostic,
  INTAKE_V4_ARTWORK_LOGO_PERIMETER_DIAGNOSTIC_NOTE,
} from "./intakeV4ArtworkLogoDiagnostic";
import type { IntakeV4QuoteGeometry } from "./intakeV4QuoteGeometry";
import {
  formatIntakeV6ReturnFinishLabel as formatIntakeV4ReturnFinishLabel,
  INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE as INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE,
} from "./intakeV6ReturnFinishOptions";
import type { IntakeV4LetterGroupFinish } from "./intakeV4LetterGroups";
import { sumActiveLetterGroupCantPerimeterM } from "./intakeV4LetterGroups";

export { INTAKE_V4_ARTWORK_LOGO_PERIMETER_DIAGNOSTIC_NOTE };

const FACE_ROLES: LayerAutoRole[] = ["face"];
const ARTWORK_ROLES = new Set<string>(["printed_artwork", "logo", "policromie"]);
const VOLUMETRIC_TEMPLATE = "TPL-VOLUMETRIC-LETTERS";
const DEFAULT_RETURN_DEPTH_MM = 60;

export const INTAKE_V4_TEXT_CHARACTERS_NA_REASON =
  "n/a — textul este convertit în curbe; aplicația numără piese de producție.";

export const INTAKE_V4_ANALYSIS_BUNDLE_PENDING_MESSAGE =
  "Material Breakdown nu este complet încă. Salvează Review/Setări pentru a persista analysis-bundle și a calcula cant, Oracal, CNC și print/laminare.";

export const INTAKE_V4_CANT_PENDING_MESSAGE =
  "Cant / volum: pending — salvează Review/Setări pentru analysis-bundle și finisaje.";

export type IntakeV4CantPerimeterSource = "outer_only" | "outer_plus_inner" | "pending";

export interface IntakeV4GeometryMetricDisplay {
  volumetricGroupCount: number | null;
  productionPartCount: number | null;
  artworkLayerCount: number | null;
  estimatedCharacterCount: null;
  estimatedCharacterCountReason: string;
  corelComparableCurveLengthM: number | null;
  artworkLogoVectorPerimeterM: number | null;
  fullVectorPerimeterM: number | null;
  ledExteriorPerimeterM: number | null;
  cncFacePerimeterM: number | null;
  cantReturnPerimeterM: number | null;
  artworkVectorPerimeterM: number | null;
  artworkVectorPerimeterDiagnosticM: number | null;
  artworkPerimeterIsDiagnostic: boolean;
  artworkPerimeterIsRasterNa: boolean;
  artworkLogoWarnings: string[];
  cantReturnDepthMm: number | null;
  cantReturnFinishLabel: string | null;
  cantPerimeterSource: IntakeV4CantPerimeterSource;
  cantPricingPending: boolean;
  cantPendingReason: string | null;
  analysisBundlePending: boolean;
  showCantSection: boolean;
  hasSoareEmblemNote: boolean;
}

function confirmedRoleForLayer(
  confirmation: LayerRoleConfirmation | null | undefined,
  layerId: string,
  layerName: string,
): LayerAutoRole | null {
  if (!confirmation) return null;
  const entry =
    confirmation.layers.find((item) => item.layerKey === layerId || item.layerKey === layerName) ??
    confirmation.layers.find((item) => item.layerName === layerName || item.layerId === layerId);
  if (!entry || entry.confirmationState === "ignored") return null;
  return entry.confirmedRole ?? entry.autoRole ?? null;
}

function effectiveRole(
  layer: SvgAnalysisCoreReport["layers"][number],
  confirmation: LayerRoleConfirmation | null | undefined,
): LayerAutoRole {
  return confirmedRoleForLayer(confirmation, layer.id, layer.name) ?? layer.autoRole;
}

function layerPerimeterM(layer: SvgAnalysisCoreReport["layers"][number]): number {
  if (layer.perimeterMl != null && layer.perimeterMl > 0) return layer.perimeterMl;
  if (layer.perimeterMm != null && layer.perimeterMm > 0) return layer.perimeterMm / 1000;
  return 0;
}

function readFinishSetup(payload: Record<string, unknown> | undefined): Record<string, unknown> {
  const finish = payload?.finish_setup;
  if (finish != null && typeof finish === "object" && !Array.isArray(finish)) {
    return finish as Record<string, unknown>;
  }
  return {};
}

function hasPersistedLetterGroupFinishes(finishSetup: Record<string, unknown>): boolean {
  const groups = finishSetup.letter_group_finishes;
  return Array.isArray(groups) && groups.length > 0;
}

export function buildIntakeV4GeometryMetricDisplay(args: {
  report: SvgAnalysisCoreReport | null | undefined;
  confirmation: LayerRoleConfirmation | null | undefined;
  geometry: IntakeV4QuoteGeometry;
  payload?: Record<string, unknown> | undefined;
  finishSetup?: Record<string, unknown> | null;
  analysisBundleReady?: boolean;
  templateCode?: string | null;
}): IntakeV4GeometryMetricDisplay {
  const finishSetup = args.finishSetup ?? readFinishSetup(args.payload);
  const analysisBundlePending = args.analysisBundleReady === false;
  const templateCode = args.templateCode ?? null;
  const isVolumetricTemplate = templateCode == null || templateCode === VOLUMETRIC_TEMPLATE;

  let volumetricGroupCount = 0;
  let artworkLayerCount = 0;
  let corelComparableCurveLengthM = 0;
  let artworkVectorPerimeterM = 0;
  let artworkVectorPerimeterDiagnosticM = 0;
  let rasterArtworkCount = 0;
  let vectorArtworkWithPerimeter = 0;
  let rasterArtworkWithOutlinePerimeter = 0;
  let hasSoareEmblemNote = false;

  if (args.report) {
    for (const layer of args.report.layers) {
      const role = effectiveRole(layer, args.confirmation);
      const perimeterM = layerPerimeterM(layer);

      if (FACE_ROLES.includes(role)) {
        volumetricGroupCount += 1;
        corelComparableCurveLengthM += perimeterM;
        if (/soare/i.test(layer.name)) {
          hasSoareEmblemNote = true;
        }
      }

      if (ARTWORK_ROLES.has(role)) {
        artworkLayerCount += 1;
        const isRasterLayer = layer.layerKind === "raster_artwork";
        if (isRasterLayer) {
          rasterArtworkCount += 1;
          if (perimeterM > 0) {
            rasterArtworkWithOutlinePerimeter += 1;
            artworkVectorPerimeterDiagnosticM += perimeterM;
          }
        } else if (perimeterM > 0) {
          vectorArtworkWithPerimeter += 1;
          artworkVectorPerimeterM += perimeterM;
        } else {
          rasterArtworkCount += 1;
        }
      }
    }
  }

  const ledExteriorPerimeterM =
    args.geometry.led_perimeter_ml ?? args.geometry.letter_perimeter_m ?? null;
  const cncFacePerimeterM =
    args.geometry.cutting_perimeter_ml ?? args.geometry.face_cutting_perimeter_ml ?? null;
  const cantReturnPerimeterM =
    args.geometry.return_material_perimeter_ml ?? args.geometry.letter_return_perimeter_ml ?? null;
  const letterReturnMl = args.geometry.letter_return_perimeter_ml;
  const holePerimeterMl = args.geometry.hole_perimeter_ml;

  let cantPerimeterSource: IntakeV4CantPerimeterSource = "pending";
  if (ledExteriorPerimeterM != null && ledExteriorPerimeterM > 0) {
    if (
      letterReturnMl != null &&
      holePerimeterMl != null &&
      holePerimeterMl > 0 &&
      letterReturnMl > ledExteriorPerimeterM + 0.001
    ) {
      cantPerimeterSource = "outer_plus_inner";
    } else if (cantReturnPerimeterM != null && cantReturnPerimeterM > ledExteriorPerimeterM + 0.001) {
      cantPerimeterSource = "outer_plus_inner";
    } else {
      cantPerimeterSource = "outer_only";
    }
  }

  const returnDepthRaw = finishSetup.return_depth_mm;
  const cantReturnDepthMm =
    typeof returnDepthRaw === "number" && Number.isFinite(returnDepthRaw) && returnDepthRaw > 0
      ? returnDepthRaw
      : DEFAULT_RETURN_DEPTH_MM;

  const returnFinishToken =
    typeof finishSetup.return_finish_type === "string" && finishSetup.return_finish_type.trim()
      ? finishSetup.return_finish_type
      : INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE;

  const cantReturnFinishLabel = formatIntakeV4ReturnFinishLabel({
    finishType: returnFinishToken,
  });

  const finishSaved = hasPersistedLetterGroupFinishes(finishSetup);
  const cantPricingPending = analysisBundlePending || !finishSaved;
  const cantPendingReason = cantPricingPending
    ? analysisBundlePending
      ? INTAKE_V4_CANT_PENDING_MESSAGE
      : "Cant / volum: pending — salvează finisajele Review pentru perimetru outer + interioare."
    : null;

  const showCantSection =
    isVolumetricTemplate && volumetricGroupCount > 0 && (args.geometry.confirmed || volumetricGroupCount > 0);

  const artworkPerimeterIsDiagnostic = rasterArtworkWithOutlinePerimeter > 0;
  const hasAnyArtworkPerimeter =
    artworkVectorPerimeterM > 0 || artworkVectorPerimeterDiagnosticM > 0;
  const artworkPerimeterIsRasterNa =
    artworkLayerCount > 0 && !hasAnyArtworkPerimeter && rasterArtworkCount > 0;

  const logoDiagnostic = buildIntakeV4ArtworkLogoDiagnostic(args.report, {
    artworkVectorPerimeterDiagnosticM:
      artworkVectorPerimeterDiagnosticM > 0 ? artworkVectorPerimeterDiagnosticM : null,
    artworkPerimeterIsRasterNa,
  });

  const roundedProductionM =
    corelComparableCurveLengthM > 0 ? Math.round(corelComparableCurveLengthM * 1000) / 1000 : null;
  const artworkLogoVectorPerimeterRaw =
    artworkVectorPerimeterM > 0
      ? artworkVectorPerimeterM
      : artworkVectorPerimeterDiagnosticM > 0 && !artworkPerimeterIsRasterNa
        ? artworkVectorPerimeterDiagnosticM
        : 0;
  const roundedArtworkLogoVectorM =
    artworkLogoVectorPerimeterRaw > 0
      ? Math.round(artworkLogoVectorPerimeterRaw * 1000) / 1000
      : null;
  const fullVectorRaw = (roundedProductionM ?? 0) + (roundedArtworkLogoVectorM ?? 0);
  const fullVectorPerimeterM =
    fullVectorRaw > 0 ? Math.round(fullVectorRaw * 1000) / 1000 : null;

  return {
    volumetricGroupCount: volumetricGroupCount > 0 ? volumetricGroupCount : null,
    productionPartCount:
      args.geometry.real_letters_count ?? args.geometry.material_piece_count ?? args.geometry.letter_count,
    artworkLayerCount: artworkLayerCount > 0 ? artworkLayerCount : null,
    estimatedCharacterCount: null,
    estimatedCharacterCountReason: INTAKE_V4_TEXT_CHARACTERS_NA_REASON,
    corelComparableCurveLengthM: roundedProductionM,
    artworkLogoVectorPerimeterM: roundedArtworkLogoVectorM,
    fullVectorPerimeterM,
    ledExteriorPerimeterM,
    cncFacePerimeterM,
    cantReturnPerimeterM,
    artworkVectorPerimeterM: artworkVectorPerimeterM > 0 ? artworkVectorPerimeterM : null,
    artworkVectorPerimeterDiagnosticM:
      artworkVectorPerimeterDiagnosticM > 0 ? artworkVectorPerimeterDiagnosticM : null,
    artworkPerimeterIsDiagnostic,
    artworkPerimeterIsRasterNa,
    artworkLogoWarnings: logoDiagnostic.artworkLogoWarnings,
    cantReturnDepthMm,
    cantReturnFinishLabel,
    cantPerimeterSource,
    cantPricingPending,
    cantPendingReason,
    analysisBundlePending,
    showCantSection,
    hasSoareEmblemNote,
  };
}

export function getFullVectorPerimeterM(metrics: IntakeV4GeometryMetricDisplay): number | null {
  return metrics.fullVectorPerimeterM;
}

export interface IntakeV4OperatorCantPerimeterDisplay {
  /** Operator card — full face vector + emblemă cu cant activ. */
  displayM: number | null;
  letterVectorPerimeterM: number | null;
  artworkVectorPerimeterM: number | null;
  quoteGeometryCantM: number | null;
  ledExteriorPerimeterM: number | null;
  fullVectorPerimeterM: number | null;
}

function artworkCantPerimeterActive(
  artworkFinishes: Array<{ return_finish_type?: string | null }> | undefined,
): boolean {
  if (!artworkFinishes?.length) return false;
  const inactive = new Set(["", "none", "no_return", "without_return"]);
  return artworkFinishes.some((row) => {
    const token = String(row.return_finish_type ?? "").trim().toLowerCase();
    return !inactive.has(token);
  });
}

export function resolveIntakeV4OperatorCantPerimeterDisplay(args: {
  geometryMetrics: IntakeV4GeometryMetricDisplay;
  geometry: IntakeV4QuoteGeometry;
  letterGroups: IntakeV4LetterGroupFinish[];
  artworkFinishes?: Array<{ return_finish_type?: string | null }>;
}): IntakeV4OperatorCantPerimeterDisplay {
  const letterVectorM =
    sumActiveLetterGroupCantPerimeterM(args.letterGroups) ??
    (args.geometryMetrics.corelComparableCurveLengthM != null &&
    args.geometryMetrics.corelComparableCurveLengthM > 0
      ? args.geometryMetrics.corelComparableCurveLengthM
      : null);

  let artworkVectorM = args.geometry.artwork_return_perimeter_ml ?? null;
  if (
    artworkVectorM == null &&
    artworkCantPerimeterActive(args.artworkFinishes) &&
    args.geometryMetrics.artworkLogoVectorPerimeterM != null &&
    args.geometryMetrics.artworkLogoVectorPerimeterM > 0
  ) {
    artworkVectorM = args.geometryMetrics.artworkLogoVectorPerimeterM;
  }

  const vectorTotalM =
    letterVectorM != null
      ? Math.round((letterVectorM + (artworkVectorM ?? 0)) * 1000) / 1000
      : null;

  const quoteGeometryCantM = args.geometryMetrics.cantReturnPerimeterM;
  const displayCandidates = [quoteGeometryCantM, vectorTotalM, args.geometryMetrics.fullVectorPerimeterM]
    .filter((value): value is number => value != null && Number.isFinite(value) && value > 0);
  const displayM =
    displayCandidates.length > 0 ? Math.round(Math.max(...displayCandidates) * 1000) / 1000 : null;

  return {
    displayM,
    letterVectorPerimeterM: letterVectorM,
    artworkVectorPerimeterM: artworkVectorM,
    quoteGeometryCantM,
    ledExteriorPerimeterM: args.geometryMetrics.ledExteriorPerimeterM,
    fullVectorPerimeterM: args.geometryMetrics.fullVectorPerimeterM,
  };
}

export function isIntakeV4MaterialBreakdownEffectivelyEmpty(
  breakdown: {
    material_rows?: unknown[];
    consumable_rows?: unknown[];
    operation_rows?: unknown[];
    edge_cant_operation_rows?: unknown[];
  } | null,
): boolean {
  if (!breakdown) return true;
  const materialCount = breakdown.material_rows?.length ?? 0;
  const consumableCount = breakdown.consumable_rows?.length ?? 0;
  const operationCount = breakdown.operation_rows?.length ?? 0;
  const edgeCantCount = breakdown.edge_cant_operation_rows?.length ?? 0;
  return materialCount + consumableCount + operationCount + edgeCantCount === 0;
}
