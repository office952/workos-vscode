import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";

export type UnifiedCatalogBucketId =
  | "current-products"
  | "candidate-products"
  | "component-first-sets"
  | "legacy-shared-modules"
  | "archived";

export type UnifiedCatalogFilter =
  | "all"
  | "current-products"
  | "candidate-products"
  | "component-first-sets"
  | "legacy-modules"
  | "archived"
  | "blocked";

export const UNIFIED_CATALOG_FILTERS: Array<{
  id: UnifiedCatalogFilter;
  label: string;
  testId: string;
}> = [
  { id: "all", label: "All", testId: "product-system-filter-all" },
  { id: "current-products", label: "Current products", testId: "product-system-filter-current-products" },
  { id: "candidate-products", label: "Candidate products", testId: "product-system-filter-candidate-products" },
  { id: "component-first-sets", label: "Component-first sets", testId: "product-system-filter-component-first-sets" },
  { id: "legacy-modules", label: "Legacy modules", testId: "product-system-filter-legacy-modules" },
  { id: "archived", label: "Archived", testId: "product-system-filter-archived" },
  { id: "blocked", label: "Blocked / Owner GO", testId: "product-system-filter-blocked" },
];

export const UNIFIED_CATALOG_BUCKETS: Array<{
  id: UnifiedCatalogBucketId;
  label: string;
  testId: string;
  toggleTestId: string;
  defaultExpanded: boolean;
  order: number;
}> = [
  {
    id: "current-products",
    label: "Current Products / Active Roots",
    testId: "product-system-catalog-bucket-current-products",
    toggleTestId: "product-system-catalog-bucket-toggle-current-products",
    defaultExpanded: true,
    order: 1,
  },
  {
    id: "candidate-products",
    label: "Candidate Products",
    testId: "product-system-catalog-bucket-candidate-products",
    toggleTestId: "product-system-catalog-bucket-toggle-candidate-products",
    defaultExpanded: true,
    order: 2,
  },
  {
    id: "component-first-sets",
    label: "Component-first Candidate Sets",
    testId: "product-system-catalog-bucket-component-first-sets",
    toggleTestId: "product-system-catalog-bucket-toggle-component-first-sets",
    defaultExpanded: true,
    order: 3,
  },
  {
    id: "legacy-shared-modules",
    label: "Legacy Shared Modules",
    testId: "product-system-catalog-bucket-legacy-shared-modules",
    toggleTestId: "product-system-catalog-bucket-toggle-legacy-shared-modules",
    defaultExpanded: false,
    order: 4,
  },
  {
    id: "archived",
    label: "Archived / Experimental",
    testId: "product-system-catalog-bucket-archived",
    toggleTestId: "product-system-catalog-bucket-toggle-archived",
    defaultExpanded: false,
    order: 5,
  },
];

export type UnifiedCatalogEntryKind = "template" | "candidate-set";

export type UnifiedCatalogEntry = {
  id: string;
  kind: UnifiedCatalogEntryKind;
  bucket: UnifiedCatalogBucketId;
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

export type UnifiedCatalogBucketGroup = {
  bucket: (typeof UNIFIED_CATALOG_BUCKETS)[number];
  entries: UnifiedCatalogEntry[];
};

export type UnifiedCatalogBucketTheme = {
  dot: string;
  badge: string;
};

export const UNIFIED_CATALOG_BUCKET_THEMES: Record<UnifiedCatalogBucketId, UnifiedCatalogBucketTheme> = {
  "current-products": {
    dot: "bg-emerald-400/80",
    badge: "border-emerald-800/40 bg-emerald-950/25 text-emerald-200/90",
  },
  "candidate-products": {
    dot: "bg-amber-400/80",
    badge: "border-amber-800/40 bg-amber-950/25 text-amber-200/90",
  },
  "component-first-sets": {
    dot: "bg-cyan-400/80",
    badge: "border-cyan-800/40 bg-cyan-950/25 text-cyan-200/90",
  },
  "legacy-shared-modules": {
    dot: "bg-slate-500/80",
    badge: "border-slate-700/60 bg-slate-900/60 text-slate-400",
  },
  archived: {
    dot: "bg-zinc-500/70",
    badge: "border-slate-700/60 bg-slate-900/60 text-slate-400",
  },
};
