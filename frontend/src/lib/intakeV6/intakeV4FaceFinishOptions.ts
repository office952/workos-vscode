const LETTER_GROUP_FACE_UI_OPTIONS = [
  { value: "oracal_651", label: "Oracal 651" },
  { value: "oracal_641", label: "Oracal 641" },
  { value: "oracal_8500", label: "Oracal 8500 — translucid" },
  { value: "print_laminate", label: "Print + laminare" },
] as const;

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

export function faceFinishDefaultRollWidthMm(faceFinishType: string | null | undefined): number | null {
  const token = String(faceFinishType ?? "").trim().toLowerCase();
  return token === "oracal_641" || token === "oracal_651" || token === "oracal_8500"
    ? INTAKE_V4_DEFAULT_ORACAL_FACE_ROLL_WIDTH_MM
    : null;
}

export function normalizeFaceVinylRollWidthMm(
  faceFinishType: string | null | undefined,
  rollWidthMm: number | null | undefined,
): number | null {
  if (!faceFinishNeedsRollWidth(faceFinishType)) return null;
  if (typeof rollWidthMm === "number" && Number.isFinite(rollWidthMm) && rollWidthMm > 0) {
    return rollWidthMm;
  }
  return faceFinishDefaultRollWidthMm(faceFinishType);
}
