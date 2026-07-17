import { describe, expect, it } from "vitest";
import type { ProductTemplateAvailabilityItem } from "@/lib/api";
import { TPL_ACM_BOXED_MOUNTING_SUPPORT } from "@/lib/acmQuoteInput";
import {
  LETTERS_TEMPLATE_CODE,
  LOGO_TEMPLATE_CODE,
} from "@/lib/productTemplateScopePresentation";
import {
  buildCanonicalCatalogProducts,
  compareCanonicalCatalogProducts,
  filterCanonicalCatalogProducts,
  isOperatorVisibleCatalogProduct,
  matchesCatalogSearch,
  resolveCatalogRollup,
  sortCanonicalCatalogProducts,
} from "./productSystemCanonicalCatalogModel";

function availability(
  overrides: Partial<ProductTemplateAvailabilityItem> &
    Pick<ProductTemplateAvailabilityItem, "template_code" | "template_id">,
): ProductTemplateAvailabilityItem {
  return {
    family_id: null,
    family_name: "Familie test",
    description: null,
    db_active: true,
    quote_offerable: false,
    runtime_module: false,
    is_parent: true,
    has_modules: false,
    parent_codes: [],
    module_codes: [],
    status: "offerable",
    status_reason: "test",
    product_system_role: "offerable_product",
    display_group: "active_products",
    importance_rank: 10,
    owner_decision_required: false,
    readiness_reason: "",
    ui_label: overrides.template_code,
    ui_description: "",
    parent_product_codes: [],
    child_module_codes: [],
    shared_with_product_codes: [],
    composition_modules: [],
    shared_component_contracts: [],
    ...overrides,
  };
}

const letters = availability({
  template_id: 1,
  template_code: LETTERS_TEMPLATE_CODE,
  quote_offerable: true,
  ui_label: "Litere volumetrice",
  family_name: "Volumetric",
  capabilities: {
    root_offerable: true,
    linked_child_offerable: false,
    internal_only: false,
  },
  readiness: {
    technical: { status: "TECHNICALLY_READY", blockers: [] },
    pricing: { status: "PRICING_INCOMPLETE", blockers: [{ code: "X", dimension: "pricing", severity: "blocking", owner: "pricing", message: "m" }] },
    execution: { status: "EXECUTION_INCOMPLETE", blockers: [] },
    commercial: { status: "OFFERABLE", blockers: [] },
    rollup: "BLOCKED",
  },
});

const acm = availability({
  template_id: 2,
  template_code: TPL_ACM_BOXED_MOUNTING_SUPPORT,
  quote_offerable: true,
  ui_label: "Suport ACM casetat",
  family_name: "ACM",
  capabilities: {
    root_offerable: true,
    linked_child_offerable: true,
    internal_only: false,
  },
  readiness: {
    technical: { status: "TECHNICALLY_READY", blockers: [] },
    pricing: { status: "PRICING_READY", blockers: [] },
    execution: { status: "EXECUTION_READY", blockers: [] },
    commercial: { status: "OFFERABLE", blockers: [] },
    rollup: "READY",
  },
});

const logo = availability({
  template_id: 3,
  template_code: LOGO_TEMPLATE_CODE,
  quote_offerable: false,
  product_system_role: "candidate_product",
  display_group: "candidate_products",
  readiness: {
    technical: { status: "DRAFT", blockers: [] },
    pricing: { status: "PRICING_INCOMPLETE", blockers: [] },
    execution: { status: "EXECUTION_INCOMPLETE", blockers: [] },
    commercial: { status: "DEPRECATED", blockers: [] },
    rollup: "DEPRECATED",
  },
});

const premount = availability({
  template_id: 4,
  template_code: "TPL-METAL-PREMOUNT-LETTERS_v1",
  runtime_module: true,
  is_parent: false,
  quote_offerable: false,
  product_system_role: "internal_module",
  display_group: "internal_modules",
  capabilities: {
    root_offerable: false,
    linked_child_offerable: true,
    internal_only: true,
  },
  readiness: {
    technical: { status: "TECHNICALLY_READY", blockers: [] },
    pricing: { status: "PRICING_READY", blockers: [] },
    execution: { status: "EXECUTION_READY", blockers: [] },
    commercial: { status: "INTERNAL_ONLY", blockers: [] },
    rollup: "INTERNAL",
  },
});

const componentFirstComposer = availability({
  template_id: 99,
  template_code: "TPL-PRODUCT-COMPOSER-LETTERS_v1",
  quote_offerable: false,
  is_parent: false,
  runtime_module: true,
  product_system_role: "internal_module",
  display_group: "internal_modules",
});

const acmRuntimeFlag = availability({
  template_id: 5,
  template_code: TPL_ACM_BOXED_MOUNTING_SUPPORT,
  quote_offerable: true,
  runtime_module: true,
  is_parent: false,
  ui_label: "Suport ACM casetat",
  family_name: "ACM",
  product_system_role: "offerable_product",
  display_group: "active_products",
});

describe("productSystemCanonicalCatalogModel", () => {
  it("keeps ACM visible when availability marks runtime_module for linked-child reuse", () => {
    expect(isOperatorVisibleCatalogProduct(acmRuntimeFlag)).toBe(true);
    const products = buildCanonicalCatalogProducts({
      templates: [],
      availabilityItems: [letters, acmRuntimeFlag],
    });
    expect(products.map((product) => product.templateCode)).toEqual(
      expect.arrayContaining([LETTERS_TEMPLATE_CODE, TPL_ACM_BOXED_MOUNTING_SUPPORT]),
    );
  });

  it("builds one canonical list without legacy bucket membership", () => {
    const products = buildCanonicalCatalogProducts({
      templates: [],
      availabilityItems: [letters, acm, logo, premount, componentFirstComposer],
    });
    expect(products.some((product) => product.templateCode === LETTERS_TEMPLATE_CODE)).toBe(true);
    expect(products.some((product) => product.templateCode === TPL_ACM_BOXED_MOUNTING_SUPPORT)).toBe(true);
    expect(products.every((product) => !("bucket" in product))).toBe(true);
  });

  it("uses commercial honesty chips instead of bare ACTIVE/CONFIRMAT", () => {
    const products = buildCanonicalCatalogProducts({
      templates: [],
      availabilityItems: [letters, acm, logo],
    });
    const byCode = Object.fromEntries(products.map((p) => [p.templateCode, p]));
    expect(byCode[LETTERS_TEMPLATE_CODE]?.commercialChipRo).toBe("Rădăcină folosită azi");
    expect(byCode[LOGO_TEMPLATE_CODE]?.commercialChipRo).toMatch(/rădăcină blocată/i);
    expect(byCode[TPL_ACM_BOXED_MOUNTING_SUPPORT]?.commercialChipRo).toMatch(/Montaj ACM/i);
    expect(byCode[LETTERS_TEMPLATE_CODE]?.commercialChipRo).not.toMatch(/^(ACTIVE|CONFIRMAT|PARTIAL)$/);
  });

  it("hides logo and component-first internals from operator visibility", () => {
    expect(isOperatorVisibleCatalogProduct(letters)).toBe(true);
    expect(isOperatorVisibleCatalogProduct(acm)).toBe(true);
    expect(isOperatorVisibleCatalogProduct(logo)).toBe(false);
    expect(isOperatorVisibleCatalogProduct(premount)).toBe(false);
  });

  it("uses readiness rollup instead of legacy status fields", () => {
    const product = buildCanonicalCatalogProducts({
      templates: [],
      availabilityItems: [letters],
    })[0];
    expect(product.rollup).toBe("BLOCKED");
    expect(resolveCatalogRollup(letters)).toBe("BLOCKED");
    expect(product.blockerCount).toBeGreaterThan(0);
  });

  it("sorts root offerable before linked-only and then by name", () => {
    const sorted = sortCanonicalCatalogProducts(
      buildCanonicalCatalogProducts({
        templates: [],
        availabilityItems: [letters, acm],
      }),
    );
    expect(sorted[0].templateCode).toBe(TPL_ACM_BOXED_MOUNTING_SUPPORT);
    expect(compareCanonicalCatalogProducts(sorted[0], sorted[1])).toBeLessThan(0);
  });

  it("filters search by name, code, and family", () => {
    const products = buildCanonicalCatalogProducts({
      templates: [],
      availabilityItems: [letters, acm],
    });
    expect(
      filterCanonicalCatalogProducts(products, {
        filter: "all",
        search: "acm",
        canViewAdvanced: false,
      }).map((product) => product.templateCode),
    ).toEqual([TPL_ACM_BOXED_MOUNTING_SUPPORT]);
    expect(matchesCatalogSearch(products[0], "volumetric")).toBe(true);
    expect(matchesCatalogSearch(products[0], "TPL-VOLUMETRIC")).toBe(true);
  });

  it("applies ready, blocked, standalone, and linked-child filters", () => {
    const products = buildCanonicalCatalogProducts({
      templates: [],
      availabilityItems: [letters, acm],
    });
    expect(
      filterCanonicalCatalogProducts(products, {
        filter: "ready",
        search: "",
        canViewAdvanced: false,
      }),
    ).toHaveLength(1);
    expect(
      filterCanonicalCatalogProducts(products, {
        filter: "blocked",
        search: "",
        canViewAdvanced: false,
      }),
    ).toHaveLength(1);
    expect(
      filterCanonicalCatalogProducts(products, {
        filter: "standalone",
        search: "",
        canViewAdvanced: false,
      }),
    ).toHaveLength(2);
    expect(
      filterCanonicalCatalogProducts(products, {
        filter: "linked-child",
        search: "",
        canViewAdvanced: false,
      }),
    ).toHaveLength(1);
  });

  it("exposes advanced-only objects only with advanced filters", () => {
    const products = buildCanonicalCatalogProducts({
      templates: [],
      availabilityItems: [letters, logo, premount],
    });
    const operatorAll = filterCanonicalCatalogProducts(products, {
      filter: "all",
      search: "",
      canViewAdvanced: false,
    });
    expect(operatorAll.map((product) => product.templateCode)).toEqual([LETTERS_TEMPLATE_CODE]);

    const deprecated = filterCanonicalCatalogProducts(products, {
      filter: "deprecated",
      search: "",
      canViewAdvanced: true,
    });
    expect(deprecated.some((product) => product.templateCode === LOGO_TEMPLATE_CODE)).toBe(true);
  });
});
