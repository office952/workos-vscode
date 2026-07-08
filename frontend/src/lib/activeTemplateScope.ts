/** Owner-valid active template scope — quote/pricing flows only. */

export const OWNER_VALID_ACTIVE_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2";

export const OWNER_VALID_ACTIVE_TEMPLATE_CODES = [
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
] as const;

const OWNER_VALID_ACTIVE_TEMPLATE_CODE_NORMALIZED = new Set(
  OWNER_VALID_ACTIVE_TEMPLATE_CODES.map(normalizeTemplateCode)
);

export function normalizeTemplateCode(code: string | null | undefined): string {
  return String(code ?? "").trim().toUpperCase();
}

export function isOwnerValidActiveTemplate(
  code: string | null | undefined
): boolean {
  return OWNER_VALID_ACTIVE_TEMPLATE_CODE_NORMALIZED.has(normalizeTemplateCode(code));
}

export function isActiveTemplateForQuote(template: {
  active?: boolean | null;
  template_code: string;
}): boolean {
  return template.active !== false && isOwnerValidActiveTemplate(template.template_code);
}

export function filterActiveTemplatesForQuote<
  T extends { active?: boolean | null; template_code: string },
>(templates: T[]): T[] {
  return templates.filter(isActiveTemplateForQuote);
}

export function filterArchivedExperimentalTemplates<
  T extends { active?: boolean | null; template_code: string },
>(templates: T[]): T[] {
  return templates.filter((t) => !isActiveTemplateForQuote(t));
}
