import type {
  ProductSystemTemplateCapabilities,
  ProductSystemTemplateReadiness,
  ProductTemplateAvailabilityItem,
  ProductTemplateEntity,
} from "@/lib/api";
import { normalizeTemplateCode, isOwnerValidActiveTemplate } from "@/lib/activeTemplateScope";
import { LOGO_TEMPLATE_CODE } from "@/lib/productTemplateScopePresentation";
import { commercialChipForTemplateCode } from "@/lib/productSystemModularityTruth";
import { getProductTemplateScopePresentation } from "@/lib/productTemplateScopePresentation";

export type CanonicalCatalogRollup =
  | "READY"
  | "PARTIALLY_READY"
  | "BLOCKED"
  | "INTERNAL"
  | "DEPRECATED";

export type CanonicalCapabilityLabel = "Standalone" | "Linked child" | "Both";

export type CanonicalCatalogFilter =
  | "all"
  | "ready"
  | "blocked"
  | "standalone"
  | "linked-child"
  | "internal"
  | "deprecated"
  | "experimental";

export const CANONICAL_CATALOG_OPERATOR_FILTERS: Array<{
  id: CanonicalCatalogFilter;
  label: string;
  testId: string;
}> = [
  { id: "all", label: "Toate operaționale", testId: "product-system-canonical-filter-all" },
  { id: "ready", label: "Pregătit pentru ofertă", testId: "product-system-canonical-filter-ready" },
  { id: "blocked", label: "Blocat (pregătire)", testId: "product-system-canonical-filter-blocked" },
  { id: "standalone", label: "De sine stătător", testId: "product-system-canonical-filter-standalone" },
  { id: "linked-child", label: "Copil legat", testId: "product-system-canonical-filter-linked-child" },
];

export const CANONICAL_CATALOG_ADVANCED_FILTERS: Array<{
  id: CanonicalCatalogFilter;
  label: string;
  testId: string;
}> = [
  { id: "internal", label: "Intern", testId: "product-system-canonical-filter-internal" },
  { id: "deprecated", label: "Depreciat", testId: "product-system-canonical-filter-deprecated" },
  { id: "experimental", label: "Experimental", testId: "product-system-canonical-filter-experimental" },
];

export type CanonicalCatalogProduct = {
  id: string;
  templateCode: string;
  displayName: string;
  familyName: string;
  availability: ProductTemplateAvailabilityItem;
  template?: ProductTemplateEntity;
  capabilityLabel: CanonicalCapabilityLabel;
  /** Operator-facing commercial/root chip — preferred over bare ACTIVE/PARTIAL. */
  commercialChipRo: string;
  rollup: CanonicalCatalogRollup;
  blockerCount: number;
  operatorVisible: boolean;
  advancedOnly: boolean;
};

const ROLLUP_SORT_WEIGHT: Record<CanonicalCatalogRollup, number> = {
  READY: 0,
  PARTIALLY_READY: 1,
  BLOCKED: 2,
  INTERNAL: 3,
  DEPRECATED: 4,
};

export const CANONICAL_READINESS_ROLLUP_LABELS: Record<CanonicalCatalogRollup, string> = {
  READY: "Pregătit pentru ofertă",
  BLOCKED: "Blocat (pregătire)",
  PARTIALLY_READY: "Parțial (compunere)",
  INTERNAL: "Intern",
  DEPRECATED: "Depreciat",
};

function normalizeRollup(
  readiness: ProductSystemTemplateReadiness | null | undefined,
): CanonicalCatalogRollup {
  const rollup = readiness?.rollup?.toUpperCase();
  if (rollup === "READY") return "READY";
  if (rollup === "PARTIALLY_READY") return "PARTIALLY_READY";
  if (rollup === "BLOCKED") return "BLOCKED";
  if (rollup === "INTERNAL") return "INTERNAL";
  if (rollup === "DEPRECATED") return "DEPRECATED";
  return "BLOCKED";
}

export function resolveCatalogRollup(
  availability: ProductTemplateAvailabilityItem,
): CanonicalCatalogRollup {
  if (availability.readiness) {
    return normalizeRollup(availability.readiness);
  }
  if (
    availability.display_group === "archived_experimental" ||
    availability.product_system_role === "archived_experimental"
  ) {
    return "DEPRECATED";
  }
  if (
    availability.product_system_role === "internal_module" ||
    availability.product_system_role === "shared_component"
  ) {
    return "INTERNAL";
  }
  if (availability.owner_decision_required || !availability.quote_offerable) {
    return "BLOCKED";
  }
  return availability.quote_offerable ? "READY" : "BLOCKED";
}

export function countReadinessBlockers(
  readiness: ProductSystemTemplateReadiness | null | undefined,
): number {
  if (!readiness) return 0;
  const dimensions = [
    readiness.technical,
    readiness.pricing,
    readiness.execution,
    readiness.commercial,
  ];
  return dimensions.reduce((sum, dimension) => sum + (dimension.blockers?.length ?? 0), 0);
}

export function capabilityLabelFromCapabilities(
  capabilities: ProductSystemTemplateCapabilities | null | undefined,
  availability?: ProductTemplateAvailabilityItem,
): CanonicalCapabilityLabel {
  const root = capabilities?.root_offerable === true;
  const linked = capabilities?.linked_child_offerable === true;
  if (root && linked) return "Both";
  if (linked) return "Linked child";
  if (root) return "Standalone";
  if (
    availability?.quote_offerable &&
    availability.product_system_role === "offerable_product" &&
    availability.runtime_module
  ) {
    return "Both";
  }
  return "Standalone";
}

function isExperimentalAvailability(item: ProductTemplateAvailabilityItem): boolean {
  return (
    item.template_code === LOGO_TEMPLATE_CODE ||
    item.display_group === "candidate_products" ||
    item.product_system_role === "candidate_product"
  );
}

function isDeprecatedAvailability(item: ProductTemplateAvailabilityItem): boolean {
  const rollup = resolveCatalogRollup(item);
  return (
    rollup === "DEPRECATED" ||
    item.display_group === "archived_experimental" ||
    item.product_system_role === "archived_experimental"
  );
}

function isInternalAvailability(item: ProductTemplateAvailabilityItem): boolean {
  const rollup = resolveCatalogRollup(item);
  return (
    rollup === "INTERNAL" ||
    item.capabilities?.internal_only === true ||
    item.product_system_role === "internal_module" ||
    item.product_system_role === "shared_component" ||
    item.display_group === "internal_modules" ||
    item.display_group === "shared_components"
  );
}

function isCanonicalProductSystemTemplate(item: ProductTemplateAvailabilityItem): boolean {
  if (isOwnerValidActiveTemplate(item.template_code)) return true;
  if (isInternalAvailability(item) && (item.is_parent || item.runtime_module)) return true;
  if (isDeprecatedAvailability(item) && item.is_parent) return true;
  if (isExperimentalAvailability(item) && item.is_parent) return true;
  return false;
}

/** Parent/standalone templates eligible for the canonical product catalog (not candidate-module sets). */
export function isCatalogEligibleAvailability(
  item: ProductTemplateAvailabilityItem,
): boolean {
  if (!isCanonicalProductSystemTemplate(item)) return false;

  if (
    item.quote_offerable &&
    item.product_system_role === "offerable_product" &&
    item.display_group === "active_products"
  ) {
    return true;
  }

  if (item.runtime_module) {
    return item.capabilities?.internal_only === true || isInternalAvailability(item);
  }

  return item.is_parent || isExperimentalAvailability(item) || isDeprecatedAvailability(item);
}

export function isOperatorVisibleCatalogProduct(
  availability: ProductTemplateAvailabilityItem,
): boolean {
  if (!isCatalogEligibleAvailability(availability)) return false;
  if (!itemActiveForOperatorCatalog(availability)) return false;

  const rollup = resolveCatalogRollup(availability);
  if (rollup === "INTERNAL" || rollup === "DEPRECATED") return false;
  if (isExperimentalAvailability(availability)) return false;
  if (isDeprecatedAvailability(availability)) return false;

  const caps = availability.capabilities;
  if (caps) {
    if (caps.internal_only) return false;
    if (caps.root_offerable) return true;
    if (caps.linked_child_offerable && !caps.root_offerable) return false;
  }

  return isOwnerValidActiveTemplate(availability.template_code);
}

function itemActiveForOperatorCatalog(item: ProductTemplateAvailabilityItem): boolean {
  if (!item.db_active) return false;
  if (item.runtime_module && !item.is_parent) {
    return item.quote_offerable && item.product_system_role === "offerable_product";
  }
  return true;
}

export function isAdvancedOnlyCatalogProduct(
  availability: ProductTemplateAvailabilityItem,
): boolean {
  if (!isCatalogEligibleAvailability(availability)) return false;
  return !isOperatorVisibleCatalogProduct(availability);
}

function templateByCode(
  templates: ProductTemplateEntity[],
  templateCode: string,
): ProductTemplateEntity | undefined {
  const normalized = normalizeTemplateCode(templateCode);
  return templates.find((template) => normalizeTemplateCode(template.template_code) === normalized);
}

export function templateEntityForAvailability(
  availability: ProductTemplateAvailabilityItem,
  templates: ProductTemplateEntity[],
): ProductTemplateEntity {
  return (
    templateByCode(templates, availability.template_code) ?? {
      id: availability.template_id,
      template_code: availability.template_code,
      family_id: availability.family_id ?? undefined,
      family_name: availability.family_name ?? availability.template_code,
      description: availability.description ?? undefined,
      active: availability.db_active,
      components_json: "[]",
      operations_json: "[]",
      required_materials_json: "[]",
    }
  );
}

export function buildCanonicalCatalogProducts({
  templates,
  availabilityItems,
}: {
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
}): CanonicalCatalogProduct[] {
  return availabilityItems
    .filter(isCatalogEligibleAvailability)
    .map((availability) => {
      const template = templateEntityForAvailability(availability, templates);
      const operatorVisible = isOperatorVisibleCatalogProduct(availability);
      const capabilityLabel = capabilityLabelFromCapabilities(
        availability.capabilities,
        availability,
      );
      const scope = getProductTemplateScopePresentation(availability);
      return {
        id: `template:${availability.template_id}`,
        templateCode: availability.template_code,
        // Prefer family/name over API ui_label when honesty chip carries commercial status.
        displayName:
          template.family_name ||
          availability.family_name ||
          availability.ui_label ||
          availability.template_code,
        familyName: availability.family_name || template.family_name || "—",
        availability,
        template,
        capabilityLabel,
        commercialChipRo:
          commercialChipForTemplateCode(availability.template_code) ?? scope.catalogStatusLabel,
        rollup: resolveCatalogRollup(availability),
        blockerCount: countReadinessBlockers(availability.readiness),
        operatorVisible,
        advancedOnly: !operatorVisible,
      };
    });
}

export function matchesCatalogSearch(product: CanonicalCatalogProduct, query: string): boolean {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return true;
  const haystack = [
    product.displayName,
    product.templateCode,
    product.familyName,
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(normalized);
}

function matchesOperatorFilter(
  product: CanonicalCatalogProduct,
  filter: CanonicalCatalogFilter,
): boolean {
  switch (filter) {
    case "ready":
      return product.rollup === "READY";
    case "blocked":
      return product.rollup === "BLOCKED" || product.rollup === "PARTIALLY_READY";
    case "standalone":
      return product.capabilityLabel === "Standalone" || product.capabilityLabel === "Both";
    case "linked-child":
      return product.capabilityLabel === "Linked child" || product.capabilityLabel === "Both";
    default:
      return true;
  }
}

function matchesAdvancedFilter(
  product: CanonicalCatalogProduct,
  filter: CanonicalCatalogFilter,
): boolean {
  switch (filter) {
    case "internal":
      return isInternalAvailability(product.availability);
    case "deprecated":
      return isDeprecatedAvailability(product.availability);
    case "experimental":
      return isExperimentalAvailability(product.availability);
    default:
      return true;
  }
}

const ADVANCED_FILTER_IDS = new Set<CanonicalCatalogFilter>(["internal", "deprecated", "experimental"]);

export function filterCanonicalCatalogProducts(
  products: CanonicalCatalogProduct[],
  {
    filter,
    search,
    canViewAdvanced,
  }: {
    filter: CanonicalCatalogFilter;
    search: string;
    canViewAdvanced: boolean;
  },
): CanonicalCatalogProduct[] {
  const isAdvancedFilter = ADVANCED_FILTER_IDS.has(filter);

  return products.filter((product) => {
    if (!matchesCatalogSearch(product, search)) return false;

    if (isAdvancedFilter) {
      if (!canViewAdvanced) return false;
      if (!product.advancedOnly) return false;
      return matchesAdvancedFilter(product, filter);
    }

    if (!product.operatorVisible) return false;
    return matchesOperatorFilter(product, filter);
  });
}

export function compareCanonicalCatalogProducts(
  a: CanonicalCatalogProduct,
  b: CanonicalCatalogProduct,
): number {
  const rootWeight = (product: CanonicalCatalogProduct) => {
    const caps = product.availability.capabilities;
    if (caps?.root_offerable) return 0;
    if (caps?.linked_child_offerable) return 1;
    return 2;
  };

  const rootDelta = rootWeight(a) - rootWeight(b);
  if (rootDelta !== 0) return rootDelta;

  const rollupDelta = ROLLUP_SORT_WEIGHT[a.rollup] - ROLLUP_SORT_WEIGHT[b.rollup];
  if (rollupDelta !== 0) return rollupDelta;

  const nameDelta = a.displayName.localeCompare(b.displayName, "ro", { sensitivity: "base" });
  if (nameDelta !== 0) return nameDelta;

  return normalizeTemplateCode(a.templateCode).localeCompare(
    normalizeTemplateCode(b.templateCode),
    "en",
    { sensitivity: "base" },
  );
}

export function sortCanonicalCatalogProducts(
  products: CanonicalCatalogProduct[],
): CanonicalCatalogProduct[] {
  return [...products].sort(compareCanonicalCatalogProducts);
}

export function splitCanonicalCatalogProducts(
  products: CanonicalCatalogProduct[],
  search = "",
): {
  operator: CanonicalCatalogProduct[];
  advanced: CanonicalCatalogProduct[];
} {
  const searched = products.filter((product) => matchesCatalogSearch(product, search));
  return {
    operator: sortCanonicalCatalogProducts(searched.filter((product) => product.operatorVisible)),
    advanced: sortCanonicalCatalogProducts(searched.filter((product) => product.advancedOnly)),
  };
}
