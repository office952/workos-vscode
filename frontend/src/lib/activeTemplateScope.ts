/** Owner-valid active template scope — quote/pricing flows only. */

import { TPL_ACM_BOXED_MOUNTING_SUPPORT } from "@/lib/acmQuoteInput";

export const OWNER_VALID_ACTIVE_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2";

/** Mirrors backend ROOT_OFFERABLE_TEMPLATE_CODES (template_usage_mode_policy.py). */
export const OWNER_VALID_ACTIVE_TEMPLATE_CODES = [
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
  TPL_ACM_BOXED_MOUNTING_SUPPORT,
] as const;

const OWNER_VALID_ACTIVE_TEMPLATE_CODE_NORMALIZED = new Set(
  OWNER_VALID_ACTIVE_TEMPLATE_CODES.map(normalizeTemplateCode),
);

export function normalizeTemplateCode(code: string | null | undefined): string {
  return String(code ?? "").trim().toUpperCase();
}

export function isOwnerValidActiveTemplate(
  code: string | null | undefined,
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

/** Parity contract with backend ROOT_OFFERABLE_TEMPLATE_CODES — update when backend policy changes. */
export const BACKEND_ROOT_OFFERABLE_TEMPLATE_CODES_PARITY = [
  "TPL-VOLUMETRIC-LETTERS_v2",
  "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
] as const;

export function assertOwnerValidScopeParityWithBackend(): void {
  const fe = [...OWNER_VALID_ACTIVE_TEMPLATE_CODES].map(normalizeTemplateCode).sort();
  const be = [...BACKEND_ROOT_OFFERABLE_TEMPLATE_CODES_PARITY].map(normalizeTemplateCode).sort();
  if (fe.length !== be.length || fe.some((code, index) => code !== be[index])) {
    throw new Error(
      `FE owner-valid scope drift: FE=[${fe.join(", ")}] BE=[${be.join(", ")}]`,
    );
  }
}
