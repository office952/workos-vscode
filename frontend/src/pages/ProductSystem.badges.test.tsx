import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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

const COMPONENT_FIRST_TAB = {
  overview: "product-system-component-first-tab-overview",
  components: "product-system-component-first-tab-components",
  dossier: "product-system-component-first-tab-dossier",
  guardsAudit: "product-system-component-first-tab-guards-audit",
} as const;

const UNIFIED_FILTER = {
  all: "product-system-filter-all",
  currentProducts: "product-system-filter-current-products",
  candidateProducts: "product-system-filter-candidate-products",
  componentFirstSets: "product-system-filter-component-first-sets",
  legacyModules: "product-system-filter-legacy-modules",
  archived: "product-system-filter-archived",
  blocked: "product-system-filter-blocked",
} as const;

const CATALOG_BUCKET = {
  currentProducts: "product-system-catalog-bucket-current-products",
  candidateProducts: "product-system-catalog-bucket-candidate-products",
  componentFirstSets: "product-system-catalog-bucket-component-first-sets",
  legacyModules: "product-system-catalog-bucket-legacy-shared-modules",
  archived: "product-system-catalog-bucket-archived",
} as const;

function openUnifiedFilter(filterTestId: string) {
  fireEvent.click(screen.getByTestId(filterTestId));
}

function openComponentFirstTab(tabTestId: string) {
  fireEvent.click(screen.getByTestId(tabTestId));
}

async function openComponentFirstCandidateDetail() {
  await waitFor(() => {
    expect(screen.getByTestId("product-system-unified-catalog")).toBeInTheDocument();
  });
  const componentFirstBucket = screen.getByTestId(CATALOG_BUCKET.componentFirstSets);
  if (componentFirstBucket.getAttribute("data-expanded") !== "true") {
    await expandCatalogBucketAsync(
      CATALOG_BUCKET.componentFirstSets,
      "product-system-catalog-bucket-toggle-component-first-sets",
    );
  }
  await waitFor(() => {
    expect(screen.getByTestId("product-system-unified-row-candidate-set")).toBeInTheDocument();
  });
  fireEvent.click(screen.getByTestId("product-system-unified-row-candidate-set"));
  await waitFor(() => {
    expect(screen.getByTestId("product-system-component-first-letters-set")).toBeInTheDocument();
  });
}

function expandCatalogBucket(bucketTestId: string, toggleTestId: string) {
  const bucket = screen.getByTestId(bucketTestId);
  if (bucket.getAttribute("data-expanded") !== "true") {
    fireEvent.click(screen.getByTestId(toggleTestId));
  }
}

async function expandCatalogBucketAsync(bucketTestId: string, toggleTestId: string) {
  await waitFor(() => {
    expect(screen.getByTestId(bucketTestId)).toBeInTheDocument();
  });
  const bucket = screen.getByTestId(bucketTestId);
  if (bucket.getAttribute("data-expanded") !== "true") {
    fireEvent.click(screen.getByTestId(toggleTestId));
    await waitFor(() => {
      expect(bucket).toHaveAttribute("data-expanded", "true");
    });
  }
}

function openCandidateGuardsReadiness() {
  openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);
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

const logoTemplate: ProductTemplateEntity = {
  id: 10,
  template_code: "TPL-VOLUMETRIC-LOGO_v1",
  family_name: "Logo volumetric",
  active: true,
  components_json: "[]",
  operations_json: "[]",
  required_materials_json: "[]",
};

const logoAvailability: ProductTemplateAvailabilityItem = {
  template_id: 10,
  template_code: "TPL-VOLUMETRIC-LOGO_v1",
  family_id: "volumetric",
  family_name: "Logo volumetric",
  description: "Logo candidate product",
  db_active: true,
  quote_offerable: false,
  runtime_module: false,
  is_parent: true,
  has_modules: true,
  parent_codes: [],
  module_codes: [],
  status: "candidate",
  status_reason: "owner_go_required",
  product_system_role: "candidate_product",
  display_group: "candidate_products",
  importance_rank: 20,
  owner_decision_required: true,
  readiness_reason: "Candidate product — linked/analyzer only.",
  ui_label: "Candidat compozitie logo",
  ui_description: "Nu porneste oferta directa in Work Intake.",
  parent_product_codes: [],
  child_module_codes: [],
  shared_with_product_codes: [],
  composition_modules: [],
  shared_component_contracts: [],
};

const legacyFaceTemplate: ProductTemplateEntity = {
  id: 11,
  template_code: "TPL-VOLUMETRIC-FACE_v1",
  family_name: "Volumetric face module",
  active: true,
  components_json: "[]",
  operations_json: "[]",
  required_materials_json: "[]",
};

const legacyFaceAvailability: ProductTemplateAvailabilityItem = {
  template_id: 11,
  template_code: "TPL-VOLUMETRIC-FACE_v1",
  family_id: "volumetric",
  family_name: "Face module",
  description: "Legacy shared face module",
  db_active: true,
  quote_offerable: false,
  runtime_module: true,
  is_parent: false,
  has_modules: false,
  parent_codes: ["TPL-VOLUMETRIC-LETTERS_v2"],
  module_codes: [],
  status: "internal",
  status_reason: "legacy_module",
  product_system_role: "internal_module",
  display_group: "internal_modules",
  importance_rank: 40,
  owner_decision_required: false,
  readiness_reason: "Legacy internal module used by parent product.",
  ui_label: "Modul intern",
  ui_description: "Folosit de produs parinte.",
  parent_product_codes: ["TPL-VOLUMETRIC-LETTERS_v2"],
  child_module_codes: [],
  shared_with_product_codes: ["TPL-VOLUMETRIC-LOGO_v1"],
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
      expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    const sourceBadge = document.querySelector('[data-source="db"]');
    expect(sourceBadge).toBeTruthy();
    expect(sourceBadge?.textContent).toMatch(/Live DB/i);
  });

  it("renders active template status badge from design-system", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2"));

    await waitFor(() => {
      expect(screen.getByTestId("product-system-template-detail-panel")).toBeInTheDocument();
    });

    const activeBadge = document.querySelector('[data-status-domain="productSystem"][data-status="active"]');
    expect(activeBadge).toBeTruthy();
    expect(activeBadge).toHaveAttribute("data-status", "active");
    expect(activeBadge).toHaveAttribute("data-status-tone", "emerald");
  });

  it("keeps TPL-VOLUMETRIC-LETTERS_v2 visible in library", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    expect(screen.getByRole("heading", { name: "Product System" })).toBeInTheDocument();
  });

  it("shows the component ownership matrix with honest cant blockers and no promote CTA", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2-action-open"));

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

    await openComponentFirstCandidateDetail();

    const panel = screen.getByTestId("product-system-component-first-letters-set");

    expect(panel).toHaveTextContent("Component-first Letters Candidate");
    expect(panel).toHaveTextContent("INACTIVE");
    expect(panel).toHaveTextContent("CANDIDATE");
    expect(panel).toHaveTextContent("READONLY");
    expect(screen.getByTestId("product-system-component-first-not-offerable")).toHaveTextContent("NOT OFFERABLE");
    expect(screen.getByTestId("product-system-component-first-source-label")).toHaveTextContent("LIVE SEEDED INACTIVE ROWS");
    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("Live rows: 7/7");
    expect(screen.queryByTestId("product-system-component-first-missing-rows")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-component-first-invalid-active-rows")).not.toBeInTheDocument();
    expect(panel).toHaveTextContent("active = false");
    expect(screen.getByTestId("product-system-component-first-forbidden-summary")).toHaveTextContent("Not exposed in Work Intake");
    expect(screen.getByTestId("product-system-component-first-forbidden-summary")).toHaveTextContent("No Pricing / Quote / Order / Execution");

    openComponentFirstTab(COMPONENT_FIRST_TAB.components);
    const composerCard = screen.getByTestId("product-system-component-first-composer-card");
    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);
    const dependencyGraph = screen.getByTestId("product-system-component-first-dependency-graph");
    openComponentFirstTab(COMPONENT_FIRST_TAB.components);
    const componentsList = screen.getByTestId("product-system-component-first-components-list");

    expect(composerCard).toHaveTextContent("TPL-LETTERS-COMPOSER_v1");
    expect(composerCard).toHaveTextContent("Composer — coordinates components only");
    expect(composerCard).toHaveTextContent("does not own material truth");
    expect(composerCard).toHaveTextContent("does not own operation truth");
    expect(composerCard).toHaveTextContent("no module links: true");

    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-FACE_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-BACK_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-RETURN-CANT_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-LED_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-FINISH_v1");
    expect(componentsList).toHaveTextContent("TPL-COMP-LETTER-MOUNTING_v1");
    expect(screen.getByTestId("product-system-component-first-components-table")).toBeInTheDocument();

    expect(dependencyGraph).toHaveTextContent("comp_letter_face_v1 -> comp_letter_return_cant_v1");
    expect(dependencyGraph).toHaveTextContent("comp_letter_face_v1 -> comp_letter_back_v1");
    expect(dependencyGraph).toHaveTextContent("comp_letter_face_v1 -> comp_letter_led_v1");
    expect(dependencyGraph).toHaveTextContent("comp_letter_back_v1 -> comp_letter_mounting_v1");
    expect(dependencyGraph).toHaveTextContent("product_root -> comp_letter_mounting_v1");

    expect(within(panel).queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /^pricing$/i })).not.toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /create quote/i })).not.toBeInTheDocument();
  });

  it("shows CODE CONTRACT FALLBACK when no component-first live rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId("product-system-component-first-source-label")).toHaveTextContent("CODE CONTRACT FALLBACK");
    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("Live rows: 0/7");
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

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId("product-system-component-first-source-label")).toHaveTextContent("PARTIAL LIVE INACTIVE ROWS");

    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("Live rows: 3/7");
    openComponentFirstTab(COMPONENT_FIRST_TAB.overview);
    expect(screen.getByTestId("product-system-component-first-missing-rows")).toHaveTextContent("TPL-COMP-LETTER-RETURN-CANT_v1");
    expect(screen.getByTestId("product-system-component-first-missing-rows")).toHaveTextContent("TPL-COMP-LETTER-MOUNTING_v1");
    openComponentFirstTab(COMPONENT_FIRST_TAB.components);
    expect(screen.getByTestId("product-system-component-first-component-row-TPL-COMP-LETTER-FACE_v1")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-component-row-TPL-COMP-LETTER-LED_v1")).toBeInTheDocument();
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

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId("product-system-component-first-source-label")).toHaveTextContent("BLOCKED / INVALID LIVE STATE");

    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("Live rows: 7/7");
    expect(screen.getByTestId("product-system-component-first-invalid-active-rows")).toHaveTextContent("TPL-LETTERS-COMPOSER_v1");
    expect(screen.queryByTestId("product-system-component-first-source-label")).not.toHaveTextContent("LIVE SEEDED INACTIVE ROWS");
  });

  it("keeps component-first readonly panel free of activation controls across completeness states", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, componentFirstComposerTemplate, componentFirstTemplates[1]]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    const panel = screen.getByTestId("product-system-component-first-letters-set");
    expect(within(panel).queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /^pricing$/i })).not.toBeInTheDocument();
    expect(within(panel).queryByRole("button", { name: /create quote/i })).not.toBeInTheDocument();
  });

  it("shows contract check drift guard with OK status when fallback contract is valid and no live rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

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

    await openComponentFirstCandidateDetail();

    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

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

    await openComponentFirstCandidateDetail();

    openComponentFirstTab(COMPONENT_FIRST_TAB.dossier);

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
    expect(screen.getByTestId("product-system-component-first-dossier-section")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-dossier-composer-card")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-dossier-cards")).toBeInTheDocument();
    expect(screen.getAllByTestId(/^product-system-component-first-dossier-card-/).length).toBe(6);
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

    await openComponentFirstCandidateDetail();

    openComponentFirstTab(COMPONENT_FIRST_TAB.dossier);

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

    await openComponentFirstCandidateDetail();

    openComponentFirstTab(COMPONENT_FIRST_TAB.dossier);

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-dossier-alignment-state")).toHaveTextContent("Alignment: BLOCKED_INVALID_LIVE_STATE");
    });
  });

  it("shows owner review card for 0/7 fallback with safe readonly wording", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

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

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId("product-system-component-first-owner-status-title")).toHaveTextContent("not offerable");

    const ownerCard = screen.getByTestId("product-system-component-first-owner-review");
    expect(ownerCard).toHaveTextContent("7/7");
    expect(ownerCard).toHaveTextContent("cannot create quote");
    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);
    expect(screen.getByTestId("product-system-component-first-drift-guard")).toBeInTheDocument();
    openComponentFirstTab(COMPONENT_FIRST_TAB.dossier);
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

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId("product-system-component-first-owner-status-title")).toHaveTextContent("Partial live rows");

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

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId("product-system-component-first-owner-status-title")).toHaveTextContent("Blocked");
  });

  it("shows Form System readiness block for 0/7 fallback without live form activation", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openCandidateGuardsReadiness();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-form-system-readiness")).toBeInTheDocument();
    });

    const formBlock = screen.getByTestId("product-system-component-first-form-system-readiness");
    expect(screen.getByTestId("product-system-component-first-form-readiness-contract-count")).toHaveTextContent("Readiness contract: 7/7");
    expect(screen.getByTestId("product-system-component-first-form-runtime-link")).toHaveTextContent("readonly contract only");
    expect(screen.getByTestId("product-system-component-first-form-readiness-state")).toHaveTextContent("READONLY_FALLBACK_ONLY");
    expect(formBlock).toHaveTextContent("no Work Intake exposure");
    expect(formBlock).toHaveTextContent("no Product Truth write");
    expect(formBlock).toHaveTextContent("TPL-COMP-LETTER-FACE_v1");
    expect(formBlock).toHaveTextContent("TPL-COMP-LETTER-RETURN-CANT_v1");
    expect(formBlock).not.toHaveTextContent("ready to quote");
    expect(formBlock).not.toHaveTextContent("offerable");
    expect(formBlock.querySelector("input")).toBeNull();
    expect(formBlock.querySelector("select")).toBeNull();
    expect(screen.queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
  });

  it("shows owner review and Form System readiness folded into Guards tab", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openCandidateGuardsReadiness();
    expect(screen.getByTestId("product-system-component-first-form-system-readiness")).toBeInTheDocument();
  });

  it("shows READONLY_READY_FOR_MAPPING when 7/7 inactive rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, componentFirstComposerTemplate, ...componentFirstTemplates]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, componentFirstAvailability],
      total: 2,
    });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openCandidateGuardsReadiness();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-form-readiness-state")).toHaveTextContent("READONLY_READY_FOR_MAPPING");
    });

    expect(screen.getByTestId("product-system-component-first-form-runtime-link")).toHaveTextContent("not linked yet");
  });

  it("shows Product Truth mapping block for 0/7 fallback without write path", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openCandidateGuardsReadiness();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-product-truth-mapping")).toBeInTheDocument();
    });

    const mappingBlock = screen.getByTestId("product-system-component-first-product-truth-mapping");
    expect(screen.getByTestId("product-system-component-first-product-truth-mapping-count")).toHaveTextContent("Mapping contract:");
    expect(screen.getByTestId("product-system-component-first-product-truth-runtime-link")).toHaveTextContent("readonly mapping only");
    expect(screen.getByTestId("product-system-component-first-product-truth-mapping-state")).toHaveTextContent("READONLY_MAPPING_FALLBACK_ONLY");
    expect(screen.getByTestId("product-system-component-first-product-truth-write-policy")).toHaveTextContent("no Product Truth write");
    expect(screen.getByTestId("product-system-component-first-product-truth-state-policy")).toHaveTextContent("suggested != confirmed");
    expect(mappingBlock).toHaveTextContent("product.components.face.material");
    expect(mappingBlock).toHaveTextContent("product.components.led.type");
    expect(mappingBlock).not.toHaveTextContent("Product Truth confirmed");
    expect(mappingBlock.querySelector("input")).toBeNull();
    expect(mappingBlock.querySelector("select")).toBeNull();
    expect(screen.queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
  });

  it("shows Form readiness and Product Truth mapping folded into Guards tab", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openCandidateGuardsReadiness();
    expect(screen.getByTestId("product-system-component-first-form-system-readiness")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-product-truth-mapping")).toBeInTheDocument();
  });

  it("shows READONLY_MAPPING_READY when 7/7 inactive rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, componentFirstComposerTemplate, ...componentFirstTemplates]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, componentFirstAvailability],
      total: 2,
    });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openCandidateGuardsReadiness();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-product-truth-mapping-state")).toHaveTextContent("READONLY_MAPPING_READY");
    });

    expect(screen.getByTestId("product-system-component-first-product-truth-runtime-link")).toHaveTextContent("not linked yet");
  });

  it("shows ProductDefinition readiness block for 0/7 fallback without runtime activation", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-product-definition-readiness")).toBeInTheDocument();
    });

    const pdBlock = screen.getByTestId("product-system-component-first-product-definition-readiness");
    expect(screen.getByTestId("product-system-component-first-product-definition-paths-count")).toHaveTextContent("29/29 paths");
    expect(screen.getByTestId("product-system-component-first-product-definition-runtime-link")).toHaveTextContent("readonly contract only");
    expect(screen.getByTestId("product-system-component-first-product-definition-readiness-state")).toHaveTextContent("READONLY_CONSUMPTION_FALLBACK_ONLY");
    expect(screen.getByTestId("product-system-component-first-product-definition-missing-behavior")).toHaveTextContent("do not invent");
    expect(screen.getByTestId("product-system-component-first-product-definition-state-policy")).toHaveTextContent("suggested/fallback/hydrated/manual draft");
    expect(pdBlock).toHaveTextContent("FACE required paths");
    expect(pdBlock).toHaveTextContent("LED required paths");
    expect(pdBlock).not.toHaveTextContent("ready to quote");
    expect(pdBlock).not.toHaveTextContent("TaskGraph active");
    expect(pdBlock.querySelector("input")).toBeNull();
    expect(pdBlock.querySelector("select")).toBeNull();
    expect(screen.queryByRole("button", { name: /write/i })).not.toBeInTheDocument();
  });

  it("shows Product Truth mapping and ProductDefinition readiness in Guards tab", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId(COMPONENT_FIRST_TAB.guardsAudit)).toBeInTheDocument();

    openCandidateGuardsReadiness();
    expect(screen.getByTestId("product-system-component-first-product-truth-mapping")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-product-definition-readiness")).toBeInTheDocument();
  });

  it("shows READONLY_CONSUMPTION_READY when 7/7 inactive rows exist", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, componentFirstComposerTemplate, ...componentFirstTemplates]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, componentFirstAvailability],
      total: 2,
    });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-product-definition-readiness-state")).toHaveTextContent("READONLY_CONSUMPTION_READY");
    });

    expect(screen.getByTestId("product-system-component-first-product-definition-runtime-link")).toHaveTextContent("not linked yet");
  });

  it("shows unified catalog with volumetric and candidate rows in bucketed surface", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-catalog-overview")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("product-system-primary-tabs")).not.toBeInTheDocument();
    expect(screen.getByTestId("product-system-unified-catalog")).toBeInTheDocument();
    expect(screen.getByTestId(CATALOG_BUCKET.currentProducts)).toBeInTheDocument();
    expect(screen.getByTestId(CATALOG_BUCKET.componentFirstSets)).toBeInTheDocument();
    await expandCatalogBucketAsync(
      CATALOG_BUCKET.componentFirstSets,
      "product-system-catalog-bucket-toggle-component-first-sets",
    );
    expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-unified-row-candidate-set")).toBeInTheDocument();
    expect(screen.queryByTestId("product-system-existing-roots")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-dossiers-tab-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-guards-audit-tab-panel")).not.toBeInTheDocument();
  });

  it("exposes four component-first candidate detail tabs", async () => {
    renderProductSystem();

    await openComponentFirstCandidateDetail();

    for (const tabId of Object.values(COMPONENT_FIRST_TAB)) {
      expect(screen.getByTestId(tabId)).toBeInTheDocument();
    }
    expect(screen.queryByTestId("product-system-component-first-tab-form-system")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-component-first-tab-product-truth")).not.toBeInTheDocument();
  });

  it("keeps dangerous offerable wording out of candidate panel context", async () => {
    renderProductSystem();

    await openComponentFirstCandidateDetail();

    const candidatePanel = screen.getByTestId("product-system-component-first-letters-set");
    expect(candidatePanel).not.toHaveTextContent("ready to quote");
    expect(candidatePanel).not.toHaveTextContent("active product");
    expect(candidatePanel).not.toHaveTextContent("available in Work Intake");
    expect(candidatePanel).not.toHaveTextContent("live form");
    expect(candidatePanel).not.toHaveTextContent("production ready");
  });

  it("shows unified candidate detail with composer summary, six component rows, and readonly settings drawers", async () => {
    renderProductSystem();

    await expandCatalogBucketAsync(
      CATALOG_BUCKET.componentFirstSets,
      "product-system-catalog-bucket-toggle-component-first-sets",
    );
    await waitFor(() => {
      expect(screen.getByTestId("product-system-unified-row-candidate-set")).toBeInTheDocument();
    });
    expect(screen.getByTestId("product-system-unified-row-candidate-set-action-open")).toHaveTextContent("Open");
    fireEvent.click(screen.getByTestId("product-system-unified-row-candidate-set-action-more"));
    expect(screen.getByTestId("product-system-unified-row-candidate-set-action-settings")).toHaveTextContent("Settings");
    expect(screen.getByTestId("product-system-unified-row-candidate-set-action-dossier")).toHaveTextContent("Dossier");

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId("product-system-component-first-product-card")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-view-product-settings")).toBeInTheDocument();

    openComponentFirstTab(COMPONENT_FIRST_TAB.components);
    expect(screen.getByTestId("product-system-component-first-composer-card")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-components-table")).toBeInTheDocument();
    expect(screen.getAllByTestId(/^product-system-component-first-component-row-TPL-COMP-LETTER-/).length).toBe(6);

    const faceCode = "TPL-COMP-LETTER-FACE_v1";
    const ledCode = "TPL-COMP-LETTER-LED_v1";
    expect(screen.getByTestId(`product-system-component-first-view-component-settings-${faceCode}`)).toBeInTheDocument();
    expect(screen.getByTestId(`product-system-component-first-view-dossier-${faceCode}`)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("product-system-component-first-view-product-settings"));
    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-settings-sheet")).toBeInTheDocument();
    });
    expect(screen.getByTestId("product-system-component-first-readonly-drawer-banner")).toHaveTextContent(
      "READONLY · NO SAVE · NO WRITE",
    );
    expect(screen.getByTestId("product-system-component-first-settings-sheet")).toHaveTextContent(
      "Product Settings — TPL-LETTERS-COMPOSER_v1",
    );
    expect(screen.queryByRole("button", { name: /^save$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^edit$/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId(`product-system-component-first-view-component-settings-${faceCode}`));
    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-settings-sheet")).toHaveTextContent(
        "Component Settings — Face",
      );
    });
    expect(screen.getByTestId("product-system-component-first-readonly-drawer-banner")).toBeVisible();

    fireEvent.click(screen.getByTestId(`product-system-component-first-view-component-settings-${ledCode}`));
    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-settings-sheet")).toHaveTextContent(
        "Component Settings — LED",
      );
    });

    openComponentFirstTab(COMPONENT_FIRST_TAB.dossier);
    expect(screen.getByTestId("product-system-component-first-dossier-workspace")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-component-first-dossier-composer-card")).toBeInTheDocument();
    expect(screen.getAllByTestId(/^product-system-component-first-dossier-card-/).length).toBe(6);

    openComponentFirstTab(COMPONENT_FIRST_TAB.components);
    fireEvent.click(screen.getByTestId(`product-system-component-first-view-dossier-${faceCode}`));
    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-panel-dossier")).toBeInTheDocument();
      expect(screen.getByTestId(`product-system-component-first-dossier-card-${faceCode}`)).toHaveAttribute(
        "data-focused",
        "true",
      );
    });
    expect(screen.getByTestId(`product-system-component-first-dossier-focused-label-${faceCode}`)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId(`product-system-component-first-dossier-focus-${faceCode}`));
    await waitFor(() => {
      expect(screen.getByTestId(`product-system-component-first-dossier-card-${faceCode}`)).toHaveAttribute(
        "data-focused",
        "true",
      );
    });
    expect(screen.getByTestId("product-system-component-first-panel-dossier")).toBeInTheDocument();

    openComponentFirstTab(COMPONENT_FIRST_TAB.overview);
    expect(screen.getByTestId("product-system-component-first-product-card")).toHaveTextContent("NOT OFFERABLE");

    expect(screen.getByTestId("product-system-candidate-sets")).toBeInTheDocument();
    expect(screen.queryByTestId("product-system-existing-roots")).not.toBeInTheDocument();

    expect(screen.queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /create quote/i })).not.toBeInTheDocument();
  });

  it("exposes unified catalog filter chips and master-detail without tab shell", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-summary-bar")).toBeInTheDocument();
    });

    expect(screen.queryByTestId("product-system-primary-tabs")).not.toBeInTheDocument();
    expect(screen.getByTestId("product-system-unified-filter-chips")).toBeInTheDocument();
    expect(screen.getByTestId(UNIFIED_FILTER.all)).toBeInTheDocument();
    expect(screen.getByTestId(UNIFIED_FILTER.currentProducts)).toBeInTheDocument();
    expect(screen.getByTestId(UNIFIED_FILTER.candidateProducts)).toBeInTheDocument();
    expect(screen.getByTestId(UNIFIED_FILTER.componentFirstSets)).toBeInTheDocument();
    expect(screen.getByTestId(UNIFIED_FILTER.legacyModules)).toBeInTheDocument();
    expect(screen.getByTestId(UNIFIED_FILTER.archived)).toBeInTheDocument();
    expect(screen.getByTestId(UNIFIED_FILTER.blocked)).toBeInTheDocument();
    expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(screen.queryByTestId("product-system-existing-roots")).not.toBeInTheDocument();

    openUnifiedFilter(UNIFIED_FILTER.componentFirstSets);
    expect(screen.getByTestId("product-system-unified-row-candidate-set")).toBeInTheDocument();

    openUnifiedFilter(UNIFIED_FILTER.currentProducts);
    expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();

    openUnifiedFilter(UNIFIED_FILTER.all);
    fireEvent.click(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2"));
    expect(screen.getByTestId("product-system-detail-panel")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-template-detail-panel")).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("product-system-unified-row-candidate-set"));
    expect(screen.getByTestId("product-system-candidate-sets")).toBeInTheDocument();
    expect(screen.queryByTestId("product-system-dossiers-tab-panel")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-guards-audit-tab-panel")).not.toBeInTheDocument();
  });

  it("groups catalog entries into lifecycle buckets with clear labels", async () => {
    mockTemplateList.mockResolvedValue([
      volumetricTemplate,
      logoTemplate,
      legacyFaceTemplate,
      componentFirstComposerTemplate,
      ...componentFirstTemplates,
    ]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, logoAvailability, legacyFaceAvailability, componentFirstAvailability],
      total: 4,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId(CATALOG_BUCKET.currentProducts)).toBeInTheDocument();
    });

    const currentBucket = screen.getByTestId(CATALOG_BUCKET.currentProducts);
    expect(currentBucket).toHaveAttribute("data-expanded", "true");

    const candidateBucket = screen.getByTestId(CATALOG_BUCKET.candidateProducts);
    expandCatalogBucket(CATALOG_BUCKET.candidateProducts, "product-system-catalog-bucket-toggle-candidate-products");
    expect(candidateBucket).toHaveAttribute("data-expanded", "true");
    expect(within(currentBucket).getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    expect(within(currentBucket).queryByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1")).not.toBeInTheDocument();

    const logoRow = within(candidateBucket).getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1");
    expect(logoRow).toHaveTextContent("Candidate product");
    expect(logoRow).toHaveTextContent("Not Work Intake");
    expect(logoRow).not.toHaveTextContent("Offerable");
    expect(logoRow).not.toHaveTextContent("Used today");

    const componentFirstBucket = screen.getByTestId(CATALOG_BUCKET.componentFirstSets);
    expandCatalogBucket(CATALOG_BUCKET.componentFirstSets, "product-system-catalog-bucket-toggle-component-first-sets");
    expect(componentFirstBucket).toHaveAttribute("data-expanded", "true");
    expect(within(componentFirstBucket).getByTestId("product-system-unified-row-candidate-set")).toBeInTheDocument();
    expect(within(componentFirstBucket).getByText(/NOT OFFERABLE/i)).toBeInTheDocument();
    expect(screen.queryByTestId("product-system-unified-row-TPL-COMP-LETTER-FACE_v1")).not.toBeInTheDocument();

    const legacyBucket = screen.getByTestId(CATALOG_BUCKET.legacyModules);
    expect(legacyBucket).toHaveAttribute("data-expanded", "false");
    fireEvent.click(screen.getByTestId("product-system-catalog-bucket-toggle-legacy-shared-modules"));
    await waitFor(() => {
      expect(legacyBucket).toHaveAttribute("data-expanded", "true");
    });
    const legacyRow = within(legacyBucket).getByTestId("product-system-unified-row-TPL-VOLUMETRIC-FACE_v1");
    expect(legacyRow).toHaveTextContent("Legacy internal module");
    expect(legacyRow).toHaveTextContent("Used by parent product");

    fireEvent.click(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2"));
    expect(screen.getByTestId("product-system-template-detail-bucket-headline")).toHaveTextContent(
      "Rădăcină activă · folosită azi",
    );

    fireEvent.click(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LOGO_v1"));
    expect(screen.getByTestId("product-system-template-detail-bucket-headline")).toHaveTextContent(
      "Produs candidate · fără Work Intake",
    );
    expect(screen.getByTestId("product-system-template-detail-overview")).toHaveTextContent("activare Logo");

    expect(screen.queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /promote/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /create quote/i })).not.toBeInTheDocument();
  });

  it("uses comfortable catalog layout with readable spacing and bucket context", async () => {
    mockTemplateList.mockResolvedValue([
      volumetricTemplate,
      logoTemplate,
      legacyFaceTemplate,
      componentFirstComposerTemplate,
      ...componentFirstTemplates,
    ]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, logoAvailability, legacyFaceAvailability, componentFirstAvailability],
      total: 4,
    });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-unified-catalog")).toHaveAttribute("data-layout", "comfortable");
    });

    expect(screen.getByTestId("product-system-catalog-toolbar")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-summary-bar")).toBeInTheDocument();
    expect(screen.getByTestId(CATALOG_BUCKET.legacyModules)).toHaveAttribute("data-expanded", "false");

    await waitFor(() => {
      expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2")).toBeInTheDocument();
    });
    const lettersRow = screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2");
    expect(within(lettersRow).getByRole("button", { name: "Open" })).toBeInTheDocument();
    fireEvent.click(within(lettersRow).getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2-action-more"));
    expect(screen.getByTestId("product-system-unified-row-TPL-VOLUMETRIC-LETTERS_v2-action-guards")).toBeInTheDocument();

    const currentBucket = screen.getByTestId(CATALOG_BUCKET.currentProducts);
    expect(currentBucket.className).not.toMatch(/border-l-emerald|border-l-cyan|border-l-amber/);
  });

  it("uses slim library header and single-line filter chip scroll", async () => {
    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-library-header")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-catalog-overview")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-unified-filter-chips-scroll")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-reload-icon")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /Blueprint Dossier/i })).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-library-create-template")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("product-system-library-more-menu"));
    expect(screen.getByTestId("product-system-library-blueprint-link")).toHaveTextContent("Blueprint Dossier");
    expect(screen.getByTestId("product-system-library-create-template")).toHaveTextContent("Șablon nou");
    expect(screen.getByTestId("product-system-library-design-time-note")).toHaveTextContent(
      "Admin design-time only",
    );
  });

  it("shows clarified catalog summary metrics for dossier contract vs live rows", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await waitFor(() => {
      expect(screen.getByTestId("product-system-summary-bar")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("product-system-summary-toggle"));

    await waitFor(() => {
      expect(screen.getByTestId("product-system-summary-dossier-contract")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-summary-dossier-contract")).toHaveTextContent("Dosare contract");
    expect(screen.getByTestId("product-system-summary-component-first-live-rows")).toHaveTextContent("0/7");
    expect(screen.getByTestId("product-system-summary-bar")).not.toHaveTextContent(/\b7 dosare\b/i);
    expect(screen.getByTestId("product-system-summary-bar")).toHaveTextContent(/dosare contract/i);

    fireEvent.click(screen.getByTestId("product-system-summary-toggle"));
    await waitFor(() => {
      expect(screen.getByTestId("product-system-summary-bar")).toHaveAttribute("data-expanded", "false");
    });
    expect(screen.getByTestId("product-system-summary-bar")).toHaveTextContent(/0\/7 randuri live/i);
  });

  it("shows blocked guard labels instead of confusing WI=true inert flags", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();
    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

    await waitFor(() => {
      expect(screen.getByTestId("product-system-component-first-inert-guard-labels")).toBeInTheDocument();
    });

    const guardLabels = screen.getByTestId("product-system-component-first-inert-guard-labels");
    expect(guardLabels).toHaveTextContent("Work Intake exposure: blocked");
    expect(guardLabels).toHaveTextContent("Pricing activation: blocked");
    expect(guardLabels).toHaveTextContent("ProductDefinition runtime: blocked");
    expect(guardLabels).toHaveTextContent("Quote/Order/Execution: blocked");
    expect(guardLabels.textContent).not.toMatch(/WI=true/i);
    expect(guardLabels.textContent).not.toMatch(/Pricing=true/i);
    expect(guardLabels.textContent).not.toMatch(/PD=true/i);
  });

  it("separates dossier contract from live rows in component-first overview", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();

    await openComponentFirstCandidateDetail();

    expect(screen.getByTestId("product-system-component-first-completeness-count")).toHaveTextContent("Live rows: 0/7");
    expect(screen.getByTestId("product-system-component-first-dossier-contract-summary")).toHaveTextContent(
      "Dossier contract: 7/7",
    );
    expect(screen.getByTestId("product-system-component-first-dossier-contract-summary")).toHaveTextContent(
      "Runtime dossier rows: not linked yet",
    );
  });

  it("shows legacy replacement readiness map with NOT READY FOR DELETE and zero delete-ready", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, legacyFaceTemplate]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, legacyFaceAvailability],
      total: 2,
    });

    renderProductSystem();

    await expandCatalogBucketAsync(CATALOG_BUCKET.legacyModules, "product-system-catalog-bucket-toggle-legacy-shared-modules");
    fireEvent.click(screen.getByTestId("product-system-legacy-bucket-view-replacement-map"));

    await waitFor(() => {
      expect(screen.getByTestId("product-system-legacy-replacement-readiness")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-legacy-replacement-global-verdict")).toHaveTextContent(
      "NOT READY FOR DELETE",
    );
    expect(screen.getByTestId("product-system-legacy-replacement-summary-delete-ready-count")).toHaveTextContent("0");

    const table = screen.getByTestId("product-system-legacy-replacement-table");
    expect(table).toHaveTextContent("TPL-VOLUMETRIC-FACE_v1");
    expect(table).toHaveTextContent("TPL-COMP-LETTER-FACE_v1");
    expect(table).toHaveTextContent("TPL-VOLUMETRIC-LED_v1");
    expect(table).toHaveTextContent("TPL-COMP-LETTER-LED_v1");
    expect(table).toHaveTextContent("TPL-VOLUM-ALUMINIU_v1");
    expect(table).toHaveTextContent("TPL-COMP-LETTER-RETURN-CANT_v1");
    expect(table.textContent?.match(/NO DELETE/g)?.length ?? 0).toBeGreaterThanOrEqual(7);
  });

  it("shows legacy bucket support copy and no delete actions", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, legacyFaceTemplate]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, legacyFaceAvailability],
      total: 2,
    });

    renderProductSystem();

    await expandCatalogBucketAsync(CATALOG_BUCKET.legacyModules, "product-system-catalog-bucket-toggle-legacy-shared-modules");

    expect(screen.getByTestId("product-system-legacy-bucket-support-copy")).toHaveTextContent(
      /Legacy support only/i,
    );
    expect(screen.getByTestId("product-system-legacy-bucket-support-copy")).toHaveTextContent(/not new component-first/i);
    expect(screen.queryByRole("button", { name: /^delete now$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /ready to delete/i })).not.toBeInTheDocument();
  });

  it("shows component-first replacement context as readonly without runtime replacement", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();
    await openComponentFirstCandidateDetail();

    const context = screen.getByTestId("product-system-component-first-replacement-context");
    expect(context).toHaveTextContent(/Nu înlocuiește runtime acum/i);
    expect(context).toHaveTextContent(/replacement map readonly/i);
    expect(screen.getByTestId("product-system-component-first-replaces-face")).toHaveTextContent(/FACE/i);
    expect(screen.getByTestId("product-system-component-first-replaces-back")).toHaveTextContent(/BACK/i);
    expect(screen.getByTestId("product-system-component-first-replaces-return-cant")).toHaveTextContent(/RETURN-CANT/i);
    expect(screen.getByTestId("product-system-component-first-replaces-led")).toHaveTextContent(/LED/i);
    expect(screen.getByTestId("product-system-component-first-replaces-finish")).toHaveTextContent(/FINISH/i);
    expect(screen.getByTestId("product-system-component-first-replaces-mounting")).toHaveTextContent(/MOUNTING/i);
  });

  it("keeps dangerous replacement wording out of legacy readiness UI", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate, legacyFaceTemplate]);
    mockAvailabilityList.mockResolvedValue({
      items: [volumetricAvailability, legacyFaceAvailability],
      total: 2,
    });

    renderProductSystem();

    await expandCatalogBucketAsync(CATALOG_BUCKET.legacyModules, "product-system-catalog-bucket-toggle-legacy-shared-modules");
    fireEvent.click(screen.getByTestId("product-system-legacy-bucket-view-replacement-map"));

    await waitFor(() => {
      expect(screen.getByTestId("product-system-legacy-replacement-readiness")).toBeInTheDocument();
    });

    const panel = screen.getByTestId("product-system-legacy-replacement-readiness");
    expect(panel.textContent?.toLowerCase()).not.toMatch(/ready to delete/);
    expect(panel.textContent?.toLowerCase()).not.toMatch(/migrated live/);
    expect(panel.textContent?.toLowerCase()).not.toMatch(/activated replacement/);
    expect(panel.textContent?.toLowerCase()).not.toMatch(/work intake exposed/);
    expect(panel.textContent?.toLowerCase()).not.toMatch(/make offerable/);
    expect(screen.queryByRole("button", { name: /activate/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /create quote/i })).not.toBeInTheDocument();
  });

  it("renders Product Truth owner workshop in component-first guards with RETURN-CANT priority", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();
    await openComponentFirstCandidateDetail();
    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

    await waitFor(() => {
      expect(screen.getByTestId("product-system-truth-owner-workshop")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-truth-workshop-global-status")).toHaveTextContent(
      "OWNER INPUT REQUIRED",
    );
    expect(screen.getByTestId("product-system-truth-workshop-disclaimer")).toHaveTextContent(
      /nu este Product Truth live/i,
    );
    expect(screen.getByTestId("product-system-truth-workshop-safety-copy")).toHaveTextContent(
      "No Product Truth write",
    );
    expect(screen.getByTestId("product-system-truth-workshop-safety-copy")).toHaveTextContent(
      "No Pricing activation",
    );
    expect(screen.getByTestId("product-system-truth-workshop-safety-copy")).toHaveTextContent(
      "No Work Intake exposure",
    );
    expect(screen.getByTestId("product-system-truth-workshop-tab-RETURN-CANT")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-truth-workshop-return-cant-finish-options")).toHaveTextContent(
      "Culoare Stock",
    );
    expect(screen.getByTestId("product-system-truth-workshop-return-cant-finish-options")).toHaveTextContent("Oracal");
    expect(screen.getByTestId("product-system-truth-workshop-return-cant-finish-options")).toHaveTextContent(
      "Vopsit RAL",
    );
    expect(screen.getByTestId("product-system-truth-workshop-owner-questions")).toHaveTextContent(
      "Întrebări pentru owner",
    );
    expect(screen.getByTestId("product-system-truth-workshop-fields-table-RETURN-CANT")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^save$/i })).not.toBeInTheDocument();
  });

  it("renders RETURN-CANT owner inputs panel with confirmed and missing sections", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();
    await openComponentFirstCandidateDetail();
    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

    await waitFor(() => {
      expect(screen.getByTestId("product-system-return-cant-owner-inputs")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-return-cant-owner-inputs-global-status")).toHaveTextContent(
      "OWNER INPUT REQUIRED",
    );
    expect(screen.getByTestId("product-system-return-cant-confirmed-so-far")).toHaveTextContent(
      /Confirmed so far/i,
    );
    expect(screen.getByTestId("product-system-return-cant-confirmed-so-far")).toHaveTextContent("Culoare Stock");
    expect(screen.getByTestId("product-system-return-cant-confirmed-so-far")).toHaveTextContent("Oracal");
    expect(screen.getByTestId("product-system-return-cant-confirmed-so-far")).toHaveTextContent("Vopsit RAL");
    expect(screen.getByTestId("product-system-return-cant-missing-before-pricing")).toHaveTextContent(
      /Still missing before pricing/i,
    );
    expect(screen.getByTestId("product-system-return-cant-missing-before-product-definition")).toHaveTextContent(
      /Still missing before ProductDefinition/i,
    );
    expect(screen.getByTestId("product-system-return-cant-owner-input-value-oracal_code_list")).toHaveTextContent(
      /Intake V6 colorRegistry/i,
    );
    expect(screen.getByTestId("product-system-return-cant-owner-inputs-safety")).toHaveTextContent(
      "No Product Truth live write",
    );
    expect(screen.getByTestId("product-system-return-cant-owner-inputs-safety")).toHaveTextContent(
      "No Pricing activation",
    );
    expect(screen.getByTestId("product-system-return-cant-owner-inputs-safety")).toHaveTextContent(
      "No Work Intake exposure",
    );
    const panel = screen.getByTestId("product-system-return-cant-owner-inputs");
    expect(panel.textContent).not.toMatch(/ORACAL-\d+/i);
  });

  it("renders RETURN-CANT catalog and price inputs panel with NOT READY FOR PRICING", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();
    await openComponentFirstCandidateDetail();
    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

    await waitFor(() => {
      expect(screen.getByTestId("product-system-return-cant-catalog-price-inputs")).toBeInTheDocument();
    });

    expect(screen.getByTestId("product-system-return-cant-catalog-price-global-status")).toHaveTextContent(
      /NOT READY FOR PRICING/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-ready-for-pricing")).toHaveTextContent(
      /Ready for pricing: NO/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-summary-pricing-active")).toHaveTextContent("0");
    expect(screen.getByTestId("product-system-return-cant-catalog-price-known-oracal_catalog_source")).toHaveTextContent(
      /Intake V6/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-known-ral_catalog_source")).toHaveTextContent(
      /Intake V6|ralColors/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-known-oracal_selector_source")).toHaveTextContent(
      /Intake V6|color registry/i,
    );
    expect(screen.getByTestId("product-system-return-cant-oracal-series-price-651")).toHaveTextContent(
      /MAT-ORACAL-651/i,
    );
    expect(screen.getByTestId("product-system-return-cant-oracal-series-price-641")).toHaveTextContent(
      /MAT-ORACAL-641/i,
    );
    expect(screen.getByTestId("product-system-return-cant-oracal-series-price-8500")).toHaveTextContent(
      /MAT-ORACAL-8500/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-ral_material_price_by_depth")).toHaveTextContent(
      /2\.00 EUR\/ml/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-ral_minimum_rule")).toHaveTextContent(
      /100 lei/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-ral_minimum_rule")).toHaveTextContent(
      /pe culoare RAL/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-value-ral_minimum_rule")).toHaveTextContent(
      /total material RAL \+ manoperă/i,
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveTextContent(
      "No Product Truth live write",
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveTextContent(
      "No Pricing activation",
    );
    expect(screen.getByTestId("product-system-return-cant-catalog-price-safety")).toHaveTextContent(
      "No Work Intake exposure",
    );
    const catalogPanel = screen.getByTestId("product-system-return-cant-catalog-price-inputs");
    expect(catalogPanel.textContent).toMatch(/MAT-ORACAL-641/);
    expect(catalogPanel.textContent).toMatch(/\/inventory\/pricing/i);
    expect(catalogPanel.textContent).not.toMatch(/8\.00 EUR\/mp|5\.00 EUR\/mp|13\.00 EUR\/mp/);
    expect(screen.queryByRole("button", { name: /^save$/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /apply/i })).not.toBeInTheDocument();
  });

  it("keeps legacy replacement NOT READY FOR DELETE alongside workshop panel", async () => {
    mockTemplateList.mockResolvedValue([volumetricTemplate]);
    mockAvailabilityList.mockResolvedValue({ items: [volumetricAvailability], total: 1 });

    renderProductSystem();
    await openComponentFirstCandidateDetail();
    openComponentFirstTab(COMPONENT_FIRST_TAB.guardsAudit);

    await waitFor(() => {
      expect(screen.getByTestId("product-system-truth-owner-workshop")).toBeInTheDocument();
    });
    expect(screen.getByTestId("product-system-legacy-replacement-global-verdict")).toHaveTextContent(
      "NOT READY FOR DELETE",
    );
  });

});
