export const COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE = "TPL-LETTERS-COMPOSER_v1";

export const COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES = [
  "TPL-COMP-LETTER-FACE_v1",
  "TPL-COMP-LETTER-BACK_v1",
  "TPL-COMP-LETTER-RETURN-CANT_v1",
  "TPL-COMP-LETTER-LED_v1",
  "TPL-COMP-LETTER-FINISH_v1",
  "TPL-COMP-LETTER-MOUNTING_v1",
] as const;

export const COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES = [
  COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
  ...COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES,
] as const;

export const COMPONENT_FIRST_EXPECTED_ROW_COUNT = COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES.length;

export type ComponentFirstTemplateCode = (typeof COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES)[number];

export type ComponentFirstSourceMode =
  | "live_seeded_inactive"
  | "partial_live_inactive"
  | "code_contract_fallback"
  | "blocked_invalid_live_state";

export type ComponentFirstCompletenessAssessment = {
  sourceMode: ComponentFirstSourceMode;
  foundRowCount: number;
  expectedRowCount: number;
  foundTemplateCodes: ComponentFirstTemplateCode[];
  missingTemplateCodes: ComponentFirstTemplateCode[];
  invalidActiveTemplateCodes: ComponentFirstTemplateCode[];
};

type ComponentFirstTemplateRow = {
  template_code: string;
  active?: boolean | null;
};

export function normalizeComponentFirstTemplateCode(templateCode: string | null | undefined): string {
  return String(templateCode ?? "").trim().toUpperCase();
}

export function isComponentFirstLettersTemplate(
  templateCode: string | null | undefined
): templateCode is ComponentFirstTemplateCode {
  const normalized = normalizeComponentFirstTemplateCode(templateCode);
  return COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES.some(
    (candidate) => normalizeComponentFirstTemplateCode(candidate) === normalized
  );
}

function isExpectedInactiveRow(template: ComponentFirstTemplateRow): boolean {
  return template.active === false;
}

function isActivationLeakRow(template: ComponentFirstTemplateRow): boolean {
  return template.active !== false;
}

export function assessComponentFirstLiveCompleteness(
  templates: ComponentFirstTemplateRow[]
): ComponentFirstCompletenessAssessment {
  const templateByCode = new Map(
    templates.map((template) => [
      normalizeComponentFirstTemplateCode(template.template_code),
      template,
    ])
  );

  const foundTemplateCodes: ComponentFirstTemplateCode[] = [];
  const missingTemplateCodes: ComponentFirstTemplateCode[] = [];
  const invalidActiveTemplateCodes: ComponentFirstTemplateCode[] = [];

  for (const expectedCode of COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES) {
    const template = templateByCode.get(normalizeComponentFirstTemplateCode(expectedCode));
    if (!template) {
      missingTemplateCodes.push(expectedCode);
      continue;
    }

    foundTemplateCodes.push(expectedCode);
    if (isActivationLeakRow(template)) {
      invalidActiveTemplateCodes.push(expectedCode);
    }
  }

  const foundRowCount = foundTemplateCodes.length;
  const expectedRowCount = COMPONENT_FIRST_EXPECTED_ROW_COUNT;

  let sourceMode: ComponentFirstSourceMode;
  if (invalidActiveTemplateCodes.length > 0) {
    sourceMode = "blocked_invalid_live_state";
  } else if (foundRowCount === 0) {
    sourceMode = "code_contract_fallback";
  } else if (
    foundRowCount === expectedRowCount &&
    foundTemplateCodes.every((code) => {
      const template = templateByCode.get(normalizeComponentFirstTemplateCode(code));
      return template ? isExpectedInactiveRow(template) : false;
    })
  ) {
    sourceMode = "live_seeded_inactive";
  } else {
    sourceMode = "partial_live_inactive";
  }

  return {
    sourceMode,
    foundRowCount,
    expectedRowCount,
    foundTemplateCodes,
    missingTemplateCodes,
    invalidActiveTemplateCodes,
  };
}

export function componentFirstSourceLabel(sourceMode: ComponentFirstSourceMode): string {
  switch (sourceMode) {
    case "live_seeded_inactive":
      return "LIVE SEEDED INACTIVE ROWS";
    case "partial_live_inactive":
      return "PARTIAL LIVE INACTIVE ROWS";
    case "code_contract_fallback":
      return "CODE CONTRACT FALLBACK";
    case "blocked_invalid_live_state":
      return "BLOCKED / INVALID LIVE STATE";
  }
}

export function componentFirstSourceTone(sourceMode: ComponentFirstSourceMode): string {
  switch (sourceMode) {
    case "live_seeded_inactive":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "partial_live_inactive":
      return "border-orange-700/40 bg-orange-900/20 text-orange-300";
    case "code_contract_fallback":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    case "blocked_invalid_live_state":
      return "border-rose-700/40 bg-rose-900/20 text-rose-300";
  }
}

export function componentFirstSourceDescription(sourceMode: ComponentFirstSourceMode): string {
  switch (sourceMode) {
    case "live_seeded_inactive":
      return "All 7 expected inactive rows exist in DB/API and remain inactive by design.";
    case "partial_live_inactive":
      return "Some expected inactive rows exist live, but the set is incomplete. Missing rows use readonly contract fallback and must not be treated as a complete live set.";
    case "code_contract_fallback":
      return "Live inert rows are absent; showing accepted readonly contract until a deliberate non-live-altering seed review step is approved.";
    case "blocked_invalid_live_state":
      return "At least one expected row is active or otherwise not safely inactive. Do not treat this set as readonly inert catalog truth.";
  }
}

export const COMPONENT_FIRST_FAMILY_ID = "litere_component_first_candidate";
export const COMPONENT_FIRST_FAMILY_NAME = "Litere component-first candidate";

export type ComponentFirstDriftState =
  | "NO_DRIFT"
  | "FALLBACK_CONTRACT_DRIFT"
  | "LIVE_ROW_CONTRACT_DRIFT"
  | "LIVE_EXTRA_EXPECTED_FAMILY_ROW"
  | "BLOCKED_INVALID_LIVE_STATE";

export type ComponentFirstContractCheckStatus = "OK" | "WARNING" | "BLOCKED";

export type ComponentFirstFallbackContractRow = {
  templateCode: ComponentFirstTemplateCode;
  rowKind: "composer" | "component";
  familyId: string;
  familyName: string;
  templateKind: "product_composer" | "component_template";
  readiness: "planned";
  active: false;
  componentId?: string;
  role?: string;
  componentKind?: string;
  targetProductTruthPath?: string;
  compositionComponentTemplateCodes?: ComponentFirstTemplateCode[];
};

export const COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE: ComponentFirstFallbackContractRow[] = [
  {
    templateCode: COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE,
    rowKind: "composer",
    familyId: COMPONENT_FIRST_FAMILY_ID,
    familyName: COMPONENT_FIRST_FAMILY_NAME,
    templateKind: "product_composer",
    readiness: "planned",
    active: false,
    compositionComponentTemplateCodes: [...COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES],
  },
  {
    templateCode: "TPL-COMP-LETTER-FACE_v1",
    rowKind: "component",
    familyId: COMPONENT_FIRST_FAMILY_ID,
    familyName: COMPONENT_FIRST_FAMILY_NAME,
    templateKind: "component_template",
    readiness: "planned",
    active: false,
    componentId: "comp_letter_face_v1",
    role: "face",
    componentKind: "structural",
    targetProductTruthPath: "components.face.instances[]",
  },
  {
    templateCode: "TPL-COMP-LETTER-BACK_v1",
    rowKind: "component",
    familyId: COMPONENT_FIRST_FAMILY_ID,
    familyName: COMPONENT_FIRST_FAMILY_NAME,
    templateKind: "component_template",
    readiness: "planned",
    active: false,
    componentId: "comp_letter_back_v1",
    role: "back",
    componentKind: "structural",
    targetProductTruthPath: "components.back.instances[]",
  },
  {
    templateCode: "TPL-COMP-LETTER-RETURN-CANT_v1",
    rowKind: "component",
    familyId: COMPONENT_FIRST_FAMILY_ID,
    familyName: COMPONENT_FIRST_FAMILY_NAME,
    templateKind: "component_template",
    readiness: "planned",
    active: false,
    componentId: "comp_letter_return_cant_v1",
    role: "return_cant",
    componentKind: "structural",
    targetProductTruthPath: "components.return_cant.instances[]",
  },
  {
    templateCode: "TPL-COMP-LETTER-LED_v1",
    rowKind: "component",
    familyId: COMPONENT_FIRST_FAMILY_ID,
    familyName: COMPONENT_FIRST_FAMILY_NAME,
    templateKind: "component_template",
    readiness: "planned",
    active: false,
    componentId: "comp_letter_led_v1",
    role: "lighting",
    componentKind: "functional",
    targetProductTruthPath: "components.led.instances[]",
  },
  {
    templateCode: "TPL-COMP-LETTER-FINISH_v1",
    rowKind: "component",
    familyId: COMPONENT_FIRST_FAMILY_ID,
    familyName: COMPONENT_FIRST_FAMILY_NAME,
    templateKind: "component_template",
    readiness: "planned",
    active: false,
    componentId: "comp_letter_finish_v1",
    role: "finish",
    componentKind: "functional",
    targetProductTruthPath: "components.finish.instances[]",
  },
  {
    templateCode: "TPL-COMP-LETTER-MOUNTING_v1",
    rowKind: "component",
    familyId: COMPONENT_FIRST_FAMILY_ID,
    familyName: COMPONENT_FIRST_FAMILY_NAME,
    templateKind: "component_template",
    readiness: "planned",
    active: false,
    componentId: "comp_letter_mounting_v1",
    role: "mounting",
    componentKind: "functional",
    targetProductTruthPath: "components.mounting.instances[]",
  },
];

export type ComponentFirstLiveTemplateRow = ComponentFirstTemplateRow & {
  family_id?: string | null;
  family_name?: string | null;
  components_json?: string | null;
  notes?: string | null;
};

export type ComponentFirstContractDriftAssessment = {
  driftState: ComponentFirstDriftState;
  contractCheckStatus: ComponentFirstContractCheckStatus;
  fallbackContractValid: boolean;
  fallbackContractIssues: string[];
  liveExtraFamilyRows: string[];
  liveRowDriftIssues: string[];
  metadataUnavailableWarnings: string[];
  completeness: ComponentFirstCompletenessAssessment;
};

function safeParseJson<T>(raw: string | null | undefined, fallback: T): T {
  if (!raw) return fallback;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function isComponentFirstFamilyTemplateCode(templateCode: string): boolean {
  const normalized = normalizeComponentFirstTemplateCode(templateCode);
  if (normalized === normalizeComponentFirstTemplateCode(COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE)) {
    return true;
  }
  return normalized.startsWith("TPL-COMP-LETTER-");
}

export function validateComponentFirstFallbackContract(
  contract: readonly ComponentFirstFallbackContractRow[] = COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE
): { valid: boolean; issues: string[] } {
  const issues: string[] = [];

  if (contract.length !== COMPONENT_FIRST_EXPECTED_ROW_COUNT) {
    issues.push(`fallback_contract_row_count_${contract.length}_expected_${COMPONENT_FIRST_EXPECTED_ROW_COUNT}`);
  }

  const seenCodes = new Set<string>();
  let composerCount = 0;
  let componentCount = 0;

  for (const row of contract) {
    const normalized = normalizeComponentFirstTemplateCode(row.templateCode);
    if (seenCodes.has(normalized)) {
      issues.push(`fallback_contract_duplicate_code_${row.templateCode}`);
    }
    seenCodes.add(normalized);

    if (!COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES.some((code) => normalizeComponentFirstTemplateCode(code) === normalized)) {
      issues.push(`fallback_contract_extra_code_${row.templateCode}`);
    }

    if (row.rowKind === "composer") {
      composerCount += 1;
      if (row.templateCode !== COMPONENT_FIRST_COMPOSER_TEMPLATE_CODE) {
        issues.push(`fallback_contract_composer_code_mismatch_${row.templateCode}`);
      }
      const composition = row.compositionComponentTemplateCodes ?? [];
      if (composition.length !== COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES.length) {
        issues.push("fallback_contract_composer_composition_count_mismatch");
      }
      for (const componentCode of COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES) {
        if (!composition.includes(componentCode)) {
          issues.push(`fallback_contract_composer_missing_component_${componentCode}`);
        }
      }
    } else {
      componentCount += 1;
      if (!COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES.includes(row.templateCode)) {
        issues.push(`fallback_contract_component_code_out_of_family_${row.templateCode}`);
      }
      if (!row.componentId || !row.role || !row.componentKind || !row.targetProductTruthPath) {
        issues.push(`fallback_contract_component_metadata_incomplete_${row.templateCode}`);
      }
    }

    if (row.active !== false || row.readiness !== "planned") {
      issues.push(`fallback_contract_inactive_candidate_marker_invalid_${row.templateCode}`);
    }
  }

  for (const expectedCode of COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES) {
    if (!seenCodes.has(normalizeComponentFirstTemplateCode(expectedCode))) {
      issues.push(`fallback_contract_missing_expected_code_${expectedCode}`);
    }
  }

  if (composerCount !== 1) {
    issues.push(`fallback_contract_composer_count_${composerCount}`);
  }
  if (componentCount !== COMPONENT_FIRST_COMPONENT_TEMPLATE_CODES.length) {
    issues.push(`fallback_contract_component_count_${componentCount}`);
  }

  return { valid: issues.length === 0, issues };
}

function compareLiveRowAgainstFallbackContract(
  liveRow: ComponentFirstLiveTemplateRow,
  fallbackRow: ComponentFirstFallbackContractRow
): { driftIssues: string[]; metadataWarnings: string[] } {
  const driftIssues: string[] = [];
  const metadataWarnings: string[] = [];

  if (normalizeComponentFirstTemplateCode(liveRow.template_code) !== normalizeComponentFirstTemplateCode(fallbackRow.templateCode)) {
    driftIssues.push(`live_row_code_mismatch_${liveRow.template_code}`);
  }

  if (liveRow.active !== false) {
    driftIssues.push(`live_row_active_not_false_${liveRow.template_code}`);
  }

  if (liveRow.family_id != null && liveRow.family_id !== fallbackRow.familyId) {
    driftIssues.push(`live_row_family_id_mismatch_${liveRow.template_code}`);
  } else if (liveRow.family_id == null) {
    metadataWarnings.push(`metadata_unavailable_family_id_${liveRow.template_code}`);
  }

  if (liveRow.family_name != null && liveRow.family_name !== fallbackRow.familyName) {
    driftIssues.push(`live_row_family_name_mismatch_${liveRow.template_code}`);
  } else if (liveRow.family_name == null) {
    metadataWarnings.push(`metadata_unavailable_family_name_${liveRow.template_code}`);
  }

  const notes = safeParseJson<Record<string, unknown>>(liveRow.notes, {});
  if (Object.keys(notes).length > 0) {
    if (notes.template_kind != null && String(notes.template_kind) !== fallbackRow.templateKind) {
      driftIssues.push(`live_row_template_kind_mismatch_${liveRow.template_code}`);
    }
    if (notes.readiness != null && String(notes.readiness) !== fallbackRow.readiness) {
      driftIssues.push(`live_row_readiness_mismatch_${liveRow.template_code}`);
    }
  } else {
    metadataWarnings.push(`metadata_unavailable_notes_${liveRow.template_code}`);
  }

  const components = safeParseJson<Array<Record<string, unknown>>>(liveRow.components_json, []);
  if (fallbackRow.rowKind === "composer") {
    if (components.length === 0) {
      metadataWarnings.push(`metadata_unavailable_composition_${liveRow.template_code}`);
    } else {
      const liveCompositionCodes = components
        .map((entry) => String(entry.component_template_code ?? ""))
        .filter(Boolean)
        .sort();
      const expectedCompositionCodes = [...(fallbackRow.compositionComponentTemplateCodes ?? [])]
        .map((code) => normalizeComponentFirstTemplateCode(code))
        .sort();
      const normalizedLiveCodes = liveCompositionCodes.map((code) => normalizeComponentFirstTemplateCode(code)).sort();
      if (normalizedLiveCodes.join("|") !== expectedCompositionCodes.join("|")) {
        driftIssues.push(`live_row_composition_mismatch_${liveRow.template_code}`);
      }
    }
  } else if (components.length > 0) {
    const component = components[0] ?? {};
    if (fallbackRow.componentId && String(component.component_id ?? "") !== fallbackRow.componentId) {
      driftIssues.push(`live_row_component_id_mismatch_${liveRow.template_code}`);
    }
    if (fallbackRow.role && String(component.role ?? component.role_key ?? "") !== fallbackRow.role) {
      driftIssues.push(`live_row_role_mismatch_${liveRow.template_code}`);
    }
    if (fallbackRow.componentKind && String(component.component_kind ?? "") !== fallbackRow.componentKind) {
      driftIssues.push(`live_row_component_kind_mismatch_${liveRow.template_code}`);
    }
    if (
      fallbackRow.targetProductTruthPath &&
      String(component.target_product_truth_path ?? "") !== fallbackRow.targetProductTruthPath
    ) {
      driftIssues.push(`live_row_target_path_mismatch_${liveRow.template_code}`);
    }
  } else {
    metadataWarnings.push(`metadata_unavailable_component_contract_${liveRow.template_code}`);
  }

  return { driftIssues, metadataWarnings };
}

function resolveContractCheckStatus(driftState: ComponentFirstDriftState, metadataWarnings: string[]): ComponentFirstContractCheckStatus {
  if (driftState === "BLOCKED_INVALID_LIVE_STATE") {
    return "BLOCKED";
  }
  if (
    driftState === "FALLBACK_CONTRACT_DRIFT" ||
    driftState === "LIVE_ROW_CONTRACT_DRIFT" ||
    driftState === "LIVE_EXTRA_EXPECTED_FAMILY_ROW" ||
    metadataWarnings.length > 0
  ) {
    return "WARNING";
  }
  return "OK";
}

export function assessComponentFirstContractDrift(
  liveTemplates: ComponentFirstLiveTemplateRow[],
  fallbackContract: readonly ComponentFirstFallbackContractRow[] = COMPONENT_FIRST_FALLBACK_CONTRACT_FIXTURE
): ComponentFirstContractDriftAssessment {
  const fallbackValidation = validateComponentFirstFallbackContract(fallbackContract);
  const completeness = assessComponentFirstLiveCompleteness(liveTemplates);
  const fallbackByCode = new Map(
    fallbackContract.map((row) => [normalizeComponentFirstTemplateCode(row.templateCode), row])
  );
  const liveByCode = new Map(
    liveTemplates.map((row) => [normalizeComponentFirstTemplateCode(row.template_code), row])
  );

  const liveExtraFamilyRows: string[] = [];
  for (const liveRow of liveTemplates) {
    const normalized = normalizeComponentFirstTemplateCode(liveRow.template_code);
    const inExpectedFamily =
      isComponentFirstFamilyTemplateCode(liveRow.template_code) ||
      liveRow.family_id === COMPONENT_FIRST_FAMILY_ID;
    const inExpectedSet = COMPONENT_FIRST_EXPECTED_TEMPLATE_CODES.some(
      (code) => normalizeComponentFirstTemplateCode(code) === normalized
    );
    if (inExpectedFamily && !inExpectedSet) {
      liveExtraFamilyRows.push(liveRow.template_code);
    }
  }

  const liveRowDriftIssues: string[] = [];
  const metadataUnavailableWarnings: string[] = [];

  if (!fallbackValidation.valid) {
    return {
      driftState: "FALLBACK_CONTRACT_DRIFT",
      contractCheckStatus: "WARNING",
      fallbackContractValid: false,
      fallbackContractIssues: fallbackValidation.issues,
      liveExtraFamilyRows,
      liveRowDriftIssues,
      metadataUnavailableWarnings,
      completeness,
    };
  }

  if (completeness.sourceMode === "blocked_invalid_live_state") {
    return {
      driftState: "BLOCKED_INVALID_LIVE_STATE",
      contractCheckStatus: "BLOCKED",
      fallbackContractValid: true,
      fallbackContractIssues: [],
      liveExtraFamilyRows,
      liveRowDriftIssues,
      metadataUnavailableWarnings,
      completeness,
    };
  }

  for (const expectedCode of completeness.foundTemplateCodes) {
    const liveRow = liveByCode.get(normalizeComponentFirstTemplateCode(expectedCode));
    const fallbackRow = fallbackByCode.get(normalizeComponentFirstTemplateCode(expectedCode));
    if (!liveRow || !fallbackRow) continue;
    const comparison = compareLiveRowAgainstFallbackContract(liveRow, fallbackRow);
    liveRowDriftIssues.push(...comparison.driftIssues);
    metadataUnavailableWarnings.push(...comparison.metadataWarnings);
  }

  let driftState: ComponentFirstDriftState = "NO_DRIFT";
  if (liveExtraFamilyRows.length > 0) {
    driftState = "LIVE_EXTRA_EXPECTED_FAMILY_ROW";
  }
  if (liveRowDriftIssues.length > 0) {
    driftState = "LIVE_ROW_CONTRACT_DRIFT";
  }

  return {
    driftState,
    contractCheckStatus: resolveContractCheckStatus(driftState, metadataUnavailableWarnings),
    fallbackContractValid: true,
    fallbackContractIssues: [],
    liveExtraFamilyRows,
    liveRowDriftIssues,
    metadataUnavailableWarnings,
    completeness,
  };
}

export function componentFirstContractCheckLabel(status: ComponentFirstContractCheckStatus): string {
  return `contract check: ${status}`;
}

export function componentFirstContractCheckTone(status: ComponentFirstContractCheckStatus): string {
  switch (status) {
    case "OK":
      return "border-emerald-700/40 bg-emerald-900/20 text-emerald-300";
    case "WARNING":
      return "border-amber-700/40 bg-amber-900/20 text-amber-300";
    case "BLOCKED":
      return "border-rose-700/40 bg-rose-900/20 text-rose-300";
  }
}

export function componentFirstDriftLabel(driftState: ComponentFirstDriftState): string {
  switch (driftState) {
    case "NO_DRIFT":
      return "NO_DRIFT";
    case "FALLBACK_CONTRACT_DRIFT":
      return "FALLBACK_CONTRACT_DRIFT";
    case "LIVE_ROW_CONTRACT_DRIFT":
      return "LIVE_ROW_CONTRACT_DRIFT";
    case "LIVE_EXTRA_EXPECTED_FAMILY_ROW":
      return "LIVE_EXTRA_EXPECTED_FAMILY_ROW";
    case "BLOCKED_INVALID_LIVE_STATE":
      return "BLOCKED_INVALID_LIVE_STATE";
  }
}
