import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  buildReturnCantCatalogPriceSummary,
  computeBlockersBeforePricing,
  formatCatalogPriceConfirmedValue,
  RETURN_CANT_CATALOG_PRICE_INPUTS,
  RETURN_CANT_RAL_CLASSIC_REGISTRY_PATH,
} from "./componentFirstReturnCantCatalogPriceInputs";
import { ReturnCantCatalogPriceInputsPanel } from "./ReturnCantCatalogPriceInputsPanel";

describe("componentFirstReturnCantCatalogPriceInputs", () => {
  it("confirms Oracal catalog target as all official Oracal codes without fake records", () => {
    const selector = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_selector_source");
    expect(selector?.status).toBe("partial_confirmed");
    expect(selector?.confirmedValue).toBe("toate codurile Oracal oficiale");
    expect(selector?.stillMissingRo).toContain("Import/listă efectivă de coduri în catalog product system");
  });

  it("confirms Oracal calculation model as roll width x used length = mp", () => {
    const model = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_calculation_model");
    expect(model?.status).toBe("owner_confirmed");
    expect(String(model?.confirmedValue)).toMatch(/lățime rolă.*lungime folosită/i);
    expect(model?.unit).toBe("mp");
  });

  it("confirms Oracal roll widths as 100 cm and 126 cm", () => {
    const widths = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_roll_widths");
    expect(widths?.status).toBe("owner_confirmed");
    expect(widths?.confirmedValue).toEqual(["100 cm", "126 cm"]);
  });

  it("keeps Oracal pricing by code/family and price table values not invented", () => {
    const mode = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_mode");
    const table = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_table");
    expect(mode?.status).toBe("owner_confirmed");
    expect(mode?.confirmedValue).toBe("preț pe cod/familie");
    expect(table?.status).toBe("partial_confirmed");
    expect(table?.stillMissingRo).toContain("Valori preț unitar pe cod/familie");
    const serialized = JSON.stringify(table);
    expect(serialized).not.toMatch(/\b\d+(\.\d+)?\s*eur\b/i);
  });

  it("confirms RAL collection as RAL Classic with registry cross-reference", () => {
    const ral = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_selector_source");
    expect(ral?.status).toBe("owner_confirmed");
    expect(ral?.confirmedValue).toBe("RAL Classic");
    expect(ral?.knownSoFarRo).toMatch(/Intake V6/i);
    expect(RETURN_CANT_RAL_CLASSIC_REGISTRY_PATH).toMatch(/ralColors\.ts/);
  });

  it("confirms RAL material prices by depth from owner", () => {
    const prices = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_material_price_by_depth");
    expect(prices?.status).toBe("owner_confirmed");
    expect(prices?.confirmedValue).toEqual([
      "30 mm: 2.00 EUR/ml (MAT-VOPSEA-RAL-CANT-30MM)",
      "60 mm: 2.50 EUR/ml (MAT-VOPSEA-RAL-CANT-60MM)",
      "80 mm: 3.00 EUR/ml (MAT-VOPSEA-RAL-CANT-80MM)",
      "100 mm: 4.00 EUR/ml (MAT-VOPSEA-RAL-CANT-100MM)",
    ]);
  });

  it("confirms RAL labor price 1.00 EUR/ml for all depths", () => {
    const labor = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_labor_price_by_depth");
    expect(labor?.status).toBe("owner_confirmed");
    expect(labor?.confirmedValue).toEqual([
      "30 mm: 1.00 EUR/ml",
      "60 mm: 1.00 EUR/ml",
      "80 mm: 1.00 EUR/ml",
      "100 mm: 1.00 EUR/ml",
    ]);
  });

  it("marks RAL minimum 100 lei partial with scope pending and no auto conversion", () => {
    const minimum = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_minimum_rule");
    expect(minimum?.status).toBe("partial_confirmed");
    expect(minimum?.confirmedValue).toBe("100 lei");
    expect(minimum?.unit).toBe("lei");
    expect(minimum?.knownSoFarRo).toMatch(/fără conversie automată/i);
    expect(minimum?.stillMissingRo.length).toBeGreaterThan(0);
  });

  it("confirms material-depth compatibility for Al 0.6 mm all depths", () => {
    const compat = RETURN_CANT_CATALOG_PRICE_INPUTS.find(
      (i) => i.key === "return_material_depth_compatibility",
    );
    expect(compat?.status).toBe("owner_confirmed");
    expect(String(compat?.confirmedValue)).toMatch(/aluminiu 0\.6 mm/i);
  });

  it("keeps pricingActive false and readyForPricing false", () => {
    for (const input of RETURN_CANT_CATALOG_PRICE_INPUTS) {
      expect(input.pricingActive).toBe(false);
    }
    const summary = buildReturnCantCatalogPriceSummary();
    expect(summary.readyForPricing).toBe(false);
    expect(summary.pricingActiveCount).toBe(0);
  });

  it("computes updated blockers before pricing", () => {
    const blockers = computeBlockersBeforePricing();
    expect(blockers).toContain("Oracal price table values not stored yet");
    expect(blockers).toContain("RAL minimum scope unresolved (100 lei confirmed)");
    expect(blockers).not.toContain("RAL material prices missing");
    expect(blockers).not.toContain("Material/depth compatibility missing");
  });

  it("does not contain fake Oracal codes or RAL color codes", () => {
    const oracalKeys = ["oracal_selector_source", "oracal_catalog_shape", "oracal_price_table"];
    for (const key of oracalKeys) {
      const input = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === key)!;
      const serialized = JSON.stringify(input);
      expect(serialized).not.toMatch(/ORACAL-\d+/i);
      expect(serialized).not.toMatch(/RAL\s*\d{4}/i);
    }
  });

  it("formats partial Oracal price table without inventing unit prices", () => {
    const table = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_table")!;
    expect(formatCatalogPriceConfirmedValue(table)).toMatch(/Owner are tabelul/i);
  });
});

describe("ReturnCantCatalogPriceInputsPanel", () => {
  it("renders NOT READY FOR PRICING with confirmed Oracal/RAL values", () => {
    render(<ReturnCantCatalogPriceInputsPanel />);
    expect(screen.getByTestId("product-system-return-cant-catalog-price-global-status")).toHaveTextContent(
      /NOT READY FOR PRICING/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-known-oracal_selector_source")).toHaveTextContent(
      /toate codurile Oracal oficiale/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-oracal_calculation_model")).toHaveTextContent(
      /lățime rolă/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-oracal_roll_widths")).toHaveTextContent(
      /100 cm.*126 cm/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-ral_selector_source")).toHaveTextContent(
      /RAL Classic/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-ral_material_price_by_depth")).toHaveTextContent(
      /2\.00 EUR\/ml/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-ral_labor_price_by_depth")).toHaveTextContent(
      /1\.00 EUR\/ml/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-ral_minimum_rule")).toHaveTextContent(
      /100 lei/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveTextContent(
      /No Pricing activation/i,
    );
    expect(screen.queryByRole("button", { name: /^save$/i })).not.toBeInTheDocument();
  });
});
