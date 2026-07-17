import { describe, expect, it } from "vitest";
import {
  CANONICAL_CONCEPTS,
  CANONICAL_ROUTES,
  CAPABILITY_TYPES,
  COMPONENT_REPRESENTATION_INVENTORY,
  LEGACY_DOSSIER_ROUTE,
  MINI_MODULE_SCOPE_ROWS,
  STABILIZATION_PRODUCTS,
  assertUniqueConceptIds,
  stabilizationClaimsBannerOrVehicle,
} from "@/lib/productSystemCanonicalModel";

describe("productSystemCanonicalModel", () => {
  it("keeps unique concept definitions and separates component / module / capability", () => {
    expect(() => assertUniqueConceptIds()).not.toThrow();
    const byId = Object.fromEntries(CANONICAL_CONCEPTS.map((c) => [c.id, c]));
    expect(byId.product_family.technicalName).toBe("Product Family");
    expect(byId.product_template.technicalName).toBe("Product Template");
    expect(byId.component_template.status).toBe("CONCEPT_CANONICAL — STORAGE_MIXED");
    expect(byId.mini_module.notRo).toMatch(/Capability/i);
    expect(byId.capability.definitionRo).toMatch(/interacțiune UI/i);
    expect(byId.capability.notRo).toMatch(/Nu activează module/);
    expect(byId.capability.notRo).toMatch(/React/);
  });

  it("limits stabilization scope to Letters, Logo and ACM only", () => {
    expect(STABILIZATION_PRODUCTS.map((p) => p.id)).toEqual(["letters", "logo", "acm"]);
    const blob = JSON.stringify(STABILIZATION_PRODUCTS);
    expect(stabilizationClaimsBannerOrVehicle(blob)).toBe(false);
    expect(blob).not.toMatch(/TPL-BANNER/i);
    expect(STABILIZATION_PRODUCTS.find((p) => p.id === "logo")?.usageStatus).toBe("PARTIAL");
    expect(STABILIZATION_PRODUCTS.find((p) => p.id === "acm")?.usageStatus).toBe("PARTIAL");
  });

  it("exposes exact Inventory, Pricing and single Dossier routes", () => {
    expect(CANONICAL_ROUTES.inventory).toBe("/inventory");
    expect(CANONICAL_ROUTES.pricing).toBe("/inventory/pricing");
    expect(CANONICAL_ROUTES.dossier).toBe("/product-system/blueprint-dossier");
    expect(LEGACY_DOSSIER_ROUTE).toBe("/product-system/dossier-completion");
    expect(CANONICAL_ROUTES.dossier).not.toBe(LEGACY_DOSSIER_ROUTE);
  });

  it("scopes mini-modules without false-generic claims", () => {
    const led = MINI_MODULE_SCOPE_ROWS.find((m) => m.moduleCode === "sistem_led");
    expect(led?.scope).toBe("LETTERS_ONLY");
    const support = MINI_MODULE_SCOPE_ROWS.find((m) => m.moduleCode === "structura_suport");
    expect(support?.scope).toBe("SHARED_WITHIN_SIGNAGE");
    expect(MINI_MODULE_SCOPE_ROWS.every((m) => m.scope !== "UNKNOWN" || m.moduleCode)).toBe(true);
  });

  it("keeps capabilities as UI interaction types that do not activate modules", () => {
    expect(CAPABILITY_TYPES.length).toBeGreaterThan(0);
    expect(CAPABILITY_TYPES.every((c) => c.activatesModule === false)).toBe(true);
  });

  it("inventories component representations including ghosts and child templates", () => {
    const statuses = new Set(COMPONENT_REPRESENTATION_INVENTORY.map((r) => r.status));
    expect(statuses.has("CANONICAL_PHYSICAL_COMPONENT")).toBe(true);
    expect(statuses.has("TEMPORARY_CHILD_TEMPLATE")).toBe(true);
    expect(statuses.has("GHOST")).toBe(true);
  });
});
