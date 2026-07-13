import { describe, expect, it } from "vitest";

import { TPL_ACM_BOXED_MOUNTING_SUPPORT } from "@/lib/acmQuoteInput";
import {
  assertOwnerValidScopeParityWithBackend,
  BACKEND_ROOT_OFFERABLE_TEMPLATE_CODES_PARITY,
  filterActiveTemplatesForQuote,
  isOwnerValidActiveTemplate,
  normalizeTemplateCode,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
  OWNER_VALID_ACTIVE_TEMPLATE_CODES,
} from "@/lib/activeTemplateScope";
import {
  buildProductSystemTemplateQuery,
  parseRequestedTemplateCode,
  resolveTemplateQuerySelection,
  TEMPLATE_UNAVAILABLE_MESSAGE,
} from "@/features/product-system/productSystemTemplateQuerySync";
import type { UnifiedCatalogEntry } from "@/features/product-system/productSystemUnifiedCatalogTypes";

function templateEntry(
  templateCode: string,
  bucket: UnifiedCatalogEntry["bucket"] = "current-products",
): UnifiedCatalogEntry {
  return {
    id: `template:1:${templateCode}`,
    kind: "template",
    bucket,
    name: templateCode,
    templateCode,
    entityType: "Product",
    lifecycleLabel: "Test",
    metadata: "",
    importanceRank: 10,
    isProduct: true,
    isComponent: false,
    isCandidateReadonly: false,
    isActiveRoot: bucket === "current-products",
    isArchived: bucket === "archived",
    isBlocked: false,
    isReadonly: false,
  };
}

describe("activeTemplateScope", () => {
  it("identifies owner-valid root offerable templates including ACM boxed", () => {
    expect(isOwnerValidActiveTemplate(OWNER_VALID_ACTIVE_TEMPLATE_CODE)).toBe(true);
    expect(isOwnerValidActiveTemplate(TPL_ACM_BOXED_MOUNTING_SUPPORT)).toBe(true);
    expect(isOwnerValidActiveTemplate("TPL-VOLUMETRIC-LOGO_v1")).toBe(false);
    expect(isOwnerValidActiveTemplate("TPL-VOLUM-ALUMINIU_v1")).toBe(false);
    expect(isOwnerValidActiveTemplate("TPL-METAL-PREMOUNT-STRUCTURE_v1")).toBe(false);
  });

  it("matches backend ROOT_OFFERABLE parity contract", () => {
    assertOwnerValidScopeParityWithBackend();
    expect(OWNER_VALID_ACTIVE_TEMPLATE_CODES.map(String).sort()).toEqual(
      [...BACKEND_ROOT_OFFERABLE_TEMPLATE_CODES_PARITY].sort(),
    );
  });

  it("keeps owner-valid root templates active for quote scope", () => {
    const templates = [
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: true },
      { template_code: TPL_ACM_BOXED_MOUNTING_SUPPORT, active: true },
      { template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1", active: true },
      { template_code: "TPL-VOLUMETRIC-LOGO_v1", active: true },
      { template_code: "TPL-LEGACY-EXPERIMENT", active: true },
    ];

    expect(filterActiveTemplatesForQuote(templates)).toEqual([
      { template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE, active: true },
      { template_code: TPL_ACM_BOXED_MOUNTING_SUPPORT, active: true },
    ]);
  });

  it("marks non-root templates as archived/experimental in the frontend guard", () => {
    expect(
      isOwnerValidActiveTemplate("TPL-ACM-CASSETTED-PANEL"),
    ).toBe(false);
  });
});

describe("productSystemTemplateQuerySync", () => {
  const entries = [
    templateEntry(OWNER_VALID_ACTIVE_TEMPLATE_CODE),
    templateEntry(TPL_ACM_BOXED_MOUNTING_SUPPORT),
    templateEntry("TPL-METAL-PREMOUNT-STRUCTURE_v1", "legacy-shared-modules"),
  ];

  it("parses template query codes", () => {
    expect(parseRequestedTemplateCode(` ${TPL_ACM_BOXED_MOUNTING_SUPPORT} `)).toBe(
      normalizeTemplateCode(TPL_ACM_BOXED_MOUNTING_SUPPORT),
    );
    expect(parseRequestedTemplateCode("")).toBeNull();
  });

  it("selects ACM entry for ACM query", () => {
    const resolution = resolveTemplateQuerySelection(
      TPL_ACM_BOXED_MOUNTING_SUPPORT,
      entries,
      [
        {
          template_code: TPL_ACM_BOXED_MOUNTING_SUPPORT,
          db_active: true,
          quote_offerable: true,
          display_group: "active_products",
          status: "offerable",
        } as never,
      ],
    );
    expect(resolution).toMatchObject({
      kind: "matched",
      templateCode: TPL_ACM_BOXED_MOUNTING_SUPPORT,
    });
  });

  it("selects letters entry for letters query", () => {
    const resolution = resolveTemplateQuerySelection(
      OWNER_VALID_ACTIVE_TEMPLATE_CODE,
      entries,
      [
        {
          template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE,
          db_active: true,
          quote_offerable: true,
          display_group: "active_products",
          status: "offerable",
        } as never,
      ],
    );
    expect(resolution.kind).toBe("matched");
    if (resolution.kind === "matched") {
      expect(resolution.templateCode).toBe(OWNER_VALID_ACTIVE_TEMPLATE_CODE);
    }
  });

  it("treats archived logo as unavailable — does not match letters", () => {
    const resolution = resolveTemplateQuerySelection(
      "TPL-VOLUMETRIC-LOGO_v1",
      entries,
      [
        {
          template_code: "TPL-VOLUMETRIC-LOGO_v1",
          db_active: false,
          quote_offerable: false,
          display_group: "archived_experimental",
          status: "archived",
        } as never,
      ],
    );
    expect(resolution).toEqual({
      kind: "unavailable",
      templateCode: "TPL-VOLUMETRIC-LOGO_v1",
      reason: "inactive",
    });
  });

  it("treats unknown template as unavailable", () => {
    const resolution = resolveTemplateQuerySelection("TPL-DOES-NOT-EXIST", entries, []);
    expect(resolution).toEqual({
      kind: "unavailable",
      templateCode: "TPL-DOES-NOT-EXIST",
      reason: "unknown",
    });
  });

  it("returns none when query absent", () => {
    expect(resolveTemplateQuerySelection(null, entries, [])).toEqual({ kind: "none" });
  });

  it("builds encoded query string", () => {
    expect(buildProductSystemTemplateQuery(TPL_ACM_BOXED_MOUNTING_SUPPORT)).toBe(
      "template=TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
    );
  });

  it("uses established unavailable message copy", () => {
    expect(TEMPLATE_UNAVAILABLE_MESSAGE).toBe("Template indisponibil sau inexistent");
  });
});
