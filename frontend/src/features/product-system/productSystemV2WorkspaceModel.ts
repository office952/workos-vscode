/**
 * Product System V2 blank workspace — list model only.
 * Reuses readiness rollup helpers; no API / PD / Aggregate behavior change.
 */
import type {
  ProductTemplateAvailabilityItem,
  ProductTemplateCompositionModule,
  ProductTemplateEntity,
  SharedVolumetricComponentSummary,
} from "@/lib/api";
import { normalizeTemplateCode } from "@/lib/activeTemplateScope";
import {
  buildCanonicalCatalogProducts,
  CANONICAL_READINESS_ROLLUP_LABELS,
  isOperatorVisibleCatalogProduct,
  sortCanonicalCatalogProducts,
  type CanonicalCatalogProduct,
  type CanonicalCatalogRollup,
} from "./productSystemCanonicalCatalogModel";
import { humanTemplateName } from "./productSystemAdminDisplay";

/** One visible Module produs row (composition only — never shared-contract duplicates). */
export type ProductSystemV2ModuleRow = {
  key: string;
  roleLabel: string;
  moduleName: string;
  moduleCode: string;
  statusLabel: string;
  uiHint: string | null;
};

/**
 * Operator-facing partition of availability read-model.
 * - core: required composition (product nucleus)
 * - optional: non-required composition (supports / conditioned mounts)
 * - contracts: shared volumetric audit layer — diagnostic only, not Module produs
 */
export type ProductSystemV2ModuleLayers = {
  core: ProductSystemV2ModuleRow[];
  optional: ProductSystemV2ModuleRow[];
  contracts: SharedVolumetricComponentSummary[];
};

/** Short chip for the structure strip — owner-scannable, like old Structură produs. */
export function formatModuleStructureChip(roleLabel: string): string {
  const short = roleLabel.split("—")[0].split(" - ")[0].split("/")[0].trim();
  return short.length > 0 ? short.toUpperCase() : roleLabel.toUpperCase();
}

function compositionRow(module: ProductTemplateCompositionModule): ProductSystemV2ModuleRow {
  return {
    key: `mod-${module.role_key}-${module.module_template_code}`,
    roleLabel: module.role_label,
    moduleName: humanTemplateName(module.module_template_code),
    moduleCode: module.module_template_code,
    statusLabel: module.status_label?.trim() || (module.is_required ? "obligatoriu" : "opțional"),
    uiHint: module.ui_hint?.trim() || null,
  };
}

export function partitionProductModulesForDisplay(
  availability: ProductTemplateAvailabilityItem,
): ProductSystemV2ModuleLayers {
  const composition = [...(availability.composition_modules ?? [])].sort(
    (a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0),
  );
  const core: ProductSystemV2ModuleRow[] = [];
  const optional: ProductSystemV2ModuleRow[] = [];
  for (const module of composition) {
    const row = compositionRow(module);
    if (module.is_required) core.push(row);
    else optional.push(row);
  }
  return {
    core,
    optional,
    contracts: [...(availability.shared_component_contracts ?? [])],
  };
}

export const PS_LEGACY_QUERY_KEY = "ps_legacy";
export const PS_LEGACY_QUERY_VALUE = "1";

export type ProductSystemV2ListItem = {
  templateCode: string;
  displayName: string;
  rollup: CanonicalCatalogRollup;
  rollupLabel: string;
  blockerCount: number;
  product: CanonicalCatalogProduct;
};

export function buildProductSystemV2List({
  templates,
  availabilityItems,
  search,
}: {
  templates: ProductTemplateEntity[];
  availabilityItems: ProductTemplateAvailabilityItem[];
  search: string;
}): ProductSystemV2ListItem[] {
  const products = buildCanonicalCatalogProducts({ templates, availabilityItems });
  const operator = sortCanonicalCatalogProducts(
    products.filter((product) => isOperatorVisibleCatalogProduct(product.availability)),
  );
  const q = search.trim().toLowerCase();
  const filtered = q
    ? operator.filter((product) => {
        const hay = [
          product.templateCode,
          product.displayName,
          product.familyName,
          humanTemplateName(product.templateCode),
        ]
          .join(" ")
          .toLowerCase();
        return hay.includes(q);
      })
    : operator;

  return filtered.map((product) => ({
    templateCode: product.templateCode,
    displayName: product.displayName || humanTemplateName(product.templateCode),
    rollup: product.rollup,
    rollupLabel: CANONICAL_READINESS_ROLLUP_LABELS[product.rollup],
    blockerCount: product.blockerCount,
    product,
  }));
}

export function findV2ListItem(
  items: ProductSystemV2ListItem[],
  templateCode: string | null | undefined,
): ProductSystemV2ListItem | null {
  if (!templateCode) return null;
  const normalized = normalizeTemplateCode(templateCode);
  return items.find((item) => normalizeTemplateCode(item.templateCode) === normalized) ?? null;
}

export function legacyCatalogHref(templateCode?: string | null): string {
  const params = new URLSearchParams();
  params.set(PS_LEGACY_QUERY_KEY, PS_LEGACY_QUERY_VALUE);
  if (templateCode) params.set("template", templateCode);
  return `/product-system/products?${params.toString()}`;
}

export function isPsLegacyCatalogEnabled(searchParams: URLSearchParams): boolean {
  return searchParams.get(PS_LEGACY_QUERY_KEY) === PS_LEGACY_QUERY_VALUE;
}
