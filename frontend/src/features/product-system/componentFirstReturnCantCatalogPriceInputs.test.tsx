import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  buildReturnCantCatalogPriceSummary,
  formatCatalogPriceConfirmedValue,
  RETURN_CANT_CATALOG_PRICE_INPUTS,
} from "./componentFirstReturnCantCatalogPriceInputs";
import { ReturnCantCatalogPriceInputsPanel } from "./ReturnCantCatalogPriceInputsPanel";

describe("componentFirstReturnCantCatalogPriceInputs", () => {
  it("marks Oracal selector partial with full list known but actual catalog missing", () => {
    const selector = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_selector_source");
    expect(selector?.status).toBe("partial_confirmed");
    expect(selector?.knownSoFarRo).toMatch(/listă completă Oracal/i);
    expect(selector?.stillMissingRo.length).toBeGreaterThan(0);
    expect(selector?.confirmedValue).toBe("listă completă Oracal");
  });

  it("confirms Oracal pricing mode but price table missing", () => {
    const mode = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_mode");
    const table = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_table");
    expect(mode?.status).toBe("owner_confirmed");
    expect(mode?.confirmedValue).toBe("preț pe cod/familie");
    expect(table?.status).toBe("owner_input_required");
    expect(table?.confirmedValue).toBeNull();
  });

  it("marks RAL selector partial with standard mode known but source/list missing", () => {
    const ral = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_selector_source");
    expect(ral?.status).toBe("partial_confirmed");
    expect(ral?.confirmedValue).toBe("selector standard RAL");
    expect(ral?.stillMissingRo).toContain("Sursa listei standard RAL");
  });

  it("confirms RAL material unit ml but price values missing", () => {
    const unit = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_material_unit");
    const prices = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_material_price_by_depth");
    expect(unit?.status).toBe("owner_confirmed");
    expect(unit?.confirmedValue).toBe("ml");
    expect(prices?.status).toBe("owner_input_required");
    expect(prices?.stillMissingRo).toContain("30 mm — OWNER INPUT REQUIRED");
  });

  it("confirms RAL labor unit ml but labor price and minimum missing", () => {
    const unit = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_labor_unit");
    const prices = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_labor_price_by_depth");
    const minimum = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_minimum_rule");
    expect(unit?.status).toBe("owner_confirmed");
    expect(unit?.confirmedValue).toBe("ml");
    expect(prices?.status).toBe("owner_input_required");
    expect(minimum?.status).toBe("owner_input_required");
  });

  it("marks material-depth compatibility as owner_input_required", () => {
    const compat = RETURN_CANT_CATALOG_PRICE_INPUTS.find(
      (i) => i.key === "return_material_depth_compatibility",
    );
    expect(compat?.status).toBe("owner_input_required");
    expect(compat?.knownSoFarRo).toMatch(/aluminiu 0\.6 mm/i);
    expect(compat?.knownSoFarRo).toMatch(/30 \/ 60 \/ 80 \/ 100 mm/i);
  });

  it("keeps pricingActive false for all entries", () => {
    for (const input of RETURN_CANT_CATALOG_PRICE_INPUTS) {
      expect(input.pricingActive).toBe(false);
    }
  });

  it("reports readyForPricing false and pricingActiveCount 0", () => {
    const summary = buildReturnCantCatalogPriceSummary();
    expect(summary.readyForPricing).toBe(false);
    expect(summary.pricingActiveCount).toBe(0);
    expect(summary.blockersBeforePricing.length).toBeGreaterThan(0);
  });

  it("does not contain fake Oracal codes, RAL codes, or prices", () => {
    const serialized = JSON.stringify(RETURN_CANT_CATALOG_PRICE_INPUTS);
    expect(serialized).not.toMatch(/ORACAL-\d+/i);
    expect(serialized).not.toMatch(/RAL\s*\d{4}/i);
    expect(serialized).not.toMatch(/\b\d+(\.\d+)?\s*(lei|eur|ron)\b/i);
  });

  it("formats null confirmed values as OWNER INPUT REQUIRED", () => {
    const table = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_table")!;
    expect(formatCatalogPriceConfirmedValue(table)).toBe("OWNER INPUT REQUIRED");
  });
});

describe("ReturnCantCatalogPriceInputsPanel", () => {
  it("renders NOT READY FOR PRICING and catalog panel sections", () => {
    render(<ReturnCantCatalogPriceInputsPanel />);
    expect(screen.getByTestId("product-system-return-cant-catalog-price-inputs")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-return-cant-catalog-price-global-status")).toHaveTextContent(
      /NOT READY FOR PRICING/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-ready-for-pricing")).toHaveTextContent(
      /Ready for pricing: NO/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveTextContent(
      /No Product Truth live write/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveTextContent(
      /No Pricing activation/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveTextContent(
      /No Work Intake exposure/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-section-oracal_catalog")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-return-cant-catalog-price-section-oracal_pricing")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-return-cant-catalog-price-section-ral_catalog")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-return-cant-catalog-price-known-oracal_selector_source")).toHaveTextContent(
      /listă completă Oracal/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-oracal_price_table")).toHaveTextContent(
      /OWNER INPUT REQUIRED/i,
    );
    expect(screen.queryByRole("button", { name: /^save$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
  });
});
