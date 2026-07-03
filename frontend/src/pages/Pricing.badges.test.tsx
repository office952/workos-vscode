import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Pricing from "./Pricing";
import type { PricingRegistryResponse } from "@/api/pricingRegistry";

const mockGetRegistry = vi.fn();

vi.mock("@/api/pricingRegistry", () => ({
  pricingRegistryApi: {
    getRegistry: () => mockGetRegistry(),
  },
}));

vi.mock("@/api/commercialMarkupPoliciesAdmin", () => ({
  commercialMarkupPoliciesAdminApi: {
    list: vi.fn().mockResolvedValue([]),
  },
}));

vi.mock("@/api/costEngine", () => ({
  costEngineApi: {
    getConfig: vi.fn().mockResolvedValue({ moneda_implicita: "RON" }),
  },
}));

const registryFixture: PricingRegistryResponse = {
  summary: {
    templates_active: 1,
    items_template_used: 2,
    materials_count: 2,
    rates_count: 0,
    markup_rules_count: 0,
    owner_confirmed: 1,
    needs_review: 0,
    missing_price: 1,
  },
  template_usage: [
    {
      template_code: "TPL-VOLUMETRIC-LETTERS",
      material_codes: ["MAT-LED-MODULE", "MAT-MISSING"],
      workcenter_codes: [],
    },
  ],
  items: [
    {
      pricing_code: "MAT-LED-MODULE",
      display_name: "LED Module",
      pricing_kind: "material",
      registry_category: "LED / electrice",
      unit: "buc",
      base_cost: 0.5,
      currency: "EUR",
      status: "active",
      confidence: "owner_confirmed",
      used_by_templates: ["TPL-VOLUMETRIC-LETTERS"],
      affects_quote_calculation: true,
      technical_source: "inventory_materials",
    },
    {
      pricing_code: "MAT-MISSING",
      display_name: "Missing Material",
      pricing_kind: "material",
      registry_category: "Consumabile",
      unit: "buc",
      base_cost: null,
      currency: "RON",
      status: "missing_price",
      confidence: "missing",
      used_by_templates: ["TPL-VOLUMETRIC-LETTERS"],
      affects_quote_calculation: true,
      technical_source: "inventory_materials",
    },
  ],
  markup_policies: [],
};

describe("Pricing design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetRegistry.mockResolvedValue(registryFixture);
  });

  it("renders SourceBadge for live registry load", async () => {
    render(
      <MemoryRouter initialEntries={["/pricing"]}>
        <Pricing />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("Pricing Registry")).toBeInTheDocument();
    });

    const sourceBadge = document.querySelector('[data-source="db"]');
    expect(sourceBadge).toBeTruthy();
    expect(sourceBadge?.textContent).toMatch(/Live DB/i);
  });

  it("renders pricing status badges from design-system on registry rows", async () => {
    render(
      <MemoryRouter initialEntries={["/pricing"]}>
        <Pricing />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("LED Module")).toBeInTheDocument();
    });

    const ownerConfirmed = screen
      .getAllByText("Owner-confirmed")
      .find((el) => el.getAttribute("data-status-domain") === "pricing");
    expect(ownerConfirmed).toBeTruthy();
    expect(ownerConfirmed).toHaveAttribute("data-status", "owner_confirmed");
    expect(ownerConfirmed).toHaveAttribute("data-status-tone", "emerald");

    const missingPrice = screen
      .getAllByText("Rată lipsă")
      .find((el) => el.getAttribute("data-status-domain") === "pricing");
    expect(missingPrice).toBeTruthy();
    expect(missingPrice).toHaveAttribute("data-status", "missing_price");
    expect(missingPrice).toHaveAttribute("data-status-tone", "red");
  });

  it("preserves unit cost display text in fixtures", async () => {
    render(
      <MemoryRouter initialEntries={["/pricing"]}>
        <Pricing />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText("LED Module")).toBeInTheDocument();
    });

    expect(screen.getByText(/0,50 EUR/)).toBeInTheDocument();
    expect(screen.getByText("Lipsă")).toBeInTheDocument();
  });
});
