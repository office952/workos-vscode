import type { IntakeV4CncOperationDryRunCandidate } from "./intakeV4Api";
import {
  formatIntakeV4LinearQuantityDisplay,
  sanitizeOperatorDisplayText,
} from "./intakeV4OperatorUiDisplay";

export const CNC_PREVIEW_SOURCE_OPERATION_ROWS = "operation_rows";
export const CNC_PREVIEW_SOURCE_COMPAT_FALLBACK = "legacy_parallel_mapping";

export function formatIntakeV4CncQuantity(quantity: number, unit: string): string {
  return formatIntakeV4LinearQuantityDisplay(quantity, unit, "cnc");
}

export function formatIntakeV4CncPricingStatus(
  status: string | null | undefined,
  operationType?: string | null,
): string {
  if (status === "missing_rate") {
    if (operationType && ["print_vinyl", "lamination", "vinyl_application"].includes(operationType)) {
      return "Preț neconfigurat / necesită tarif operație print/laminare/colantare";
    }
    return "Preț operație neconfigurat";
  }
  return status ?? "Preț operație neconfigurat";
}

export function formatIntakeV4CncPreviewSource(source: string | null | undefined): string {
  if (source === CNC_PREVIEW_SOURCE_OPERATION_ROWS) {
    return "operation_rows (debug)";
  }
  if (source === CNC_PREVIEW_SOURCE_COMPAT_FALLBACK) {
    return "compat_mapping_fallback";
  }
  return source ?? "—";
}

export function formatIntakeV4CncWorkstation(key: string | null | undefined): string {
  if (key === "cnc_router") {
    return "CNC router";
  }
  return key ?? "—";
}

export function isIntakeV4CncOperationRowCandidate(
  candidate: IntakeV4CncOperationDryRunCandidate,
): boolean {
  return candidate.source === CNC_PREVIEW_SOURCE_OPERATION_ROWS;
}

export function cncCandidateOperationKey(candidate: IntakeV4CncOperationDryRunCandidate): string {
  return candidate.operation_key;
}

export function formatIntakeV4CncCandidateTitle(title: string): string {
  return sanitizeOperatorDisplayText(title);
}
