/**
 * Pricing Studio tab eligibility — Product System detail.
 * Products always get Prețuri template. Selected modules keep their bucket
 * but may expose the shared Studio when API recipe truth exists.
 */

function normalizeTemplateCode(code: string): string {
  return String(code || "")
    .trim()
    .toUpperCase();
}

/** Modules that keep non-product bucket identity but need Prețuri template access. */
const PRICING_STUDIO_ELIGIBLE_MODULE_CODES: ReadonlySet<string> = new Set([
  "TPL-VOLUM-ALUMINIU_V1",
]);

export function isPricingStudioEligibleModule(templateCode: string): boolean {
  return PRICING_STUDIO_ELIGIBLE_MODULE_CODES.has(normalizeTemplateCode(templateCode));
}

export function showTemplatePricingStudio(args: {
  isProduct: boolean;
  templateCode: string;
}): boolean {
  return args.isProduct || isPricingStudioEligibleModule(args.templateCode);
}
