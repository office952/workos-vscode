/**
 * V2 Product System rail status — page-local display only.
 * Reads existing modularity vocabulary. Does not recompute readiness or change authority.
 */
import { normalizeTemplateCode } from "@/lib/activeTemplateScope";
import {
  ACM_BOXED_TEMPLATE_CODE,
  LETTERS_TEMPLATE_CODE,
  LOGO_TEMPLATE_CODE,
  getProductModularityTruth,
} from "@/lib/productSystemModularityTruth";

export const PRODUCT_SYSTEM_V2_RAIL_TITLE_RO = "Produse";

export type ProductSystemV2RailStatusKind = "active" | "partial" | "blocked";

export type ProductSystemV2RailStatus = {
  kind: ProductSystemV2RailStatusKind;
  labelRo: string;
};

function modularityForTemplateCode(templateCode: string) {
  const normalized = normalizeTemplateCode(templateCode);
  if (normalized === normalizeTemplateCode(LETTERS_TEMPLATE_CODE)) {
    return getProductModularityTruth(LETTERS_TEMPLATE_CODE);
  }
  if (normalized === normalizeTemplateCode(ACM_BOXED_TEMPLATE_CODE)) {
    return getProductModularityTruth(ACM_BOXED_TEMPLATE_CODE);
  }
  if (normalized === normalizeTemplateCode(LOGO_TEMPLATE_CODE)) {
    return getProductModularityTruth(LOGO_TEMPLATE_CODE);
  }
  return getProductModularityTruth(templateCode);
}

export function productSystemV2RailStatus(
  templateCode: string | null | undefined,
): ProductSystemV2RailStatus | null {
  if (!templateCode) return null;
  const truth = modularityForTemplateCode(templateCode);
  if (!truth) return null;
  const normalized = normalizeTemplateCode(templateCode);
  if (normalized === normalizeTemplateCode(LETTERS_TEMPLATE_CODE)) {
    return { kind: "active", labelRo: truth.commercialChipRo };
  }
  if (normalized === normalizeTemplateCode(ACM_BOXED_TEMPLATE_CODE)) {
    return { kind: "partial", labelRo: truth.commercialChipRo };
  }
  if (normalized === normalizeTemplateCode(LOGO_TEMPLATE_CODE)) {
    return { kind: "blocked", labelRo: truth.commercialChipRo };
  }
  return null;
}

export function productSystemV2MissingTemplateCopy(templateCode: string): {
  headlineRo: string;
  detailRo: string;
  status: ProductSystemV2RailStatus | null;
} {
  const status = productSystemV2RailStatus(templateCode);
  if (status?.kind === "blocked") {
    return {
      headlineRo: status.labelRo,
      detailRo:
        "Rădăcina nu este ofertabilă. Șablonul există ca candidat — nu ca produs live în această listă.",
      status,
    };
  }
  return {
    headlineRo: `Template necunoscut în listă: ${templateCode}`,
    detailRo: "",
    status,
  };
}
