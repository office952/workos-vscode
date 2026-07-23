import {
  CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
  CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES,
  normalizeCandidateModuleProdusTemplateCode,
  type CandidateModuleProdusLiveTemplateRow,
  type CandidateModuleProdusTemplateCode,
} from "./candidateModuleProdusReadonlyCompleteness";
import type { CandidateModuleProdusFormSystemReadinessAssessment } from "./candidateModuleProdusReadonlyFormSystemReadiness";
import type { CandidateModuleProdusOwnerSummary } from "./candidateModuleProdusReadonlyOwnerSummary";
import {
  CANDIDATE_MODULE_PRODUCT_TRUTH_MAPPING_CONTRACT,
  type CandidateModuleProdusProductTruthMappingAssessment,
} from "./candidateModuleProdusReadonlyProductTruthMapping";

export type CandidateModuleProdusForbiddenValueState =
  | "suggested"
  | "fallback_readonly"
  | "hydrated_readonly"
  | "manual_draft"
  | "blocked";

export type CandidateModuleProdusAllowedFutureValueState = "confirmed_later";

export type CandidateModuleProdusMissingTruthBehavior =
  | "report_missing_truth"
  | "produce_readiness_blocker"
  | "do_not_invent"
  | "do_not_price"
  | "do_not_create_aggregate"
  | "do_not_materialize_tasks";

export type CandidateModuleProdusProductDefinitionAllowedOutput =
  | "component_readiness"
  | "missing_fields"
  | "validation_warnings"
  | "technical_definition_after_confirmed_truth";

export type CandidateModuleProdusProductDefinitionForbiddenOutput =
  | "price"
  | "quote"
  | "order"
  | "ProductAggregate"
  | "TaskGraph"
  | "ExecutionPlan"
  | "task_materialization"
  | "confirmed_product_truth";

export type CandidateModuleProdusProductDefinitionRuntimeLinkState =
  | "NOT_LINKED_YET"
  | "READONLY_CONSUMPTION_CONTRACT_ONLY"
  | "BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK";

export type CandidateModuleProdusOverallProductDefinitionReadinessState =
  | "READONLY_CONSUMPTION_READY"
  | "READONLY_CONSUMPTION_FALLBACK_ONLY"
  | "READONLY_CONSUMPTION_PARTIAL"
  | "BLOCKED_INVALID_LIVE_STATE"
  | "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK"
  | "BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK";

export type CandidateModuleProdusProductDefinitionConsumptionEntry = {
  templateCode: CandidateModuleProdusTemplateCode | typeof CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE;
  componentRole: string;
  requiredProductTruthPaths: string[];
  optionalProductTruthPaths: string[];
  forbiddenValueStates: CandidateModuleProdusForbiddenValueState[];
  allowedFutureValueState: CandidateModuleProdusAllowedFutureValueState;
  missingTruthBehavior: CandidateModuleProdusMissingTruthBehavior[];
  productDefinitionAllowedOutput: CandidateModuleProdusProductDefinitionAllowedOutput[];
  productDefinitionForbiddenOutput: CandidateModuleProdusProductDefinitionForbiddenOutput[];
  mayActivateProductDefinitionNow: false;
};

export const CANDIDATE_MODULE_PRODUCT_DEFINITION_FORBIDDEN_VALUE_STATES: CandidateModuleProdusForbiddenValueState[] = [
  "suggested",
  "fallback_readonly",
  "hydrated_readonly",
  "manual_draft",
  "blocked",
];

export const CANDIDATE_MODULE_PRODUCT_DEFINITION_MISSING_TRUTH_BEHAVIOR: CandidateModuleProdusMissingTruthBehavior[] = [
  "report_missing_truth",
  "produce_readiness_blocker",
  "do_not_invent",
  "do_not_price",
  "do_not_create_aggregate",
  "do_not_materialize_tasks",
];

export const CANDIDATE_MODULE_PRODUCT_DEFINITION_ALLOWED_OUTPUT: CandidateModuleProdusProductDefinitionAllowedOutput[] = [
  "component_readiness",
  "missing_fields",
  "validation_warnings",
  "technical_definition_after_confirmed_truth",
];

export const CANDIDATE_MODULE_PRODUCT_DEFINITION_FORBIDDEN_OUTPUT: CandidateModuleProdusProductDefinitionForbiddenOutput[] = [
  "price",
  "quote",
  "order",
  "ProductAggregate",
  "TaskGraph",
  "ExecutionPlan",
  "task_materialization",
  "confirmed_product_truth",
];

function consumptionEntry(
  templateCode: CandidateModuleProdusProductDefinitionConsumptionEntry["templateCode"],
  componentRole: string,
  requiredProductTruthPaths: string[],
  optionalProductTruthPaths: string[] = []
): CandidateModuleProdusProductDefinitionConsumptionEntry {
  return {
    templateCode,
    componentRole,
    requiredProductTruthPaths,
    optionalProductTruthPaths,
    forbiddenValueStates: [...CANDIDATE_MODULE_PRODUCT_DEFINITION_FORBIDDEN_VALUE_STATES],
    allowedFutureValueState: "confirmed_later",
    missingTruthBehavior: [...CANDIDATE_MODULE_PRODUCT_DEFINITION_MISSING_TRUTH_BEHAVIOR],
    productDefinitionAllowedOutput: [...CANDIDATE_MODULE_PRODUCT_DEFINITION_ALLOWED_OUTPUT],
    productDefinitionForbiddenOutput: [...CANDIDATE_MODULE_PRODUCT_DEFINITION_FORBIDDEN_OUTPUT],
    mayActivateProductDefinitionNow: false,
  };
}

export const CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT: CandidateModuleProdusProductDefinitionConsumptionEntry[] = [
  consumptionEntry(CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE, "composer_orchestration", [
    "product.composer.selected_components",
    "product.composer.component_compatibility",
    "product.composer.overall_readiness",
  ]),
  consumptionEntry("TPL-COMP-LETTER-FACE_v1", "face", [
    "product.components.face.material",
    "product.components.face.thickness",
    "product.components.face.finish_target",
    "product.components.face.cutting_method",
  ]),
  consumptionEntry("TPL-COMP-LETTER-BACK_v1", "back", [
    "product.components.back.material",
    "product.components.back.thickness",
    "product.components.back.mounting_backing_mode",
    "product.components.back.cutting_preparation",
  ]),
  consumptionEntry("TPL-COMP-LETTER-RETURN-CANT_v1", "return_cant", [
    "product.components.return_cant.material",
    "product.components.return_cant.depth",
    "product.components.return_cant.finish",
    "product.components.return_cant.joining_method",
  ]),
  consumptionEntry("TPL-COMP-LETTER-LED_v1", "led", [
    "product.components.led.illumination_mode",
    "product.components.led.type",
    "product.components.led.density",
    "product.components.led.power_supply_policy",
    "product.components.led.wiring_notes",
  ]),
  consumptionEntry("TPL-COMP-LETTER-FINISH_v1", "finish", [
    "product.components.finish.type",
    "product.components.finish.stock_color",
    "product.components.finish.oracal_code",
    "product.components.finish.ral_code",
    "product.components.finish.print_lamination_policy",
  ]),
  consumptionEntry("TPL-COMP-LETTER-MOUNTING_v1", "mounting", [
    "product.components.mounting.surface",
    "product.components.mounting.spacer_policy",
    "product.components.mounting.template_drilling_policy",
    "product.components.mounting.site_installation_notes",
  ]),
];

export const CANDIDATE_MODULE_PRODUCT_DEFINITION_REQUIRED_PATHS_COUNT =
  CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT.reduce(
    (count, entry) => count + entry.requiredProductTruthPaths.length,
    0
  );

export type CandidateModuleProdusProductDefinitionCompactPathSummary = {
  label: string;
  paths: string;
};

export const CANDIDATE_MODULE_PRODUCT_DEFINITION_COMPACT_PATH_SUMMARIES: CandidateModuleProdusProductDefinitionCompactPathSummary[] = [
  {
    label: "FACE",
    paths: "material, thickness, finish target, cutting method",
  },
  {
    label: "RETURN/CANT",
    paths: "material, depth, finish, joining method",
  },
  {
    label: "LED",
    paths: "illumination mode, type, density, power supply, wiring notes",
  },
  {
    label: "FINISH/MOUNTING",
    paths: "finish type/stock/oracal/ral/print; mounting surface/spacer/drilling/site notes",
  },
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

function detectProductDefinitionRuntimeLeakSignals(liveTemplates: CandidateModuleProdusLiveTemplateRow[]): string[] {
  const issues: string[] = [];

  for (const row of liveTemplates) {
    if (!isCandidateModuleProdusFamilyRow(row.template_code)) continue;

    const notes = safeParseJson<Record<string, unknown>>(row.notes, {});
    if (notes.product_definition_active === true) issues.push(`product_definition_active_${row.template_code}`);
    if (notes.product_aggregate_runtime_consumed === true) issues.push(`product_aggregate_runtime_${row.template_code}`);
    if (notes.pricing_active === true) issues.push(`pricing_active_${row.template_code}`);
    if (notes.task_materialization === true) issues.push(`task_materialization_${row.template_code}`);
    if (notes.execution_plan_active === true) issues.push(`execution_plan_${row.template_code}`);
    if (notes.quote_mode === "active") issues.push(`quote_mode_${row.template_code}`);
  }

  return issues;
}

export function validateCandidateModuleProdusProductDefinitionConsumptionContract(
  contract: readonly CandidateModuleProdusProductDefinitionConsumptionEntry[] = CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT
): { valid: boolean; issues: string[] } {
  const issues: string[] = [];

  if (contract.length !== 7) {
    issues.push(`product_definition_contract_template_count_${contract.length}`);
  }

  for (const entry of contract) {
    if (entry.mayActivateProductDefinitionNow !== false) {
      issues.push(`product_definition_activation_enabled_${entry.templateCode}`);
    }
    if (!entry.missingTruthBehavior.includes("do_not_invent")) {
      issues.push(`product_definition_missing_do_not_invent_${entry.templateCode}`);
    }
    if (!entry.missingTruthBehavior.includes("report_missing_truth")) {
      issues.push(`product_definition_missing_report_missing_truth_${entry.templateCode}`);
    }
    if (!entry.productDefinitionForbiddenOutput.includes("price")) {
      issues.push(`product_definition_missing_forbidden_price_${entry.templateCode}`);
    }
    if (!entry.productDefinitionForbiddenOutput.includes("ProductAggregate")) {
      issues.push(`product_definition_missing_forbidden_aggregate_${entry.templateCode}`);
    }
    if (entry.forbiddenValueStates.includes("confirmed_later" as CandidateModuleProdusForbiddenValueState)) {
      issues.push(`product_definition_confirmed_in_forbidden_states_${entry.templateCode}`);
    }
  }

  return { valid: issues.length === 0, issues };
}

export type CandidateModuleProdusProductDefinitionReadinessAssessment = {
  requiredPathsCount: number;
  mappedPathsCount: number;
  missingPaths: string[];
  unsafeValueStatePaths: string[];
  forbiddenOutputSignals: string[];
  runtimeProductDefinitionLinkState: CandidateModuleProdusProductDefinitionRuntimeLinkState;
  overallProductDefinitionReadinessState: CandidateModuleProdusOverallProductDefinitionReadinessState;
  contractEntries: CandidateModuleProdusProductDefinitionConsumptionEntry[];
  compactPathSummaries: CandidateModuleProdusProductDefinitionCompactPathSummary[];
};

export function assessCandidateModuleProdusProductDefinitionReadiness(
  productTruthMapping: CandidateModuleProdusProductTruthMappingAssessment,
  formReadiness: CandidateModuleProdusFormSystemReadinessAssessment,
  ownerSummary: CandidateModuleProdusOwnerSummary,
  options?: {
    liveTemplates?: CandidateModuleProdusLiveTemplateRow[];
    contract?: readonly CandidateModuleProdusProductDefinitionConsumptionEntry[];
  }
): CandidateModuleProdusProductDefinitionReadinessAssessment {
  const contract = options?.contract ?? CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT;
  const contractValidation = validateCandidateModuleProdusProductDefinitionConsumptionContract(contract);
  const runtimeLeakSignals = options?.liveTemplates
    ? detectProductDefinitionRuntimeLeakSignals(options.liveTemplates)
    : [];

  const expectedPaths = contract.flatMap((entry) => entry.requiredProductTruthPaths);
  const mappedPaths = new Set(
    productTruthMapping.contractEntries.map((entry) => entry.futureProductTruthPath)
  );
  const missingPaths = expectedPaths.filter((path) => !mappedPaths.has(path));

  const writeEnabledEntries = contract.filter((entry) => entry.mayActivateProductDefinitionNow !== false);
  const forbiddenOutputSignals = contract
    .filter((entry) => entry.productDefinitionForbiddenOutput.length === 0)
    .map((entry) => entry.templateCode);

  const unsafeValueStatePaths = contract
    .filter((entry) => !entry.forbiddenValueStates.includes("suggested"))
    .flatMap((entry) => entry.requiredProductTruthPaths);

  if (formReadiness.unsafeSignals.some((signal) => signal.includes("product_definition_active"))) {
    runtimeLeakSignals.push("form_readiness_product_definition_active");
  }

  let runtimeProductDefinitionLinkState: CandidateModuleProdusProductDefinitionRuntimeLinkState = "NOT_LINKED_YET";
  if (runtimeLeakSignals.length > 0 || forbiddenOutputSignals.length > 0) {
    runtimeProductDefinitionLinkState = "BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK";
  } else if (productTruthMapping.overallMappingState === "READONLY_MAPPING_FALLBACK_ONLY") {
    runtimeProductDefinitionLinkState = "READONLY_CONSUMPTION_CONTRACT_ONLY";
  }

  let overallProductDefinitionReadinessState: CandidateModuleProdusOverallProductDefinitionReadinessState;
  if (runtimeLeakSignals.length > 0 || writeEnabledEntries.length > 0) {
    overallProductDefinitionReadinessState = "BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK";
  } else if (productTruthMapping.overallMappingState === "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK") {
    overallProductDefinitionReadinessState = "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK";
  } else if (
    productTruthMapping.overallMappingState === "BLOCKED_INVALID_LIVE_STATE" ||
    formReadiness.overallFormReadinessState === "BLOCKED_INVALID_LIVE_STATE" ||
    ownerSummary.statusLevel === "BLOCKED"
  ) {
    overallProductDefinitionReadinessState = "BLOCKED_INVALID_LIVE_STATE";
  } else if (!contractValidation.valid || missingPaths.length > 0) {
    overallProductDefinitionReadinessState = "READONLY_CONSUMPTION_PARTIAL";
  } else if (productTruthMapping.overallMappingState === "READONLY_MAPPING_READY") {
    overallProductDefinitionReadinessState = "READONLY_CONSUMPTION_READY";
  } else if (productTruthMapping.overallMappingState === "READONLY_MAPPING_FALLBACK_ONLY") {
    overallProductDefinitionReadinessState = "READONLY_CONSUMPTION_FALLBACK_ONLY";
  } else {
    overallProductDefinitionReadinessState = "READONLY_CONSUMPTION_PARTIAL";
  }

  return {
    requiredPathsCount: expectedPaths.length,
    mappedPathsCount: expectedPaths.length - missingPaths.length,
    missingPaths,
    unsafeValueStatePaths,
    forbiddenOutputSignals,
    runtimeProductDefinitionLinkState,
    overallProductDefinitionReadinessState,
    contractEntries: contract,
    compactPathSummaries: CANDIDATE_MODULE_PRODUCT_DEFINITION_COMPACT_PATH_SUMMARIES,
  };
}

export function candidateModuleProdusProductDefinitionReadinessLabel(
  state: CandidateModuleProdusOverallProductDefinitionReadinessState
): string {
  return state;
}

export function candidateModuleProdusProductDefinitionReadinessTone(
  state: CandidateModuleProdusOverallProductDefinitionReadinessState
): string {
  switch (state) {
    case "READONLY_CONSUMPTION_READY":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "READONLY_CONSUMPTION_FALLBACK_ONLY":
    case "READONLY_CONSUMPTION_PARTIAL":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    case "BLOCKED_INVALID_LIVE_STATE":
    case "BLOCKED_PRODUCT_TRUTH_WRITE_LEAK":
    case "BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK":
      return "border-rose-700/40 bg-rose-900/20 text-rose-300";
  }
}

export function candidateModuleProdusProductDefinitionRuntimeLinkLabel(
  state: CandidateModuleProdusProductDefinitionRuntimeLinkState
): string {
  switch (state) {
    case "NOT_LINKED_YET":
      return "Runtime ProductDefinition link: not linked yet";
    case "READONLY_CONSUMPTION_CONTRACT_ONLY":
      return "Runtime ProductDefinition link: readonly contract only";
    case "BLOCKED_PRODUCT_DEFINITION_RUNTIME_LEAK":
      return "Runtime ProductDefinition link: blocked runtime leak";
  }
}

export function getCandidateModuleProdusProductDefinitionEntry(
  templateCode: CandidateModuleProdusTemplateCode | typeof CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
  contract: readonly CandidateModuleProdusProductDefinitionConsumptionEntry[] = CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT
): CandidateModuleProdusProductDefinitionConsumptionEntry | undefined {
  const normalized = normalizeCandidateModuleProdusTemplateCode(templateCode);
  return contract.find((entry) => normalizeCandidateModuleProdusTemplateCode(entry.templateCode) === normalized);
}

export function getCandidateModuleProdusProductDefinitionPathsForRole(
  role: string,
  contract: readonly CandidateModuleProdusProductDefinitionConsumptionEntry[] = CANDIDATE_MODULE_PRODUCT_DEFINITION_CONSUMPTION_CONTRACT
): string[] {
  const entry = contract.find((item) => item.componentRole === role);
  return entry?.requiredProductTruthPaths ?? [];
}
