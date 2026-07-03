/** Intake V4 backing mode - operator selection for Forex spate litere. */

export type IntakeV4BackingMode = "none" | "forex_10_no_bevel" | "forex_10_with_bevel";

export type IntakeV4EmblemLightingMode = "excluded" | "area_lit" | "needs_decision";

export const INTAKE_V4_BACKING_MODE_OPTIONS: Array<{ value: IntakeV4BackingMode; label: string }> = [
  { value: "forex_10_no_bevel", label: "Forex 10 mm fara sanfren" },
  { value: "forex_10_with_bevel", label: "Forex 10 mm cu sanfren" },
];

export const INTAKE_V4_EMBLEM_LIGHTING_OPTIONS: Array<{ value: IntakeV4EmblemLightingMode; label: string }> = [
  { value: "area_lit", label: "Emblema luminoasa - calcul pe arie" },
  { value: "excluded", label: "Emblema neluminoasa" },
];

export function normalizeIntakeV4BackingMode(raw: unknown): IntakeV4BackingMode {
  const token = String(raw ?? "forex_10_no_bevel").trim().toLowerCase();
  if (token === "forex_10_no_bevel" || token === "forex_10_with_bevel") return token;
  return "forex_10_no_bevel";
}

export function backingModeLabel(mode: IntakeV4BackingMode | string | null | undefined): string {
  const normalized = normalizeIntakeV4BackingMode(mode);
  return (
    INTAKE_V4_BACKING_MODE_OPTIONS.find((o) => o.value === normalized)?.label ??
    "Forex 10 mm fara sanfren"
  );
}

export function normalizeEmblemLightingMode(raw: unknown): IntakeV4EmblemLightingMode {
  const token = String(raw ?? "area_lit").trim().toLowerCase();
  if (token === "excluded" || token === "area_lit") return token;
  return "area_lit";
}
