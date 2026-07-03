/**
 * TPL-VOLUMETRIC-LETTERS — template-specific quote workspace state.
 * Precedence: user edit > Work Intake prefill > template defaults.
 */

import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import {
  getEffectiveQuoteGeometrySpec,
  isVectorGeometryCurrentForQuote,
} from "@/lib/vectorGeometryInvalidation";
import {
  siteAuditToTerrainChecks,
  type IntakeSiteAuditJson,
} from "@/lib/intakeSiteAudit";
import {
  applyVolumetricQuoteInputDefaults,
  buildVolumetricQuoteInputPayload,
  effectiveReturnDepthMm,
  isCantRalPaintEnabled,
  isVolumetricLettersTemplateCode,
  mapProductSpecToVolumetricQuotePrefill,
  TPL_VOLUMETRIC_LETTERS,
  VOLUMETRIC_DEFAULT_MOUNTING_BAR_PROFILE,
  volumetricQuoteInputStepValid,
} from "@/lib/volumetricQuoteInput";

export type VolumetricCalculationMethod =
  | "vector_first"
  | "manual_geometry"
  | "quick_estimate";

export const VOLUMETRIC_TEMPLATE_DEFAULTS = {
  widthMm: 1000,
  heightMm: 2000,
  depthMm: 80,
} as const;

export const TPL_METAL_PREMOUNT_STRUCTURE = "TPL-METAL-PREMOUNT-STRUCTURE_v1";

const METAL_SUPPORT_MOUNTING_SYSTEMS = new Set(["steel_bars", "aluminum_bars"]);

export interface TerrainReadinessChecks {
  locationVerified: boolean;
  photosVerified: boolean;
  powerVerified: boolean;
  accessVerified: boolean;
}

export interface VolumetricQuoteFlowState {
  method: VolumetricCalculationMethod;
  text: string;
  widthMm: number;
  heightMm: number;
  depthMm: number;
  quoteInput: Record<string, string>;
  materialsExpanded: boolean;
  /** Keys suggested from intake (editable, not user-entered). */
  suggestedKeys: string[];
  /** Keys the operator edited in the quote flow. */
  userEditedKeys: string[];
  terrainChecks: TerrainReadinessChecks;
}

export type ClientMaterialCategory =
  | "vector"
  | "location_photo"
  | "sketch"
  | "reference"
  | "document"
  | "other";

export type ClientMaterialStatus =
  | "received"
  | "mapped"
  | "unverified"
  | "reference";

export interface ClientMaterialFile {
  id: string;
  name: string;
  category: ClientMaterialCategory;
  status: ClientMaterialStatus;
  /** Context only — never used for costing. */
  contextOnly: boolean;
}

export function shouldRouteToVolumetricQuoteFlow(
  templateCode: string | undefined | null
): boolean {
  return isVolumetricLettersTemplateCode(templateCode);
}

export interface VolumetricQuoteNavState {
  openWizard?: boolean;
  templateCode?: string;
  productSpec?: IntakeProductSpec | null;
  clientName?: string;
  intakeRequestId?: string;
  fromIntake?: boolean;
  confirmedTemplateCode?: string;
  deliveryType?: string;
  siteAudit?: IntakeSiteAuditJson | null;
  intakeStatus?: string;
}

/** True when intake handoff should show the volumetric workspace (not quotes list / spinner). */
export function shouldShowVolumetricQuoteWorkspace(
  wizardOpen: boolean,
  navState: Pick<VolumetricQuoteNavState, "templateCode"> | null | undefined
): boolean {
  return wizardOpen && shouldRouteToVolumetricQuoteFlow(navState?.templateCode);
}

export function shouldOpenWizardFromNav(
  navState: Pick<VolumetricQuoteNavState, "openWizard"> | null | undefined
): boolean {
  return Boolean(navState?.openWizard);
}

/**
 * Commercial handoff mode: source intake completed verification and opened QuoteWizard.
 * Reuses the current quote-input readiness pipeline — no separate handoff flag required.
 */
export function isVolumetricWorkIntakeHandoffCommercialMode(params: {
  openedFromIntake: boolean;
  embedded?: boolean;
  templateCode?: string | null;
  productSpec?: IntakeProductSpec | null;
}): boolean {
  if (!params.openedFromIntake || params.embedded) return false;
  if (!isVolumetricLettersTemplateCode(params.templateCode)) return false;
  const spec = params.productSpec;
  if (!spec || Object.keys(spec).length === 0) return false;

  const flowState = buildInitialVolumetricQuoteFlowState(spec);
  return isSimulateInputReady(flowState, spec);
}

function parsePositive(raw: string | undefined): number | undefined {
  if (raw === undefined || raw === "") return undefined;
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) return undefined;
  return n;
}

function dimensionFromPrefill(
  values: Record<string, string>,
  key: string,
  specValue: number | undefined,
  fallback: number
): number {
  const fromValues = parsePositive(values[key]);
  if (fromValues != null) return fromValues;
  if (specValue != null && Number.isFinite(specValue) && specValue > 0) {
    return specValue;
  }
  return fallback;
}

function parsePositiveFromRecord(
  values: Record<string, unknown>,
  key: string
): number | undefined {
  const raw = values[key];
  if (raw === undefined || raw === null || raw === "") return undefined;
  const n = Number(raw);
  if (!Number.isFinite(n) || n <= 0) return undefined;
  return n;
}

function buildMetalSupportLinkedModule(input: {
  quoteInput: Record<string, unknown>;
  widthMm: number;
}): Record<string, unknown> | null {
  const mountingSystem = String(input.quoteInput.mounting_system ?? "").trim();
  if (!METAL_SUPPORT_MOUNTING_SYSTEMS.has(mountingSystem)) return null;

  const barCount = parsePositiveFromRecord(input.quoteInput, "mounting_bar_count") ?? 2;
  const explicitLength = parsePositiveFromRecord(input.quoteInput, "mounting_bar_length_m");
  const lengthM = explicitLength ?? (input.widthMm / 1000) * barCount;
  const barMaterial = mountingSystem === "aluminum_bars" ? "aluminum" : "steel";

  return {
    module_template_code: TPL_METAL_PREMOUNT_STRUCTURE,
    relation_type: "optional_addon",
    pricing_mode: "separate_quote_line",
    execution_mode: "linked_child_work",
    input_payload: {
      premount_bar_length_ml: Number(lengthM.toFixed(6)),
      mounting_bar_length_m: Number(lengthM.toFixed(6)),
      letter_perimeter_m: Number(lengthM.toFixed(6)),
      mounting_bar_count: barCount,
      mounting_bar_profile:
        String(input.quoteInput.mounting_bar_profile ?? "").trim() ||
        VOLUMETRIC_DEFAULT_MOUNTING_BAR_PROFILE,
      bar_material: barMaterial,
      width_mm: input.widthMm,
    },
  };
}

export function deriveDefaultCalculationMethod(
  spec: IntakeProductSpec | null | undefined
): VolumetricCalculationMethod {
  if (!spec) return "manual_geometry";
  if (spec.intake_input_pathway === "vector") return "vector_first";
  if (spec.intake_input_pathway === "quick_estimate") return "quick_estimate";
  if (spec.intake_input_pathway === "manual") return "manual_geometry";
  if (
    spec.vector_file_name?.trim() ||
    (spec.svg_layer_mappings &&
      Object.keys(spec.svg_layer_mappings).length > 0)
  ) {
    return "vector_first";
  }
  if (
    spec.letter_face_area_m2 != null &&
    spec.letter_perimeter_m != null &&
    spec.letter_count != null
  ) {
    return "manual_geometry";
  }
  return "manual_geometry";
}

export function suggestMountingTemplateAreaM2(
  values: Record<string, string>,
  spec: IntakeProductSpec | null | undefined
): { values: Record<string, string>; suggestedKeys: string[] } {
  const next = { ...values };
  const suggestedKeys: string[] = [];
  const enabled =
    next.mounting_template_enabled === "true" ||
    spec?.mounting_template_enabled === true;
  if (!enabled || next.mounting_template_area_m2?.trim()) {
    return { values: next, suggestedKeys };
  }
  const areaRaw =
    next.letter_face_area_m2?.trim() ||
    (spec?.letter_face_area_m2 != null
      ? String(spec.letter_face_area_m2)
      : "");
  if (areaRaw) {
    next.mounting_template_area_m2 = areaRaw;
    suggestedKeys.push("mounting_template_area_m2");
  }
  return { values: next, suggestedKeys };
}

export function buildInitialVolumetricQuoteFlowState(
  spec: IntakeProductSpec | null | undefined,
  siteAudit?: IntakeSiteAuditJson | null
): VolumetricQuoteFlowState {
  const effectiveSpec = getEffectiveQuoteGeometrySpec(spec);
  const prefill = mapProductSpecToVolumetricQuotePrefill(effectiveSpec);
  let quoteInput = applyVolumetricQuoteInputDefaults(prefill, effectiveSpec);
  const { values: withSuggestion, suggestedKeys } =
    suggestMountingTemplateAreaM2(quoteInput, effectiveSpec);
  quoteInput = withSuggestion;

  const depthCandidate =
    effectiveReturnDepthMm(effectiveSpec) ??
    parsePositive(quoteInput.return_depth_mm) ??
    parsePositive(quoteInput.depth_mm);
  const depthMm =
    depthCandidate != null &&
    Number.isFinite(depthCandidate) &&
    depthCandidate > 0
      ? depthCandidate
      : VOLUMETRIC_TEMPLATE_DEFAULTS.depthMm;
  quoteInput = {
    ...quoteInput,
    return_depth_mm: quoteInput.return_depth_mm?.trim() || String(depthMm),
    depth_mm: quoteInput.depth_mm?.trim() || String(depthMm),
  };

  return {
    method: deriveDefaultCalculationMethod(effectiveSpec),
    text: effectiveSpec?.text?.trim() ?? "",
    widthMm: dimensionFromPrefill(
      quoteInput,
      "width_mm",
      effectiveSpec?.width_mm,
      VOLUMETRIC_TEMPLATE_DEFAULTS.widthMm
    ),
    heightMm: dimensionFromPrefill(
      quoteInput,
      "height_mm",
      effectiveSpec?.height_mm ?? effectiveSpec?.letter_height_mm,
      VOLUMETRIC_TEMPLATE_DEFAULTS.heightMm
    ),
    depthMm,
    quoteInput,
    materialsExpanded: false,
    suggestedKeys,
    userEditedKeys: [],
    terrainChecks: siteAuditToTerrainChecks(siteAudit),
  };
}

export function switchCalculationMethod(
  state: VolumetricQuoteFlowState,
  method: VolumetricCalculationMethod
): VolumetricQuoteFlowState {
  return { ...state, method };
}

export function updateFlowDimension(
  state: VolumetricQuoteFlowState,
  field: "widthMm" | "heightMm" | "depthMm",
  value: number,
  quoteInputKey: "width_mm" | "height_mm" | "depth_mm"
): VolumetricQuoteFlowState {
  let userEditedKeys = state.userEditedKeys.includes(quoteInputKey)
    ? [...state.userEditedKeys]
    : [...state.userEditedKeys, quoteInputKey];
  const quoteInput = { ...state.quoteInput, [quoteInputKey]: String(value) };
  if (quoteInputKey === "depth_mm") {
    quoteInput.return_depth_mm = String(value);
    if (!userEditedKeys.includes("return_depth_mm")) {
      userEditedKeys = [...userEditedKeys, "return_depth_mm"];
    }
  }
  return {
    ...state,
    [field]: value,
    userEditedKeys,
    quoteInput,
  };
}

export function updateFlowQuoteInputField(
  state: VolumetricQuoteFlowState,
  key: string,
  value: string
): VolumetricQuoteFlowState {
  let userEditedKeys = state.userEditedKeys.includes(key)
    ? [...state.userEditedKeys]
    : [...state.userEditedKeys, key];
  const suggestedKeys = state.suggestedKeys.filter((k) => k !== key);
  const quoteInput = { ...state.quoteInput, [key]: value };
  let depthMm = state.depthMm;
  if (key === "return_depth_mm") {
    quoteInput.depth_mm = value;
    const parsed = parsePositive(value);
    if (parsed != null) depthMm = parsed;
    if (!userEditedKeys.includes("depth_mm")) {
      userEditedKeys = [...userEditedKeys, "depth_mm"];
    }
  }
  return {
    ...state,
    depthMm,
    userEditedKeys,
    suggestedKeys,
    quoteInput,
  };
}

export function updateFlowText(
  state: VolumetricQuoteFlowState,
  text: string
): VolumetricQuoteFlowState {
  return {
    ...state,
    text,
    userEditedKeys: state.userEditedKeys.includes("text")
      ? state.userEditedKeys
      : [...state.userEditedKeys, "text"],
  };
}

export function buildEffectiveQuoteInputStrings(
  state: VolumetricQuoteFlowState
): Record<string, string> {
  return {
    ...state.quoteInput,
    width_mm: String(state.widthMm),
    height_mm: String(state.heightMm),
    depth_mm: String(state.depthMm),
  };
}

export function buildSimulateQuoteInputPayload(
  state: VolumetricQuoteFlowState,
  spec?: IntakeProductSpec | null
) {
  const strings = buildEffectiveQuoteInputStrings(state);
  const depth =
    parsePositive(strings.return_depth_mm) ??
    parsePositive(strings.depth_mm) ??
    state.depthMm;
  const syncedStrings = {
    ...strings,
    return_depth_mm: String(depth),
    depth_mm: String(depth),
  };
  const qi = buildVolumetricQuoteInputPayload(syncedStrings);
  const effectiveSpec = getEffectiveQuoteGeometrySpec(spec);
  if (!isCantRalPaintEnabled(effectiveSpec)) {
    delete qi.paint_tube_count;
    delete qi.paint_ral_code;
    delete qi.paint_ral_name;
    qi.volume_finish = "none";
  } else {
    qi.volume_finish =
      effectiveSpec?.volume_finish ?? "paint_after_face_miter_bond";
  }
  const payload = {
    ...qi,
    width_mm: state.widthMm,
    height_mm: state.heightMm,
    depth_mm: depth,
    return_depth_mm: depth,
  };
  const linkedMetalSupport = buildMetalSupportLinkedModule({
    quoteInput: payload,
    widthMm: state.widthMm,
  });
  if (!linkedMetalSupport) return payload;
  return {
    ...payload,
    parent_mounting_system: payload.mounting_system,
    mounting_system: "direct_wall",
    metal_support_required: true,
    linked_support_pricing_mode: "separate_quote_line",
    support_module_template_code: TPL_METAL_PREMOUNT_STRUCTURE,
    linked_modules: [linkedMetalSupport],
  };
}

export function isSimulateInputReady(
  state: VolumetricQuoteFlowState,
  spec?: IntakeProductSpec | null
): boolean {
  const effectiveSpec = getEffectiveQuoteGeometrySpec(spec);
  return volumetricQuoteInputStepValid(buildEffectiveQuoteInputStrings(state), {
    widthMm: state.widthMm,
    cantRalPaintEnabled: isCantRalPaintEnabled(effectiveSpec),
  });
}

export function hasIntakeGeometryPrefill(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec) return false;
  return (
    (spec.width_mm != null && spec.width_mm > 0) ||
    (spec.height_mm != null && spec.height_mm > 0) ||
    (spec.letter_height_mm != null && spec.letter_height_mm > 0)
  );
}

export function hasExtractedVectorGeometry(
  spec: IntakeProductSpec | null | undefined
): boolean {
  if (!spec || !isVectorGeometryCurrentForQuote(spec)) return false;
  const src = spec.vector_metrics_source;
  if (src !== "svg_analysis" && src !== "dxf_analysis") return false;
  return (
    spec.letter_face_area_m2 != null &&
    spec.letter_perimeter_m != null &&
    spec.letter_count != null
  );
}

export function buildClientMaterialFiles(
  spec: IntakeProductSpec | null | undefined,
  description?: string
): ClientMaterialFile[] {
  const files: ClientMaterialFile[] = [];
  if (spec?.vector_file_name?.trim()) {
    const mapped =
      spec.vector_layer_mapping_status === "mapped" ||
      Boolean(spec.svg_layer_mappings && Object.keys(spec.svg_layer_mappings).length);
    files.push({
      id: "vector-primary",
      name: spec.vector_file_name.trim(),
      category: "vector",
      status: mapped ? "mapped" : "received",
      contextOnly: false,
    });
  }
  if (description?.trim()) {
    const photoMatches = description.match(
      /\b[\w.-]+\.(jpg|jpeg|png|webp)\b/gi
    );
    for (const match of photoMatches ?? []) {
      files.push({
        id: `photo-${match}`,
        name: match,
        category: "location_photo",
        status: "unverified",
        contextOnly: true,
      });
    }
  }
  return files;
}

export function summarizeClientMaterials(files: ClientMaterialFile[]): string {
  if (files.length === 0) return "Materiale client: niciun fișier înregistrat";
  const mapped = files.filter((f) => f.status === "mapped").length;
  const unverified = files.filter((f) => f.status === "unverified").length;
  const parts = [`Materiale client: ${files.length} fișiere`];
  if (mapped > 0) parts.push("vector mapat");
  if (unverified > 0) parts.push(`${unverified} poze neverificate`);
  return parts.join(" · ");
}

export function countTerrainChecks(checks: TerrainReadinessChecks): {
  done: number;
  total: number;
} {
  const items = [
    checks.locationVerified,
    checks.photosVerified,
    checks.powerVerified,
  ];
  return {
    done: items.filter(Boolean).length,
    total: items.length,
  };
}

export { TPL_VOLUMETRIC_LETTERS };
