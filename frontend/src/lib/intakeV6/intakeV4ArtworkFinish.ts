import type { LayerRoleConfirmation, SvgAnalysisCoreReport, SvgAnalysisLayer } from "@/lib/svgAnalyzer";
import { isArtworkLayerName } from "@/lib/intakeSvgContracts";
import { layerHasLetterPathGeometry, layerIsArtworkCandidate } from "./intakeV6ArtworkOnlyGuard";
import type {
  SvgArtworkColorMode,
  SvgArtworkExecutionType,
} from "@/lib/svgArtworkContracts";
import {
  SVG_ARTWORK_COLOR_MODE_OPTIONS,
  SVG_ARTWORK_EXECUTION_OPTIONS,
} from "@/lib/svgArtworkContracts";
import { INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE } from "@/lib/intakeV6/intakeV6ReturnFinishOptions";
import { getOperatorLayerLabel } from "@/lib/intakeV6/intakeV4OperatorUiDisplay";

export type IntakeV4ArtworkPrintTransparency = "standard" | "translucent" | "transparent";

export interface IntakeV4ArtworkFinish {
  layer_key: string;
  layer_name: string;
  execution_type: SvgArtworkExecutionType;
  color_mode: SvgArtworkColorMode;
  print_transparency?: IntakeV4ArtworkPrintTransparency;
  material_code?: string | null;
  estimated_area_m2?: number | null;
  element_count?: number | null;
  distinct_fill_count?: number | null;
  return_finish_type: string;
  return_oracal_code?: string | null;
  return_oracal_name?: string | null;
  return_depth_mm?: number | null;
  confirmed: boolean;
}

const ARTWORK_ROLES = new Set(["printed_artwork", "logo", "policromie"]);

function layerEntry(
  confirmation: LayerRoleConfirmation,
  layerId: string,
  layerName: string,
) {
  return (
    confirmation.layers.find((item) => item.layerKey === layerId || item.layerKey === layerName) ??
    confirmation.layers.find((item) => item.layerName === layerName)
  );
}

function isArtworkLayer(
  layer: SvgAnalysisLayer,
  role: string | null | undefined,
): boolean {
  if (role && ARTWORK_ROLES.has(role)) return true;
  if (isArtworkLayerName(layer.name) || isArtworkLayerName(layer.id)) return true;
  if (!layerHasLetterPathGeometry(layer) && layerIsArtworkCandidate(layer)) return true;
  return false;
}

function layerAreaM2(layer: SvgAnalysisLayer): number | null {
  const area = layer.filledAreaSqm ?? layer.boundingAreaSqm;
  return area != null && area > 0 ? area : null;
}

export function deriveArtworkFinishesFromAnalyzer(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
  defaultReturnDepthMm = 60,
): IntakeV4ArtworkFinish[] {
  if (!report || !confirmation) return [];

  const rows: IntakeV4ArtworkFinish[] = [];
  for (const layer of report.layers) {
    const entry = layerEntry(confirmation, layer.id, layer.name);
    if (!entry || entry.confirmationState === "ignored") continue;
    const role = entry.confirmedRole ?? entry.autoRole;
    if (!isArtworkLayer(layer, role)) continue;

    rows.push({
      layer_key: entry.layerKey,
      layer_name: getOperatorLayerLabel(layer.id, layer.name),
      execution_type: "print_laminate",
      color_mode: "polychrome",
      print_transparency: "translucent",
      estimated_area_m2: layerAreaM2(layer),
      element_count: layer.elementCount,
      distinct_fill_count: layer.colors?.length ?? null,
      return_finish_type: INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE,
      return_depth_mm: defaultReturnDepthMm,
      confirmed: false,
    });
  }
  return rows;
}

export function mergeArtworkFinishes(
  derived: IntakeV4ArtworkFinish[],
  saved: IntakeV4ArtworkFinish[] | undefined,
): IntakeV4ArtworkFinish[] {
  if (!saved?.length) return derived;
  const byKey = new Map(saved.map((row) => [row.layer_key, row]));
  return derived.map((row) => {
    const prior = byKey.get(row.layer_key);
    if (!prior) return row;
    return {
      ...row,
      execution_type:
        prior.execution_type && prior.execution_type !== "needs_decision"
          ? prior.execution_type
          : row.execution_type,
      color_mode:
        prior.color_mode && prior.color_mode !== "unknown" ? prior.color_mode : row.color_mode,
      print_transparency: prior.print_transparency ?? row.print_transparency,
      material_code: prior.material_code,
      return_finish_type: prior.return_finish_type ?? row.return_finish_type,
      return_oracal_code: prior.return_oracal_code ?? row.return_oracal_code,
      return_oracal_name: prior.return_oracal_name ?? row.return_oracal_name,
      return_depth_mm: prior.return_depth_mm ?? row.return_depth_mm,
      confirmed: prior.confirmed,
    };
  });
}

export function artworkFinishesFromPayload(
  payload: Record<string, unknown> | undefined,
): IntakeV4ArtworkFinish[] {
  const finish = payload?.finish_setup;
  if (finish == null || typeof finish !== "object" || Array.isArray(finish)) return [];
  const raw = (finish as Record<string, unknown>).artwork_finishes;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((item): item is Record<string, unknown> => item != null && typeof item === "object")
    .map((item) => ({
      layer_key: String(item.layer_key ?? ""),
      layer_name: String(item.layer_name ?? item.layer_key ?? ""),
      execution_type: (item.execution_type as SvgArtworkExecutionType) ?? "print_laminate",
      color_mode: (item.color_mode as SvgArtworkColorMode) ?? "polychrome",
      print_transparency:
        item.print_transparency === "translucent" ||
        item.print_transparency === "transparent" ||
        item.print_transparency === "standard"
          ? item.print_transparency
          : "standard",
      material_code: typeof item.material_code === "string" ? item.material_code : null,
      estimated_area_m2:
        typeof item.estimated_area_m2 === "number" ? item.estimated_area_m2 : null,
      element_count: typeof item.element_count === "number" ? item.element_count : null,
      distinct_fill_count:
        typeof item.distinct_fill_count === "number" ? item.distinct_fill_count : null,
      return_finish_type:
        typeof item.return_finish_type === "string"
          ? item.return_finish_type
          : INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE,
      return_oracal_code:
        typeof item.return_oracal_code === "string" ? item.return_oracal_code : null,
      return_oracal_name:
        typeof item.return_oracal_name === "string" ? item.return_oracal_name : null,
      return_depth_mm: typeof item.return_depth_mm === "number" ? item.return_depth_mm : null,
      confirmed: item.confirmed === true,
    }))
    .filter((row) => row.layer_key.length > 0);
}

export { SVG_ARTWORK_COLOR_MODE_OPTIONS, SVG_ARTWORK_EXECUTION_OPTIONS };
