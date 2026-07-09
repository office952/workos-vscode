import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ProductSystem from "./ProductSystem";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { TooltipProvider } from "@/components/ui/tooltip";

function renderProductSystem() {
  return render(
    <TooltipProvider>
      <MemoryRouter initialEntries={["/product-system"]}>
        <ProductSystem />
      </MemoryRouter>
    </TooltipProvider>,
  );
}

vi.mock("@/lib/mockGuard", () => ({
  isMockEnabled: () => false,
}));

const mockTemplateList = vi.fn();
const mockAvailabilityList = vi.fn();

vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    productTemplatesApi: {
      ...actual.productTemplatesApi,
      list: () => mockTemplateList(),
    },
    productTemplateAvailabilityApi: {
      list: () => mockAvailabilityList(),
    },
    materialsApi: {
      ...actual.materialsApi,
      list: vi.fn().mockResolvedValue([]),
    },
  };
});

vi.mock("@/api/productFamilies", () => ({
  productFamiliesApi: {
    list: vi.fn().mockResolvedValue({ items: [] }),
  },
}));

vi.mock("@/features/product-system/useProductAggregateLibrarySummaries", () => ({
  useProductAggregateLibrarySummaries: () => ({ summaries: new Map() }),
}));

vi.mock("@/features/product-system/useProductAggregate", () => ({
  useProductAggregate: () => ({
    aggregate: null,
    status: "fallback",
    fallbackReason: "ProductAggregate unavailable; falling back to legacy template display.",
    usingFallback: true,
    isLoading: false,
  }),
}));

const volumetricTemplate: ProductTemplateEntity = {
  id: 1,
  template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  family_name: "Litere volumetrice",
  active: true,
  components_json: "[]",
  operations_json: "[]",
  required_materials_json: "[]",
};

const volumetricAvailability: ProductTemplateAvailabilityItem = {
  template_id: 1,
  template_code: "TPL-VOLUMETRIC-LETTERS_v2",
  family_id: "volumetric",
  family_name: "Litere volumetrice",
  description: "Volumetric letters",
  db_active: true,
  quote_offerable: true,
  runtime_module: false,
  is_parent: true,
  has_modules: true,
  parent_codes: [],
  module_codes: [
    "TPL-VOLUMETRIC-FACE_v1",
    "TPL-VOLUMETRIC-BACK_v1",
    "TPL-VOLUM-ALUMINIU_v1",
    "TPL-VOLUMETRIC-FINISH_v1",
    "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    "TPL-VOLUMETRIC-LED_v1",
  ],
  status: "offerable",
  status_reason: "owner_valid_letters",
  product_system_role: "offerable_product",
  display_group: "active_products",
  importance_rank: 10,
  owner_decision_required: false,
  readiness_reason: "Produs valid pentru ofertare in Work Intake.",
  ui_label: "Produs activ pentru ofertare",
  ui_description: "Poate fi ales ca produs initial in Work Intake.",
  parent_product_codes: [],
  child_module_codes: [
    "TPL-VOLUMETRIC-FACE_v1",
    "TPL-VOLUMETRIC-BACK_v1",
    "TPL-VOLUM-ALUMINIU_v1",
    "TPL-VOLUMETRIC-FINISH_v1",
    "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    "TPL-VOLUMETRIC-LED_v1",
  ],
  shared_with_product_codes: ["TPL-VOLUMETRIC-LOGO_v1"],
  composition_modules: [],
  shared_component_contracts: [
    {
      component_key: "volumetric_face",
      display_name: "Face / front",
      profile_key: "letters",
      module_template_code: "TPL-VOLUMETRIC-FACE_v1",
      confidence: "MEDIUM",
      owner_decision: "APPROVE_AS_DIRECTION",
      shared_truth_fields: ["selected_layer_refs", "material"],
      not_confirmed: ["material", "finish_target"],
      shared_module_template_code: "TPL-VOLUMETRIC-FACE_v1",
    },
    {
      component_key: "volumetric_back",
      display_name: "Back / spate",
      profile_key: "letters",
      module_template_code: "TPL-VOLUMETRIC-BACK_v1",
      confidence: "MEDIUM",
      owner_decision: "APPROVE_AS_DIRECTION",
      shared_truth_fields: ["backing_mode"],
      not_confirmed: ["material"],
      shared_module_template_code: "TPL-VOLUMETRIC-BACK_v1",
    },
    {
      component_key: "volumetric_return_side",
      display_name: "VOLUM ALUMINIU / CANT",
      profile_key: "letters",
      module_template_code: "TPL-VOLUM-ALUMINIU_v1",
      confidence: "PARTIAL",
      owner_decision: "APPROVE_AS_DIRECTION",
      shared_truth_fields: ["return_depth_mm", "finish_type"],
      not_confirmed: ["material_profile", "perimeter_source", "confirmation_state"],
      shared_module_template_code: "TPL-VOLUM-ALUMINIU_v1",
    },
    {
      component_key: "volumetric_surface_finish",
      display_name: "Finish / artwork",
      profile_key: "letters",
      module_template_code: "TPL-VOLUMETRIC-FINISH_v1",
      confidence: "LOW",
      owner_decision: "KEEP_SEPARATE_NOW",
      shared_truth_fields: ["finish_target"],
      not_confirmed: ["print_required"],
      shared_module_template_code: "TPL-VOLUMETRIC-FINISH_v1",
    },
    {
      component_key: "volumetric_mounting_interface",
      display_name: "Mounting / support",
      profile_key: "letters",
      module_template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1",
      confidence: "LOW",
      owner_decision: "KEEP_SEPARATE_NOW",
      shared_truth_fields: ["mounting_system"],
      not_confirmed: ["support_required"],
      shared_module_template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1",
    },
    {
      component_key: "volumetric_lighting",
      display_name: "Lighting",
      profile_key: "letters",
      module_template_code: "TPL-VOLUMETRIC-LED_v1",
      confidence: "PARTIAL",
      owner_decision: "NEEDS_MORE_AUDIT",
      shared_truth_fields: ["illumination_type"],
      not_confirmed: ["led_module_count", "strategy_profile"],
      shared_module_template_code: "TPL-VOLUMETRIC-LED_v1",
      strategy_status: "current LED strategy",
      strategy_meaning: "Letters use the shared LED contract.",
    },
  ],
};

describe("ProductSystem design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });
  });

  it("renders SourceBadge mapped from live API load mode", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    const sourceBadge = document.querySelector('[data-source="db"]');
    expect(sourceBadge).toBeTruthy();
    expect(sourceBadge?.textContent).toMatch(/Live DB/i);
  });

  it("renders active template status badge from design-system", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("product-system-density-detailed"));
    fireEvent.click(screen.getByTestId("product-system-view-tab-products"));

    await waitFor(() => {
      expect(screen.getByTestId("product-system-template-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    const activeBadge = document.querySelector('[data-status-domain="productSystem"][data-status="active"]');
    expect(activeBadge).toBeTruthy();
    expect(activeBadge).toHaveAttribute("data-status", "active");
    expect(activeBadge).toHaveAttribute("data-status-tone", "emerald");
  });

  it("keeps TPL-VOLUMETRIC-LETTERS_v2 visible in library", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "Product System Catalog" })).toBeInTheDocument();
  });

  it("shows the component ownership matrix with honest cant blockers and no promote CTA", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByText("TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("product-system-density-detailed"));
    fireEvent.click(screen.getByTestId("product-system-view-tab-products"));

    await waitFor(() => {
      expect(screen.getByTestId("product-system-template-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("product-system-template-TPL-VOLUMETRIC-LETTERS_v2"));

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-ownership-panel")).toBeInTheDocument();
    });

    const returnCantSourcePaths = screen.getByTestId("product-system-return-cant-source-paths");
    const structuralMap = screen.getByTestId("product-system-structural-composition-map");
    const functionalMap = screen.getByTestId("product-system-functional-composition-map");

    expect(screen.getByTestId("product-system-ownership-composer-badge")).toHaveTextContent("Product Template = composer");
    expect(screen.getByTestId("product-system-ownership-product-template-warning")).toHaveTextContent("Product Template still carries component-owned defaults");
    expect(screen.getByTestId("product-system-ownership-status-volumetric_return_side")).toHaveTextContent("partial_ready");
    expect(structuralMap).toBeInTheDocument();
    expect(functionalMap).toBeInTheDocument();
    expect(screen.getByText("Structural composition map")).toBeInTheDocument();
    expect(structuralMap).toHaveTextContent("FACE / FATA");
    expect(structuralMap).toHaveTextContent("BACK / SPATE");
    expect(structuralMap).toHaveTextContent("RETURN_CANT / VOLUM");
    expect(structuralMap).toHaveTextContent("comp_face_litere");
    expect(structuralMap).toHaveTextContent("comp_spate_litere");
    expect(structuralMap).toHaveTextContent("comp_lateral_litere");
    expect(structuralMap).toHaveTextContent("PARTIAL");
    expect(screen.getByTestId("product-system-structural-composition-map-aggregate-boundary")).toHaveTextContent("ProductAggregate is derived read model");
    expect(functionalMap).toHaveTextContent("LIGHTING / LED");
    expect(functionalMap).toHaveTextContent("FINISH / FINISAJ");
    expect(functionalMap).toHaveTextContent("SUPPORT / MOUNTING");
    expect(returnCantSourcePaths).toBeInTheDocument();
    expect(screen.getByText("Separate calculation source paths")).toBeInTheDocument();
    expect(returnCantSourcePaths).toHaveTextContent("return_depth_mm");
    expect(returnCantSourcePaths).toHaveTextContent("return_finish_type");
    expect(returnCantSourcePaths).toHaveTextContent("material cant / profil aluminiu");
    expect(returnCantSourcePaths).toHaveTextContent("operation: modelare_cant");
    expect(returnCantSourcePaths).toHaveTextContent("operation: bonding / lipire cant");
    expect(returnCantSourcePaths).toHaveTextContent("resources / tools");
    expect(returnCantSourcePaths).toHaveTextContent("operation_resource_requirements");
    expect(screen.getByTestId("product-system-return-cant-logo-reuse-note")).toHaveTextContent("TPL-VOLUMETRIC-LOGO_v1");
    expect(screen.getByText("perimeter_source")).toBeInTheDocument();
    expect(screen.getAllByText(/parent aggregate only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/form system only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/component-owned source missing/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/source not wired yet/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/component-owned source missing/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/calculation blocked until component-scoped confirmation exists/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/ready for future calculation/i)).not.toBeInTheDocument();
  });

});
