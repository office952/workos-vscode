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
