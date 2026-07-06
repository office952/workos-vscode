import type { LayerRoleConfirmation, SvgAnalysisCoreReport, SvgAnalysisLayer } from "@/lib/svgAnalyzer";
import { ALLOWED_RETURN_DEPTH_MM } from "@/lib/volumetricQuoteInput";
import { normalizeFaceVinylRollWidthMm } from "./intakeV4FaceFinishOptions";
import { applyNearestOracal651ToLetterGroup } from "./intakeV4NearestOracalColor";
import { INTAKE_V6_DEFAULT_RETURN_FINISH_TYPE as INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE } from "./intakeV6ReturnFinishOptions";
import { layerHasLetterPathGeometry } from "./intakeV6ArtworkOnlyGuard";

export { ALLOWED_RETURN_DEPTH_MM };

export interface IntakeV4LetterGroupFinish {
  group_key: string;
  layer_name: string;
  source_fill_color?: string | null;
  face_area_m2?: number | null;
  perimeter_m?: number | null;
  element_count?: number | null;
  face_finish_type: string;
  face_oracal_code?: string | null;
  face_oracal_name?: string | null;
  return_finish_type: string;
  return_oracal_code?: string | null;
  return_oracal_name?: string | null;
  return_depth_mm?: number | null;
  face_vinyl_roll_width_mm?: number | null;
  confirmed: boolean;
}

export const DEFAULT_RETURN_DEPTH_MM = 60;

// Transitional compatibility alias until all V6 imports stop referring to the V4 export name.
export const INTAKE_V4_DEFAULT_RETURN_DEPTH_MM = DEFAULT_RETURN_DEPTH_MM;

function layerMetrics(layer: SvgAnalysisLayer) {
  const perimeterM =
    layer.perimeterMl ?? (layer.perimeterMm != null ? layer.perimeterMm / 1000 : null);
  const area = layer.filledAreaSqm ?? layer.boundingAreaSqm;
  return {
    perimeter_m: perimeterM != null && perimeterM > 0 ? perimeterM : null,
    face_area_m2: area != null && area > 0 ? area : null,
    element_count: layer.elementCount > 0 ? layer.elementCount : null,
    source_fill_color: layer.colors?.[0] ?? null,
  };
}

export function normalizeLetterGroupFaceRollWidth<T extends IntakeV4LetterGroupFinish>(group: T): T {
  return {
    ...group,
    face_vinyl_roll_width_mm: normalizeFaceVinylRollWidthMm(
      group.face_finish_type,
      group.face_vinyl_roll_width_mm,
    ),
  };
}

export function deriveLetterGroupsFromAnalyzer(
  report: SvgAnalysisCoreReport | null | undefined,
  confirmation: LayerRoleConfirmation | null | undefined,
  defaultReturnDepthMm = DEFAULT_RETURN_DEPTH_MM,
): IntakeV4LetterGroupFinish[] {
  if (!report || !confirmation) return [];

  const groups: IntakeV4LetterGroupFinish[] = [];

  for (const layer of report.layers) {
    const entry =
      confirmation.layers.find((item) => item.layerKey === layer.id || item.layerKey === layer.name) ??
      confirmation.layers.find((item) => item.layerName === layer.name);
    if (!entry || entry.confirmationState === "ignored") continue;

    const role = entry.confirmedRole ?? entry.autoRole;
    if (role !== "face") continue;

    const reportLayer =
      report.layers.find((item) => item.id === layer.id || item.name === layer.name) ?? layer;
    if (!layerHasLetterPathGeometry(reportLayer)) continue;

    groups.push(
      normalizeLetterGroupFaceRollWidth(applyNearestOracal651ToLetterGroup({
        group_key: entry.layerKey,
        layer_name: layer.name,
        ...layerMetrics(layer),
        face_finish_type: "none",
        return_finish_type: INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE,
        return_depth_mm: defaultReturnDepthMm,
        confirmed: false,
      })),
    );
  }

  return groups;
}

export function mergeLetterGroupFinishes(
  derived: IntakeV4LetterGroupFinish[],
  saved: IntakeV4LetterGroupFinish[] | undefined,
): IntakeV4LetterGroupFinish[] {
  if (!saved?.length) return derived;
  const savedByKey = new Map(saved.map((item) => [item.group_key, item]));
  return derived.map((item) => {
    const prior = savedByKey.get(item.group_key);
    const sameSourceFill =
      !prior ||
      (prior.source_fill_color != null &&
        item.source_fill_color != null &&
        prior.source_fill_color.trim().toLowerCase() === item.source_fill_color.trim().toLowerCase());
    const merged = prior
      ? {
          ...item,
          face_finish_type: sameSourceFill ? prior.face_finish_type ?? item.face_finish_type : item.face_finish_type,
          face_oracal_code: sameSourceFill ? prior.face_oracal_code : item.face_oracal_code,
          face_oracal_name: sameSourceFill ? prior.face_oracal_name : item.face_oracal_name,
          return_finish_type: sameSourceFill ? prior.return_finish_type ?? item.return_finish_type : item.return_finish_type,
          return_oracal_code: sameSourceFill ? prior.return_oracal_code : item.return_oracal_code,
          return_oracal_name: sameSourceFill ? prior.return_oracal_name : item.return_oracal_name,
          return_depth_mm: sameSourceFill ? prior.return_depth_mm ?? item.return_depth_mm : item.return_depth_mm,
          face_vinyl_roll_width_mm: sameSourceFill
            ? prior.face_vinyl_roll_width_mm ?? item.face_vinyl_roll_width_mm
            : item.face_vinyl_roll_width_mm,
          confirmed: sameSourceFill ? prior.confirmed : false,
        }
      : item;
    return normalizeLetterGroupFaceRollWidth(applyNearestOracal651ToLetterGroup(merged));
  });
}

const RETURN_INACTIVE = new Set(["", "none", "no_return", "without_return"]);

function returnFinishActive(finishType: string | null | undefined): boolean {
  const token = String(finishType ?? "").trim().toLowerCase();
  return !RETURN_INACTIVE.has(token);
}

/** Sum layer vector perimeters for letter groups with active cant — Corel-comparable scope. */
export function sumActiveLetterGroupCantPerimeterM(
  groups: IntakeV4LetterGroupFinish[],
): number | null {
  let sum = 0;
  let any = false;
  for (const group of groups) {
    if (!returnFinishActive(group.return_finish_type)) continue;
    if (group.perimeter_m != null && group.perimeter_m > 0) {
      sum += group.perimeter_m;
      any = true;
    }
  }
  return any ? sum : null;
}

export function letterGroupFinishesFromPayload(
  payload: Record<string, unknown> | undefined,
): IntakeV4LetterGroupFinish[] {
  const finish = payload?.finish_setup;
  if (finish == null || typeof finish !== "object" || Array.isArray(finish)) return [];
  const raw = (finish as Record<string, unknown>).letter_group_finishes;
  if (!Array.isArray(raw)) return [];
  return raw
    .filter((item): item is Record<string, unknown> => item != null && typeof item === "object")
    .map((item) =>
      normalizeLetterGroupFaceRollWidth({
        group_key: String(item.group_key ?? ""),
        layer_name: String(item.layer_name ?? item.group_key ?? ""),
        source_fill_color: typeof item.source_fill_color === "string" ? item.source_fill_color : null,
        face_area_m2: typeof item.face_area_m2 === "number" ? item.face_area_m2 : null,
        perimeter_m: typeof item.perimeter_m === "number" ? item.perimeter_m : null,
        element_count: typeof item.element_count === "number" ? item.element_count : null,
        face_finish_type: typeof item.face_finish_type === "string" ? item.face_finish_type : "oracal_651",
        face_oracal_code: typeof item.face_oracal_code === "string" ? item.face_oracal_code : null,
        face_oracal_name: typeof item.face_oracal_name === "string" ? item.face_oracal_name : null,
        return_finish_type:
          typeof item.return_finish_type === "string"
            ? item.return_finish_type
            : INTAKE_V4_DEFAULT_RETURN_FINISH_TYPE,
        return_oracal_code: typeof item.return_oracal_code === "string" ? item.return_oracal_code : null,
        return_oracal_name: typeof item.return_oracal_name === "string" ? item.return_oracal_name : null,
        return_depth_mm: typeof item.return_depth_mm === "number" ? item.return_depth_mm : null,
        face_vinyl_roll_width_mm:
          typeof item.face_vinyl_roll_width_mm === "number" ? item.face_vinyl_roll_width_mm : null,
        confirmed: item.confirmed === true,
      }),
    )
    .filter((item) => item.group_key.length > 0);
}
