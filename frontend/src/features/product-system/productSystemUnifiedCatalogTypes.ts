import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";

export type UnifiedCatalogFilter =
  | "all"
  | "products"
  | "components"
  | "candidate-sets"
  | "active-roots"
  | "readonly"
  | "blocked"
  | "archived";

export const UNIFIED_CATALOG_FILTERS: Array<{
  id: UnifiedCatalogFilter;
  label: string;
  testId: string;
}> = [
  { id: "all", label: "All", testId: "product-system-filter-all" },
  { id: "products", label: "Products", testId: "product-system-filter-products" },
  { id: "components", label: "Components", testId: "product-system-filter-components" },
  { id: "candidate-sets", label: "Candidate sets", testId: "product-system-filter-candidate-sets" },
  { id: "active-roots", label: "Active roots", testId: "product-system-filter-active-roots" },
  { id: "readonly", label: "Readonly", testId: "product-system-filter-readonly" },
  { id: "blocked", label: "Blocked / Owner GO", testId: "product-system-filter-blocked" },
  { id: "archived", label: "Archived", testId: "product-system-filter-archived" },
];

export type UnifiedCatalogEntryKind = "template" | "candidate-set";

export type UnifiedCatalogEntry = {
  id: string;
  kind: UnifiedCatalogEntryKind;
  name: string;
  templateCode: string;
  entityType: string;
  lifecycleLabel: string;
  metadata: string;
  importanceRank: number;
  isProduct: boolean;
  isComponent: boolean;
  isCandidateReadonly: boolean;
  isActiveRoot: boolean;
  isArchived: boolean;
  isBlocked: boolean;
  isReadonly: boolean;
  template?: ProductTemplateEntity;
  availability?: ProductTemplateAvailabilityItem;
};

export type UnifiedCatalogDetailSection =
  | "overview"
  | "composition"
  | "components"
  | "dossier"
  | "fields"
  | "product-truth-paths"
  | "guards";
