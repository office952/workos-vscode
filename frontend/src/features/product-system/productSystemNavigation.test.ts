import { describe, it, expect } from "vitest";
import type { ProductTemplateEntity } from "@/lib/api";
import { OWNER_VALID_ACTIVE_TEMPLATE_CODE } from "@/lib/activeTemplateScope";
import {
  filterLibraryTemplates,
  getInitialProductSystemScreen,
  isTemplateEditableForQuote,
  shouldShowEditorScreen,
  shouldShowLibraryScreen,
} from "@/features/product-system/productSystemNavigation";

function makeTemplate(
  partial: Partial<ProductTemplateEntity> & Pick<ProductTemplateEntity, "id" | "template_code">
): ProductTemplateEntity {
  return {
    family_name: "Test",
    active: partial.active ?? true,
    ...partial,
  };
}

describe("productSystemNavigation", () => {
  it("starts on library screen, not editor", () => {
    expect(getInitialProductSystemScreen()).toBe("library");
    expect(shouldShowLibraryScreen("library")).toBe(true);
    expect(shouldShowEditorScreen("library", null)).toBe(false);
  });

  it("shows editor only after template selection", () => {
    expect(shouldShowEditorScreen("editor", { template_code: "TPL-X" })).toBe(true);
    expect(shouldShowEditorScreen("editor", null)).toBe(false);
  });

  it("filters active templates for quote scope", () => {
    const templates = [
      makeTemplate({ id: 1, template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE }),
      makeTemplate({ id: 2, template_code: "TPL-ARCHIVED", active: false }),
    ];
    const active = filterLibraryTemplates(templates, "active", "");
    expect(active).toHaveLength(1);
    expect(active[0].template_code).toBe(OWNER_VALID_ACTIVE_TEMPLATE_CODE);
    expect(isTemplateEditableForQuote(active[0])).toBe(true);
    expect(isTemplateEditableForQuote(templates[1])).toBe(false);
  });

  it("filters archived templates separately from active", () => {
    const templates = [
      makeTemplate({ id: 1, template_code: OWNER_VALID_ACTIVE_TEMPLATE_CODE }),
      makeTemplate({ id: 2, template_code: "TPL-OLD", active: false }),
    ];
    const archived = filterLibraryTemplates(templates, "archived", "");
    expect(archived).toHaveLength(1);
    expect(archived[0].template_code).toBe("TPL-OLD");
  });

  it("searches by template_code and family_name", () => {
    const templates = [
      makeTemplate({ id: 1, template_code: "TPL-A", family_name: "Alpha" }),
      makeTemplate({ id: 2, template_code: "TPL-B", family_name: "Beta" }),
    ];
    expect(filterLibraryTemplates(templates, "all", "alpha")).toHaveLength(1);
    expect(filterLibraryTemplates(templates, "all", "tpl-b")).toHaveLength(1);
  });
});
