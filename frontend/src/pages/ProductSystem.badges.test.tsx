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

const componentFirstComposerTemplate: ProductTemplateEntity = {
  id: 2,
  template_code: "TPL-LETTERS-COMPOSER_v1",
  family_name: "Litere component-first candidate",
  active: false,
  components_json: JSON.stringify([
    {
      component_id: "comp_letter_face_v1",
      component_template_code: "TPL-COMP-LETTER-FACE_v1",
      role: "face",
      kind: "structural",
      target_product_truth_path: "components.face.instances[]",
    },
    {
      component_id: "comp_letter_back_v1",
      component_template_code: "TPL-COMP-LETTER-BACK_v1",
      role: "back",
      kind: "structural",
      target_product_truth_path: "components.back.instances[]",
    },
    {
      component_id: "comp_letter_return_cant_v1",
      component_template_code: "TPL-COMP-LETTER-RETURN-CANT_v1",
      role: "return_cant",
      kind: "structural",
      target_product_truth_path: "components.return_cant.instances[]",
    },
    {
      component_id: "comp_letter_led_v1",
      component_template_code: "TPL-COMP-LETTER-LED_v1",
      role: "lighting",
      kind: "functional",
      target_product_truth_path: "components.led.instances[]",
    },
    {
      component_id: "comp_letter_finish_v1",
      component_template_code: "TPL-COMP-LETTER-FINISH_v1",
      role: "finish",
      kind: "functional",
      target_product_truth_path: "components.finish.instances[]",
    },
    {
      component_id: "comp_letter_mounting_v1",
      component_template_code: "TPL-COMP-LETTER-MOUNTING_v1",
      role: "mounting",
      kind: "functional",
      target_product_truth_path: "components.mounting.instances[]",
    },
  ]),
  operations_json: "[]",
  required_materials_json: "[]",
  notes: JSON.stringify({
    readiness: "planned",
    offerable: false,
    work_intake_exposed: false,
    pricing_active: false,
    product_definition_active: false,
    product_aggregate_runtime_consumed: false,
    no_executable_operations: true,
    no_executable_bom: true,
    activation_guard: "COMPONENT_FIRST_SET_INERT_UNTIL_OWNER_GO",
    blockers: [
      "OWNER_GO_REQUIRED",
      "COMPONENT_TRUTH_NOT_IMPLEMENTED",
      "WORK_INTAKE_NOT_ENABLED",
      "PRICING_NOT_ENABLED",
      "PRODUCT_DEFINITION_NOT_ENABLED",
    ],
    component_dependency_graph: [
      { from: "comp_letter_face_v1", to: "comp_letter_return_cant_v1" },
      { from: "comp_letter_face_v1", to: "comp_letter_back_v1" },
      { from: "comp_letter_face_v1", to: "comp_letter_led_v1" },
      { from: "comp_letter_face_v1", to: "comp_letter_finish_v1" },
      { from: "comp_letter_back_v1", to: "comp_letter_finish_v1" },
      { from: "comp_letter_return_cant_v1", to: "comp_letter_finish_v1" },
      { from: "comp_letter_back_v1", to: "comp_letter_mounting_v1" },
      { from: "product_root", to: "comp_letter_mounting_v1" },
    ],
  }),
};

function componentFirstContractTemplate(
  id: number,
  templateCode: string,
  componentId: string,
  roleLabel: string,
  componentKind: string,
  targetProductTruthPath: string,
  dependencies: Array<string | Record<string, string>>,
  blockers: string[],
  activationGuard: string,
): ProductTemplateEntity {
  return {
    id,
    template_code: templateCode,
    family_name: "Litere component-first candidate",
    active: false,
    components_json: JSON.stringify([
      {
        component_id: componentId,
        role_label: roleLabel,
        component_kind: componentKind,
        target_product_truth_path: targetProductTruthPath,
        dependencies,
        blockers,
        readiness_state: "planned",
        activation_guard: activationGuard,
      },
    ]),
    operations_json: "[]",
    required_materials_json: "[]",
    notes: JSON.stringify({
      readiness: "planned",
      offerable: false,
      work_intake_exposed: false,
      pricing_active: false,
      product_definition_active: false,
      activation_guard: activationGuard,
    }),
  };
}

const componentFirstTemplates: ProductTemplateEntity[] = [
  componentFirstComposerTemplate,
  componentFirstContractTemplate(
    3,
    "TPL-COMP-LETTER-FACE_v1",
    "comp_letter_face_v1",
    "structural face",
    "structural",
    "components.face.instances[]",
    [],
    ["SOURCE_LAYERS_UNCONFIRMED", "FACE_MATERIAL_MISSING"],
    "FACE_CONTRACT_ONLY_NOT_EXECUTABLE",
  ),
  componentFirstContractTemplate(
    4,
    "TPL-COMP-LETTER-BACK_v1",
    "comp_letter_back_v1",
    "structural back",
    "structural",
    "components.back.instances[]",
    [{ source_component_id: "comp_letter_face_v1" }],
    ["FACE_GEOMETRY_REF_MISSING", "BACK_MATERIAL_MISSING"],
    "BACK_CONTRACT_ONLY_NOT_EXECUTABLE",
  ),
  componentFirstContractTemplate(
    5,
    "TPL-COMP-LETTER-RETURN-CANT_v1",
    "comp_letter_return_cant_v1",
    "structural return/cant",
    "structural",
    "components.return_cant.instances[]",
    [{ source_path: "components.face.confirmed_perimeter" }],
    ["SOURCE_FACE_PERIMETER_REF_MISSING", "MATERIAL_PROFILE_MISSING"],
    "RETURN_CANT_CONTRACT_ONLY_NOT_EXECUTABLE",
  ),
  componentFirstContractTemplate(
    6,
    "TPL-COMP-LETTER-LED_v1",
    "comp_letter_led_v1",
    "functional lighting",
    "functional",
    "components.led.instances[]",
    [{ source_path: "components.face.confirmed_area" }],
    ["LIGHTING_MODE_MISSING", "LED_DENSITY_CONFIG_MISSING"],
    "LED_CONTRACT_ONLY_NOT_EXECUTABLE",
  ),
  componentFirstContractTemplate(
    7,
    "TPL-COMP-LETTER-FINISH_v1",
    "comp_letter_finish_v1",
    "functional finish",
    "functional",
    "components.finish.instances[]",
    ["comp_letter_face_v1", "comp_letter_back_v1", "comp_letter_return_cant_v1"],
    ["FINISH_TARGET_MISSING", "FINISH_TYPE_MISSING"],
    "FINISH_CONTRACT_ONLY_NOT_EXECUTABLE",
  ),
  componentFirstContractTemplate(
    8,
    "TPL-COMP-LETTER-MOUNTING_v1",
    "comp_letter_mounting_v1",
    "functional mounting",
    "functional",
    "components.mounting.instances[]",
    [{ source_component_id: "comp_letter_back_v1" }, { source_path: "product.install_context" }],
    ["MOUNTING_MODE_MISSING", "INSTALL_CONTEXT_MISSING"],
    "MOUNTING_CONTRACT_ONLY_NOT_EXECUTABLE",
  ),
];

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

const componentFirstAvailability: ProductTemplateAvailabilityItem = {
  template_id: 2,
  template_code: "TPL-LETTERS-COMPOSER_v1",
  family_id: "litere_component_first_candidate",
  family_name: "Litere component-first candidate",
  description: "Inactive component-first letters composer",
  db_active: false,
  quote_offerable: false,
  runtime_module: false,
  is_parent: false,
  has_modules: false,
  parent_codes: [],
  module_codes: [],
  status: "archived",
  status_reason: "db_inactive",
  product_system_role: "archived_experimental",
  display_group: "archived_experimental",
  importance_rank: 80,
  owner_decision_required: true,
  readiness_reason: "Inactive candidate / readonly only.",
  ui_label: "Catalog entry inactiv",
  ui_description: "Nu apare in Work Intake.",
  parent_product_codes: [],
  child_module_codes: [],
  shared_with_product_codes: [],
  composition_modules: [],
  shared_component_contracts: [],
};

describe("ProductSystem design-system badges", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTemplateList.mockResolvedValue([volumetricTemplate, ...componentFirstTemplates]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability, componentFirstAvailability], total: 2 });
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
    const truthContainer = screen.getByTestId("product-system-return-cant-truth-container");

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
    expect(truthContainer).toBeInTheDocument();
    expect(truthContainer).toHaveTextContent("components.return_cant.instances[]");
    expect(truthContainer).toHaveTextContent("source_face_perimeter_ref");
    expect(screen.getByTestId("product-system-return-cant-face-dependency")).toHaveTextContent("components.face.confirmed_perimeter");
    expect(screen.getByTestId("product-system-return-cant-legacy-alias")).toHaveTextContent("components.returnCant.depthMm");
    expect(truthContainer).toHaveTextContent("status: BLOCKED");
    expect(truthContainer).toHaveTextContent("component_template_code");
    expect(truthContainer).toHaveTextContent("resource_requirements_ref");
    expect(truthContainer).toHaveTextContent("component dependency anchor");
    expect(truthContainer).toHaveTextContent("Form System capture");
    expect(truthContainer).toHaveTextContent("root geometry context");
    expect(truthContainer).toHaveTextContent("quote_geometry.letter_perimeter_m");
    expect(truthContainer).toHaveTextContent("confirmed_perimeter_m");
    expect(truthContainer).not.toHaveTextContent("confirmed_perimeter_m confirmed");
    expect(screen.getByTestId("product-system-return-cant-aggregate-boundary")).toHaveTextContent("ProductAggregate is derived read model");
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
    expect(truthContainer).toHaveTextContent("perimeter_source");
    expect(screen.getAllByText(/parent aggregate only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/form system only/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/component-owned source missing/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/source not wired yet/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/component-owned source missing/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/calculation blocked until component-scoped confirmation exists/i)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByText(/ready for future calculation/i)).not.toBeInTheDocument();
  });

  it("shows the inactive component-first letters set as readonly candidate with no activation controls", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-letters-set")).toBeInTheDocument();
    });

    const panel = screen.getByTestId("product-system-component-first-letters-set");
    const composerCard = screen.getByTestId("product-system-component-first-composer-card");
    const dependencyGraph = screen.getByTestId("product-system-component-first-dependency-graph");
    const componentsList = screen.getByTestId("product-system-component-first-components-list");

    expect(panel).toHaveTextContent("Component-first letters template set");
    expect(panel).toHaveTextContent("INACTIVE");
    expect(panel).toHaveTextContent("CANDIDATE");
    expect(panel).toHaveTextContent("READONLY");
    expect(screen.getByTestId("product-system-component-first-source-label")).toHaveTextContent("LIVE SEEDED INACTIVE ROWS");
    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("completeness: 7/7");
    expect(screen.queryByTestId("product-system-component-first-missing-rows")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-component-first-invalid-active-rows")).not.toBeInTheDocument();
    expect(panel).toHaveTextContent("active = false");
    expect(panel).toHaveTextContent("No Work Intake exposure: true");
    expect(panel).toHaveTextContent("No Pricing activation: true");
    expect(panel).toHaveTextContent("No ProductDefinition activation: true");
    expect(panel).toHaveTextContent("No ProductAggregate runtime wiring: true");
    expect(panel).toHaveTextContent("No executable operations: true");
    expect(panel).toHaveTextContent("No executable BOM: true");

    expect(composerCard).toHaveTextContent("TPL-LETTERS-COMPOSER_v1");
    expect(composerCard).toHaveTextContent("Product Template / composer only");
    expect(composerCard).toHaveTextContent("does not own material truth");
    expect(composerCard).toHaveTextContent("does not own operation truth");
    expect(composerCard).toHaveTextContent("no module links: true");

    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-FACE_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-BACK_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-RETURN-CANT_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-LED_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-FINISH_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-MOUNTING_v1");
    expect(componentsList).toHaveTextContent("comp_letter_face_v1");
    expect(componentsList).toHaveTextContent("comp_letter_back_v1");
    expect(componentsList).toHaveTextContent("components.face.instances[]");
    expect(componentsList).toHaveTextContent("components.return_cant.instances[]");
    expect(componentsList).toHaveTextContent("components.led.instances[]");
    expect(componentsList).toHaveTextContent("components.finish.instances[]");
    expect(componentsList).toHaveTextContent("components.mounting.instances[]");

    expect(dependencyGraph).toHaveTextContent("comp_letter_face_v1 -> comp_letter_return_cant_v1");
    expect(dependencyGraph).toHaveTextContent("comp_letter_face_v1 -> comp_letter_back_v1");
    expect(dependencyGraph).toHaveTextContent("comp_letter_face_v1 -> comp_letter_led_v1");
    expect(dependencyGraph).toHaveTextContent("comp_letter_back_v1 -> comp_letter_mounting_v1");
    expect(dependencyGraph).toHaveTextContent("product_root -> comp_letter_mounting_v1");

    expect(screen.queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /pricing/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /create quote/i })).not.toBeInTheDocument();
  });

  it("shows CODE CONTRACT FALLBACK when no component-first live rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-letters-set")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-component-first-source-label")).toHaveTextContent("CODE CONTRACT FALLBACK");
    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("completeness: 0/7");
    expect(screen.getByTestId("product-system-component-first-missing-rows")).toHaveTextContent("TPL-LETTERS-COMPOSER_v1");
    expect(screen.getByTestId("product-system-component-first-missing-rows")).toHaveTextContent("TPL-COMP-LETTER-MOUNTING_v1");
  });

  it("shows PARTIAL LIVE INACTIVE ROWS when only some expected rows exist", async () => {
    mockTemplateList.mockResolvedValue([
      volumetricTemplate,
      componentFirstComposerTemplate,
      componentFirstTemplates[1],
      componentFirstTemplates[2],
    ]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, componentFirstAvailability],
      total: 2,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-source-label")).toHaveTextContent("PARTIAL LIVE INACTIVE ROWS");
    });

    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("completeness: 3/7");
    expect(screen.getByTestId("product-system-component-first-missing-rows")).toHaveTextContent("TPL-COMP-LETTER-RETURN-CANT_v1");
    expect(screen.getByTestId("product-system-component-first-missing-rows")).toHaveTextContent("TPL-COMP-LETTER-MOUNTING_v1");
    expect(screen.getByTestId("product-system-component-first-component-TPL-COMP-LETTER-FACE_v1")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-component-TPL-COMP-LETTER-LED_v1")).toHaveTextContent("contract fallback row");
  });

  it("shows BLOCKED / INVALID LIVE STATE when any expected row is active", async () => {
    const activeLeakComposer = {
      ...componentFirstComposerTemplate,
      active: true,
    };

    mockTemplateList.mockResolvedValue([volumetricTemplate, activeLeakComposer, ...componentFirstTemplates.slice(1)]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, { ...componentFirstAvailability, db_active: true }],
      total: 2,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-source-label")).toHaveTextContent("BLOCKED / INVALID LIVE STATE");
    });

    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("completeness: 7/7");
    expect(screen.getByTestId("product-system-component-first-invalid-active-rows")).toHaveTextContent("TPL-LETTERS-COMPOSER_v1");
    expect(screen.queryByTestId("product-system-component-first-source-label")).not.toHaveTextContent("LIVE SEEDED INACTIVE ROWS");
  });

  it("keeps component-first readonly panel free of activation controls across completeness states", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, componentFirstComposerTemplate, componentFirstTemplates[1]]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-letters-set")).toBeInTheDocument();
    });

    expect(screen.queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /pricing/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /create quote/i })).not.toBeInTheDocument();
  });

  it("shows contract check drift guard with OK status when fallback contract is valid and no live rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-drift-guard")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-component-first-contract-check")).toHaveTextContent("contract check: OK");
    expect(screen.getByTestId("product-system-component-first-drift-guard")).toHaveTextContent("drift: NO_DRIFT");
    expect(screen.getByTestId("product-system-component-first-drift-guard")).toHaveTextContent("live rows: 0/7");
    expect(screen.getByTestId("product-system-component-first-drift-guard")).toHaveTextContent("expected rows: 7");
  });

  it("shows WARNING contract check when live rows exist but metadata is unavailable", async () => {
    const sparseLiveRows = componentFirstTemplates.map((template) => ({
      ...template,
      family_id: undefined,
      family_name: undefined,
      notes: undefined,
      components_json: "[]",
    }));

    mockTemplateList.mockResolvedValue([volumetricTemplate, ...sparseLiveRows]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability, componentFirstAvailability], total: 2 });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-contract-check")).toHaveTextContent("contract check: WARNING");
    });

    expect(screen.getByTestId("product-system-component-first-metadata-warnings")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-drift-guard")).toHaveTextContent("live rows: 7/7");
    expect(screen.queryByTestId("product-system-component-first-drift-warnings")).not.toBeInTheDocument();
  });

  it("shows dossier alignment readonly contract with no runtime dossier linkage", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-dossier-alignment")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-component-first-dossier-contract-count")).toHaveTextContent("Dossier contract: 7/7");
    expect(screen.getByTestId("product-system-component-first-dossier-runtime-link")).toHaveTextContent("Runtime dossier rows: readonly contract only");
    expect(screen.getByTestId("product-system-component-first-dossier-alignment-state")).toHaveTextContent("Alignment: READONLY_FALLBACK_ONLY");
    expect(screen.getByTestId("product-system-component-first-dossier-truth-ownership")).toHaveTextContent("Composer = product orchestration only");
    expect(screen.getByTestId("product-system-component-first-dossier-truth-ownership")).toHaveTextContent("component-owned truth");
    expect(screen.getByTestId("product-system-component-first-dossier-guard")).toHaveTextContent("No task materialization");
    expect(screen.getByTestId("product-system-component-first-dossier-guard")).toHaveTextContent("No ProductAggregate runtime");
    expect(screen.queryByTestId("product-system-component-first-dossier-activation-leak")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
  });

  it("shows READONLY_ALIGNED dossier alignment when 7/7 live inactive rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, componentFirstComposerTemplate, ...componentFirstTemplates]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, componentFirstAvailability],
      total: 2,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-dossier-alignment-state")).toHaveTextContent("Alignment: READONLY_ALIGNED");
    });

    expect(screen.getByTestId("product-system-component-first-dossier-contract-count")).toHaveTextContent("Dossier contract: 7/7");
    expect(screen.getByTestId("product-system-component-first-dossier-runtime-link")).toHaveTextContent("Runtime dossier rows: not linked yet");
    expect(screen.queryByTestId("product-system-component-first-dossier-activation-leak")).not.toBeInTheDocument();
  });

  it("shows BLOCKED dossier alignment when any expected row is active", async () => {
    const activeLeakComposer = {
      ...componentFirstComposerTemplate,
      active: true,
    };

    mockTemplateList.mockResolvedValue([volumetricTemplate, activeLeakComposer, ...componentFirstTemplates.slice(1)]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, { ...componentFirstAvailability, db_active: true }],
      total: 2,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-dossier-alignment-state")).toHaveTextContent("Alignment: BLOCKED_INVALID_LIVE_STATE");
    });
  });

  it("shows owner review card for 0/7 fallback with safe readonly wording", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-owner-review")).toBeInTheDocument();
    });

    const ownerCard = screen.getByTestId("product-system-component-first-owner-review");
    expect(screen.getByTestId("product-system-component-first-owner-status-title")).toHaveTextContent("Safe readonly contract");
    expect(ownerCard).toHaveTextContent("Live seeded rows:");
    expect(ownerCard).toHaveTextContent("0/7");
    expect(ownerCard).toHaveTextContent("Work Intake exposure:");
    expect(ownerCard).toHaveTextContent("no");
    expect(ownerCard).toHaveTextContent("Pricing / Quote / Order / Execution:");
    expect(ownerCard).toHaveTextContent("no");
    expect(ownerCard).toHaveTextContent("Cannot use in Work Intake");
    expect(ownerCard).not.toHaveTextContent("ready to quote");
    expect(ownerCard).not.toHaveTextContent("offerable");
    expect(ownerCard).not.toHaveTextContent("active product");
    expect(ownerCard).not.toHaveTextContent("available in Work Intake");
    expect(screen.queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
  });

  it("shows owner review complete-but-not-offerable when 7/7 inactive rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, componentFirstComposerTemplate, ...componentFirstTemplates]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, componentFirstAvailability],
      total: 2,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-owner-status-title")).toHaveTextContent("not offerable");
    });

    const ownerCard = screen.getByTestId("product-system-component-first-owner-review");
    expect(ownerCard).toHaveTextContent("7/7");
    expect(ownerCard).toHaveTextContent("Cannot create quote");
    expect(screen.getByTestId("product-system-component-first-drift-guard")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-dossier-alignment")).toBeInTheDocument();
  });

  it("shows owner review partial state when only some live rows exist", async () => {
    mockTemplateList.mockResolvedValue([
      volumetricTemplate,
      componentFirstComposerTemplate,
      componentFirstTemplates[1],
      componentFirstTemplates[2],
    ]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, componentFirstAvailability],
      total: 2,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-owner-status-title")).toHaveTextContent("Partial live rows");
    });

    expect(screen.getByTestId("product-system-component-first-owner-review")).toHaveTextContent("not complete");
  });

  it("shows owner review blocked state when any expected row is active", async () => {
    const activeLeakComposer = {
      ...componentFirstComposerTemplate,
      active: true,
    };

    mockTemplateList.mockResolvedValue([volumetricTemplate, activeLeakComposer, ...componentFirstTemplates.slice(1)]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, { ...componentFirstAvailability, db_active: true }],
      total: 2,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-owner-status-title")).toHaveTextContent("Blocked");
    });
  });

});
