/**
 * Product 001 / TPL-VOLUMETRIC-LETTERS — quote_input helpers for QuoteWizard.
 * Geometry metrics are never invented from SVG; only explicit intake/spec fields map.
 *
 * Composition direction: this template is letters-only. Support bars and ACM casetted
 * panels belong to separate templates (future quote composition) — see
 * docs/architecture/PRODUCT_TEMPLATE_COMPOSITION_DIRECTION.md.
 *
 * TODO(finish-assignment): Single global Oracal/color is not sufficient for real SVGs.
 * Future flow must support per-letter-group component finishes (face + return/cant) — see
 * docs/architecture/SVG_FINISH_ASSIGNMENT_AND_LETTER_GROUPS_DIRECTION.md.
 */

import type { QuoteInputPayload } from "@/api/quotes";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import {
  intakeFaceFinishToQuoteCostingType,
  resolveIntakeBackBevelEnabled,
  resolveIntakeFaceFinishType,
  resolveIntakeMountingSystem,
  resolveIntakeMountingTemplateEnabled,
} from "@/lib/intakeVolumetricSpec";
import {
  isIntakeIlluminationDisabled,
  resolveMountingTemplateMode,
} from "@/lib/volumetricIntakeSelectors";
import { getEffectiveQuoteGeometrySpec } from "@/lib/vectorGeometryInvalidation";

export const TPL_VOLUMETRIC_LETTERS = "TPL-VOLUMETRIC-LETTERS";
export const TPL_VOLUMETRIC_LETTERS_V2 = "TPL-VOLUMETRIC-LETTERS_v2";

export const VOLUMETRIC_LED_MODULE_LENGTH_MM = 75;
export const VOLUMETRIC_LED_MODULE_GAP_MM = 25;
export const VOLUMETRIC_LED_PITCH_MM =
  VOLUMETRIC_LED_MODULE_LENGTH_MM + VOLUMETRIC_LED_MODULE_GAP_MM;

export const VOLUMETRIC_PSU_WATTAGE_OPTIONS = [60, 100, 160, 200] as const;

export const VOLUMETRIC_FACE_FINISH_OPTIONS = [
  { value: "none", label: "Fără finisaj suplimentar (plexi față)" },
  { value: "oracal_651", label: "Oracal 651" },
  { value: "printed_vinyl", label: "Autocolant print" },
  { value: "printed_laminated_vinyl", label: "Autocolant print + laminare" },
] as const;

export const VOLUMETRIC_MOUNTING_SYSTEM_OPTIONS = [
  { value: "direct_wall", label: "Montaj direct pe perete" },
  { value: "steel_bars", label: "Bare oțel premontaj" },
  { value: "aluminum_bars", label: "Bare aluminiu premontaj" },
  { value: "acm_panel", label: "Panou ACM casetat" },
] as const;

export const VOLUMETRIC_DEFAULT_FACE_FINISH_TYPE = "none";
export const VOLUMETRIC_DEFAULT_MOUNTING_SYSTEM = "direct_wall";
export const VOLUMETRIC_DEFAULT_MOUNTING_TEMPLATE_ENABLED = true;
export const VOLUMETRIC_DEFAULT_MOUNTING_BAR_PROFILE = "30x30x1.5";

export type VolumetricFaceFinishType =
  (typeof VOLUMETRIC_FACE_FINISH_OPTIONS)[number]["value"];
export type VolumetricMountingSystem =
  (typeof VOLUMETRIC_MOUNTING_SYSTEM_OPTIONS)[number]["value"];

export interface VolumetricQuoteInputFieldSpec {
  key: keyof QuoteInputPayload & string;
  label: string;
  unit: string;
  placeholder: string;
  helper: string;
  min: number;
  /** When true, value is derived (e.g. LED count from perimeter) — not user-editable. */
  computed?: boolean;
  /** Boolean checkbox — not required when optional. */
  boolean?: boolean;
  /** Skip required validation (e.g. optional checkbox defaulting false). */
  optional?: boolean;
  /** PSU wattage select instead of free numeric input. */
  selectOptions?: readonly number[];
  /** String enum select (face finish, mounting system). */
  enumOptions?: readonly { value: string; label: string }[];
  /** Default enum value when unset. */
  defaultEnum?: string;
}

export const VOLUMETRIC_QUOTE_INPUT_FIELDS: VolumetricQuoteInputFieldSpec[] = [
  {
    key: "letter_face_area_m2",
    label: "Aria față litere",
    unit: "m²",
    placeholder: "2.88",
    helper: "Suprafața totală față (mp) — necesară pentru material față/spate.",
    min: 0,
  },
  {
    key: "letter_perimeter_m",
    label: "Perimetru total litere",
    unit: "m",
    placeholder: "18.0",
    helper: "Perimetru cumulat litere — LED, profil lateral, CNC șablon.",
    min: 0,
  },
  {
    key: "letter_count",
    label: "Număr litere",
    unit: "buc",
    placeholder: "9",
    helper: "Număr de caractere/litere (montaj LED, cablaj).",
    min: 1,
  },
  {
    key: "return_depth_mm",
    label: "Adâncime cant / profil",
    unit: "mm",
    placeholder: "60",
    helper: "Variantă profil: 30 / 60 / 80 / 100 — preluat din intake dacă există.",
    min: 0,
  },
  {
    key: "face_finish_type",
    label: "Finisaj față litere",
    unit: "",
    placeholder: "",
    helper:
      "Oracal 651 (5 EUR/mp) și print/laminare (10 EUR/mp) + aplicare 3 EUR/mp — prețuri owner în Pricing Registry.",
    min: 0,
    enumOptions: VOLUMETRIC_FACE_FINISH_OPTIONS,
    defaultEnum: VOLUMETRIC_DEFAULT_FACE_FINISH_TYPE,
  },
  {
    key: "mounting_system",
    label: "Sistem montaj / premontaj",
    unit: "",
    placeholder: "",
    helper:
      "Sistemul de suport/montaj. Șablonul Forex este opțional și independent (checkbox separat).",
    min: 0,
    enumOptions: VOLUMETRIC_MOUNTING_SYSTEM_OPTIONS,
    defaultEnum: VOLUMETRIC_DEFAULT_MOUNTING_SYSTEM,
  },
  {
    key: "mounting_template_enabled",
    label: "Șablon montaj Forex",
    unit: "",
    placeholder: "",
    helper:
      "Opțional. Se poate folosi indiferent de sistemul de montaj (direct pe perete, bare, ACM).",
    min: 0,
    boolean: true,
    optional: true,
  },
  {
    key: "mounting_template_area_m2",
    label: "Aria șablon montaj",
    unit: "m²",
    placeholder: "2.88",
    helper: "Suprafața Forex 3 mm pentru șablon (material mp; CNC separat).",
    min: 0,
  },
  {
    key: "mounting_bar_length_m",
    label: "Lungime totală bare premontaj override",
    unit: "ml",
    placeholder: "5",
    helper:
      "Opțional. Dacă este gol, se calculează automat: lățimea ansamblului × număr bare (implicit 2: sus + jos).",
    min: 0,
    optional: true,
  },
  {
    key: "mounting_bar_count",
    label: "Număr bare premontaj",
    unit: "buc",
    placeholder: "2",
    helper: "Implicit 2: o bară sus și una jos.",
    min: 1,
    optional: true,
  },
  {
    key: "mounting_bar_profile",
    label: "Profil bare premontaj",
    unit: "mm",
    placeholder: "30x30x1.5",
    helper:
      "Preț confirmat momentan pentru 30×30×1.5. Alte profile pot necesita preț separat în Pricing.",
    min: 0,
    optional: true,
  },
  {
    key: "back_bevel_enabled",
    label: "Șanfren spate litere",
    unit: "",
    placeholder: "",
    helper:
      "Opțional. Dacă este bifat, spatele Forex 10 mm se calculează cu 2 treceri suplimentare (5 treceri în loc de 3).",
    min: 0,
    boolean: true,
    optional: true,
  },
  {
    key: "selected_psu_watts",
    label: "Putere sursă LED",
    unit: "W",
    placeholder: "100",
    helper: "Selectați varianta PSU (60 / 100 / 160 / 200 W).",
    min: 0,
    selectOptions: VOLUMETRIC_PSU_WATTAGE_OPTIONS,
  },
  {
    key: "paint_tube_count",
    label: "Tuburi vopsea RAL estimate",
    unit: "tub",
    placeholder: "3",
    helper:
      "Doar când cantul se vopsește RAL (nu pentru cant alb/negru din stoc). Estimare: ~1 tub / 6 ml perimetru.",
    min: 0,
  },
  {
    key: "led_module_count",
    label: "Module LED (calculat)",
    unit: "buc",
    placeholder: "180",
    helper: `Calcul: ceil(perimetru_m × 1000 / ${VOLUMETRIC_LED_PITCH_MM}) — nu introduceți manual dacă perimetrul e completat.`,
    min: 0,
    computed: true,
  },
];

export function isVolumetricLettersTemplateCode(
  templateCode: string | undefined | null
): boolean {
  const normalized = (templateCode ?? "").trim().toUpperCase();
  return normalized === TPL_VOLUMETRIC_LETTERS || normalized === TPL_VOLUMETRIC_LETTERS_V2.toUpperCase();
}

export function computeLedModuleCountFromPerimeter(
  letterPerimeterM: number
): number {
  if (!Number.isFinite(letterPerimeterM) || letterPerimeterM <= 0) {
    return 0;
  }
  return Math.ceil((letterPerimeterM * 1000) / VOLUMETRIC_LED_PITCH_MM);
}

/** Geometry / costing metrics that must not be invented from intake capture. */
export const VOLUMETRIC_MANUAL_GEOMETRY_KEYS = [
  "letter_face_area_m2",
  "letter_perimeter_m",
  "mounting_template_area_m2",
] as const;

export interface VolumetricIntakePrefillField {
  key: string;
  label: string;
  value: string;
}

export interface VolumetricIntakePrefillSummary {
  prefilledFields: VolumetricIntakePrefillField[];
  manualGeometryFields: Array<{ key: string; label: string }>;
  manualOtherFields: Array<{ key: string; label: string }>;
  warnings: string[];
}

function fieldLabel(key: string): string {
  return (
    VOLUMETRIC_QUOTE_INPUT_FIELDS.find((f) => f.key === key)?.label ?? key
  );
}

function enumLabel(
  fieldKey: string,
  value: string
): string {
  const field = VOLUMETRIC_QUOTE_INPUT_FIELDS.find((f) => f.key === fieldKey);
  return (
    field?.enumOptions?.find((o) => o.value === value)?.label ?? value
  );
}

/** Map intake face_finish (legacy) → canonical face_finish_type for costing. */
export function mapIntakeFaceFinishToQuoteType(
  faceFinish: IntakeProductSpec["face_finish"] | undefined
): VolumetricFaceFinishType | undefined {
  const canonical = resolveIntakeFaceFinishType({ face_finish: faceFinish });
  const costing = intakeFaceFinishToQuoteCostingType(canonical);
  return costing as VolumetricFaceFinishType | undefined;
}

/** Map intake mounting fields → mounting_system. */
export function mapIntakeMountingToQuoteSystem(
  spec: Pick<
    IntakeProductSpec,
    "mounting_type" | "premounting_type" | "premount_bar_material" | "mounting_system"
  >
): VolumetricMountingSystem | undefined {
  const resolved = resolveIntakeMountingSystem(spec as IntakeProductSpec);
  return resolved as VolumetricMountingSystem | undefined;
}

/** Intake premounted+none or explicit flag → Forex mounting template enabled. */
export function mapIntakeMountingTemplateEnabled(
  spec: Pick<
    IntakeProductSpec,
    "mounting_type" | "premounting_type" | "mounting_template_enabled"
  >
): boolean | undefined {
  return resolveIntakeMountingTemplateEnabled(spec as IntakeProductSpec);
}

const VOLUMETRIC_METADATA_STRING_KEYS = [
  "paint_ral_code",
  "paint_ral_name",
  "paint_finish",
  "face_vinyl_color_code",
  "face_vinyl_color_name",
  "face_vinyl_finish",
  "face_vinyl_notes",
  "mounting_notes",
  "lighting_notes",
] as const;

export const ALLOWED_RETURN_DEPTH_MM = [30, 60, 80, 100] as const;

/** Canonical return depth — prefers return_depth_mm, accepts depth_mm alias. */
export function effectiveReturnDepthMm(
  spec: IntakeProductSpec | null | undefined
): number | undefined {
  if (!spec) return undefined;
  if (
    spec.return_depth_mm != null &&
    (ALLOWED_RETURN_DEPTH_MM as readonly number[]).includes(spec.return_depth_mm)
  ) {
    return spec.return_depth_mm;
  }
  if (
    spec.depth_mm != null &&
    (ALLOWED_RETURN_DEPTH_MM as readonly number[]).includes(spec.depth_mm)
  ) {
    return spec.depth_mm;
  }
  return undefined;
}

/** Cant alb/negru din stoc — fără vopsire RAL pe lateral. */
export function isCantRalPaintEnabled(
  spec: Pick<IntakeProductSpec, "volume_finish"> | null | undefined
): boolean {
  return spec?.volume_finish === "paint_after_face_miter_bond";
}

/** Operator estimate — ~1 tub per 6 ml perimetru cant (Product 001 reference). */
export function estimatePaintTubeCount(input: {
  letter_perimeter_m?: number | null;
  letter_count?: number | null;
}): number {
  const perimeter = input.letter_perimeter_m;
  if (perimeter != null && Number.isFinite(perimeter) && perimeter > 0) {
    return Math.max(1, Math.ceil(perimeter / 6));
  }
  const count = input.letter_count;
  if (count != null && Number.isFinite(count) && count >= 1) {
    return Math.max(1, Math.ceil(count / 3));
  }
  return 1;
}

/** Apply enum defaults for volumetric wizard state. */
export interface VolumetricQuoteInputValidationContext {
  /** Step 2 assembly width — enables auto bar length when override is empty. */
  widthMm?: number;
  /** When false, paint_tube_count is not required for simulate. */
  cantRalPaintEnabled?: boolean;
}

export function applyVolumetricQuoteInputDefaults(
  values: Record<string, string>,
  spec?: IntakeProductSpec | null
): Record<string, string> {
  const next = { ...values };
  if (next.mounting_system === "forex_template") {
    next.mounting_system = VOLUMETRIC_DEFAULT_MOUNTING_SYSTEM;
    next.mounting_template_enabled = "true";
  }
  for (const field of VOLUMETRIC_QUOTE_INPUT_FIELDS) {
    if (!field.enumOptions) continue;
    if (!next[field.key]) {
      next[field.key] = field.defaultEnum ?? field.enumOptions[0]?.value ?? "";
    }
  }
  if (!next.mounting_template_enabled) {
    next.mounting_template_enabled = VOLUMETRIC_DEFAULT_MOUNTING_TEMPLATE_ENABLED
      ? "true"
      : "false";
  }
  if (!next.mounting_bar_profile) {
    next.mounting_bar_profile = VOLUMETRIC_DEFAULT_MOUNTING_BAR_PROFILE;
  }
  if (!next.mounting_bar_count) {
    next.mounting_bar_count = "2";
  }
  return enrichVolumetricQuoteInputStrings(next, spec);
}

function assignPrefillPositive(
  out: Record<string, string>,
  key: string,
  value: number | undefined,
  opts?: { allowed?: number[]; min?: number }
): void {
  if (value == null || !Number.isFinite(value) || value <= (opts?.min ?? 0)) return;
  if (opts?.allowed && !opts.allowed.includes(value)) return;
  out[key] = String(value);
}

/** Safe prefill from intake product_spec_json — no invented geometry.
 * TODO(finish-assignment): consume letterGroupFinishAssignments when CostEngine supports per-group inputs.
 */
export function mapProductSpecToVolumetricQuotePrefill(
  spec: IntakeProductSpec | null | undefined
): Record<string, string> {
  const out: Record<string, string> = {};
  if (!spec) return out;
  spec = getEffectiveQuoteGeometrySpec(spec) ?? spec;

  const depth = effectiveReturnDepthMm(spec);
  assignPrefillPositive(out, "return_depth_mm", depth, {
    allowed: [30, 60, 80, 100],
  });
  assignPrefillPositive(out, "depth_mm", depth, {
    allowed: [30, 60, 80, 100],
  });
  assignPrefillPositive(out, "width_mm", spec.width_mm);
  assignPrefillPositive(out, "height_mm", spec.height_mm ?? spec.letter_height_mm);
  assignPrefillPositive(out, "letter_face_area_m2", spec.letter_face_area_m2);
  assignPrefillPositive(out, "letter_perimeter_m", spec.letter_perimeter_m);
  assignPrefillPositive(out, "letter_count", spec.letter_count, { min: 1 });
  assignPrefillPositive(out, "mounting_template_area_m2", spec.mounting_template_area_m2);
  if (isCantRalPaintEnabled(spec)) {
    assignPrefillPositive(out, "paint_tube_count", spec.paint_tube_count, { min: 1 });
    const ral = spec.paint_ral_code?.trim() ?? spec.ral_color?.trim();
    if (ral) out.paint_ral_code = ral;
  }
  assignPrefillPositive(out, "mounting_bar_count", spec.mounting_bar_count, { min: 1 });
  assignPrefillPositive(out, "mounting_bar_length_m", spec.mounting_bar_length_m);
  assignPrefillPositive(out, "face_vinyl_roll_width_mm", spec.face_vinyl_roll_width_mm, {
    allowed: [1000, 1260],
  });

  const templateMode = resolveMountingTemplateMode(spec);
  out.mounting_template_enabled = templateMode === "none" ? "false" : "true";
  out.mounting_template_material_type = templateMode;

  if (isIntakeIlluminationDisabled(spec)) {
    out.illumination_type = "non_illuminated";
    out.lighting_system_type = "none";
  } else {
    out.illumination_type = "frontlit";
    out.lighting_system_type =
      spec.lighting_system_type === "led_strip" ? "led_strip" : "led_modules";
    assignPrefillPositive(out, "selected_psu_watts", spec.selected_psu_watts, {
      allowed: [...VOLUMETRIC_PSU_WATTAGE_OPTIONS],
    });
    if (
      !out.selected_psu_watts &&
      spec.psu_allocation_status === "ok" &&
      Array.isArray(spec.psu_configuration) &&
      spec.psu_configuration.length > 0
    ) {
      const maxUnit = Math.max(...spec.psu_configuration);
      assignPrefillPositive(out, "selected_psu_watts", maxUnit, {
        allowed: [...VOLUMETRIC_PSU_WATTAGE_OPTIONS],
      });
    }
    assignPrefillPositive(out, "total_led_watts", spec.total_led_watts);
    assignPrefillPositive(out, "required_psu_watts", spec.required_psu_watts);
  }

  if (resolveIntakeBackBevelEnabled(spec)) {
    out.back_bevel_enabled = "true";
  }

  const faceCanonical = resolveIntakeFaceFinishType(spec);
  const faceCosting = intakeFaceFinishToQuoteCostingType(faceCanonical);
  if (faceCosting) {
    out.face_finish_type = faceCosting;
  }
  if (faceCanonical === "oracal_8500") {
    out.face_finish_subtype = "oracal_8500";
  }

  const mounting = resolveIntakeMountingSystem(spec);
  if (mounting) {
    out.mounting_system = mounting;
  }

  if (spec.mounting_bar_profile?.trim()) {
    out.mounting_bar_profile = spec.mounting_bar_profile.trim();
  }

  for (const key of VOLUMETRIC_METADATA_STRING_KEYS) {
    if (
      (key === "paint_ral_code" || key === "paint_ral_name") &&
      !isCantRalPaintEnabled(spec)
    ) {
      continue;
    }
    const raw = spec[key as keyof IntakeProductSpec];
    if (typeof raw === "string" && raw.trim()) {
      out[key] = raw.trim();
    }
  }
  if (isCantRalPaintEnabled(spec) && !out.paint_ral_code && spec.ral_color?.trim()) {
    out.paint_ral_code = spec.ral_color.trim();
  }

  return out;
}

/** UI summary for Intake → QuoteWizard — which keys are prefilled vs manual. */
export function describeVolumetricIntakePrefill(
  spec: IntakeProductSpec | null | undefined
): VolumetricIntakePrefillSummary {
  const prefill = mapProductSpecToVolumetricQuotePrefill(spec);
  const prefilledFields = Object.entries(prefill).map(([key, value]) => ({
    key,
    label: fieldLabel(key),
    value:
      key === "face_finish_type" || key === "mounting_system"
        ? enumLabel(key, value)
        : value,
  }));

  const manualGeometryFields = VOLUMETRIC_MANUAL_GEOMETRY_KEYS.map((key) => ({
    key,
    label: fieldLabel(key),
  }));

  const manualOtherFields = VOLUMETRIC_QUOTE_INPUT_FIELDS.filter(
    (f) =>
      !f.computed &&
      !f.optional &&
      !VOLUMETRIC_MANUAL_GEOMETRY_KEYS.includes(
        f.key as (typeof VOLUMETRIC_MANUAL_GEOMETRY_KEYS)[number]
      ) &&
      prefill[f.key] === undefined &&
      (f.key !== "paint_tube_count" || isCantRalPaintEnabled(spec))
  ).map((f) => ({ key: f.key, label: f.label }));

  const warnings: string[] = [];
  if (!spec || Object.keys(spec).length === 0) {
    warnings.push(
      "Specificația Product 001 lipsește — completați manual toți parametrii de cost."
    );
  } else if (!prefill.return_depth_mm) {
    warnings.push(
      "Adâncimea profil (return_depth_mm) nu este salvată în intake — selectați 30 / 60 / 80 / 100 mm în wizard."
    );
  }

  const face = resolveIntakeFaceFinishType(spec ?? {});
  if (face === "oracal_651" || face === "oracal_8500") {
    if (!prefill.face_vinyl_color_code) {
      warnings.push(
        "Cod culoare Oracal lipsește în intake — completați în cerere sau în wizard înainte de producție."
      );
    }
    if (!prefill.face_vinyl_roll_width_mm) {
      warnings.push(
        "Lățime rolă Oracal (1000 / 1260 mm) lipsește în intake — necesară pentru producție."
      );
    }
  }
  if (
    isCantRalPaintEnabled(spec) &&
    (spec?.paint_tube_count ?? 0) > 0 &&
    !prefill.paint_ral_code
  ) {
    warnings.push(
      "Cod RAL vopsea necompletat în intake — informație de producție, nu blochează simulate."
    );
  }

  return {
    prefilledFields,
    manualGeometryFields,
    manualOtherFields,
    warnings,
  };
}

function parsePositiveField(
  values: Record<string, string>,
  key: string
): number | undefined {
  const raw = values[key];
  if (raw === undefined || raw === "") return undefined;
  const n = Number(raw);
  if (!Number.isFinite(n) || n < 0) return undefined;
  return n;
}

/** Build numeric quote_input for CostEngine (includes derived led_module_count + psu_watts mirror). */
export function buildVolumetricQuoteInputPayload(
  values: Record<string, string>
): QuoteInputPayload {
  const payload: QuoteInputPayload = {};
  for (const field of VOLUMETRIC_QUOTE_INPUT_FIELDS) {
    if (field.computed || field.boolean || field.enumOptions) continue;
    if (
      field.key === "mounting_bar_length_m" ||
      field.key === "mounting_bar_count" ||
      field.key === "mounting_bar_profile"
    ) {
      continue;
    }
    const n = parsePositiveField(values, field.key);
    if (n === undefined) continue;
    if (field.key === "letter_count" && n < 1) continue;
    if (field.key === "paint_tube_count" && n <= 0) continue;
    payload[field.key] = n;
  }

  const illuminationDisabled =
    values.illumination_type === "non_illuminated" || values.lighting_system_type === "none";

  if (!illuminationDisabled) {
    const perimeter = parsePositiveField(values, "letter_perimeter_m");
    if (perimeter != null && perimeter > 0) {
      payload.led_module_count = computeLedModuleCountFromPerimeter(perimeter);
    } else {
      const manualLed = parsePositiveField(values, "led_module_count");
      if (manualLed != null && manualLed > 0) {
        payload.led_module_count = manualLed;
      }
    }

    const psu = payload.selected_psu_watts;
    if (psu != null) {
      payload.psu_watts = psu;
    }
    if (values.illumination_type === "frontlit") {
      payload.illumination_type = "frontlit";
    }
    const lighting = values.lighting_system_type?.trim();
    if (lighting === "led_modules" || lighting === "led_strip") {
      payload.lighting_system_type = lighting;
    }
  } else {
    payload.illumination_type = "non_illuminated";
    payload.lighting_system_type = "none";
    delete payload.led_module_count;
    delete payload.selected_psu_watts;
    delete payload.psu_watts;
  }

  payload.back_bevel_enabled = values.back_bevel_enabled === "true";

  const templateMaterial = values.mounting_template_material_type?.trim();
  if (templateMaterial === "none" || templateMaterial === "paper" || templateMaterial === "forex") {
    payload.mounting_template_material_type = templateMaterial;
    payload.mounting_template_enabled = templateMaterial !== "none";
  } else {
    payload.mounting_template_enabled = values.mounting_template_enabled !== "false";
  }

  const mountRaw = values.mounting_system ?? VOLUMETRIC_DEFAULT_MOUNTING_SYSTEM;
  if (mountRaw === "steel_bars" || mountRaw === "aluminum_bars") {
    payload.mounting_bar_profile =
      values.mounting_bar_profile?.trim() || VOLUMETRIC_DEFAULT_MOUNTING_BAR_PROFILE;
    const barCount = parsePositiveField(values, "mounting_bar_count");
    payload.mounting_bar_count = barCount != null && barCount >= 1 ? barCount : 2;
    const barOverride = parsePositiveField(values, "mounting_bar_length_m");
    if (barOverride != null && barOverride > 0) {
      payload.mounting_bar_length_m = barOverride;
    }
  }

  for (const field of VOLUMETRIC_QUOTE_INPUT_FIELDS) {
    if (!field.enumOptions) continue;
    const raw = values[field.key] ?? field.defaultEnum;
    if (raw) {
      payload[field.key] = raw;
    }
  }

  for (const key of VOLUMETRIC_METADATA_STRING_KEYS) {
    const raw = values[key]?.trim();
    if (raw) {
      payload[key] = raw;
    }
  }

  const rollWidth = parsePositiveField(values, "face_vinyl_roll_width_mm");
  if (rollWidth === 1000 || rollWidth === 1260) {
    payload.face_vinyl_roll_width_mm = rollWidth;
  }

  const subtype = values.face_finish_subtype?.trim();
  if (subtype) {
    payload.face_finish_subtype = subtype;
  }

  const widthMm = parsePositiveField(values, "width_mm");
  if (widthMm != null && widthMm > 0) {
    payload.width_mm = widthMm;
  }

  return payload;
}

/** String form for wizard state after prefill + derived LED count. */
export function enrichVolumetricQuoteInputStrings(
  values: Record<string, string>,
  spec?: IntakeProductSpec | null
): Record<string, string> {
  const next = { ...values };
  const perimeter = parsePositiveField(values, "letter_perimeter_m");
  const illuminationDisabled =
    values.illumination_type === "non_illuminated" || values.lighting_system_type === "none";

  if (!illuminationDisabled) {
    if (perimeter != null && perimeter > 0) {
      next.led_module_count = String(
        computeLedModuleCountFromPerimeter(perimeter)
      );
    }
  } else {
    delete next.led_module_count;
    delete next.selected_psu_watts;
    delete next.psu_watts;
  }

  if (spec !== undefined) {
    const paintEnabled = isCantRalPaintEnabled(spec);
    if (!paintEnabled) {
      delete next.paint_tube_count;
      delete next.paint_ral_code;
      delete next.paint_ral_name;
    } else if (!next.paint_tube_count?.trim()) {
      next.paint_tube_count = String(
        estimatePaintTubeCount({
          letter_perimeter_m: perimeter,
          letter_count: parsePositiveField(values, "letter_count"),
        })
      );
    }
  }

  return next;
}

function isMountingTemplateEnabled(values: Record<string, string>): boolean {
  if (values.mounting_system === "forex_template") {
    return true;
  }
  return values.mounting_template_enabled !== "false";
}

function mountingUsesPremountBars(values: Record<string, string>): boolean {
  const raw = values.mounting_system ?? VOLUMETRIC_DEFAULT_MOUNTING_SYSTEM;
  return raw === "steel_bars" || raw === "aluminum_bars";
}

export function volumetricPremountBarsInputValid(
  values: Record<string, string>,
  context: VolumetricQuoteInputValidationContext = {}
): boolean {
  if (!mountingUsesPremountBars(values)) {
    return true;
  }
  const hasOverride =
    parsePositiveField(values, "mounting_bar_length_m") != null;
  const hasWidth =
    context.widthMm != null && Number.isFinite(context.widthMm) && context.widthMm > 0;
  return hasOverride || hasWidth;
}

export function volumetricQuoteInputStepValid(
  values: Record<string, string>,
  context: VolumetricQuoteInputValidationContext = {}
): boolean {
  for (const field of VOLUMETRIC_QUOTE_INPUT_FIELDS) {
    if (field.computed || field.boolean || field.optional) continue;
    if (field.enumOptions) {
      const raw = values[field.key] ?? field.defaultEnum ?? "";
      if (!field.enumOptions.some((o) => o.value === raw)) return false;
      continue;
    }
    if (
      field.key === "mounting_template_area_m2" &&
      !isMountingTemplateEnabled(values)
    ) {
      continue;
    }
    if (
      (field.key === "mounting_bar_length_m" || field.key === "mounting_bar_count") &&
      !mountingUsesPremountBars(values)
    ) {
      continue;
    }
    if (field.key === "paint_tube_count" && context.cantRalPaintEnabled !== true) {
      continue;
    }
    const raw = values[field.key];
    if (raw === undefined || raw === "") return false;
    const n = Number(raw);
    const min = field.key === "letter_count" ? 1 : field.min;
    if (!Number.isFinite(n) || n < min) return false;
    if (
      field.key === "selected_psu_watts" &&
      !VOLUMETRIC_PSU_WATTAGE_OPTIONS.includes(
        n as (typeof VOLUMETRIC_PSU_WATTAGE_OPTIONS)[number]
      )
    ) {
      return false;
    }
    if (
      field.key === "return_depth_mm" &&
      ![30, 60, 80, 100].includes(n)
    ) {
      return false;
    }
    if (field.key === "paint_tube_count" && n <= 0) {
      return false;
    }
  }
  const perimeter = parsePositiveField(values, "letter_perimeter_m");
  if (perimeter == null || perimeter <= 0) return false;
  if (!volumetricPremountBarsInputValid(values, context)) return false;
  return computeLedModuleCountFromPerimeter(perimeter) > 0;
}
