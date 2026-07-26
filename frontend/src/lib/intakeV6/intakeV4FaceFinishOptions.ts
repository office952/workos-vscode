const LETTER_GROUP_FACE_UI_OPTIONS = [
  { value: "oracal_651", label: "Oracal 651" },
  { value: "oracal_641", label: "Oracal 641" },
  { value: "oracal_8500", label: "Oracal 8500" },
  { value: "print_laminate", label: "Printat / Laminat" },
] as const;

export const INTAKE_V4_ORACAL_FACE_ROLL_WIDTH_OPTIONS = [
  { value: 1000, label: "1000 mm" },
  { value: 1260, label: "1260 mm" },
] as const;

export const PRINT_LAMINATION_ROLL_WIDTHS_MM = [1050, 1320, 1500] as const;

export const PRINT_LAMINATION_SIDE_RETRACTION_MM = 20;

export const PRINT_LAMINATION_TOTAL_RETRACTION_MM = PRINT_LAMINATION_SIDE_RETRACTION_MM * 2;

export const PRINT_LAMINATION_ROLL_WIDTH_OPTIONS = PRINT_LAMINATION_ROLL_WIDTHS_MM.map((width) => ({
  value: width,
  label: `${width} mm`,
})) as Array<{ value: (typeof PRINT_LAMINATION_ROLL_WIDTHS_MM)[number]; label: string }>;

export const INTAKE_V4_FACE_FINISH_OPTIONS = [
  { value: "none", label: "Fără finisaj — plexiglas brut" },
  ...LETTER_GROUP_FACE_UI_OPTIONS,
] as const;

export type IntakeV4FaceFinishType = (typeof INTAKE_V4_FACE_FINISH_OPTIONS)[number]["value"];

export function faceFinishNeedsVinyl(faceFinishType: string | null | undefined): boolean {
  const token = (faceFinishType ?? "").trim().toLowerCase();
  return token === "oracal_651" || token === "oracal_8500" || token === "oracal_641" || token === "print_laminate";
}

export function faceFinishNeedsColorPicker(faceFinishType: string | null | undefined): boolean {
  const token = (faceFinishType ?? "").trim().toLowerCase();
  return token === "oracal_651" || token === "oracal_641" || token === "oracal_8500";
}

/** Oracal series persisted on finish payload (pricing / material identity). */
export function oracalSeriesForFace(faceFinishType: string): "651" | "8500" | "641" {
  if (faceFinishType === "oracal_8500") return "8500";
  if (faceFinishType === "oracal_641") return "641";
  return "651";
}

/** Color registry filter series — 641 reuses the 651 palette per operator policy. */
export function oracalColorPaletteSeriesForFace(faceFinishType: string): "651" | "8500" {
  if (faceFinishType === "oracal_8500") return "8500";
  return "651";
}

export function faceFinishNeedsRollWidth(faceFinishType: string | null | undefined): boolean {
  return faceFinishNeedsVinyl(faceFinishType);
}

export const INTAKE_V4_DEFAULT_ORACAL_FACE_ROLL_WIDTH_MM = 1000;

export const INTAKE_V4_DEFAULT_PRINT_LAMINATION_ROLL_WIDTH_MM = 1050;

function allowedRollWidthsForFace(faceFinishType: string | null | undefined): readonly number[] {
  const token = String(faceFinishType ?? "").trim().toLowerCase();
  if (token === "print_laminate") return PRINT_LAMINATION_ROLL_WIDTHS_MM;
  if (token === "oracal_641" || token === "oracal_651" || token === "oracal_8500") {
    return INTAKE_V4_ORACAL_FACE_ROLL_WIDTH_OPTIONS.map((option) => option.value);
  }
  return [];
}

export function faceFinishRollWidthOptions(
  faceFinishType: string | null | undefined,
): readonly { value: number; label: string }[] {
  const token = String(faceFinishType ?? "").trim().toLowerCase();
  if (token === "print_laminate") return PRINT_LAMINATION_ROLL_WIDTH_OPTIONS;
  if (token === "oracal_641" || token === "oracal_651" || token === "oracal_8500") {
    return INTAKE_V4_ORACAL_FACE_ROLL_WIDTH_OPTIONS;
  }
  return [];
}

export function faceFinishDefaultRollWidthMm(faceFinishType: string | null | undefined): number | null {
  const token = String(faceFinishType ?? "").trim().toLowerCase();
  if (token === "print_laminate") return INTAKE_V4_DEFAULT_PRINT_LAMINATION_ROLL_WIDTH_MM;
  return token === "oracal_641" || token === "oracal_651" || token === "oracal_8500"
    ? INTAKE_V4_DEFAULT_ORACAL_FACE_ROLL_WIDTH_MM
    : null;
}

export function normalizeFaceVinylRollWidthMm(
  faceFinishType: string | null | undefined,
  rollWidthMm: number | null | undefined,
): number | null {
  if (!faceFinishNeedsRollWidth(faceFinishType)) return null;
  const allowed = allowedRollWidthsForFace(faceFinishType);
  if (typeof rollWidthMm === "number" && Number.isFinite(rollWidthMm) && allowed.includes(rollWidthMm)) {
    return rollWidthMm;
  }
  return faceFinishDefaultRollWidthMm(faceFinishType);
}
