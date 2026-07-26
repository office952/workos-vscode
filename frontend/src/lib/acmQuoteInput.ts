/**
 * ACM template pack quote_input helpers — TPL-ACM-CASSETTED-PANEL, TPL-CUT-ACM-LETTERS.
 */

export const TPL_ACM_CASSETTED_PANEL = "TPL-ACM-CASSETTED-PANEL";
export const TPL_ACM_BOXED_MOUNTING_SUPPORT = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1";
export const TPL_CUT_ACM_LETTERS = "TPL-CUT-ACM-LETTERS";

export const ACM_THICKNESS_OPTIONS = [3, 4] as const;
/** Boxed mounting intake — 4 mm deferred until owner price. */
export const ACM_BOXED_MOUNTING_THICKNESS_OPTIONS = [3] as const;
export const ACM_BOXED_MOUNTING_SUPPORTED_THICKNESS_MM = ACM_BOXED_MOUNTING_THICKNESS_OPTIONS;
export const ACM_FOLD_SIDES_OPTIONS = [
  { value: "all", label: "Toate laturile" },
  { value: "top_bottom", label: "Sus + jos" },
  { value: "left_right", label: "Stânga + dreapta" },
] as const;

export interface AcmCasettedFieldSpec {
  key: string;
  label: string;
  unit: string;
  placeholder: string;
  helper: string;
  min?: number;
  selectOptions?: readonly { value: string; label: string }[];
  numberOptions?: readonly number[];
}

export const ACM_CASSETTED_QUOTE_INPUT_FIELDS: AcmCasettedFieldSpec[] = [
  {
    key: "panel_width_mm",
    label: "Lățime panou",
    unit: "mm",
    placeholder: "2880",
    helper: "Dimensiune panou ACM — fundal / suport premontaj.",
    min: 0,
  },
  {
    key: "panel_height_mm",
    label: "Înălțime panou",
    unit: "mm",
    placeholder: "1000",
    helper: "Nu confunda cu spate literă Forex 10 mm.",
    min: 0,
  },
  {
    key: "acm_thickness_mm",
    label: "Grosime ACM",
    unit: "mm",
    placeholder: "3",
    helper: "3 mm owner-confirmed; 4 mm needs_owner_review.",
    numberOptions: ACM_THICKNESS_OPTIONS,
  },
  {
    key: "return_depth_mm",
    label: "Adâncime cant / casetare",
    unit: "mm",
    placeholder: "60",
    helper: "Cant return panou casetat.",
    min: 0,
  },
  {
    key: "rear_lip_mm",
    label: "Buză spate (rear lip)",
    unit: "mm",
    placeholder: "25",
    helper: "Minim 25 mm pentru casetare cu două pliuri.",
    min: 0,
  },
  {
    key: "fold_sides",
    label: "Laturi pliate",
    unit: "",
    placeholder: "all",
    helper: "Pliuri de obicei pe toate laturile.",
    selectOptions: ACM_FOLD_SIDES_OPTIONS,
  },
  {
    key: "v_groove_angle_deg",
    label: "Unghi V-groove",
    unit: "°",
    placeholder: "135",
    helper: "Freza router V — implicit 135°.",
    min: 0,
  },
  {
    key: "frame_clearance_mm",
    label: "Luft / clearance cadru",
    unit: "mm",
    placeholder: "0",
    helper: "Spațiu față de cadru / structură.",
    min: 0,
  },
];

export const ACM_BOXED_MOUNTING_QUOTE_INPUT_FIELDS: AcmCasettedFieldSpec[] =
  ACM_CASSETTED_QUOTE_INPUT_FIELDS.map((field) =>
    field.key === "acm_thickness_mm"
      ? {
          ...field,
          numberOptions: ACM_BOXED_MOUNTING_THICKNESS_OPTIONS,
          helper: "3 mm owner-confirmed; 4 mm deferred until owner price.",
        }
      : field,
  );

export const CUT_ACM_QUOTE_INPUT_FIELDS: AcmCasettedFieldSpec[] = [
  {
    key: "cut_area_m2",
    label: "Arie tăiere",
    unit: "m²",
    placeholder: "0.5",
    helper: "Suprafață totală litere/forme tăiate din ACM.",
    min: 0,
  },
  {
    key: "cut_perimeter_m",
    label: "Perimetru tăiere",
    unit: "m",
    placeholder: "12",
    helper: "Perimetru cumulat traseu CNC.",
    min: 0,
  },
  {
    key: "acm_thickness_mm",
    label: "Grosime ACM",
    unit: "mm",
    placeholder: "3",
    helper: "3 mm owner-confirmed; 4 mm needs_owner_review.",
    numberOptions: ACM_THICKNESS_OPTIONS,
  },
];

function foldLengthMm(
  widthMm: number,
  heightMm: number,
  foldSides: string
): number | null {
  const sides = foldSides.trim().toLowerCase();
  if (sides === "all") return 2 * (widthMm + heightMm);
  if (sides === "top_bottom") return 2 * widthMm;
  if (sides === "left_right") return 2 * heightMm;
  return null;
}

export function deriveAcmCasettedQuoteInput(raw: Record<string, unknown>): {
  payload: Record<string, unknown>;
  warnings: string[];
  blockers: string[];
} {
  const stringValues: Record<string, string> = {};
  for (const [key, value] of Object.entries(raw)) {
    if (value != null && value !== "") {
      stringValues[key] = String(value);
    }
  }
  const payload = buildAcmCasettedQuoteInputPayload(stringValues) as Record<string, unknown>;
  const warnings: string[] = [];
  const blockers: string[] = [];
  const w = Number(raw.panel_width_mm);
  const h = Number(raw.panel_height_mm);
  if (!Number.isFinite(w) || !Number.isFinite(h) || w <= 0 || h <= 0) {
    blockers.push("missing_panel_dimensions");
  }
  const rearLip = Number(raw.rear_lip_mm ?? 0);
  const lipWarning = rearLipWarning(rearLip);
  if (lipWarning) warnings.push(lipWarning);
  return { payload, warnings, blockers };
}

export function rearLipWarning(rearLipMm: number): string | null {
  if (rearLipMm > 0 && rearLipMm < 25) {
    return "rear_lip_mm sub 25 mm — verificare obligatorie pentru casetare cu două pliuri";
  }
  return null;
}

export function buildAcmCasettedQuoteInputPayload(
  values: Record<string, string>
): Record<string, number | string> {
  const out: Record<string, number | string> = {};
  const w = parseFloat(values.panel_width_mm ?? "");
  const h = parseFloat(values.panel_height_mm ?? "");
  if (Number.isFinite(w) && w > 0) out.panel_width_mm = w;
  if (Number.isFinite(h) && h > 0) out.panel_height_mm = h;
  if (Number.isFinite(w) && Number.isFinite(h) && w > 0 && h > 0) {
    out.panel_area_m2 = Math.round((w * h) / 1_000_000 * 1e6) / 1e6;
    out.panel_perimeter_m = Math.round((2 * (w + h)) / 1000 * 1e6) / 1e6;
  }

  const thickness = parseInt(values.acm_thickness_mm ?? "3", 10);
  if (ACM_THICKNESS_OPTIONS.includes(thickness as (typeof ACM_THICKNESS_OPTIONS)[number])) {
    out.acm_thickness_mm = thickness;
  }

  const returnDepth = parseFloat(values.return_depth_mm ?? "");
  if (Number.isFinite(returnDepth) && returnDepth > 0) {
    out.return_depth_mm = returnDepth;
  }

  const rearLip = parseFloat(values.rear_lip_mm ?? "");
  if (Number.isFinite(rearLip) && rearLip >= 0) out.rear_lip_mm = rearLip;

  const foldSides = values.fold_sides?.trim() || "all";
  out.fold_sides = foldSides;

  const vGroove = parseFloat(values.v_groove_angle_deg ?? "135");
  if (Number.isFinite(vGroove) && vGroove > 0) out.v_groove_angle_deg = vGroove;

  const clearance = parseFloat(values.frame_clearance_mm ?? "");
  if (Number.isFinite(clearance) && clearance >= 0) {
    out.frame_clearance_mm = clearance;
  }

  if (Number.isFinite(w) && Number.isFinite(h) && w > 0 && h > 0) {
    const foldMm = foldLengthMm(w, h, foldSides);
    if (foldMm != null) {
      out.fold_length_m = Math.round((foldMm / 1000) * 1e6) / 1e6;
      if (Number.isFinite(returnDepth) && returnDepth > 0) {
        out.return_strip_area_m2 =
          Math.round((foldMm / 1000) * (returnDepth / 1000) * 1e6) / 1e6;
      }
    }
  }

  return out;
}

export function buildCutAcmQuoteInputPayload(
  values: Record<string, string>
): Record<string, number | string> {
  const out: Record<string, number | string> = {};
  const area = parseFloat(values.cut_area_m2 ?? "");
  const perim = parseFloat(values.cut_perimeter_m ?? "");
  if (Number.isFinite(area) && area > 0) out.cut_area_m2 = area;
  if (Number.isFinite(perim) && perim > 0) out.cut_perimeter_m = perim;
  const thickness = parseInt(values.acm_thickness_mm ?? "3", 10);
  if (ACM_THICKNESS_OPTIONS.includes(thickness as (typeof ACM_THICKNESS_OPTIONS)[number])) {
    out.acm_thickness_mm = thickness;
  }
  return out;
}

export function isAcmTemplateCode(code: string | null | undefined): boolean {
  return (
    code === TPL_ACM_CASSETTED_PANEL ||
    code === TPL_ACM_BOXED_MOUNTING_SUPPORT ||
    code === TPL_CUT_ACM_LETTERS
  );
}
