import type { IntakeV4EdgeCantOperationDryRunCandidate } from "./intakeV4Api";
import { formatIntakeV4Quantity } from "./intakeV4QuantityDisplay";

export const EDGE_CANT_PREVIEW_SOURCE = "shared_edge_cant_rules";

export function formatIntakeV4EdgeCantQuantity(quantity: number, unit: string): string {
  if (unit === "linear_meter" || unit === "m") {
    return formatIntakeV4Quantity(quantity, "m");
  }
  if (unit === "m2") {
    return formatIntakeV4Quantity(quantity, "m2");
  }
  return formatIntakeV4Quantity(quantity, unit);
}

export function formatIntakeV4EdgeCantPricingStatus(status: string | null | undefined): string {
  if (status === "missing_rate") {
    return "Preț neconfigurat / necesită tarif operație";
  }
  return status ?? "Preț neconfigurat / necesită tarif operație";
}

export function formatIntakeV4EdgeCantPreviewSource(source: string | null | undefined): string {
  if (source === EDGE_CANT_PREVIEW_SOURCE) {
    return "shared_edge_cant_rules";
  }
  return source ?? "—";
}
