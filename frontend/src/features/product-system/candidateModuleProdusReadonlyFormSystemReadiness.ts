import {
  CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
  CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES,
  CANDIDATE_MODULE_EXPECTED_ROW_COUNT,
  CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES,
  normalizeCandidateModuleProdusTemplateCode,
  type CandidateModuleProdusCompletenessAssessment,
  type CandidateModuleProdusContractDriftAssessment,
  type CandidateModuleProdusLiveTemplateRow,
  type CandidateModuleProdusTemplateCode,
} from "./candidateModuleProdusReadonlyCompleteness";
import type { CandidateModuleProdusDossierAlignmentAssessment } from "./candidateModuleProdusReadonlyDossierAlignment";
import type { CandidateModuleProdusOwnerSummary } from "./candidateModuleProdusReadonlyOwnerSummary";

export type CandidateModuleProdusFormSystemRole = "compose_component_sections" | "own_component_fields";

export type CandidateModuleProdusFieldSource =
  | "svg_suggestion"
  | "manual_operator_input"
  | "catalog_default_readonly";

export type CandidateModuleProdusRequiredStatePolicy =
  | "suggested_not_confirmed"
  | "confirmed_required_before_product_truth";

export type CandidateModuleProdusFormForbiddenNow =
  | "no_runtime_form_activation"
  | "no_work_intake_exposure"
  | "no_product_truth_write"
  | "no_pricing"
  | "no_quote_order_execution";

export type CandidateModuleProdusFormSystemRuntimeLinkState =
  | "NOT_LINKED_YET"
  | "READONLY_CONTRACT_ONLY"
  | "BLOCKED_RUNTIME_FORM_ACTIVATION_LEAK";

export type CandidateModuleProdusOverallFormReadinessState =
  | "READONLY_READY_FOR_MAPPING"
  | "READONLY_FALLBACK_ONLY"
  | "READONLY_PARTIAL_LIVE_ROWS"
  | "BLOCKED_INVALID_LIVE_STATE"
  | "BLOCKED_FORM_ACTIVATION_LEAK";

export type CandidateModuleProdusComposerFormReadinessEntry = {
  templateCode: typeof CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE;
  role: "product_composer";
  formSystemRole: "compose_component_sections";
  ownsTruth: false;
  coordinates: string[];
  forbiddenNow: CandidateModuleProdusFormForbiddenNow[];
};

export type CandidateModuleProdusComponentFormReadinessEntry = {
  templateCode: CandidateModuleProdusTemplateCode;
  role: "component_template";
  formSystemRole: "own_component_fields";
  ownsTruth: true;
  fieldGroups: string[];
  possibleSources: CandidateModuleProdusFieldSource[];
  requiredStatePolicy: CandidateModuleProdusRequiredStatePolicy[];
  forbiddenNow: CandidateModuleProdusFormForbiddenNow[];
};

export type CandidateModuleProdusFormReadinessEntry =
  | CandidateModuleProdusComposerFormReadinessEntry
  | CandidateModuleProdusComponentFormReadinessEntry;

export const CANDIDATE_MODULE_FORM_FORBIDDEN_NOW: CandidateModuleProdusFormForbiddenNow[] = [
  "no_runtime_form_activation",
  "no_work_intake_exposure",
  "no_product_truth_write",
  "no_pricing",
  "no_quote_order_execution",
];

export const CANDIDATE_MODULE_FORM_SYSTEM_READINESS_CONTRACT: CandidateModuleProdusFormReadinessEntry[] = [
  {
    templateCode: CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
    role: "product_composer",
    formSystemRole: "compose_component_sections",
    ownsTruth: false,
    coordinates: ["selected components", "component compatibility", "overall readiness"],
    forbiddenNow: [...CANDIDATE_MODULE_FORM_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-FACE_v1",
    role: "component_template",
    formSystemRole: "own_component_fields",
    ownsTruth: true,
    fieldGroups: ["face_material", "face_thickness", "face_finish_target", "face_cutting_method"],
    possibleSources: ["svg_suggestion", "manual_operator_input", "catalog_default_readonly"],
    requiredStatePolicy: ["suggested_not_confirmed", "confirmed_required_before_product_truth"],
    forbiddenNow: [...CANDIDATE_MODULE_FORM_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-BACK_v1",
    role: "component_template",
    formSystemRole: "own_component_fields",
    ownsTruth: true,
    fieldGroups: ["back_material", "back_thickness", "mounting_backing_mode", "cnc_or_cutting_preparation"],
    possibleSources: ["svg_suggestion", "manual_operator_input", "catalog_default_readonly"],
    requiredStatePolicy: ["suggested_not_confirmed", "confirmed_required_before_product_truth"],
    forbiddenNow: [...CANDIDATE_MODULE_FORM_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-RETURN-CANT_v1",
    role: "component_template",
    formSystemRole: "own_component_fields",
    ownsTruth: true,
    fieldGroups: ["return_material", "return_depth", "return_finish", "return_joining_method"],
    possibleSources: ["svg_suggestion", "manual_operator_input", "catalog_default_readonly"],
    requiredStatePolicy: ["suggested_not_confirmed", "confirmed_required_before_product_truth"],
    forbiddenNow: [...CANDIDATE_MODULE_FORM_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-LED_v1",
    role: "component_template",
    formSystemRole: "own_component_fields",
    ownsTruth: true,
    fieldGroups: ["illumination_mode", "led_type", "led_density", "power_supply_policy", "wiring_notes"],
    possibleSources: ["manual_operator_input", "catalog_default_readonly"],
    requiredStatePolicy: ["suggested_not_confirmed", "confirmed_required_before_product_truth"],
    forbiddenNow: [...CANDIDATE_MODULE_FORM_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-FINISH_v1",
    role: "component_template",
    formSystemRole: "own_component_fields",
    ownsTruth: true,
    fieldGroups: ["finish_type", "stock_color", "oracal_code", "ral_code", "print_lamination_policy"],
    possibleSources: ["manual_operator_input", "catalog_default_readonly"],
    requiredStatePolicy: ["suggested_not_confirmed", "confirmed_required_before_product_truth"],
    forbiddenNow: [...CANDIDATE_MODULE_FORM_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-MOUNTING_v1",
    role: "component_template",
    formSystemRole: "own_component_fields",
    ownsTruth: true,
    fieldGroups: ["mounting_surface", "spacer_policy", "template_drilling_policy", "site_installation_notes"],
    possibleSources: ["manual_operator_input", "catalog_default_readonly"],
    requiredStatePolicy: ["suggested_not_confirmed", "confirmed_required_before_product_truth"],
    forbiddenNow: [...CANDIDATE_MODULE_FORM_FORBIDDEN_NOW],
  },
];

export type CandidateModuleProdusFormSystemCompactFieldSummary = {
  label: string;
  fields: string;
};

export const CANDIDATE_MODULE_FORM_SYSTEM_COMPACT_SUMMARIES: CandidateModuleProdusFormSystemCompactFieldSummary[] = [
  { label: "Face", fields: "material, thickness, finish target" },
  { label: "Back", fields: "material, thickness, mounting backing" },
  { label: "Return/cant", fields: "material, depth, finish" },
  { label: "LED", fields: "mode, density, power supply" },
  { label: "Finish", fields: "stock/oracal/ral/print policy" },
  { label: "Mounting", fields: "surface, spacer, drilling/site notes" },
];

function safeParseJson<T>(raw: string | null | undefined, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function isCandidateModuleProdusFamilyRow(templateCode: string): boolean {
  const normalized = normalizeCandidateModuleProdusTemplateCode(templateCode);
  return CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES.some(
    (code) => normalizeCandidateModuleProdusTemplateCode(code) === normalized
  );
}

function detectFormActivationLeakSignals(liveTemplates: CandidateModuleProdusLiveTemplateRow[]): string[] {
  const issues: string[] = [];

  for (const row of liveTemplates) {
    if (!isCandidateModuleProdusFamilyRow(row.template_code)) continue;

    const notes = safeParseJson<Record<string, unknown>>(row.notes, {});
    if (notes.work_intake_exposed === true) issues.push(`work_intake_exposed_${row.template_code}`);
    if (notes.form_system_active === true) issues.push(`form_system_active_${row.template_code}`);
    if (notes.runtime_form_activation === true) issues.push(`runtime_form_activation_${row.template_code}`);
    if (notes.product_truth_write === true) issues.push(`product_truth_write_${row.template_code}`);
    if (notes.intake_v6_exposed === true) issues.push(`intake_v6_exposed_${row.template_code}`);
    if (notes.pricing_active === true) issues.push(`pricing_active_${row.template_code}`);
    if (notes.product_definition_active === true) issues.push(`product_definition_active_${row.template_code}`);
  }

  return issues;
}

export function validateCandidateModuleProdusFormSystemReadinessContract(
  contract: readonly CandidateModuleProdusFormReadinessEntry[] = CANDIDATE_MODULE_FORM_SYSTEM_READINESS_CONTRACT
): { valid: boolean; issues: string[] } {
  const issues: string[] = [];

  if (contract.length !== CANDIDATE_MODULE_EXPECTED_ROW_COUNT) {
    issues.push(`form_readiness_contract_row_count_${contract.length}`);
  }

  const seen = new Set<string>();
  let composerCount = 0;
  let componentCount = 0;

  for (const entry of contract) {
    const normalized = normalizeCandidateModuleProdusTemplateCode(entry.templateCode);
    if (seen.has(normalized)) issues.push(`form_readiness_duplicate_${entry.templateCode}`);
    seen.add(normalized);

    if (entry.role === "product_composer") {
      composerCount += 1;
      if (entry.ownsTruth !== false) issues.push(`composer_owns_truth_invalid_${entry.templateCode}`);
      if (entry.formSystemRole !== "compose_component_sections") {
        issues.push(`composer_form_role_invalid_${entry.templateCode}`);
      }
    } else {
      componentCount += 1;
      if (entry.ownsTruth !== true) issues.push(`component_owns_truth_invalid_${entry.templateCode}`);
      if (entry.fieldGroups.length === 0) issues.push(`component_field_groups_missing_${entry.templateCode}`);
    }
  }

  if (composerCount !== 1) issues.push(`form_readiness_composer_count_${composerCount}`);
  if (componentCount !== CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES.length) {
    issues.push(`form_readiness_component_count_${componentCount}`);
  }

  for (const expectedCode of CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES) {
    if (!seen.has(normalizeCandidateModuleProdusTemplateCode(expectedCode))) {
      issues.push(`form_readiness_missing_${expectedCode}`);
    }
  }

  return { valid: issues.length === 0, issues };
}

export type CandidateModuleProdusFormSystemReadinessAssessment = {
  expectedComponents: number;
  readinessContractEntries: number;
  runtimeFormSystemLinkState: CandidateModuleProdusFormSystemRuntimeLinkState;
  overallFormReadinessState: CandidateModuleProdusOverallFormReadinessState;
  missingComponentCodes: CandidateModuleProdusTemplateCode[];
  unsafeSignals: string[];
  contractEntries: CandidateModuleProdusFormReadinessEntry[];
  compactFieldSummaries: CandidateModuleProdusFormSystemCompactFieldSummary[];
};

export function assessCandidateModuleProdusFormSystemReadiness(
  completeness: CandidateModuleProdusCompletenessAssessment,
  dossier: CandidateModuleProdusDossierAlignmentAssessment,
  ownerSummary: CandidateModuleProdusOwnerSummary,
  options?: {
    drift?: CandidateModuleProdusContractDriftAssessment;
    liveTemplates?: CandidateModuleProdusLiveTemplateRow[];
    contract?: readonly CandidateModuleProdusFormReadinessEntry[];
  }
): CandidateModuleProdusFormSystemReadinessAssessment {
  const contract = options?.contract ?? CANDIDATE_MODULE_FORM_SYSTEM_READINESS_CONTRACT;
  const contractValidation = validateCandidateModuleProdusFormSystemReadinessContract(contract);
  const unsafeSignals = options?.liveTemplates ? detectFormActivationLeakSignals(options.liveTemplates) : [];

  if (dossier.runtimeActivationLeakIssues.length > 0) {
    unsafeSignals.push(...dossier.runtimeActivationLeakIssues.map((issue) => `dossier_${issue}`));
  }

  let runtimeFormSystemLinkState: CandidateModuleProdusFormSystemRuntimeLinkState = "NOT_LINKED_YET";
  if (unsafeSignals.length > 0) {
    runtimeFormSystemLinkState = "BLOCKED_RUNTIME_FORM_ACTIVATION_LEAK";
  } else if (completeness.foundRowCount === 0) {
    runtimeFormSystemLinkState = "READONLY_CONTRACT_ONLY";
  }

  let overallFormReadinessState: CandidateModuleProdusOverallFormReadinessState;
  if (unsafeSignals.length > 0) {
    overallFormReadinessState = "BLOCKED_FORM_ACTIVATION_LEAK";
  } else if (
    completeness.sourceMode === "blocked_invalid_live_state" ||
    dossier.overallAlignmentState === "BLOCKED_INVALID_LIVE_STATE" ||
    dossier.overallAlignmentState === "BLOCKED_DOSSIER_ACTIVATION_LEAK" ||
    ownerSummary.statusLevel === "BLOCKED"
  ) {
    overallFormReadinessState = "BLOCKED_INVALID_LIVE_STATE";
  } else if (!contractValidation.valid) {
    overallFormReadinessState = "READONLY_PARTIAL_LIVE_ROWS";
  } else if (completeness.sourceMode === "live_seeded_inactive") {
    overallFormReadinessState = "READONLY_READY_FOR_MAPPING";
  } else if (completeness.sourceMode === "code_contract_fallback") {
    overallFormReadinessState = "READONLY_FALLBACK_ONLY";
  } else {
    overallFormReadinessState = "READONLY_PARTIAL_LIVE_ROWS";
  }

  return {
    expectedComponents: CANDIDATE_MODULE_EXPECTED_ROW_COUNT,
    readinessContractEntries: contract.length,
    runtimeFormSystemLinkState,
    overallFormReadinessState,
    missingComponentCodes: completeness.missingTemplateCodes,
    unsafeSignals,
    contractEntries: contract,
    compactFieldSummaries: CANDIDATE_MODULE_FORM_SYSTEM_COMPACT_SUMMARIES,
  };
}

export function candidateModuleProdusFormReadinessLabel(state: CandidateModuleProdusOverallFormReadinessState): string {
  return state;
}

export function candidateModuleProdusFormReadinessTone(state: CandidateModuleProdusOverallFormReadinessState): string {
  switch (state) {
    case "READONLY_READY_FOR_MAPPING":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "READONLY_FALLBACK_ONLY":
    case "READONLY_PARTIAL_LIVE_ROWS":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    case "BLOCKED_INVALID_LIVE_STATE":
    case "BLOCKED_FORM_ACTIVATION_LEAK":
      return "border-rose-700/40 bg-rose-900/20 text-rose-300";
  }
}

export function candidateModuleProdusFormRuntimeLinkLabel(state: CandidateModuleProdusFormSystemRuntimeLinkState): string {
  switch (state) {
    case "NOT_LINKED_YET":
      return "Runtime Form System link: not linked yet";
    case "READONLY_CONTRACT_ONLY":
      return "Runtime Form System link: readonly contract only";
    case "BLOCKED_RUNTIME_FORM_ACTIVATION_LEAK":
      return "Runtime Form System link: blocked activation leak";
  }
}

export function getCandidateModuleProdusFormReadinessEntry(
  templateCode: CandidateModuleProdusTemplateCode,
  contract: readonly CandidateModuleProdusFormReadinessEntry[] = CANDIDATE_MODULE_FORM_SYSTEM_READINESS_CONTRACT
): CandidateModuleProdusFormReadinessEntry | undefined {
  const normalized = normalizeCandidateModuleProdusTemplateCode(templateCode);
  return contract.find((entry) => normalizeCandidateModuleProdusTemplateCode(entry.templateCode) === normalized);
}
