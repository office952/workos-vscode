/**
 * Canonical operator display for letter-face finish materials.
 * Owner lock 2026-07-23 — same labels in Product System, Intake, Pricing.
 * Stable registry codes are never renamed.
 * No BADGE-FACE-* codes — identity is label + MAT-* (CNC remains the only capability badge).
 */

export const LETTERS_FACE_FINISH_ORACAL_8500_DISPLAY_NAME = "Oracal 8500";
export const LETTERS_FACE_FINISH_ORACAL_641_DISPLAY_NAME = "Oracal 641";
export const LETTERS_FACE_FINISH_ORACAL_651_DISPLAY_NAME = "Oracal 651";
export const LETTERS_FACE_FINISH_PRINT_LAMINATED_DISPLAY_NAME = "Printat / Laminat";

export const LETTERS_FACE_FINISH_ORACAL_8500_REGISTRY_CODE = "MAT-ORACAL-8500";
export const LETTERS_FACE_FINISH_ORACAL_641_REGISTRY_CODE = "MAT-ORACAL-641";
export const LETTERS_FACE_FINISH_ORACAL_651_REGISTRY_CODE = "MAT-ORACAL-651";
export const LETTERS_FACE_FINISH_PRINT_LAMINATED_REGISTRY_CODE = "MAT-VINYL-PRINT-LAMINATED";

export type LettersFaceFinishMaterialEntry = {
  id: "face_oracal_8500" | "face_oracal_641" | "face_oracal_651" | "face_print_laminate";
  labelRo: string;
  materialCode: string;
  /** Owner-confirmed purchase evidence (EUR/mp, excl. TVA) — display only. */
  unitCostEurMp: number;
  meaningRo: string;
  intakeTokens: readonly string[];
};

/** Owner order — catalog options on Letters face + Inventory/Pricing identity. */
export const LETTERS_FACE_FINISH_MATERIALS: readonly LettersFaceFinishMaterialEntry[] = [
  {
    id: "face_oracal_8500",
    labelRo: LETTERS_FACE_FINISH_ORACAL_8500_DISPLAY_NAME,
    materialCode: LETTERS_FACE_FINISH_ORACAL_8500_REGISTRY_CODE,
    unitCostEurMp: 20.0,
    meaningRo:
      "Finisaj față Oracal 8500 — FINISH după asamblare; nu proces CNC pe plexi. Vizibil în Inventory / Pricing.",
    intakeTokens: ["oracal_8500"],
  },
  {
    id: "face_oracal_641",
    labelRo: LETTERS_FACE_FINISH_ORACAL_641_DISPLAY_NAME,
    materialCode: LETTERS_FACE_FINISH_ORACAL_641_REGISTRY_CODE,
    unitCostEurMp: 6.5,
    meaningRo:
      "Finisaj față Oracal 641 — FINISH după asamblare; nu proces CNC pe plexi. Vizibil în Inventory / Pricing.",
    intakeTokens: ["oracal_641"],
  },
  {
    id: "face_oracal_651",
    labelRo: LETTERS_FACE_FINISH_ORACAL_651_DISPLAY_NAME,
    materialCode: LETTERS_FACE_FINISH_ORACAL_651_REGISTRY_CODE,
    unitCostEurMp: 9.0,
    meaningRo:
      "Finisaj față Oracal 651 — FINISH după asamblare; nu proces CNC pe plexi. Vizibil în Inventory / Pricing.",
    intakeTokens: ["oracal_651"],
  },
  {
    id: "face_print_laminate",
    labelRo: LETTERS_FACE_FINISH_PRINT_LAMINATED_DISPLAY_NAME,
    materialCode: LETTERS_FACE_FINISH_PRINT_LAMINATED_REGISTRY_CODE,
    unitCostEurMp: 10.0,
    meaningRo:
      "Finisaj față Printat / Laminat — FINISH după asamblare; nu proces CNC pe plexi. Vizibil în Inventory / Pricing.",
    intakeTokens: ["print_laminate", "printed_laminated_vinyl"],
  },
] as const;

/** Intake / Product System face-finish option tokens → display label. */
export const LETTERS_FACE_FINISH_OPTION_LABEL_BY_TOKEN: Record<string, string> = Object.fromEntries(
  LETTERS_FACE_FINISH_MATERIALS.flatMap((entry) =>
    entry.intakeTokens.map((token) => [token, entry.labelRo] as const),
  ),
);

export function lettersFaceFinishOptionLabel(token: string | null | undefined): string | null {
  const key = String(token ?? "")
    .trim()
    .toLowerCase();
  return LETTERS_FACE_FINISH_OPTION_LABEL_BY_TOKEN[key] ?? null;
}

export function getLettersFaceFinishMaterialByCode(
  materialCode: string | null | undefined,
): LettersFaceFinishMaterialEntry | null {
  const code = String(materialCode ?? "")
    .trim()
    .toUpperCase();
  return LETTERS_FACE_FINISH_MATERIALS.find((entry) => entry.materialCode === code) ?? null;
}

export function getLettersFaceFinishMaterialById(
  id: string | null | undefined,
): LettersFaceFinishMaterialEntry | null {
  return LETTERS_FACE_FINISH_MATERIALS.find((entry) => entry.id === id) ?? null;
}

export const LETTERS_FACE_FINISH_MATERIAL_CODES = LETTERS_FACE_FINISH_MATERIALS.map(
  (entry) => entry.materialCode,
);
