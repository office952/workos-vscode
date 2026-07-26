import {
  CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
  CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES,
  CANDIDATE_MODULE_EXPECTED_ROW_COUNT,
  CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES,
  assessCandidateModuleProdusContractDrift,
  assessCandidateModuleProdusLiveCompleteness,
  normalizeCandidateModuleProdusTemplateCode,
  type CandidateModuleProdusCompletenessAssessment,
  type CandidateModuleProdusContractDriftAssessment,
  type CandidateModuleProdusLiveTemplateRow,
  type CandidateModuleProdusTemplateCode,
} from "./candidateModuleProdusReadonlyCompleteness";

export type CandidateModuleProdusDossierExpectedKind = "product_composer" | "component_template";

export type CandidateModuleProdusDossierRole =
  | "composer_orchestration"
  | "face"
  | "back"
  | "return_cant"
  | "led"
  | "finish"
  | "mounting";

export type CandidateModuleProdusTruthOwner = "product_composer" | "component_owned_truth";

export type CandidateModuleProdusDossierAlignmentState =
  | "READY_FOR_READONLY_DOSSIER_MAPPING"
  | "MISSING_LIVE_ROW"
  | "PARTIAL_LIVE_ROW"
  | "INVALID_ACTIVE_ROW"
  | "DOSSIER_METADATA_NOT_AVAILABLE"
  | "BLOCKED_DOSSIER_ACTIVATION_LEAK";

export type CandidateModuleProdusDossierRuntimeLinkState =
  | "NOT_LINKED_YET"
  | "READONLY_CONTRACT_ONLY"
  | "PARTIAL_RUNTIME_LINK"
  | "BLOCKED_RUNTIME_ACTIVATION_LEAK";

export type CandidateModuleProdusOverallAlignmentState =
  | "READONLY_ALIGNED"
  | "READONLY_PARTIAL"
  | "READONLY_FALLBACK_ONLY"
  | "BLOCKED_INVALID_LIVE_STATE"
  | "BLOCKED_DOSSIER_ACTIVATION_LEAK";

export type CandidateModuleProdusFutureDossierMetadata =
  | "technical_fields"
  | "material_rules"
  | "operation_hints"
  | "validations"
  | "produced_outputs"
  | "calculation_readiness";

export type CandidateModuleProdusDossierForbiddenNow =
  | "task_materialization"
  | "execution_plan"
  | "product_aggregate_runtime"
  | "pricing"
  | "quote_order"
  | "work_intake_exposure";

export type CandidateModuleProdusDossierContractEntry = {
  templateCode: CandidateModuleProdusTemplateCode;
  expectedKind: CandidateModuleProdusDossierExpectedKind;
  expectedDossierRole: CandidateModuleProdusDossierRole;
  expectedTruthOwner: CandidateModuleProdusTruthOwner;
  dossierAlignmentState: CandidateModuleProdusDossierAlignmentState;
  futureAllowedMetadata: CandidateModuleProdusFutureDossierMetadata[];
  forbiddenNow: CandidateModuleProdusDossierForbiddenNow[];
};

export const CANDIDATE_MODULE_DOSSIER_FORBIDDEN_NOW: CandidateModuleProdusDossierForbiddenNow[] = [
  "task_materialization",
  "execution_plan",
  "product_aggregate_runtime",
  "pricing",
  "quote_order",
  "work_intake_exposure",
];

export const CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE: CandidateModuleProdusDossierContractEntry[] = [
  {
    templateCode: CANDIDATE_MODULE_COMPOSER_TEMPLATE_CODE,
    expectedKind: "product_composer",
    expectedDossierRole: "composer_orchestration",
    expectedTruthOwner: "product_composer",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "validations", "calculation_readiness"],
    forbiddenNow: [...CANDIDATE_MODULE_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-FACE_v1",
    expectedKind: "component_template",
    expectedDossierRole: "face",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...CANDIDATE_MODULE_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-BACK_v1",
    expectedKind: "component_template",
    expectedDossierRole: "back",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...CANDIDATE_MODULE_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-RETURN-CANT_v1",
    expectedKind: "component_template",
    expectedDossierRole: "return_cant",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...CANDIDATE_MODULE_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-LED_v1",
    expectedKind: "component_template",
    expectedDossierRole: "led",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...CANDIDATE_MODULE_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-FINISH_v1",
    expectedKind: "component_template",
    expectedDossierRole: "finish",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...CANDIDATE_MODULE_DOSSIER_FORBIDDEN_NOW],
  },
  {
    templateCode: "TPL-COMP-LETTER-MOUNTING_v1",
    expectedKind: "component_template",
    expectedDossierRole: "mounting",
    expectedTruthOwner: "component_owned_truth",
    dossierAlignmentState: "READY_FOR_READONLY_DOSSIER_MAPPING",
    futureAllowedMetadata: ["technical_fields", "material_rules", "operation_hints", "validations", "produced_outputs", "calculation_readiness"],
    forbiddenNow: [...CANDIDATE_MODULE_DOSSIER_FORBIDDEN_NOW],
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

function detectRuntimeActivationLeakSignals(liveTemplates: CandidateModuleProdusLiveTemplateRow[]): string[] {
  const issues: string[] = [];

  for (const row of liveTemplates) {
    if (!isCandidateModuleProdusFamilyRow(row.template_code)) continue;

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

export function validateCandidateModuleProdusDossierContract(
  contract: readonly CandidateModuleProdusDossierContractEntry[] = CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE
): { valid: boolean; issues: string[] } {
  const issues: string[] = [];

  if (contract.length !== CANDIDATE_MODULE_EXPECTED_ROW_COUNT) {
    issues.push(`dossier_contract_row_count_${contract.length}`);
  }

  const seen = new Set<string>();
  let composerCount = 0;
  let componentCount = 0;

  for (const entry of contract) {
    const normalized = normalizeCandidateModuleProdusTemplateCode(entry.templateCode);
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
      if (!CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES.includes(entry.templateCode)) {
        issues.push(`component_code_out_of_family_${entry.templateCode}`);
      }
    }
  }

  if (composerCount !== 1) issues.push(`dossier_contract_composer_count_${composerCount}`);
  if (componentCount !== CANDIDATE_MODULE_COMPONENT_TEMPLATE_CODES.length) {
    issues.push(`dossier_contract_component_count_${componentCount}`);
  }

  for (const expectedCode of CANDIDATE_MODULE_EXPECTED_TEMPLATE_CODES) {
    if (!seen.has(normalizeCandidateModuleProdusTemplateCode(expectedCode))) {
      issues.push(`dossier_contract_missing_${expectedCode}`);
    }
  }

  return { valid: issues.length === 0, issues };
}

export type CandidateModuleProdusDossierAlignmentAssessment = {
  expectedCount: number;
  liveFoundCount: number;
  missingCodes: CandidateModuleProdusTemplateCode[];
  invalidActiveCodes: CandidateModuleProdusTemplateCode[];
  dossierContractCount: number;
  dossierRuntimeLinkState: CandidateModuleProdusDossierRuntimeLinkState;
  overallAlignmentState: CandidateModuleProdusOverallAlignmentState;
  runtimeActivationLeakIssues: string[];
  metadataUnavailableCodes: CandidateModuleProdusTemplateCode[];
  completeness: CandidateModuleProdusCompletenessAssessment;
  drift: CandidateModuleProdusContractDriftAssessment;
  contractEntries: CandidateModuleProdusDossierContractEntry[];
};

export function assessCandidateModuleProdusDossierAlignment(
  liveTemplates: CandidateModuleProdusLiveTemplateRow[],
  options?: {
    completeness?: CandidateModuleProdusCompletenessAssessment;
    drift?: CandidateModuleProdusContractDriftAssessment;
    dossierContract?: readonly CandidateModuleProdusDossierContractEntry[];
  }
): CandidateModuleProdusDossierAlignmentAssessment {
  const dossierContract = options?.dossierContract ?? CANDIDATE_MODULE_DOSSIER_CONTRACT_FIXTURE;
  const contractValidation = validateCandidateModuleProdusDossierContract(dossierContract);
  const completeness = options?.completeness ?? assessCandidateModuleProdusLiveCompleteness(liveTemplates);
  const drift = options?.drift ?? assessCandidateModuleProdusContractDrift(liveTemplates);
  const runtimeActivationLeakIssues = detectRuntimeActivationLeakSignals(liveTemplates);

  const liveByCode = new Map(
    liveTemplates.map((row) => [normalizeCandidateModuleProdusTemplateCode(row.template_code), row])
  );

  const metadataUnavailableCodes: CandidateModuleProdusTemplateCode[] = [];
  for (const expectedCode of completeness.foundTemplateCodes) {
    const liveRow = liveByCode.get(normalizeCandidateModuleProdusTemplateCode(expectedCode));
    if (!liveRow) continue;
    const notes = safeParseJson<Record<string, unknown>>(liveRow.notes, {});
    const components = safeParseJson<unknown[]>(liveRow.components_json, []);
    if (Object.keys(notes).length === 0 || components.length === 0) {
      metadataUnavailableCodes.push(expectedCode);
    }
  }

  let dossierRuntimeLinkState: CandidateModuleProdusDossierRuntimeLinkState = "NOT_LINKED_YET";
  if (runtimeActivationLeakIssues.length > 0) {
    dossierRuntimeLinkState = "BLOCKED_RUNTIME_ACTIVATION_LEAK";
  } else if (completeness.foundRowCount === 0) {
    dossierRuntimeLinkState = "READONLY_CONTRACT_ONLY";
  } else if (completeness.foundRowCount < completeness.expectedRowCount) {
    dossierRuntimeLinkState = "PARTIAL_RUNTIME_LINK";
  } else {
    dossierRuntimeLinkState = "NOT_LINKED_YET";
  }

  let overallAlignmentState: CandidateModuleProdusOverallAlignmentState;
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
    expectedCount: CANDIDATE_MODULE_EXPECTED_ROW_COUNT,
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

export function candidateModuleProdusOverallAlignmentLabel(state: CandidateModuleProdusOverallAlignmentState): string {
  return state;
}

export function candidateModuleProdusOverallAlignmentTone(state: CandidateModuleProdusOverallAlignmentState): string {
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

export function candidateModuleProdusDossierRuntimeLinkLabel(state: CandidateModuleProdusDossierRuntimeLinkState): string {
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
