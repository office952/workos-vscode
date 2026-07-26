import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { MaterialMarketPriceRegistryPanel } from "./MaterialMarketPriceRegistryPanel";

vi.mock("@/api/materialMarketPriceRegistry", () => ({
  materialMarketPriceRegistryApi: {
    getRegistry: vi.fn(),
  },
}));

import { materialMarketPriceRegistryApi } from "@/api/materialMarketPriceRegistry";

const mock = {
  schema_version: "1.0.0",
  ownership_note_ro: "Inventory detine identitatea.",
  source_precedence: ["OWNER_CONFIRMED", "MISSING"],
  freshness_policy: {},
  summary: {
    total: 2,
    priced: 1,
    missing: 1,
    stale: 0,
    review_soon: 0,
    unknown_date: 1,
    with_supplier: 1,
    active_template_critical_missing: 1,
    temporary_ai_fallback: 0,
  },
  items: [
    {
      material_code: "MAT-ACM-BOND-3MM",
      display_name: "ACM Bond 3mm",
      source_type: "OWNER_CONFIRMED" as const,
      raw_unit: "mp",
      raw_price: 15,
      currency: "EUR",
      normalization: {
        raw_unit: "mp",
        raw_price: 15,
        currency: "EUR",
        normalized_unit: "mp",
        normalized_price: 15,
        conversion_applied: false,
      },
      preferred: true,
      freshness: "CURRENT" as const,
      confidence: "high" as const,
      temporary_ai_fallback: false,
      canonical: true,
      active_templates: ["TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"],
      history: [],
      inventory_href: "/inventory?material=MAT-ACM-BOND-3MM",
      pricing_href: "/inventory/pricing",
    },
    {
      material_code: "MAT-ADEZIV-CANT-LITERE",
      display_name: "Adeziv cant",
      source_type: "MISSING" as const,
      raw_price: null,
      normalization: { conversion_applied: false },
      preferred: true,
      freshness: "UNKNOWN_DATE" as const,
      confidence: "low" as const,
      temporary_ai_fallback: false,
      canonical: false,
      blocker: "Pret material lipsa",
      active_templates: ["TPL-VOLUMETRIC-LETTERS_v2"],
      history: [],
      inventory_href: "/inventory?material=MAT-ADEZIV-CANT-LITERE",
      pricing_href: "/inventory/pricing",
    },
  ],
  critical_missing: ["MAT-ADEZIV-CANT-LITERE"],
  warnings: [],
};

describe("MaterialMarketPriceRegistryPanel", () => {
  beforeEach(() => {
    vi.mocked(materialMarketPriceRegistryApi.getRegistry).mockResolvedValue(mock as never);
  });

  it("renders priced and missing materials", async () => {
    render(
      <MemoryRouter>
        <MaterialMarketPriceRegistryPanel />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("material-market-price-registry")).toBeInTheDocument();
    });
    expect(screen.getByText(/Surse reale de achiziție/i)).toBeInTheDocument();
    expect(screen.getByText("ACM Bond 3mm")).toBeInTheDocument();
    expect(screen.getByTestId("material-market-critical-missing")).toHaveTextContent(
      "MAT-ADEZIV-CANT-LITERE",
    );
  });
});
