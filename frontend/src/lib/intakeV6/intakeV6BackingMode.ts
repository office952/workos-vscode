export type IntakeV6BackingMode = "none" | "forex_10_no_bevel" | "forex_10_with_bevel";

export type IntakeV6EmblemLightingMode = "excluded" | "area_lit" | "needs_decision";

export const INTAKE_V6_BACKING_MODE_OPTIONS: Array<{ value: IntakeV6BackingMode; label: string }> = [
  { value: "forex_10_no_bevel", label: "Forex 10 mm fara sanfren" },
  { value: "forex_10_with_bevel", label: "Forex 10 mm cu sanfren" },
];

export const INTAKE_V6_EMBLEM_LIGHTING_OPTIONS: Array<{ value: IntakeV6EmblemLightingMode; label: string }> = [
  { value: "area_lit", label: "Emblema luminoasa - calcul pe arie" },
  { value: "excluded", label: "Emblema neluminoasa" },
];

export function normalizeIntakeV6BackingMode(raw: unknown): IntakeV6BackingMode {
  const token = String(raw ?? "forex_10_no_bevel").trim().toLowerCase();
  if (token === "forex_10_no_bevel" || token === "forex_10_with_bevel") return token;
  return "forex_10_no_bevel";
}

export function backingModeLabel(mode: IntakeV6BackingMode | string | null | undefined): string {
  const normalized = normalizeIntakeV6BackingMode(mode);
  return (
    INTAKE_V6_BACKING_MODE_OPTIONS.find((option) => option.value === normalized)?.label ??
    "Forex 10 mm fara sanfren"
  );
}

export function normalizeEmblemLightingMode(raw: unknown): IntakeV6EmblemLightingMode {
  const token = String(raw ?? "area_lit").trim().toLowerCase();
  if (token === "excluded" || token === "area_lit") return token;
  return "area_lit";
}
