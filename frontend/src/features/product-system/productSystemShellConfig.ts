import type { Permission } from "@/lib/rbac";

export const PRODUCT_SYSTEM_BASE_PATH = "/product-system";
export const PRODUCT_SYSTEM_PRODUCTS_PATH = "/product-system/products";

export const PRODUCT_SYSTEM_PLANNED_BADGE_RO = "Planificat";

export const PRODUCT_SYSTEM_PLANNED_SECTION_MESSAGE =
  "Această secțiune este planificată — nu este operațională acum. Nu configurați aici date de produs; folosiți Products pentru catalogul activ.";

/** Existing admin-only permission — no new RBAC codes. */
export const PRODUCT_SYSTEM_ADVANCED_PERMISSION: Permission = "view:governance";

export type ProductSystemShellNavId =
  | "products"
  | "components"
  | "resources"
  | "operations"
  | "dependencies"
  | "validation"
  | "advanced";

export type ProductSystemShellNavItem = {
  id: ProductSystemShellNavId;
  label: string;
  path: string;
  requiresAdvancedAccess?: boolean;
  plannedSection?: boolean;
};

export const PRODUCT_SYSTEM_SHELL_NAV: ProductSystemShellNavItem[] = [
  { id: "products", label: "Products", path: PRODUCT_SYSTEM_PRODUCTS_PATH },
  {
    id: "components",
    label: "Components",
    path: "/product-system/components",
    plannedSection: true,
  },
  {
    id: "resources",
    label: "Resources",
    path: "/product-system/resources",
    plannedSection: true,
  },
  {
    id: "operations",
    label: "Operations",
    path: "/product-system/operations",
    plannedSection: true,
  },
  {
    id: "dependencies",
    label: "Dependencies",
    path: "/product-system/dependencies",
    plannedSection: true,
  },
  {
    id: "validation",
    label: "Validation",
    path: "/product-system/validation",
    plannedSection: true,
  },
  {
    id: "advanced",
    label: "Advanced",
    path: "/product-system/advanced",
    requiresAdvancedAccess: true,
    plannedSection: true,
  },
];

export const PRICING_REGISTRY_PATH = "/inventory/pricing";
