/**
 * Canonical operator display for letter volume (return/cant) aluminum profile.
 * Same material family, four widths — associated with structure step «Volum aluminiu».
 * Owner-confirmed depths 30/60/80/100 mm; Al 0.6 mm; unit ml.
 * Stable registry codes are never renamed.
 */

export const LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO = "Volum aluminiu";
export const LETTERS_VOLUME_ALUMINUM_THICKNESS_NOTE_RO = "profil Al 0.6 mm";
export const LETTERS_VOLUME_ALUMINUM_SELECTOR_CODE = "MAT-PROFIL-LATERAL-LITERE";

/** Selector row — not a purchase SKU; resolves by return_depth_mm. */
export const LETTERS_VOLUME_ALUMINUM_SELECTOR_DISPLAY_NAME =
  "Volum aluminiu — alege lățimea (30/60/80/100)";

/** Structure row subtitle under VOLUM ALUMINIU. */
export const LETTERS_VOLUME_STRUCTURE_DISPLAY_NAME = `${LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO} — ${LETTERS_VOLUME_ALUMINUM_THICKNESS_NOTE_RO}`;

/**
 * Not these (avoid operator confusion):
 * - MAT-ACM-BOND-* / casetă (panou ACM)
 * - MAT-PREMOUNT-BAR-ALUMINUM (țeavă premontaj)
 * - MAT-PROFIL-ALU-BOX (profil casetă)
 */
export const LETTERS_VOLUME_ALUMINUM_NOT_THESE_CODES = [
  "MAT-ACM-BOND-3MM",
  "MAT-ACM-BOND-4MM",
  "MAT-PREMOUNT-BAR-ALUMINUM",
  "MAT-PROFIL-ALU-BOX",
] as const;

export type LettersVolumeAluminumWidthEntry = {
  id: "volume_alu_30" | "volume_alu_60" | "volume_alu_80" | "volume_alu_100";
  depthMm: 30 | 60 | 80 | 100;
  labelRo: string;
  materialCode: string;
  /** Owner-confirmed purchase evidence (EUR/ml, excl. TVA) — display only. */
  unitCostEurMl: number;
  meaningRo: string;
};

/** Owner order — four widths for the Volum aluminiu step. */
export const LETTERS_VOLUME_ALUMINUM_WIDTHS: readonly LettersVolumeAluminumWidthEntry[] = [
  {
    id: "volume_alu_30",
    depthMm: 30,
    labelRo: "30 mm",
    materialCode: "MAT-PROFIL-LATERAL-LITERE-30MM",
    unitCostEurMl: 2.0,
    meaningRo:
      "Volum aluminiu 30 mm — profil Al 0.6 mm pentru pasul Volum aluminiu (RETURN-CANT). Nu ACM, nu premontaj, nu casetă.",
  },
  {
    id: "volume_alu_60",
    depthMm: 60,
    labelRo: "60 mm",
    materialCode: "MAT-PROFIL-LATERAL-LITERE-60MM",
    unitCostEurMl: 3.0,
    meaningRo:
      "Volum aluminiu 60 mm — profil Al 0.6 mm pentru pasul Volum aluminiu (RETURN-CANT). Nu ACM, nu premontaj, nu casetă.",
  },
  {
    id: "volume_alu_80",
    depthMm: 80,
    labelRo: "80 mm",
    materialCode: "MAT-PROFIL-LATERAL-LITERE-80MM",
    unitCostEurMl: 4.0,
    meaningRo:
      "Volum aluminiu 80 mm — profil Al 0.6 mm pentru pasul Volum aluminiu (RETURN-CANT). Nu ACM, nu premontaj, nu casetă.",
  },
  {
    id: "volume_alu_100",
    depthMm: 100,
    labelRo: "100 mm",
    materialCode: "MAT-PROFIL-LATERAL-LITERE-100MM",
    unitCostEurMl: 5.0,
    meaningRo:
      "Volum aluminiu 100 mm — profil Al 0.6 mm pentru pasul Volum aluminiu (RETURN-CANT). Nu ACM, nu premontaj, nu casetă.",
  },
] as const;

export const LETTERS_VOLUME_ALUMINUM_MATERIAL_CODES = LETTERS_VOLUME_ALUMINUM_WIDTHS.map(
  (entry) => entry.materialCode,
);

/** Pricing / Inventory display: family + width. */
export function lettersVolumeAluminumPricingLabel(depthMm: number): string {
  return `${LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO} ${depthMm} mm`;
}

export function getLettersVolumeAluminumByCode(
  materialCode: string | null | undefined,
): LettersVolumeAluminumWidthEntry | null {
  const code = String(materialCode ?? "")
    .trim()
    .toUpperCase();
  return LETTERS_VOLUME_ALUMINUM_WIDTHS.find((entry) => entry.materialCode === code) ?? null;
}

export function getLettersVolumeAluminumByDepthMm(
  depthMm: number | null | undefined,
): LettersVolumeAluminumWidthEntry | null {
  return LETTERS_VOLUME_ALUMINUM_WIDTHS.find((entry) => entry.depthMm === depthMm) ?? null;
}

/** Documented production paths for this step (not CNC-on-plexi). */
export const LETTERS_VOLUME_ALUMINUM_PROCESS_STEPS = [
  {
    id: "volume_form",
    labelRo: "Formare profil",
    meaningRo: "Profil debitat și format înainte de asamblarea finală (side_forming).",
  },
  {
    id: "volume_oracal_before",
    labelRo: "Oracal 651 înainte de formare",
    meaningRo: "Dacă cant colantat — aplicare Oracal 651 înainte de modelare la mașină.",
  },
  {
    id: "volume_ral_after",
    labelRo: "RAL după lipire față",
    meaningRo: "Dacă cant vopsit — vopsire RAL după lipirea volumului pe șanfren față.",
  },
] as const;
