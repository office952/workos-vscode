import type {
  IntakeV4FaceBackPrepCostDraftResponse,
  IntakeV4FaceBackPrepCostRowStatus,
} from "@/lib/intakeV6/intakeV4Api";

export const INTAKE_V4_FACE_BACK_PREP_BOUNDARY_LINE =
  "Nu creează quote · Nu creează taskuri reale · Nu consumă stock · Nu scrie ExecutionPlan/tasks_json · Nu folosește CostEngine final";

export const INTAKE_V4_FACE_BACK_PREP_VECTOR_PERIMETER_WARNING =
  "Perimetrul vectorial lipsește sau are încredere scăzută. Costul CNC nu se calculează din bbox/nesting.";

export function formatFaceBackPrepMoney(
  value: number | null | undefined,
  currency = "EUR",
): string {
  if (value == null) return "—";
  const normalizedCurrency = currency.trim().toUpperCase() || "EUR";
  try {
    return new Intl.NumberFormat("ro-RO", {
      style: "currency",
      currency: normalizedCurrency,
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  } catch {
    return `${value.toFixed(2)} ${normalizedCurrency}`;
  }
}

export function formatFaceBackPrepStatusLabel(status: IntakeV4FaceBackPrepCostRowStatus): string {
  switch (status) {
    case "calculated":
      return "calculat";
    case "calculated_when_enabled":
      return "calculat când activ";
    case "missing_price":
      return "preț lipsă";
    case "manual_required":
      return "manual required";
    case "optional":
      return "opțional";
    case "skipped":
      return "sărit";
    default:
      return status;
  }
}

export function buildFaceBackPrepFormulaSummary(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
  shanfrenForexEnabled: boolean,
): string[] {
  const lines = [
    "Plexiglas față: P_face × 2 × 1.5 EUR",
    "Forex fără șanfren: P_back × 3 × 1.5 EUR",
  ];
  if (shanfrenForexEnabled) {
    lines.push("Forex cu șanfren: P_back × 5 × 1.5 EUR (3 treceri debitare + 2 treceri șanfren)");
  }
  const rate = draft.cnc_rate_eur_per_ml;
  if (rate !== 1.5) {
    lines.push(`Tarif CNC draft: ${rate} EUR/ml/trecere`);
  }
  return lines;
}

export function sortFaceBackPrepTaskDrafts(
  taskDrafts: IntakeV4FaceBackPrepCostDraftResponse["task_drafts"],
) {
  return [...taskDrafts].sort((left, right) => left.order_index - right.order_index);
}

export function hasFaceBackPrepVectorPerimeterWarning(
  warnings: IntakeV4FaceBackPrepCostDraftResponse["warnings"],
): boolean {
  return warnings.some((warning) => warning.code === "vector_perimeter_missing_or_low_confidence");
}

export function hasFaceBackPrepManualRequiredOperations(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): boolean {
  return draft.operations.some((row) => row.status === "manual_required");
}

/** CNC totals are not operator-trustworthy until vector perimeter is verified. */
export function needsFaceBackPrepPerimeterVerification(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): boolean {
  return (
    hasFaceBackPrepVectorPerimeterWarning(draft.warnings) ||
    hasFaceBackPrepManualRequiredOperations(draft)
  );
}

export const FACE_BACK_PREP_OPERATOR_STATUS_NEEDS_VERIFICATION = "Necesită verificare perimetru";
export const FACE_BACK_PREP_OPERATOR_STATUS_CALCULABLE = "calculabil";
export const FACE_BACK_PREP_CNC_UNAVAILABLE_LABEL =
  "indisponibil până la verificare perimetru";
export const FACE_BACK_PREP_TOTAL_UNAVAILABLE_LABEL = "indisponibil";
export const FACE_BACK_PREP_VERIFICATION_REASON =
  "Perimetru vectorial lipsă sau încredere scăzută";

export const FACE_BACK_PREP_SHORT_VERIFICATION_ALERT =
  "Necesită verificare perimetru — cost CNC indisponibil.";

export const FACE_BACK_PREP_IGNORED_RAW_CNC_LABEL =
  "Valoare brută ignorată (status manual_required / perimetru neverificat)";

export function formatFaceBackPrepPerimeterM(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${value.toFixed(3)} m`;
}

export function resolveFaceBackPrepCncPerimeterM(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): number | null {
  if (needsFaceBackPrepPerimeterVerification(draft)) return null;
  const calculatedVector = draft.operations.filter(
    (op) =>
      op.status === "calculated" &&
      op.is_vector_perimeter_source &&
      Number.isFinite(op.quantity) &&
      op.quantity > 0,
  );
  if (calculatedVector.length === 0) return null;
  const faceCut = calculatedVector.find(
    (op) =>
      op.component === "FACE_PLEXI" &&
      (op.operation_key.includes("cut") || op.task_key.includes("CUT")),
  );
  if (faceCut) return faceCut.quantity;
  return calculatedVector[0]!.quantity;
}

export function resolveFaceBackPrepDisplayMaterialCost(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): number | null {
  return draft.totals.material_cost ?? null;
}

export function resolveFaceBackPrepDisplayCncCost(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): number | null {
  if (needsFaceBackPrepPerimeterVerification(draft)) return null;
  return draft.totals.operation_cost ?? null;
}

export function resolveFaceBackPrepDisplayTotalInternal(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): number | null {
  if (needsFaceBackPrepPerimeterVerification(draft)) return null;
  return draft.totals.total_internal_cost ?? null;
}

/** Raw backend operation_cost when UI must not treat it as valid. */
export function resolveFaceBackPrepIgnoredRawCncCost(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): number | null {
  if (!needsFaceBackPrepPerimeterVerification(draft)) return null;
  const raw = draft.totals.operation_cost;
  return raw != null && Number.isFinite(raw) ? raw : null;
}

export function resolveFaceBackPrepOperatorStatusLabel(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): string {
  if (needsFaceBackPrepPerimeterVerification(draft)) {
    return FACE_BACK_PREP_OPERATOR_STATUS_NEEDS_VERIFICATION;
  }
  if (draft.totals.total_internal_cost != null) {
    return FACE_BACK_PREP_OPERATOR_STATUS_CALCULABLE;
  }
  if (draft.missing_prices.length > 0) {
    return "lipsesc prețuri materiale";
  }
  return "parțial";
}

export function faceBackPrepTotalUnavailableReason(
  draft: IntakeV4FaceBackPrepCostDraftResponse,
): string | null {
  if (draft.totals.total_internal_cost != null) return null;
  if (hasFaceBackPrepVectorPerimeterWarning(draft.warnings) || hasFaceBackPrepManualRequiredOperations(draft)) {
    return "Total intern draft indisponibil — perimetru vectorial lipsă / manual required";
  }
  if (draft.missing_prices.length > 0) {
    return "Total intern draft indisponibil — preț material lipsă";
  }
  return "Total intern draft indisponibil";
}
