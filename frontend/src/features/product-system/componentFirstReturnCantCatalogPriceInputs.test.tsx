import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import {
  buildOracalSeriesPricingSummary,
  buildReturnCantCatalogPriceSummary,
  computeBlockersBeforePricing,
  formatCatalogPriceConfirmedValue,
  RETURN_CANT_CATALOG_PRICE_INPUTS,
  RETURN_CANT_INTAKE_V6_ORACAL_CATALOG_SOURCE,
  RETURN_CANT_INTAKE_V6_RAL_CATALOG_SOURCE,
  RETURN_CANT_ORACAL_SERIES_PRICES,
  RETURN_CANT_RAL_CLASSIC_REGISTRY_PATH,
  RETURN_CANT_RAL_MINIMUM,
} from "./componentFirstReturnCantCatalogPriceInputs";
import { ReturnCantCatalogPriceInputsPanel } from "./ReturnCantCatalogPriceInputsPanel";

describe("componentFirstReturnCantCatalogPriceInputs", () => {
  it("records Oracal Intake V6 catalog source path for readonly cross-reference", () => {
    expect(RETURN_CANT_INTAKE_V6_ORACAL_CATALOG_SOURCE.sourceFile).toMatch(/colorRegistry\.ts/);
    expect(RETURN_CANT_INTAKE_V6_ORACAL_CATALOG_SOURCE.sourceFiles).toContain(
      "frontend/src/lib/colorRegistry/oracal651.ts",
    );
    expect(RETURN_CANT_INTAKE_V6_ORACAL_CATALOG_SOURCE.duplicationPolicy).toBe("do_not_duplicate_catalog");

    const source = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_catalog_source");
    expect(source?.status).toBe("owner_confirmed");
    expect(String(source?.confirmedValue)).toMatch(/Intake V6/i);
    expect(String(source?.knownSoFarRo)).toMatch(/oracal651\.ts/i);
  });

  it("records RAL Intake V6 catalog source path for readonly cross-reference", () => {
    expect(RETURN_CANT_INTAKE_V6_RAL_CATALOG_SOURCE.sourceFile).toBe(RETURN_CANT_RAL_CLASSIC_REGISTRY_PATH);
    expect(RETURN_CANT_INTAKE_V6_RAL_CATALOG_SOURCE.catalogFormat).toMatch(/RAL Classic/i);

    const source = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_catalog_source");
    expect(source?.status).toBe("owner_confirmed");
    expect(String(source?.confirmedValue)).toMatch(/Intake V6/i);
    expect(String(source?.knownSoFarRo)).toMatch(/ralColors\.ts/i);
  });

  it("confirms Oracal series prices 651/641/8500 without inventing extra series", () => {
    expect(RETURN_CANT_ORACAL_SERIES_PRICES).toHaveLength(3);
    expect(RETURN_CANT_ORACAL_SERIES_PRICES.find((p) => p.series === "651")?.price).toBe(8);
    expect(RETURN_CANT_ORACAL_SERIES_PRICES.find((p) => p.series === "641")?.price).toBe(5);
    expect(RETURN_CANT_ORACAL_SERIES_PRICES.find((p) => p.series === "8500")?.price).toBe(13);
    for (const entry of RETURN_CANT_ORACAL_SERIES_PRICES) {
      expect(entry.currency).toBe("EUR");
      expect(entry.unit).toBe("mp");
      expect(entry.pricingActive).toBe(false);
    }

    const seriesInput = RETURN_CANT_CATALOG_PRICE_INPUTS.find(
      (i) => i.key === "oracal_series_prices_by_series",
    );
    expect(seriesInput?.status).toBe("owner_confirmed");
    expect(seriesInput?.confirmedValue).toEqual(["651 = 8.00 EUR/mp", "641 = 5.00 EUR/mp", "8500 = 13.00 EUR/mp"]);
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

  it("keeps Oracal full price table partial while known series prices are confirmed", () => {
    const mode = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_mode");
    const table = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_table");
    expect(mode?.status).toBe("owner_confirmed");
    expect(mode?.confirmedValue).toBe("preț pe cod/familie");
    expect(table?.status).toBe("partial_confirmed");
    expect(table?.stillMissingRo).toContain("Valori preț unitar pe cod/familie în afara seriilor confirmate");

    const summary = buildOracalSeriesPricingSummary();
    expect(summary.confirmedOracalSeriesPriceCount).toBe(3);
    expect(summary.oracalSeriesPricingReadyForKnownSeries).toBe(true);
    expect(summary.oracalFullPricingReady).toBe(false);
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

  it("confirms RAL minimum 100 lei per RAL color on material plus labor total without auto conversion", () => {
    expect(RETURN_CANT_RAL_MINIMUM.ral_minimum_amount).toBe(100);
    expect(RETURN_CANT_RAL_MINIMUM.ral_minimum_currency).toBe("lei");
    expect(RETURN_CANT_RAL_MINIMUM.ral_minimum_scope).toBe("per_ral_color");
    expect(RETURN_CANT_RAL_MINIMUM.ral_minimum_scope_label_ro).toMatch(/pe culoare RAL/i);
    expect(RETURN_CANT_RAL_MINIMUM.ral_minimum_applies_to).toBe("material_plus_labor_total");
    expect(RETURN_CANT_RAL_MINIMUM.ral_minimum_applies_to_label_ro).toMatch(/total material RAL \+ manoperă/i);
    expect(RETURN_CANT_RAL_MINIMUM.ral_minimum_conversion_policy).toBe("no_auto_conversion");

    const minimum = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "ral_minimum_rule");
    expect(minimum?.status).toBe("owner_confirmed");
    expect(minimum?.confirmedValue).toMatch(/100 lei/i);
    expect(minimum?.confirmedValue).toMatch(/pe culoare RAL/i);
    expect(minimum?.confirmedValue).toMatch(/total material RAL \+ manoperă/i);
    expect(minimum?.unit).toBe("lei");
    expect(minimum?.knownSoFarRo).toMatch(/fără conversie automată/i);
    expect(minimum?.stillMissingRo).toContain("Formulă runtime — neactivată în acest task");
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
    for (const entry of RETURN_CANT_ORACAL_SERIES_PRICES) {
      expect(entry.pricingActive).toBe(false);
    }
    const summary = buildReturnCantCatalogPriceSummary();
    expect(summary.readyForPricing).toBe(false);
    expect(summary.pricingActiveCount).toBe(0);
    expect(summary.oracalSeriesPricing.oracalSeriesPricingReadyForKnownSeries).toBe(true);
  });

  it("computes updated blockers before pricing", () => {
    const blockers = computeBlockersBeforePricing();
    expect(blockers).toContain("Oracal price table for all official codes/series not complete");
    expect(blockers).toContain(
      "Stable shared catalog extraction remains future work if Product System catalog materialization is needed",
    );
    expect(blockers).toContain("Pricing activation not allowed");
    expect(blockers).toContain("Product Truth live write not allowed");
    expect(blockers).not.toContain("Oracal actual catalog data/import not stored yet");
    expect(blockers).not.toContain("RAL list data/source not materialized in product system catalog");
    expect(blockers).not.toContain("RAL minimum scope unresolved (100 lei confirmed)");
  });

  it("does not contain fake Oracal codes or RAL color codes", () => {
    const oracalKeys = ["oracal_catalog_source", "oracal_selector_source", "oracal_price_table"];
    for (const key of oracalKeys) {
      const input = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === key)!;
      const serialized = JSON.stringify(input);
      expect(serialized).not.toMatch(/ORACAL-\d+/i);
      expect(serialized).not.toMatch(/RAL\s*\d{4}/i);
    }
  });

  it("formats partial Oracal price table without inventing unconfirmed unit prices", () => {
    const table = RETURN_CANT_CATALOG_PRICE_INPUTS.find((i) => i.key === "oracal_price_table")!;
    expect(formatCatalogPriceConfirmedValue(table)).toMatch(/651\/641\/8500 confirmate/i);
  });
});

describe("ReturnCantCatalogPriceInputsPanel", () => {
  it("renders NOT READY FOR PRICING with Intake V6 cross-ref and Oracal series prices", () => {
    render(<ReturnCantCatalogPriceInputsPanel />);
    expect(screen.getByTestId("product-system-return-cant-catalog-price-global-status")).toHaveTextContent(
      /NOT READY FOR PRICING/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-known-oracal_catalog_source")).toHaveTextContent(
      /Intake V6/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-known-ral_catalog_source")).toHaveTextContent(
      /Intake V6|ralColors/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-oracal_calculation_model")).toHaveTextContent(
      /lățime rolă/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-oracal_roll_widths")).toHaveTextContent(
      /100 cm.*126 cm/i,
    );
    expect(screen.getByTestId("product-system-return-cant-oracal-series-price-651")).toHaveTextContent(/8\.00 EUR\/mp/i);
    expect(screen.getByTestId("product-system-return-cant-oracal-series-price-641")).toHaveTextContent(/5\.00 EUR\/mp/i);
    expect(screen.getByTestId("product-system-return-cant-oracal-series-price-8500")).toHaveTextContent(
      /13\.00 EUR\/mp/i,
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
