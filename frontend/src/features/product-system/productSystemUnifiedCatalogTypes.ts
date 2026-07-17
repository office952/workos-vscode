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
  { id: "all", label: "Toate", testId: "product-system-filter-all" },
  { id: "current-products", label: "Produse active", testId: "product-system-filter-current-products" },
  { id: "candidate-products", label: "Produse candidate", testId: "product-system-filter-candidate-products" },
  { id: "component-first-sets", label: "Seturi component-first", testId: "product-system-filter-component-first-sets" },
  { id: "legacy-modules", label: "Module legacy", testId: "product-system-filter-legacy-modules" },
  { id: "archived", label: "Arhivate", testId: "product-system-filter-archived" },
  { id: "blocked", label: "Blocate / Owner GO", testId: "product-system-filter-blocked" },
];

export const UNIFIED_CATALOG_BUCKETS: Array<{
  id: UnifiedCatalogBucketId;
  label: string;
  description: string;
  testId: string;
  toggleTestId: string;
  defaultExpanded: boolean;
  order: number;
}> = [
  {
    id: "current-products",
    label: "Produse active",
    description: "Rădăcini folosite azi în Work Intake și ofertare.",
    testId: "product-system-catalog-bucket-current-products",
    toggleTestId: "product-system-catalog-bucket-toggle-current-products",
    defaultExpanded: false,
    order: 1,
  },
  {
    id: "candidate-products",
    label: "Produse candidate",
    description: "Necesită decizie owner înainte de expunere directă.",
    testId: "product-system-catalog-bucket-candidate-products",
    toggleTestId: "product-system-catalog-bucket-toggle-candidate-products",
    defaultExpanded: false,
    order: 2,
  },
  {
    id: "component-first-sets",
    label: "Seturi component-first",
    description: "Inspectare readonly — fără activare sau Work Intake.",
    testId: "product-system-catalog-bucket-component-first-sets",
    toggleTestId: "product-system-catalog-bucket-toggle-component-first-sets",
    defaultExpanded: false,
    order: 3,
  },
  {
    id: "legacy-shared-modules",
    label: "Module legacy partajate",
    description: "Legacy support only — used by parent product, not new component-first.",
    testId: "product-system-catalog-bucket-legacy-shared-modules",
    toggleTestId: "product-system-catalog-bucket-toggle-legacy-shared-modules",
    defaultExpanded: false,
    order: 4,
  },
  {
    id: "archived",
    label: "Arhivate / experimentale",
    description: "Șabloane retrase din fluxul curent de ofertare.",
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
  | "lifecycle"
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
  header: string;
};

export const UNIFIED_CATALOG_BUCKET_THEMES: Record<UnifiedCatalogBucketId, UnifiedCatalogBucketTheme> = {
  "current-products": {
    dot: "bg-emerald-400",
    badge: "border-emerald-800/40 bg-emerald-950/25 text-emerald-200/90",
    header: "border-emerald-900/30 bg-emerald-950/10",
  },
  "candidate-products": {
    dot: "bg-amber-400",
    badge: "border-amber-800/40 bg-amber-950/25 text-amber-200/90",
    header: "border-amber-900/30 bg-amber-950/10",
  },
  "component-first-sets": {
    dot: "bg-cyan-400",
    badge: "border-cyan-800/40 bg-cyan-950/25 text-cyan-200/90",
    header: "border-cyan-900/30 bg-cyan-950/10",
  },
  "legacy-shared-modules": {
    dot: "bg-slate-500",
    badge: "border-slate-700/60 bg-slate-900/60 text-slate-400",
    header: "border-slate-800/80 bg-slate-950/20",
  },
  archived: {
    dot: "bg-zinc-500",
    badge: "border-slate-700/60 bg-slate-900/60 text-slate-400",
    header: "border-slate-800/80 bg-slate-950/20",
  },
};
