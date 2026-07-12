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
import { buildOperatorLogoLabelMap, getOperatorLayerLabel } from "@/lib/intakeV6/intakeV4OperatorUiDisplay";
import { stableLayerInstanceKey } from "@/lib/intakeV6/layerInstanceIdentity";
import { normalizeIntakeV4BackingMode, type IntakeV4BackingMode } from "./intakeV4BackingMode";

export type IntakeV4ArtworkPrintTransparency = "standard" | "translucent" | "transparent";

export interface IntakeV4ArtworkFinish {
  layer_key: string;
  layer_name: string;
  display_name?: string | null;
  source_layer_name?: string | null;
  original_detected_label?: string | null;
  position_hint?: string | null;
  execution_type: SvgArtworkExecutionType;
  color_mode: SvgArtworkColorMode;
  print_transparency?: IntakeV4ArtworkPrintTransparency;
  material_code?: string | null;
  face_personalization_method?: "none_raw_plexi" | "oracal" | "print_laminate" | null;
  face_roll_width_mm?: number | null;
  print_roll_width_mm?: number | null;
  lamination_roll_width_mm?: number | null;
  roll_side_retraction_mm?: number | null;
  roll_total_retraction_mm?: number | null;
  face_oracal_code?: string | null;
  face_oracal_name?: string | null;
  print_material_code?: string | null;
  lamination_material_code?: string | null;
  estimated_area_m2?: number | null;
  element_count?: number | null;
  distinct_fill_count?: number | null;
  return_finish_type: string;
  return_oracal_code?: string | null;
  return_oracal_name?: string | null;
  return_depth_mm?: number | null;
  backing_mode?: IntakeV4BackingMode | null;
  confirmed: boolean;
}

const ARTWORK_ROLES = new Set(["printed_artwork", "logo", "policromie"]);

export function normalizeArtworkFinishState(
  row: IntakeV4ArtworkFinish,
): IntakeV4ArtworkFinish {
  if (row.face_personalization_method === "none_raw_plexi") {
    return {
      ...row,
      execution_type: "none_raw_plexi",
      color_mode: "none",
      material_code: null,
      face_oracal_code: null,
      face_oracal_name: null,
      print_material_code: null,
      lamination_material_code: null,
      face_roll_width_mm: null,
      print_roll_width_mm: null,
      lamination_roll_width_mm: null,
      roll_side_retraction_mm: null,
      roll_total_retraction_mm: null,
    };
  }
  if (row.face_personalization_method === "print_laminate") {
    return {
      ...row,
      execution_type: "print_laminate",
      color_mode: "polychrome",
      material_code: "ORAFOL_PRINT_LAMINATION",
      print_material_code: row.print_material_code ?? "ORAFOL_PRINT",
      lamination_material_code: row.lamination_material_code ?? "ORAFOL_LAMINATION",
      face_oracal_code: null,
      face_oracal_name: null,
    };
  }
  if (row.face_personalization_method === "oracal") {
    const materialCode = row.material_code === "ORACAL_641"
      ? "ORACAL_641"
      : row.material_code === "ORACAL_8500" || row.execution_type === "translucent_vinyl"
        ? "ORACAL_8500"
        : "ORACAL_651";
    return {
      ...row,
      execution_type: materialCode === "ORACAL_8500" ? "translucent_vinyl" : "cut_vinyl",
      color_mode: "monochrome",
      material_code: materialCode,
      print_material_code: null,
      lamination_material_code: null,
    };
  }
  return row;
}

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
  const logoLabelMap = buildOperatorLogoLabelMap(report.layers);
  for (const layer of report.layers) {
    const entry = layerEntry(confirmation, layer.id, layer.name);
    if (!entry || entry.confirmationState === "ignored") continue;
    const role = entry.confirmedRole ?? entry.autoRole;
    if (!isArtworkLayer(layer, role)) continue;

    rows.push({
      layer_key: stableLayerInstanceKey({
        layerId: entry.layerId ?? layer.id,
        layerKey: entry.layerKey,
        layerName: layer.name,
      }),
      layer_name: getOperatorLayerLabel(layer.id, layer.name, { logoLabelMap }),
      source_layer_name: layer.name,
      original_detected_label: layer.name,
      position_hint: null,
      execution_type: "print_laminate",
      color_mode: "polychrome",
      print_transparency: "translucent",
      face_personalization_method: "print_laminate",
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
    return normalizeArtworkFinishState({
      ...row,
      execution_type:
        prior.execution_type && prior.execution_type !== "needs_decision"
          ? prior.execution_type
          : row.execution_type,
      display_name: prior.display_name ?? row.display_name,
      source_layer_name: prior.source_layer_name ?? row.source_layer_name,
      original_detected_label: prior.original_detected_label ?? row.original_detected_label,
      position_hint: prior.position_hint ?? row.position_hint,
      color_mode:
        prior.color_mode && prior.color_mode !== "unknown" ? prior.color_mode : row.color_mode,
      print_transparency: prior.print_transparency ?? row.print_transparency,
      material_code: prior.material_code,
      face_personalization_method: prior.face_personalization_method ?? row.face_personalization_method,
      face_roll_width_mm: prior.face_roll_width_mm ?? row.face_roll_width_mm,
      print_roll_width_mm: prior.print_roll_width_mm ?? row.print_roll_width_mm,
      lamination_roll_width_mm: prior.lamination_roll_width_mm ?? row.lamination_roll_width_mm,
      roll_side_retraction_mm: prior.roll_side_retraction_mm ?? row.roll_side_retraction_mm,
      roll_total_retraction_mm: prior.roll_total_retraction_mm ?? row.roll_total_retraction_mm,
      face_oracal_code: prior.face_oracal_code ?? row.face_oracal_code,
      face_oracal_name: prior.face_oracal_name ?? row.face_oracal_name,
      print_material_code: prior.print_material_code ?? row.print_material_code,
      lamination_material_code: prior.lamination_material_code ?? row.lamination_material_code,
      return_finish_type: prior.return_finish_type ?? row.return_finish_type,
      return_oracal_code: prior.return_oracal_code ?? row.return_oracal_code,
      return_oracal_name: prior.return_oracal_name ?? row.return_oracal_name,
      return_depth_mm: prior.return_depth_mm ?? row.return_depth_mm,
      confirmed: prior.confirmed,
    });
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
    .map((item) => normalizeArtworkFinishState({
      layer_key: String(item.layer_key ?? ""),
      layer_name: String(item.layer_name ?? item.layer_key ?? ""),
      display_name: typeof item.display_name === "string" ? item.display_name : null,
      source_layer_name: typeof item.source_layer_name === "string" ? item.source_layer_name : null,
      original_detected_label: typeof item.original_detected_label === "string" ? item.original_detected_label : null,
      position_hint: typeof item.position_hint === "string" ? item.position_hint : null,
      execution_type: (item.execution_type as SvgArtworkExecutionType) ?? "print_laminate",
      color_mode: (item.color_mode as SvgArtworkColorMode) ?? "polychrome",
      print_transparency:
        item.print_transparency === "translucent" ||
        item.print_transparency === "transparent" ||
        item.print_transparency === "standard"
          ? item.print_transparency
          : "standard",
      material_code: typeof item.material_code === "string" ? item.material_code : null,
      face_personalization_method:
        item.face_personalization_method === "none_raw_plexi" ||
        item.face_personalization_method === "oracal" ||
        item.face_personalization_method === "print_laminate"
          ? item.face_personalization_method
          : null,
      face_roll_width_mm: typeof item.face_roll_width_mm === "number" ? item.face_roll_width_mm : null,
      print_roll_width_mm: typeof item.print_roll_width_mm === "number" ? item.print_roll_width_mm : null,
      lamination_roll_width_mm: typeof item.lamination_roll_width_mm === "number" ? item.lamination_roll_width_mm : null,
      roll_side_retraction_mm: typeof item.roll_side_retraction_mm === "number" ? item.roll_side_retraction_mm : null,
      roll_total_retraction_mm: typeof item.roll_total_retraction_mm === "number" ? item.roll_total_retraction_mm : null,
      face_oracal_code: typeof item.face_oracal_code === "string" ? item.face_oracal_code : null,
      face_oracal_name: typeof item.face_oracal_name === "string" ? item.face_oracal_name : null,
      print_material_code: typeof item.print_material_code === "string" ? item.print_material_code : null,
      lamination_material_code: typeof item.lamination_material_code === "string" ? item.lamination_material_code : null,
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
      backing_mode:
        item.backing_mode != null
          ? normalizeIntakeV4BackingMode(item.backing_mode)
          : null,
      confirmed: item.confirmed === true,
    }))
    .filter((row) => row.layer_key.length > 0);
}

export { SVG_ARTWORK_COLOR_MODE_OPTIONS, SVG_ARTWORK_EXECUTION_OPTIONS };
