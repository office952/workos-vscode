import type { IntakeV4SheetQuoteMaterialCandidates } from "./intakeV4Api";
import type { IntakeV4SheetFootprintOverride } from "./intakeV4SheetFootprintOverride";
import { formatSheetFootprintSqm } from "./intakeV4SheetFootprintOverride";

export type IntakeV4SheetFootprintSourceKey =
  | "eligible_area_floor"
  | "face_union_bbox"
  | "layout_occupied_area"
  | "operator_manual_footprint"
  | "full_sheet_allocation";

export interface IntakeV4SheetFootprintSourceOption {
  key: IntakeV4SheetFootprintSourceKey;
  label: string;
  areaSqm: number | null;
  disabled: boolean;
  disabledReason?: string;
}

const SOURCE_LABELS: Record<IntakeV4SheetFootprintSourceKey, string> = {
  eligible_area_floor: "Aria pieselor eligibile",
  face_union_bbox: "Face union bbox",
  layout_occupied_area: "Layout auto shelf",
  operator_manual_footprint: "Manual Corel",
  full_sheet_allocation: "Placă fizică",
};

export function formatIntakeV4SheetFootprintSourceLabel(
  source: string | null | undefined,
): string {
  if (!source) return "—";
  const key = source as IntakeV4SheetFootprintSourceKey;
  return SOURCE_LABELS[key] ?? source;
}

export function readPersistedSheetFootprintSource(
  override: IntakeV4SheetFootprintOverride | null | undefined,
): IntakeV4SheetFootprintSourceKey | null {
  const useForEstimate = Boolean(
    override?.useForQuoteEstimate ?? override?.use_for_quote_estimate,
  );
  if (!useForEstimate) return null;
  const raw =
    override?.selectedFootprintSource ??
    override?.selected_footprint_source ??
    null;
  if (raw && raw in SOURCE_LABELS) return raw as IntakeV4SheetFootprintSourceKey;
  if (override?.widthCm != null || override?.width_cm != null) {
    return "operator_manual_footprint";
  }
  return null;
}

export function resolveDefaultSheetFootprintSource(
  candidates: IntakeV4SheetQuoteMaterialCandidates | null | undefined,
  override: IntakeV4SheetFootprintOverride | null | undefined,
): IntakeV4SheetFootprintSourceKey {
  const persisted = readPersistedSheetFootprintSource(override);
  if (persisted) return persisted;
  const autoSource =
    candidates?.selection?.selected_source ??
    candidates?.selected_quote_sheet_area_source ??
    "eligible_area_floor";
  if (autoSource === "face_union_bbox") return "face_union_bbox";
  if (autoSource === "layout_occupied_area") return "layout_occupied_area";
  if (autoSource === "full_sheet_allocation") return "full_sheet_allocation";
  if (autoSource === "operator_manual_footprint") return "operator_manual_footprint";
  return "eligible_area_floor";
}

function readCandidateArea(
  candidates: IntakeV4SheetQuoteMaterialCandidates | null | undefined,
  key: IntakeV4SheetFootprintSourceKey,
): number | null {
  if (!candidates) return null;
  switch (key) {
    case "eligible_area_floor":
      return candidates.eligible_face_area_sqm ?? null;
    case "face_union_bbox":
      return candidates.face_union_bbox_sqm ?? null;
    case "layout_occupied_area":
      return candidates.layout_occupied_area_sqm ?? null;
    case "full_sheet_allocation":
      return candidates.full_sheet_allocation_sqm ?? null;
    case "operator_manual_footprint":
      return candidates.operator_manual_footprint_sqm ?? null;
    default:
      return null;
  }
}

export function buildIntakeV4SheetFootprintSourceOptions(args: {
  candidates: IntakeV4SheetQuoteMaterialCandidates | null | undefined;
  manualAreaSqm?: number | null;
}): IntakeV4SheetFootprintSourceOption[] {
  const { candidates, manualAreaSqm } = args;
  const primaryKeys: IntakeV4SheetFootprintSourceKey[] = [
    "eligible_area_floor",
    "face_union_bbox",
    "layout_occupied_area",
    "operator_manual_footprint",
  ];

  return primaryKeys.map((key) => {
    const areaSqm =
      key === "operator_manual_footprint"
        ? (manualAreaSqm ?? readCandidateArea(candidates, key))
        : readCandidateArea(candidates, key);
    const disabled = key !== "operator_manual_footprint" && (areaSqm == null || areaSqm <= 0);
    return {
      key,
      label: SOURCE_LABELS[key],
      areaSqm,
      disabled,
      disabledReason: disabled ? "Valoare indisponibilă în analiza curentă" : undefined,
    };
  });
}

export function resolveSelectedFootprintDisplay(args: {
  sourceKey: IntakeV4SheetFootprintSourceKey;
  candidates: IntakeV4SheetQuoteMaterialCandidates | null | undefined;
  manualAreaSqm?: number | null;
  persistedAreaSqm?: number | null;
}): { label: string; areaText: string; areaSqm: number | null } {
  const label = SOURCE_LABELS[args.sourceKey];
  let areaSqm = args.persistedAreaSqm ?? null;
  if (areaSqm == null) {
    if (args.sourceKey === "operator_manual_footprint") {
      areaSqm = args.manualAreaSqm ?? readCandidateArea(args.candidates, args.sourceKey);
    } else {
      areaSqm = readCandidateArea(args.candidates, args.sourceKey);
    }
  }
  return {
    label,
    areaSqm,
    areaText: formatSheetFootprintSqm(areaSqm),
  };
}

export function readFullSheetFootprintDetail(
  candidates: IntakeV4SheetQuoteMaterialCandidates | null | undefined,
): string {
  return formatSheetFootprintSqm(candidates?.full_sheet_allocation_sqm ?? null);
}
