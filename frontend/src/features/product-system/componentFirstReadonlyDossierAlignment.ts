import {
  COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES,
  COMPONENT_FIRST_EXPECTED_ROW_COUNT,
  COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES,
  assessComponentFirstContractDrift,
  assessComponentFirstLiveCompleteness,
  normalizeComponentFirstTemplateCode,
  type ComponentFirstCompletenessAssessment,
  type ComponentFirstContractDriftAssessment,
  type ComponentFirstLiveTemplateRow,
  type ComponentFirstTemplateCode,
} from "./componentFirstReadonlyCompleteness";

export type ComponentFirstDossierExpectedKind = "product_composer" | "component_template";

export type ComponentFirstDossierRole =
  | "composer_orchestration"
  | "face"
  | "back"
  | "return_cant"
  | "led"
  | "finish"
  | "mounting";

export type ComponentFirstTruthOwner = "product_composer" | "component_owned_truth";

export type ComponentFirstDossierAlignmentState =
  | "READY_FOR_READONLY_DOSSIER_MAPPING"
  | "MISSING_LIVE_ROW"
  | "PARTIAL_LIVE_ROW"
  | "INVALID_ACTIVE_ROW"
  | "DOSSIER_METADATA_NOT_AVAILABLE"
  | "BLOCKED_DOSSIER_ACTIVATION_LEAK";

export type ComponentFirstDossierRuntimeLinkState =
  | "NOT_LINKED_YET"
  | "READONLY_CONTRACT_ONLY"
  | "PARTIAL_RUNTIME_LINK"
  | "BLOCKED_RUNTIME_ACTIVATION_LEAK";

export type ComponentFirstOverallAlignmentState =
  | "READONLY_ALIGNED"
  | "READONLY_PARTIAL"
  | "READONLY_FALLBACK_ONLY"
  | "BLOCKED_INVALID_LIVE_STATE"
  | "BLOCKED_DOSSIER_ACTIVATION_LEAK";

export type ComponentFirstFutureDossierMetadata =
  | "technical_fields"
  | "material_rules"
  | "operation_hints"
  | "validations"
  | "produced_outputs"
  | "calculation_readiness";

export type ComponentFirstDossierForbiddenNow =
  | "task_materialization"
  | "execution_plan"
  | "product_aggregate_runtime"
  | "pricing"
  | "quote_order"
  | "work_intake_exposure";

export type ComponentFirstDossierContractEntry = {
  templateCode: ComponentFirstTemplateCode;
  expectedKind: ComponentFirstDossierExpectedKind;
  expectedDossierRole: ComponentFirstDossierRole;
  expectedTruthOwner: ComponentFirstTruthOwner;
  dossierAlignmentState: ComponentFirstDossierAlignmentState;
  futureAllowedMetadata: ComponentFirstFutureDossierMetadata[];
  forbiddenNow: ComponentFirstDossierForbiddenNow[];
};

export const COMPONENT_FIRST_DOSSIER_FORBIDDEN_NOW: ComponentFirstDossierForbiddenNow[] = [
  "task_materialization",
  "execution_plan",
  "product_aggregate_runtime",
  "pricing",
  "quote_order",
  "work_intake_exposure",
];

export const COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE: ComponentFirstDossierContractEntry[] = [
  {
    templateCode: COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
    expectedKind: "product_composer",
    expectedDossierRole: "composer_orchestration",
    expectedTruthOwner: "product_composer",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "validations", "calculation_readiness"],
    forbiddenNow: [...COMPONENT_FIRST_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-FACE_v1",
    expectedKind: "component_template",
    expectedDossierRole: "face",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...COMPONENT_FIRST_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-BACK_v1",
    expectedKind: "component_template",
    expectedDossierRole: "back",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...COMPONENT_FIRST_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-RETURN-CANT_v1",
    expectedKind: "component_template",
    expectedDossierRole: "return_cant",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...COMPONENT_FIRST_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-LED_v1",
    expectedKind: "component_template",
    expectedDossierRole: "led",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...COMPONENT_FIRST_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-FINISH_v1",
    expectedKind: "component_template",
    expectedDossierRole: "finish",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...COMPONENT_FIRST_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-MOUNTING_v1",
    expectedKind: "component_template",
    expectedDossierRole: "mounting",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...COMPONENT_FIRST_DOSSIER_FORBIDDEN_NOW],
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

function isComponentFirstFamilyRow(templateCode: string): boolean {
  const normalized = normalizeComponentFirstTemplateCode(templateCode);
  return COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES.some(
    (code) => normalizeComponentFirstTemplateCode(code) === normalized
  );
}

function detectRuntimeActivationLeakSignals(liveTemplates: ComponentFirstLiveTemplateRow[]): string[] {
  const issues: string[] = [];

  for (const row of liveTemplates) {
    if (!isComponentFirstFamilyRow(row.template_code)) continue;

    const notes = safeParseJson<Record<string, unknown>>(row.notes, {});
    if (notes.work_intake_exposed === true) issues.push(`work_intake_exposed_${row.template_code}`);
    if (notes.pricing_active === true) issues.push(`pricing_active_${row.template_code}`);
    if (notes.product_definition_active === true) issues.push(`product_definition_active_${row.template_code}`);
    if (notes.product_aggregate_runtime_consumed === true) issues.push(`product_aggregate_runtime_${row.template_code}`);
    if (notes.component_root_active === true) issues.push(`component_root_active_${row.template_code}`);
    if (notes.task_materialization === true) issues.push(`task_materialization_${row.template_code}`);
    if (notes.execution_plan_active === true) issues.push(`execution_plan_${row.template_code}`);
    if (typeof notes.quote_mode === "string" && notes.quote_mode !== "inactive_only") {
      issues.push(`quote_mode_${row.template_code}`);
    }
    if (typeof notes.dossier_runtime_link === "string" && notes.dossier_runtime_link !== "not_linked") {
      issues.push(`dossier_runtime_link_${row.template_code}`);
    }

    const operations = safeParseJson<unknown[]>(row.operations_json, []);
    if (operations.length > 0) {
      issues.push(`executable_operations_${row.template_code}`);
    }
  }

  return issues;
}

export function validateComponentFirstDossierContract(
  contract: readonly ComponentFirstDossierContractEntry[] = COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE
): { valid: boolean; issues: string[] } {
  const issues: string[] = [];

  if (contract.length !== COMPONENT_FIRST_EXPECTED_ROW_COUNT) {
    issues.push(`dossier_contract_row_count_${contract.length}`);
  }

  const seen = new Set<string>();
  let composerCount = 0;
  let componentCount = 0;

  for (const entry of contract) {
    const normalized = normalizeComponentFirstTemplateCode(entry.templateCode);
    if (seen.has(normalized)) {
      issues.push(`dossier_contract_duplicate_${entry.templateCode}`);
    }
    seen.add(normalized);

    if (entry.expectedKind === "product_composer") {
      composerCount += 1;
      if (entry.expectedTruthOwner !== "product_composer") {
        issues.push(`composer_truth_owner_mismatch_${entry.templateCode}`);
      }
      if (entry.expectedDossierRole !== "composer_orchestration") {
        issues.push(`composer_role_mismatch_${entry.templateCode}`);
      }
    } else {
      componentCount += 1;
      if (entry.expectedTruthOwner !== "component_owned_truth") {
        issues.push(`component_truth_owner_mismatch_${entry.templateCode}`);
      }
      if (!COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES.includes(entry.templateCode)) {
        issues.push(`component_code_out_of_family_${entry.templateCode}`);
      }
    }
  }

  if (composerCount !== 1) issues.push(`dossier_contract_composer_count_${composerCount}`);
  if (componentCount !== COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES.length) {
    issues.push(`dossier_contract_component_count_${componentCount}`);
  }

  for (const expectedCode of COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES) {
    if (!seen.has(normalizeComponentFirstTemplateCode(expectedCode))) {
      issues.push(`dossier_contract_missing_${expectedCode}`);
    }
  }

  return { valid: issues.length === 0, issues };
}

export type ComponentFirstDossierAlignmentAssessment = {
  expectedCount: number;
  liveFoundCount: number;
  missingCodes: ComponentFirstTemplateCode[];
  invalidActiveCodes: ComponentFirstTemplateCode[];
  dossierContractCount: number;
  dossierRuntimeLinkState: ComponentFirstDossierRuntimeLinkState;
  overallAlignmentState: ComponentFirstOverallAlignmentState;
  runtimeActivationLeakIssues: string[];
  metadataUnavailableCodes: ComponentFirstTemplateCode[];
  completeness: ComponentFirstCompletenessAssessment;
  drift: ComponentFirstContractDriftAssessment;
  contractEntries: ComponentFirstDossierContractEntry[];
};

export function assessComponentFirstDossierAlignment(
  liveTemplates: ComponentFirstLiveTemplateRow[],
  options?: {
    completeness?: ComponentFirstCompletenessAssessment;
    drift?: ComponentFirstContractDriftAssessment;
    dossierContract?: readonly ComponentFirstDossierContractEntry[];
  }
): ComponentFirstDossierAlignmentAssessment {
  const dossierContract = options?.dossierContract ?? COMPONENT_FIRST_DOSSIER_CONTRACT_FIXTURE;
  const contractValidation = validateComponentFirstDossierContract(dossierContract);
  const completeness = options?.completeness ?? assessComponentFirstLiveCompleteness(liveTemplates);
  const drift = options?.drift ?? assessComponentFirstContractDrift(liveTemplates);
  const runtimeActivationLeakIssues = detectRuntimeActivationLeakSignals(liveTemplates);

  const liveByCode = new Map(
    liveTemplates.map((row) => [normalizeComponentFirstTemplateCode(row.template_code), row])
  );

  const metadataUnavailableCodes: ComponentFirstTemplateCode[] = [];
  for (const expectedCode of completeness.foundTemplateCodes) {
    const liveRow = liveByCode.get(normalizeComponentFirstTemplateCode(expectedCode));
    if (!liveRow) continue;
    const notes = safeParseJson<Record<string, unknown>>(liveRow.notes, {});
    const components = safeParseJson<unknown[]>(liveRow.components_json, []);
    if (Object.keys(notes).length === 0 || components.length === 0) {
      metadataUnavailableCodes.push(expectedCode);
    }
  }

  let dossierRuntimeLinkState: ComponentFirstDossierRuntimeLinkState = "NOT_LINKED_YET";
  if (runtimeActivationLeakIssues.length > 0) {
    dossierRuntimeLinkState = "BLOCKED_RUNTIME_ACTIVATION_LEAK";
  } else if (completeness.foundRowCount === 0) {
    dossierRuntimeLinkState = "READONLY_CONTRACT_ONLY";
  } else if (completeness.foundRowCount < completeness.expectedRowCount) {
    dossierRuntimeLinkState = "PARTIAL_RUNTIME_LINK";
  } else {
    dossierRuntimeLinkState = "NOT_LINKED_YET";
  }

  let overallAlignmentState: ComponentFirstOverallAlignmentState;
  if (runtimeActivationLeakIssues.length > 0) {
    overallAlignmentState = "BLOCKED_DOSSIER_ACTIVATION_LEAK";
  } else if (
    completeness.sourceMode === "blocked_invalid_live_state" ||
    drift.driftState === "BLOCKED_INVALID_LIVE_STATE" ||
    completeness.invalidActiveTemplateCodes.length > 0
  ) {
    overallAlignmentState = "BLOCKED_INVALID_LIVE_STATE";
  } else if (!contractValidation.valid) {
    overallAlignmentState = "READONLY_PARTIAL";
  } else if (completeness.sourceMode === "live_seeded_inactive") {
    overallAlignmentState = "READONLY_ALIGNED";
  } else if (completeness.sourceMode === "code_contract_fallback") {
    overallAlignmentState = "READONLY_FALLBACK_ONLY";
  } else {
    overallAlignmentState = "READONLY_PARTIAL";
  }

  return {
    expectedCount: COMPONENT_FIRST_EXPECTED_ROW_COUNT,
    liveFoundCount: completeness.foundRowCount,
    missingCodes: completeness.missingTemplateCodes,
    invalidActiveCodes: completeness.invalidActiveTemplateCodes,
    dossierContractCount: dossierContract.length,
    dossierRuntimeLinkState,
    overallAlignmentState,
    runtimeActivationLeakIssues,
    metadataUnavailableCodes,
    completeness,
    drift,
    contractEntries: dossierContract,
  };
}

export function componentFirstOverallAlignmentLabel(state: ComponentFirstOverallAlignmentState): string {
  return state;
}

export function componentFirstOverallAlignmentTone(state: ComponentFirstOverallAlignmentState): string {
  switch (state) {
    case "READONLY_ALIGNED":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "READONLY_PARTIAL":
    case "READONLY_FALLBACK_ONLY":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    case "BLOCKED_INVALID_LIVE_STATE":
    case "BLOCKED_DOSSIER_ACTIVATION_LEAK":
      return "border-rose-700/40 bg-rose-900/20 text-rose-300";
  }
}

export function componentFirstDossierRuntimeLinkLabel(state: ComponentFirstDossierRuntimeLinkState): string {
  switch (state) {
    case "NOT_LINKED_YET":
      return "Runtime dossier rows: not linked yet";
    case "READONLY_CONTRACT_ONLY":
      return "Runtime dossier rows: readonly contract only";
    case "PARTIAL_RUNTIME_LINK":
      return "Runtime dossier rows: partial live catalog only";
    case "BLOCKED_RUNTIME_ACTIVATION_LEAK":
      return "Runtime dossier rows: blocked activation leak";
  }
}
