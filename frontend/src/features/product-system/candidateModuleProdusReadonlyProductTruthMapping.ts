import {
  CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
  CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES,
  normalizeCandidateModuleProdusTemplateCode,
  type CandidateModuleProdusTemplateCode,
} from "./candidateModuleProdusReadonlyCompleteness";
import type { CandidateModuleProdusFormSystemReadinessAssessment } from "./candidateModuleProdusReadonlyFormSystemReadiness";
import type { CandidateModuleProdusOwnerSummary } from "./candidateModuleProdusReadonlyOwnerSummary";

export type CandidateModuleProdusProductTruthAllowedSource =
  | "svg_suggestion"
  | "manual_operator_input"
  | "catalog_default_readonly"
  | "hydrated_existing_value"
  | "owner_confirmed_value_later";

export type CandidateModuleProdusProductTruthAllowedValueState =
  | "suggested"
  | "fallback_readonly"
  | "hydrated_readonly"
  | "manual_draft"
  | "confirmed_later"
  | "blocked";

export type CandidateModuleProdusProductTruthWritePolicy = "readonly_mapping_only";

export type CandidateModuleProdusProductTruthRuntimeLinkState =
  | "NOT_LINKED_YET"
  | "READONLY_MAPPING_ONLY"
  | "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK";

export type CandidateModuleProdusOverallMappingState =
  | "READONLY_MAPPING_READY"
  | "READONLY_MAPPING_FALLBACK_ONLY"
  | "READONLY_MAPPING_PARTIAL"
  | "BLOCKED_INVALID_LIVE_STATE"
  | "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK";

export type CandidateModuleProdusProductTruthMappingEntry = {
  templateCode: CandidateModuleProdusTemplateCode | typeof CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE;
  componentRole: string;
  fieldGroup: string;
  futureProductTruthPath: string;
  truthOwner: "product_composer" | "component_owned_truth";
  allowedSources: CandidateModuleProdusProductTruthAllowedSource[];
  allowedValueStates: CandidateModuleProdusProductTruthAllowedValueState[];
  blockedUntil: "owner_go_and_operator_confirmation";
  mayWriteNow: false;
  writePolicy: CandidateModuleProdusProductTruthWritePolicy;
};

export const CANDIDATE_MODULE_PRODUCT_TRUTH_DEFAULT_SOURCES: CandidateModuleProdusProductTruthAllowedSource[] = [
  "svg_suggestion",
  "manual_operator_input",
  "catalog_default_readonly",
  "hydrated_existing_value",
  "owner_confirmed_value_later",
];

export const CANDIDATE_MODULE_PRODUCT_TRUTH_DEFAULT_VALUE_STATES: CandidateModuleProdusProductTruthAllowedValueState[] = [
  "suggested",
  "fallback_readonly",
  "hydrated_readonly",
  "manual_draft",
  "confirmed_later",
  "blocked",
];

const NON_CONFIRMED_STATES: CandidateModuleProdusProductTruthAllowedValueState[] = [
  "suggested",
  "fallback_readonly",
  "hydrated_readonly",
  "manual_draft",
];

function componentMappingEntry(
  templateCode: CandidateModuleProdusProductTruthMappingEntry["templateCode"],
  componentRole: string,
  fieldGroup: string,
  futureProductTruthPath: string,
  truthOwner: CandidateModuleProdusProductTruthMappingEntry["truthOwner"],
  allowedSources: CandidateModuleProdusProductTruthAllowedSource[] = CANDIDATE_MODULE_PRODUCT_TRUTH_DEFAULT_SOURCES
): CandidateModuleProdusProductTruthMappingEntry {
  return {
    templateCode,
    componentRole,
    fieldGroup,
    futureProductTruthPath,
    truthOwner,
    allowedSources,
    allowedValueStates: [...CANDIDATE_MODULE_PRODUCT_TRUTH_DEFAULT_VALUE_STATES],
    blockedUntil: "owner_go_and_operator_confirmation",
    mayWriteNow: false,
    writePolicy: "readonly_mapping_only",
  };
}

export const CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT: CandidateModuleProdusProductTruthMappingEntry[] = [
  componentMappingEntry(
    CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
    "composer_orchestration",
    "selected_components",
    "product.composer.selected_components",
    "product_composer",
    ["manual_operator_input", "catalog_default_readonly", "hydrated_existing_value", "owner_confirmed_value_later"]
  ),
  componentMappingEntry(
    CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
    "composer_orchestration",
    "component_compatibility",
    "product.composer.component_compatibility",
    "product_composer",
    ["manual_operator_input", "catalog_default_readonly", "hydrated_existing_value", "owner_confirmed_value_later"]
  ),
  componentMappingEntry(
    CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
    "composer_orchestration",
    "overall_readiness",
    "product.composer.overall_readiness",
    "product_composer",
    ["manual_operator_input", "catalog_default_readonly", "hydrated_existing_value", "owner_confirmed_value_later"]
  ),
  componentMappingEntry("TPL-COMP-LETTER-FACE_v1", "face", "face_material", "product.components.face.material", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-FACE_v1", "face", "face_thickness", "product.components.face.thickness", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-FACE_v1", "face", "face_finish_target", "product.components.face.finish_target", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-FACE_v1", "face", "face_cutting_method", "product.components.face.cutting_method", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-BACK_v1", "back", "back_material", "product.components.back.material", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-BACK_v1", "back", "back_thickness", "product.components.back.thickness", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-BACK_v1", "back", "mounting_backing_mode", "product.components.back.mounting_backing_mode", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-BACK_v1", "back", "cnc_or_cutting_preparation", "product.components.back.cutting_preparation", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-RETURN-CANT_v1", "return_cant", "return_material", "product.components.return_cant.material", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-RETURN-CANT_v1", "return_cant", "return_depth", "product.components.return_cant.depth", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-RETURN-CANT_v1", "return_cant", "return_finish", "product.components.return_cant.finish", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-RETURN-CANT_v1", "return_cant", "return_joining_method", "product.components.return_cant.joining_method", "component_owned_truth"),
  componentMappingEntry("TPL-COMP-LETTER-LED_v1", "led", "illumination_mode", "product.components.led.illumination_mode", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-LED_v1", "led", "led_type", "product.components.led.type", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-LED_v1", "led", "led_density", "product.components.led.density", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-LED_v1", "led", "power_supply_policy", "product.components.led.power_supply_policy", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-LED_v1", "led", "wiring_notes", "product.components.led.wiring_notes", "component_owned_truth", [
    "manual_operator_input",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-FINISH_v1", "finish", "finish_type", "product.components.finish.type", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-FINISH_v1", "finish", "stock_color", "product.components.finish.stock_color", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-FINISH_v1", "finish", "oracal_code", "product.components.finish.oracal_code", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-FINISH_v1", "finish", "ral_code", "product.components.finish.ral_code", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-FINISH_v1", "finish", "print_lamination_policy", "product.components.finish.print_lamination_policy", "component_owned_truth", [
    "manual_operator_input",
    "catalog_default_readonly",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-MOUNTING_v1", "mounting", "mounting_surface", "product.components.mounting.surface", "component_owned_truth", [
    "manual_operator_input",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-MOUNTING_v1", "mounting", "spacer_policy", "product.components.mounting.spacer_policy", "component_owned_truth", [
    "manual_operator_input",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-MOUNTING_v1", "mounting", "template_drilling_policy", "product.components.mounting.template_drilling_policy", "component_owned_truth", [
    "manual_operator_input",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
  componentMappingEntry("TPL-COMP-LETTER-MOUNTING_v1", "mounting", "site_installation_notes", "product.components.mounting.site_installation_notes", "component_owned_truth", [
    "manual_operator_input",
    "hydrated_existing_value",
    "owner_confirmed_value_later",
  ]),
];

export const CANDIDATE_MODULE_EXPECTED_MAPPING_ENTRY_COUNT = CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.length;

export type CandidateModuleProdusProductTruthCompactPathSummary = {
  label: string;
  pathPrefix: string;
};

export const CANDIDATE_MODULE_PRODUCT_TRUTH_COMPACT_PATH_SUMMARIES: CandidateModuleProdusProductTruthCompactPathSummary[] = [
  { label: "FACE", pathPrefix: "product.components.face.*" },
  { label: "BACK", pathPrefix: "product.components.back.*" },
  { label: "RETURN/CANT", pathPrefix: "product.components.return_cant.*" },
  { label: "LED", pathPrefix: "product.components.led.*" },
  { label: "FINISH", pathPrefix: "product.components.finish.*" },
  { label: "MOUNTING", pathPrefix: "product.components.mounting.*" },
];

function entryTreatsNonConfirmedAsConfirmed(entry: CandidateModuleProdusProductTruthMappingEntry): boolean {
  const hasConfirmedLater = entry.allowedValueStates.includes("confirmed_later");
  const hasNonConfirmed = NON_CONFIRMED_STATES.some((state) => entry.allowedValueStates.includes(state));
  return hasConfirmedLater && !hasNonConfirmed;
}

export function validateCandidateModuleProdusProductTruthMappingContract(
  contract: readonly CandidateModuleProdusProductTruthMappingEntry[] = CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT
): { valid: boolean; issues: string[] } {
  const issues: string[] = [];
  const seen = new Set<string>();

  for (const entry of contract) {
    const key = `${normalizeCandidateModuleProdusTemplateCode(entry.templateCode)}::${entry.fieldGroup}`;
    if (seen.has(key)) issues.push(`mapping_duplicate_${entry.fieldGroup}`);
    seen.add(key);

    if (entry.mayWriteNow !== false) issues.push(`mapping_write_enabled_${entry.fieldGroup}`);
    if (entry.writePolicy !== "readonly_mapping_only") issues.push(`mapping_write_policy_${entry.fieldGroup}`);
    if (entryTreatsNonConfirmedAsConfirmed(entry)) {
      issues.push(`mapping_unsafe_state_policy_${entry.fieldGroup}`);
    }
    if (!entry.allowedValueStates.includes("confirmed_later")) {
      issues.push(`mapping_missing_confirmed_later_${entry.fieldGroup}`);
    }
    if (
      entry.allowedValueStates.includes("suggested") &&
      !entry.allowedValueStates.includes("confirmed_later")
    ) {
      issues.push(`mapping_suggested_without_confirmed_later_${entry.fieldGroup}`);
    }
  }

  const expectedFieldGroups = new Set(
    CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.map((entry) => entry.fieldGroup)
  );
  for (const fieldGroup of expectedFieldGroups) {
    if (![...seen].some((key) => key.endsWith(`::${fieldGroup}`))) {
      issues.push(`mapping_missing_${fieldGroup}`);
    }
  }

  return { valid: issues.length === 0, issues };
}

export type CandidateModuleProdusProductTruthMappingAssessment = {
  mappingContractEntriesCount: number;
  expectedMappingEntriesCount: number;
  missingMappingEntries: string[];
  writeEnabledEntries: string[];
  unsafeStatePolicyEntries: string[];
  runtimeProductTruthLinkState: CandidateModuleProdusProductTruthRuntimeLinkState;
  overallMappingState: CandidateModuleProdusOverallMappingState;
  contractEntries: CandidateModuleProdusProductTruthMappingEntry[];
  compactPathSummaries: CandidateModuleProdusProductTruthCompactPathSummary[];
};

export function assessCandidateModuleProdusProductTruthMapping(
  formReadiness: CandidateModuleProdusFormSystemReadinessAssessment,
  ownerSummary: CandidateModuleProdusOwnerSummary,
  contract: readonly CandidateModuleProdusProductTruthMappingEntry[] = CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT
): CandidateModuleProdusProductTruthMappingAssessment {
  const validation = validateCandidateModuleProdusProductTruthMappingContract(contract);

  const writeEnabledEntries = contract
    .filter((entry) => entry.mayWriteNow !== false)
    .map((entry) => entry.fieldGroup);

  const unsafeStatePolicyEntries = contract
    .filter((entry) => entryTreatsNonConfirmedAsConfirmed(entry))
    .map((entry) => entry.fieldGroup);

  const expectedKeys = new Set(
    CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT.map(
      (entry) => `${normalizeCandidateModuleProdusTemplateCode(entry.templateCode)}::${entry.fieldGroup}`
    )
  );
  const actualKeys = new Set(
    contract.map((entry) => `${normalizeCandidateModuleProdusTemplateCode(entry.templateCode)}::${entry.fieldGroup}`)
  );
  const missingMappingEntries = [...expectedKeys].filter((key) => !actualKeys.has(key));

  let runtimeProductTruthLinkState: CandidateModuleProdusProductTruthRuntimeLinkState = "NOT_LINKED_YET";
  if (writeEnabledEntries.length > 0 || unsafeStatePolicyEntries.length > 0) {
    runtimeProductTruthLinkState = "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK";
  } else if (formReadiness.overallFormReadinessState === "READONLY_FALLBACK_ONLY") {
    runtimeProductTruthLinkState = "READONLY_MAPPING_ONLY";
  }

  let overallMappingState: CandidateModuleProdusOverallMappingState;
  if (writeEnabledEntries.length > 0 || unsafeStatePolicyEntries.length > 0) {
    overallMappingState = "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK";
  } else if (
    formReadiness.overallFormReadinessState === "BLOCKED_FORM_ACTIVATION_LEAK" ||
    ownerSummary.statusLevel === "BLOCKED"
  ) {
    overallMappingState = "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK";
  } else if (formReadiness.overallFormReadinessState === "BLOCKED_INVALID_LIVE_STATE") {
    overallMappingState = "BLOCKED_INVALID_LIVE_STATE";
  } else if (!validation.valid || missingMappingEntries.length > 0) {
    overallMappingState = "READONLY_MAPPING_PARTIAL";
  } else if (formReadiness.overallFormReadinessState === "READONLY_READY_FOR_MAPPING") {
    overallMappingState = "READONLY_MAPPING_READY";
  } else if (formReadiness.overallFormReadinessState === "READONLY_FALLBACK_ONLY") {
    overallMappingState = "READONLY_MAPPING_FALLBACK_ONLY";
  } else {
    overallMappingState = "READONLY_MAPPING_PARTIAL";
  }

  return {
    mappingContractEntriesCount: contract.length,
    expectedMappingEntriesCount: CANDIDATE_MODULE_EXPECTED_MAPPING_ENTRY_COUNT,
    missingMappingEntries,
    writeEnabledEntries,
    unsafeStatePolicyEntries,
    runtimeProductTruthLinkState,
    overallMappingState,
    contractEntries: contract,
    compactPathSummaries: CANDIDATE_MODULE_PRODUCT_TRUTH_COMPACT_PATH_SUMMARIES,
  };
}

export function candidateModuleProdusProductTruthMappingLabel(state: CandidateModuleProdusOverallMappingState): string {
  return state;
}

export function candidateModuleProdusProductTruthMappingTone(state: CandidateModuleProdusOverallMappingState): string {
  switch (state) {
    case "READONLY_MAPPING_READY":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "READONLY_MAPPING_FALLBACK_ONLY":
    case "READONLY_MAPPING_PARTIAL":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    case "BLOCKED_INVALID_LIVE_STATE":
    case "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK":
      return "border-rose-700/40 bg-rose-900/20 text-rose-300";
  }
}

export function candidateModuleProdusProductTruthRuntimeLinkLabel(
  state: CandidateModuleProdusProductTruthRuntimeLinkState
): string {
  switch (state) {
    case "NOT_LINKED_YET":
      return "Runtime Product Truth link: not linked yet";
    case "READONLY_MAPPING_ONLY":
      return "Runtime Product Truth link: readonly mapping only";
    case "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK":
      return "Runtime Product Truth link: blocked write leak";
  }
}

export function getCandidateModuleProdusProductTruthMappingsForRole(
  rolePrefix: string,
  contract: readonly CandidateModuleProdusProductTruthMappingEntry[] = CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT
): CandidateModuleProdusProductTruthMappingEntry[] {
  return contract.filter((entry) => entry.futureProductTruthPath.includes(rolePrefix));
}

export function isSuggestedTreatedAsConfirmed(entry: CandidateModuleProdusProductTruthMappingEntry): boolean {
  return (
    entry.allowedValueStates.includes("suggested") &&
    !NON_CONFIRMED_STATES.some(
      (state) => state !== "suggested" && entry.allowedValueStates.includes(state)
    ) &&
    entry.allowedValueStates.length === 1
  );
}
