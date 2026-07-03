import { describe, it, expect, beforeEach, vi } from "vitest";
import type { ProductTemplateEntity } from "@/lib/api";
import {
  getLastOpenedTemplateId,
  getMostUsedTemplateIds,
  getRecentTemplateIds,
  recordTemplateOpened,
  resolveDefaultTemplate,
} from "@/features/product-system/templateSelectionStorage";

function makeTemplate(
  partial: Partial<ProductTemplateEntity> & Pick<ProductTemplateEntity, "id" | "template_code">
): ProductTemplateEntity {
  return {
    family_name: "Test",
    active: partial.active ?? true,
    ...partial,
  };
}

describe("templateSelectionStorage", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.stubGlobal("localStorage", {
      store: {} as Record<string, string>,
      getItem(key: string) {
        return this.store[key] ?? null;
      },
      setItem(key: string, value: string) {
        this.store[key] = value;
      },
      removeItem(key: string) {
        delete this.store[key];
      },
      clear() {
        this.store = {};
      },
    });
  });

  it("records last opened and recent templates", () => {
    recordTemplateOpened(42);
    recordTemplateOpened(7);
    expect(getLastOpenedTemplateId()).toBe(7);
    expect(getRecentTemplateIds()).toEqual([7, 42]);
  });

  it("tracks local open counts for most-used ordering", () => {
    recordTemplateOpened(1);
    recordTemplateOpened(2);
    recordTemplateOpened(1);
    expect(getMostUsedTemplateIds()).toEqual([1, 2]);
  });

  it("resolves default by last opened first", () => {
    const templates = [
      makeTemplate({ id: 1, template_code: "TPL-A", created_at: "2024-01-01" }),
      makeTemplate({ id: 2, template_code: "TPL-VOLUMETRIC-LETTERS", created_at: "2025-01-01" }),
    ];
    recordTemplateOpened(1);
    expect(resolveDefaultTemplate(templates)?.id).toBe(1);
  });

  it("prefers latest created then volumetric when no open history", () => {
    const templates = [
      makeTemplate({ id: 1, template_code: "TPL-OLD", active: false, created_at: "2023-01-01" }),
      makeTemplate({ id: 2, template_code: "TPL-VOLUMETRIC-LETTERS", created_at: "2024-01-01" }),
    ];
    expect(resolveDefaultTemplate(templates)?.template_code).toBe("TPL-VOLUMETRIC-LETTERS");
  });
});
