import type { ProductTemplateAvailabilityItem } from "@/lib/api";
import {
  ACM_BOXED_TEMPLATE_CODE,
  commercialChipForTemplateCode,
  LETTERS_TEMPLATE_CODE,
  LOGO_TEMPLATE_CODE,
} from "@/lib/productSystemModularityTruth";

export { LETTERS_TEMPLATE_CODE, LOGO_TEMPLATE_CODE };

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
  const honestyChip = commercialChipForTemplateCode(template.template_code);

  let shortDescription =
    template.ui_description?.trim() ||
    template.description?.trim() ||
    (isDirectRootAllowed
      ? "Product Template activ în Product System."
      : "Product Template disponibil doar prin analyzer / linked composition.");

  if (template.template_code === LETTERS_TEMPLATE_CODE) {
    shortDescription =
      "Rădăcină ofertabilă pentru litere volumetrice. Slice 1 stabilizat; stabilizare generală parțială.";
  } else if (template.template_code === LOGO_TEMPLATE_CODE || isCandidateComposition) {
    shortDescription =
      "Candidat Logo — rădăcină blocată. Disponibil doar ca linked-child / analyzer. Nu pornește ofertă directă.";
  } else if (template.template_code === ACM_BOXED_TEMPLATE_CODE) {
    shortDescription =
      "Montaj ACM boxed — parțial. Panoul independent și casetatul nu sunt pregătite.";
  }

  let catalogStatusLabel = honestyChip;
  if (!catalogStatusLabel) {
    catalogStatusLabel = isCandidateComposition
      ? "Candidat · rădăcină blocată"
      : isDirectRootAllowed
        ? "Rădăcină folosită azi"
        : template.ui_label?.trim() || "Arhivat / experimental";
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
      ? "Ofertabil ca rădăcină"
      : "Blocat ca rădăcină până la owner GO",
    statusLabel: isDirectRootAllowed
      ? "Rădăcină folosită azi"
      : isCandidateComposition
        ? "Candidat · rădăcină blocată"
        : "Neofertabil ca rădăcină",
    catalogStatusLabel,
    usageModeLabel: isCandidateComposition
      ? "copil legat / candidate"
      : isDirectRootAllowed
        ? "rădăcină ofertabilă"
        : "nu rădăcină directă",
    shortDescription,
    isDirectRootAllowed,
    isCandidateComposition,
    forbiddenReason: isDirectRootAllowed ? null : "Necesită GO owner pentru ofertare.",
  };
}
