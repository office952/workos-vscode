/** Operator-facing quantity formatting for Intake V4 material / production previews. */

import {
  formatIntakeV4LinearQuantityDisplay,
  isAdhesiveQuantityUnit,
  type IntakeV4LinearQuantityContext,
} from "./intakeV4OperatorUiDisplay";

const DISCRETE_UNITS = new Set([
  "buc",
  "pcs",
  "piece",
  "pieces",
  "modul",
  "module",
  "psu",
]);

export function isDiscreteIntakeV4QuantityUnit(unit: string): boolean {
  const token = unit.trim().toLowerCase();
  return DISCRETE_UNITS.has(token);
}

function resolveQuantityContext(
  unit: string,
  options?: { materialKey?: string | null; displayName?: string | null },
): IntakeV4LinearQuantityContext {
  if (isAdhesiveQuantityUnit(options?.materialKey, options?.displayName)) {
    return "adhesive";
  }
  const haystack = `${options?.materialKey ?? ""} ${options?.displayName ?? ""}`.toLowerCase();
  if (/cablu|cable|wiring/.test(haystack)) {
    return "cable";
  }
  if (unit === "ml" || unit === "m" || unit === "linear_meter") {
    return "generic";
  }
  return "generic";
}

export function formatIntakeV4Quantity(
  value: number,
  unit: string,
  options?: { materialKey?: string | null; displayName?: string | null },
): string {
  return formatIntakeV4LinearQuantityDisplay(
    value,
    unit,
    resolveQuantityContext(unit, options),
    options,
  );
}

export function formatIntakeV4PricingQuantity(
  baseQty: number,
  pricedQty: number,
  unit: string,
  wastePercent: number | null | undefined,
  options?: { materialKey?: string | null; displayName?: string | null },
): string {
  const priced = formatIntakeV4Quantity(pricedQty, unit, options);
  if (wastePercent != null && pricedQty !== baseQty) {
    return `${priced} (+${wastePercent}% pierdere)`;
  }
  return priced;
}
