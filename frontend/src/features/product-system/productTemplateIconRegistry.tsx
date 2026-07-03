import type { ComponentType, SVGProps } from "react";
import { Box, Package } from "lucide-react";
import lettersIconUrl from "@/assets/product-system/icons/tpl-letters.svg";

export type ProductTemplateIconConfig = {
  templateCode: string;
  iconUrl?: string;
  Icon?: ComponentType<SVGProps<SVGSVGElement>>;
  color: string;
  backgroundColor: string;
  borderColor: string;
  label: string;
  source: "specific" | "fallback";
};

const PRODUCT_TEMPLATE_ICON_CONFIG: Record<string, ProductTemplateIconConfig> = {
  "TPL-VOLUMETRIC-LETTERS_v2": {
    templateCode: "TPL-VOLUMETRIC-LETTERS_v2",
    iconUrl: lettersIconUrl,
    color: "#8B5CF6",
    backgroundColor: "rgba(139, 92, 246, 0.12)",
    borderColor: "rgba(139, 92, 246, 0.28)",
    label: "Icon litere volumetrice",
    source: "specific",
  },
};

const PRODUCT_FALLBACK_ICON_CONFIG: ProductTemplateIconConfig = {
  templateCode: "__product_fallback__",
  Icon: Package,
  color: "#94A3B8",
  backgroundColor: "rgba(148, 163, 184, 0.10)",
  borderColor: "rgba(148, 163, 184, 0.20)",
  label: "Icon template produs",
  source: "fallback",
};

const COMPONENT_FALLBACK_ICON_CONFIG: ProductTemplateIconConfig = {
  templateCode: "__component_fallback__",
  Icon: Box,
  color: "#64748B",
  backgroundColor: "rgba(100, 116, 139, 0.10)",
  borderColor: "rgba(100, 116, 139, 0.18)",
  label: "Icon componenta Product System",
  source: "fallback",
};

export function getProductTemplateIconConfig(
  templateCode: string,
  productSystemRole?: string | null
): ProductTemplateIconConfig {
  const configured = PRODUCT_TEMPLATE_ICON_CONFIG[templateCode];
  if (configured) return configured;

  if (productSystemRole === "internal_module" || productSystemRole === "shared_component") {
    return { ...COMPONENT_FALLBACK_ICON_CONFIG, templateCode };
  }

  return { ...PRODUCT_FALLBACK_ICON_CONFIG, templateCode };
}