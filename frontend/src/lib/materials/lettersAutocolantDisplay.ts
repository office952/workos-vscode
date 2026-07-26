/**
 * Operator display for letter-face finish options (Oracal / print-laminate).
 * Family word «Autocolant» is not a peer badge to CNC — options are individual chips.
 */
import {
  LETTERS_FACE_FINISH_MATERIALS,
  LETTERS_FACE_FINISH_ORACAL_641_DISPLAY_NAME,
  LETTERS_FACE_FINISH_ORACAL_651_DISPLAY_NAME,
  LETTERS_FACE_FINISH_ORACAL_8500_DISPLAY_NAME,
} from "@/lib/materials/lettersFaceFinishMaterialDisplay";

export { LETTERS_FACE_FINISH_MATERIALS };

/** Section label only — not a capability badge. */
export const LETTERS_FACE_FINISH_SECTION_LABEL_RO = "Finisaj față";

/** Legacy family word — cant mode / copy that still needs the noun. */
export const LETTERS_AUTOCOLANT_DISPLAY_FAMILY = "Autocolant";

/** Owner order — face finish option chips (from material meaning contract). */
export const LETTERS_FACE_AUTOCOLANT_OPTIONS = LETTERS_FACE_FINISH_MATERIALS.map((entry) => ({
  id: entry.id,
  labelRo: entry.labelRo,
  materialCode: entry.materialCode,
  unitCostEurMp: entry.unitCostEurMp,
  meaningRo: entry.meaningRo,
}));

export type LettersFaceAutocolantOptionId = (typeof LETTERS_FACE_AUTOCOLANT_OPTIONS)[number]["id"];

/**
 * Shared labor for any face finish option (Oracal / print-laminate).
 * Short operator chips — same pair regardless of material choice.
 */
export const LETTERS_FACE_FINISH_LABOR_STEPS = [
  {
    id: "face_finish_apply",
    labelRo: "Aplicare față",
    meaningRo: "Aplicare pe fața literei — după asamblare.",
  },
  {
    id: "face_finish_trim",
    labelRo: "Decupare contur",
    meaningRo: "Decupare manuală pe lângă fața literei.",
  },
] as const;

export function lettersAutocolantSeriesLabel(series: string): string {
  const s = String(series || "").trim();
  if (s === "8500") return LETTERS_FACE_FINISH_ORACAL_8500_DISPLAY_NAME;
  if (s === "641") return LETTERS_FACE_FINISH_ORACAL_641_DISPLAY_NAME;
  if (s === "651") return LETTERS_FACE_FINISH_ORACAL_651_DISPLAY_NAME;
  return s ? `Oracal ${s}` : LETTERS_AUTOCOLANT_DISPLAY_FAMILY;
}
