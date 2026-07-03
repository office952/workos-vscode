import type { LayerAutoRole, LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import type { IntakeV4QuoteGeometry } from "@/lib/intakeV4/intakeV4QuoteGeometry";
import { extractQuoteGeometryFromAnalyzer } from "@/lib/intakeV4/intakeV4QuoteGeometry";
import {
  COREL_ANA_MARIA_REFERENCE,
  compareCorelAnaMariaPerimeters,
  type CorelPerimeterComparison,
} from "./corelAnaMariaReference";

const FACE_ROLES: LayerAutoRole[] = ["face"];
const ARTWORK_ROLES = new Set<string>(["printed_artwork", "logo", "policromie"]);

function roleForLayer(
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

function layerPerimeterM(layer: SvgAnalysisCoreReport["layers"][number]): number {
  if (layer.perimeterMl != null && layer.perimeterMl > 0) return layer.perimeterMl;
  if (layer.perimeterMm != null && layer.perimeterMm > 0) return layer.perimeterMm / 1000;
  return 0;
}

export interface AnaMariaPerimeterDiagnostic {
  fileName: string;
  widthMm: number | null;
  heightMm: number | null;
  layerCount: number;
  productionGeometryLayerCount: number;
  artworkLayerCount: number;
  layerSummaries: Array<{
    id: string;
    name: string;
    role: string | null;
    layerKind: string | null;
    perimeterM: number;
  }>;
  childPartsCount: number | null;
  realLettersCount: number | null;
  corelReference: typeof COREL_ANA_MARIA_REFERENCE;
  applicationMetrics: {
    volumetricLettersPerimeterM: number | null;
    artworkLogoPerimeterM: number | null;
    totalVectorPerimeterM: number | null;
    cncFacePerimeterM: number | null;
    ledExteriorPerimeterM: number | null;
    returnMaterialPerimeterM: number | null;
    geometrySource: string;
  };
  comparison: CorelPerimeterComparison;
}

export function buildAnaMariaPerimeterDiagnostic(
  report: SvgAnalysisCoreReport,
  confirmation: LayerRoleConfirmation | null | undefined,
  fileName = "ana-maria-gradinita-fara-layere.svg",
): AnaMariaPerimeterDiagnostic {
  let volumetricLettersPerimeterM = 0;
  let artworkLogoPerimeterM = 0;
  let productionGeometryLayerCount = 0;
  let artworkLayerCount = 0;

  const layerSummaries: AnaMariaPerimeterDiagnostic["layerSummaries"] = [];

  for (const layer of report.layers) {
    const role = roleForLayer(confirmation, layer.id, layer.name);
    const perimeterM = layerPerimeterM(layer);
    layerSummaries.push({
      id: layer.id,
      name: layer.name,
      role: role ?? layer.autoRole ?? null,
      layerKind: layer.layerKind ?? null,
      perimeterM,
    });

    if (role != null && ARTWORK_ROLES.has(role)) {
      artworkLayerCount += 1;
      artworkLogoPerimeterM += perimeterM;
      continue;
    }
    if (role != null && FACE_ROLES.includes(role)) {
      productionGeometryLayerCount += 1;
      volumetricLettersPerimeterM += perimeterM;
    }
  }

  const docPerimeterM =
    report.geometry.perimeterMl ??
    (report.geometry.perimeterMm != null ? report.geometry.perimeterMm / 1000 : null);

  const quote: IntakeV4QuoteGeometry = extractQuoteGeometryFromAnalyzer(report, confirmation);

  const volumetricLetters =
    volumetricLettersPerimeterM > 0 ? volumetricLettersPerimeterM : quote.letter_perimeter_m;
  const artworkLogo =
    artworkLogoPerimeterM > 0 ? artworkLogoPerimeterM : quote.artwork_return_perimeter_ml;

  const comparison = compareCorelAnaMariaPerimeters({
    volumetricLettersPerimeterM: volumetricLetters,
    artworkLogoPerimeterM: artworkLogo > 0 ? artworkLogo : null,
    totalVectorPerimeterM: docPerimeterM,
    ledExteriorPerimeterM: quote.led_perimeter_ml ?? quote.letter_perimeter_m,
    cncFacePerimeterM: quote.face_cutting_perimeter_ml ?? quote.cutting_perimeter_ml,
    geometrySource: quote.geometry_source,
    productionGeometryLayerCount,
    artworkLayerCount,
  });

  return {
    fileName,
    widthMm: report.document.widthMm,
    heightMm: report.document.heightMm,
    layerCount: report.layers.length,
    productionGeometryLayerCount,
    artworkLayerCount,
    layerSummaries,
    childPartsCount: report.parts?.count ?? null,
    realLettersCount: quote.real_letters_count ?? quote.letter_count,
    corelReference: COREL_ANA_MARIA_REFERENCE,
    applicationMetrics: {
      volumetricLettersPerimeterM: volumetricLetters,
      artworkLogoPerimeterM: artworkLogo > 0 ? artworkLogo : null,
      totalVectorPerimeterM: docPerimeterM,
      cncFacePerimeterM: quote.face_cutting_perimeter_ml ?? quote.cutting_perimeter_ml,
      ledExteriorPerimeterM: quote.led_perimeter_ml ?? quote.letter_perimeter_m,
      returnMaterialPerimeterM: quote.return_material_perimeter_ml,
      geometrySource: quote.geometry_source,
    },
    comparison,
  };
}
