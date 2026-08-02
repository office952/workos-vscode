import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  PRODUCT_SYSTEM_SPINE_STEPS,
  PRODUCT_SYSTEM_WORKSPACE_SUBTITLE,
} from "./productTemplateModulesVocabulary";

describe("productSystemBlankWorkspaceIa", () => {
  it("keeps Product System spine free of Oferta as a primary step", () => {
    expect(PRODUCT_SYSTEM_SPINE_STEPS).toHaveLength(4);
    expect(PRODUCT_SYSTEM_SPINE_STEPS.some((s) => s.id === "offer")).toBe(false);
    expect(PRODUCT_SYSTEM_SPINE_STEPS.some((s) => s.id === "modules")).toBe(false);
    expect(PRODUCT_SYSTEM_SPINE_STEPS.some((s) => s.id === "structure")).toBe(true);
    expect(PRODUCT_SYSTEM_WORKSPACE_SUBTITLE).toMatch(/Product Template/);
    expect(PRODUCT_SYSTEM_WORKSPACE_SUBTITLE).toMatch(/StructurÄƒ produs/);
    expect(PRODUCT_SYSTEM_WORKSPACE_SUBTITLE).not.toMatch(/Module produs/);
    expect(PRODUCT_SYSTEM_WORKSPACE_SUBTITLE).not.toMatch(/vechi/i);
    expect(PRODUCT_SYSTEM_WORKSPACE_SUBTITLE).not.toMatch(/legacy/i);
  });

  it("reduces detail primary IA to Template / StructurÄƒ / Compiler / Readiness", () => {
    const detail = readFileSync(
      resolve(__dirname, "ProductSystemTemplateDetailPanel.tsx"),
      "utf8",
    );
    expect(detail).toMatch(/label: "Product Template"/);
    expect(detail).toMatch(/label: "StructurÄƒ produs"/);
    expect(detail).not.toMatch(/label: "Module produs"/);
    expect(detail).toMatch(/label: "Product Compiler"/);
    expect(detail).toMatch(/label: "PregÄƒtire"/);
    expect(detail).toMatch(/PRODUCT_ADMIN_SECTIONS/);
    expect(detail).toMatch(/Admin \/ debug \/ diagnostic/);
    // Laboratory closure only under admin publication drawer â€” not overview chrome
    expect(detail).toMatch(/product-system-admin-lab-closure/);
    const labIdx = detail.indexOf("product-system-admin-lab-closure");
    const overviewIdx = detail.indexOf('section === "overview"');
    const compilerIdx = detail.indexOf('section === "compiler"');
    expect(overviewIdx).toBeGreaterThan(-1);
    expect(compilerIdx).toBeGreaterThan(overviewIdx);
    expect(labIdx).toBeGreaterThan(compilerIdx);
    const primaryBlock = detail.slice(
      detail.indexOf("PRODUCT_PRIMARY_SECTIONS"),
      detail.indexOf("PRODUCT_ADMIN_SECTIONS"),
    );
    expect(primaryBlock).not.toMatch(/PreÈ›uri template/);
    expect(primaryBlock).not.toMatch(/Publicare/);
    expect(primaryBlock).not.toMatch(/Previzualizare runtime/);
  });

  it("hides planned shell nav and pricing chip from ProductSystemLayout primary chrome", () => {
    const layout = readFileSync(resolve(__dirname, "ProductSystemLayout.tsx"), "utf8");
    expect(layout).not.toMatch(/product-system-shell-nav-planned/);
    expect(layout).not.toMatch(/product-system-pricing-registry-link/);
    expect(layout).toMatch(/!item\.plannedSection/);
    expect(layout).toMatch(/data-workspace="blank"/);
  });

  it("keeps a single Produse title with commercial-flow continuity chrome", () => {
    const layout = readFileSync(resolve(__dirname, "ProductSystemLayout.tsx"), "utf8");
    expect(layout).toMatch(/showSectionNav = operationalNav\.length > 1/);
    expect(layout).toMatch(/product-system-shell-title/);
    expect(layout).toMatch(/Produse/);
    expect(layout).toMatch(/CommercialFlowStrip/);
    expect(layout).not.toMatch(/PRODUCT_SYSTEM_WORKSPACE_SUBTITLE/);

    const page = readFileSync(resolve(__dirname, "../../pages/ProductSystem.tsx"), "utf8");
    expect(page).toMatch(/product-system-v2-page-toolbar/);
    expect(page).toMatch(/No second title here/);

    const v2 = readFileSync(resolve(__dirname, "ProductSystemV2Workspace.tsx"), "utf8");
    expect(v2).toMatch(/ProductSystemSpineBand compact/);
    expect(v2).toMatch(/TechnicalDetailsDisclosure/);
    expect(v2).not.toMatch(/Workspace produs/);
  });
});
