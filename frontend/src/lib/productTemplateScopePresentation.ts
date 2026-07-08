import type { ProductTemplateAvailabilityItem } from "@/lib/api";

export const LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2";
export const LOGO_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO_v1";

export type ProductTemplateScopePresentation = {
  templateCode: string;
  isProductTemplate: boolean;
  familyLabel: string;
  workIntakeLabel: string;
  workIntakeValueLabel: "Da" | "Nu";
  rootDirectLabel: string;
  statusLabel: string;
  catalogStatusLabel: string;
  usageModeLabel: string;
  shortDescription: string;
  isDirectRootAllowed: boolean;
  isCandidateComposition: boolean;
  forbiddenReason: string | null;
};

export type AnalyzerFirstScopePresentation = {
  templateCode: null;
  isProductTemplate: false;
  statusLabel: string;
  shortDescription: string;
};

export function getAnalyzerFirstScopePresentation(): AnalyzerFirstScopePresentation {
  return {
    templateCode: null,
    isProductTemplate: false,
    statusLabel: "Recomandat",
    shortDescription: "SVG-ul decide compoziția: logo, litere, sau litere + logo.",
  };
}

function isCandidateProductTemplate(template: ProductTemplateAvailabilityItem): boolean {
  return (
    template.template_code === LOGO_TEMPLATE_CODE ||
    template.product_system_role === "candidate_product" ||
    template.display_group === "candidate_products"
  );
}

function isOfferableProductTemplate(template: ProductTemplateAvailabilityItem): boolean {
  return (
    template.template_code === LETTERS_TEMPLATE_CODE ||
    template.product_system_role === "offerable_product" ||
    template.display_group === "active_products" ||
    template.quote_offerable
  );
}

export function getProductTemplateScopePresentation(
  template: ProductTemplateAvailabilityItem,
): ProductTemplateScopePresentation {
  const isCandidateComposition = isCandidateProductTemplate(template);
  const isDirectRootAllowed = isOfferableProductTemplate(template) && !isCandidateComposition;
  const workIntakeValueLabel = isDirectRootAllowed ? "Da" : "Nu";

  let shortDescription =
    template.ui_description?.trim() ||
    template.description?.trim() ||
    (isDirectRootAllowed
      ? "Product Template activ in Product System."
      : "Product Template disponibil doar prin analyzer / linked composition.");

  if (template.template_code === LETTERS_TEMPLATE_CODE) {
    shortDescription =
      "Product Template activ pentru litere volumetrice. Porneste cerere directa pentru root-ul ofertabil curent.";
  } else if (isCandidateComposition) {
    shortDescription =
      "Product Template logo volumetric. Disponibil pentru analyzer / linked composition. Nu porneste oferta directa.";
  }

  return {
    templateCode: template.template_code,
    isProductTemplate:
      template.product_system_role === "offerable_product" ||
      template.product_system_role === "candidate_product" ||
      template.display_group === "active_products" ||
      template.display_group === "candidate_products" ||
      template.template_code === LETTERS_TEMPLATE_CODE ||
      template.template_code === LOGO_TEMPLATE_CODE,
    familyLabel: template.family_name ?? "Product System",
    workIntakeLabel: `Work Intake ${isDirectRootAllowed ? "DA" : "NU"}`,
    workIntakeValueLabel,
    rootDirectLabel: isDirectRootAllowed
      ? "Root direct: permis"
      : "Root direct: blocat pana la owner GO",
    statusLabel: isDirectRootAllowed ? "Activ pentru ofertare" : "Candidat compozitie",
    catalogStatusLabel: isCandidateComposition
      ? "In pregatire"
      : isDirectRootAllowed
        ? "Produs ofertabil"
        : template.ui_label?.trim() || "Arhivat / experimental",
    usageModeLabel: isCandidateComposition ? "candidate / linked child" : isDirectRootAllowed ? "offerable" : "not direct root",
    shortDescription,
    isDirectRootAllowed,
    isCandidateComposition,
    forbiddenReason: isDirectRootAllowed ? null : "Necesita GO owner pentru ofertare.",
  };
}