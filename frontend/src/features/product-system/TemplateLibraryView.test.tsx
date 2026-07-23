import { useState } from "react";
import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { ProductTemplateAvailabilityItem, ProductTemplateEntity } from "@/lib/api";
import { getProductTemplateIconConfig } from "./productTemplateIconRegistry";
import {
  TemplateLibraryView,
  type CatalogDensity,
  type ProductSystemCatalogView,
  type TemplateLibraryRowSummary,
} from "./TemplateLibraryView";

const LETTERS = "TPL-VOLUMETRIC-LETTERS_v2";
const LOGO = "TPL-VOLUMETRIC-LOGO_v1";
const VOLUM_ALUMINUM = "TPL-VOLUM-ALUMINIU_v1";
const FACE = "TPL-VOLUMETRIC-FACE_v1";
const LOGO_FACE = "TPL-VOLUMETRIC-LOGO-FACE_v1";
const OLD_LOGO_BACKING_TEMPLATE_CODES = [
  "TPL-VOLUMETRIC-LOGO-FACE_v1",
  "TPL-VOLUMETRIC-LOGO-BACK_v1",
  "TPL-VOLUMETRIC-LOGO-RETURN_v1",
  "TPL-VOLUMETRIC-LOGO-FINISH_v1",
  "TPL-VOLUMETRIC-LOGO-MOUNTING_v1",
];
const OLD_LOGO_BACKING_LABELS = ["Fata logo", "Spate logo", "Return logo", "Cant logo", "Montaj logo", "Finisaje logo"];

const LETTER_SHARED_CONTRACTS = [
  { component_key: "volumetric_face", display_name: "Volumetric face", profile_key: "letters", module_template_code: FACE, confidence: "MEDIUM", owner_decision: "APPROVE_AS_DIRECTION", shared_truth_fields: ["component_role", "area"], not_confirmed: [] },
  { component_key: "volumetric_back", display_name: "Volumetric back", profile_key: "letters", module_template_code: "TPL-VOLUMETRIC-BACK_v1", confidence: "MEDIUM", owner_decision: "APPROVE_AS_DIRECTION", shared_truth_fields: ["component_role", "area"], not_confirmed: [] },
  { component_key: "volumetric_return_side", display_name: "Volumetric return / side", profile_key: "letters", module_template_code: VOLUM_ALUMINUM, confidence: "MEDIUM", owner_decision: "APPROVE_AS_DIRECTION", shared_truth_fields: ["component_role", "perimeter"], not_confirmed: [] },
  { component_key: "volumetric_lighting", display_name: "Volumetric lighting", profile_key: "letters", module_template_code: "TPL-VOLUMETRIC-LED_v1", confidence: "PARTIAL", owner_decision: "NEEDS_MORE_AUDIT", shared_truth_fields: ["led_module_count", "psu_selection"], not_confirmed: ["lighting_zones"], calculation_strategy_key: "letters_standard_led_calculation", strategy_source_template_code: "TPL-VOLUMETRIC-LED_v1", strategy_status: "ACTIVE_FOR_LETTERS", strategy_meaning: "Letters lighting calculation strategy is carried by the shared LED module.", required_truth: ["face_area", "lighting_mode", "led_density_config", "psu_config"], shared_module_template_code: "TPL-VOLUMETRIC-LED_v1", legacy_replaced_by: null, reserved_module_template_code: null },
  { component_key: "volumetric_surface_finish", display_name: "Volumetric surface finish", profile_key: "letters", module_template_code: "TPL-VOLUMETRIC-FINISH_v1", confidence: "LOW", owner_decision: "KEEP_SEPARATE_NOW", shared_truth_fields: ["finish_target"], not_confirmed: ["shared_packaging_qc_boundary"] },
  { component_key: "volumetric_mounting_interface", display_name: "Volumetric mounting interface", profile_key: "letters", module_template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1", confidence: "LOW", owner_decision: "KEEP_SEPARATE_NOW", shared_truth_fields: ["mounting_support_requirement"], not_confirmed: ["mounting_alignment"] },
];

const LOGO_SHARED_CONTRACTS = LETTER_SHARED_CONTRACTS.map((contract) => ({
  ...contract,
  profile_key: "logo",
  module_template_code: contract.component_key === "volumetric_face"
    ? LOGO_FACE
    : contract.component_key === "volumetric_back"
      ? "TPL-VOLUMETRIC-LOGO-BACK_v1"
      : contract.component_key === "volumetric_return_side"
        ? "TPL-VOLUMETRIC-LOGO-RETURN_v1"
        : contract.component_key === "volumetric_lighting"
          ? "TPL-VOLUMETRIC-LOGO-LIGHTING_v1"
          : contract.component_key === "volumetric_surface_finish"
            ? "TPL-VOLUMETRIC-LOGO-FINISH_v1"
            : "TPL-VOLUMETRIC-LOGO-MOUNTING_v1",
  not_confirmed: contract.component_key === "volumetric_lighting" ? ["irregular_shape_impact"] : contract.not_confirmed,
  calculation_strategy_key: contract.component_key === "volumetric_lighting" ? "logo_led_calculation_strategy" : contract.calculation_strategy_key,
  strategy_source_template_code: contract.component_key === "volumetric_lighting" ? "TPL-VOLUMETRIC-LOGO-LIGHTING_v1" : contract.strategy_source_template_code,
  strategy_status: contract.component_key === "volumetric_lighting" ? "NEEDS_PRODUCT_TRUTH" : contract.strategy_status,
  strategy_meaning: contract.component_key === "volumetric_lighting" ? "Logo lighting module is a profile/backing strategy source, not a duplicated primary LED module." : contract.strategy_meaning,
  required_truth: contract.component_key === "volumetric_lighting" ? ["logo_lighting_mode", "logo_illuminated_area", "logo_shape_complexity", "lighting_zones", "psu_config"] : contract.required_truth,
  shared_module_template_code: contract.component_key === "volumetric_lighting" ? "TPL-VOLUMETRIC-LED_v1" : contract.shared_module_template_code,
  legacy_replaced_by: contract.component_key === "volumetric_lighting" ? null : contract.legacy_replaced_by,
  reserved_module_template_code: contract.component_key === "volumetric_lighting" ? "TPL-VOLUMETRIC-LOGO-LIGHTING_v1" : contract.reserved_module_template_code,
}));

const LETTER_COMPOSITION = [
  { role_key: "front_face", role_label: "Fata litera", module_template_code: FACE, module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 10, ui_hint: "Fata vizuala debitata din plexiglas.", status_label: "Modul intern activ" },
  { role_key: "back_panel", role_label: "Spate litera", module_template_code: "TPL-VOLUMETRIC-BACK_v1", module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 20, ui_hint: "Spatele literei / inchidere corp.", status_label: "Modul intern activ" },
  { role_key: "sidewall_return", role_label: "Cant / laterale", module_template_code: VOLUM_ALUMINUM, module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 30, ui_hint: "Volum/cant lateral din aluminiu.", status_label: "Modul intern activ" },
  { role_key: "lighting", role_label: "LED / iluminare", module_template_code: "TPL-VOLUMETRIC-LED_v1", module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 40, ui_hint: "Sistem de iluminare al produsului.", status_label: "Modul intern activ" },
  { role_key: "finishes", role_label: "Finisaje", module_template_code: "TPL-VOLUMETRIC-FINISH_v1", module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 50, ui_hint: "Folie, print, laminare sau finisaje vizuale.", status_label: "Modul intern activ" },
  { role_key: "mounting_structure", role_label: "Structura montaj", module_template_code: "TPL-METAL-PREMOUNT-STRUCTURE_v1", module_product_system_role: "internal_module", relation_type: "optional_addon", is_required: false, sort_order: 60, ui_hint: "Structura suport/montaj, optionala dupa caz.", status_label: "Optional / conditionat" },
];

const LOGO_COMPOSITION = [
  { role_key: "logo_front_face", role_label: "Fata logo", module_template_code: LOGO_FACE, module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 10, ui_hint: "Fata vizuala pentru logo volumetric.", status_label: "Modul intern activ" },
  { role_key: "logo_return", role_label: "Return / cant logo", module_template_code: "TPL-VOLUMETRIC-LOGO-RETURN_v1", module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 20, ui_hint: "Cant/return lateral pentru logo.", status_label: "Modul intern activ" },
  { role_key: "logo_back", role_label: "Spate logo", module_template_code: "TPL-VOLUMETRIC-LOGO-BACK_v1", module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 30, ui_hint: "Spate/inchidere logo.", status_label: "Modul intern activ" },
  { role_key: "logo_lighting", role_label: "Iluminare logo", module_template_code: "TPL-VOLUMETRIC-LOGO-LIGHTING_v1", module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 40, ui_hint: "Sistem iluminare/electrica pentru logo.", status_label: "Modul intern activ" },
  { role_key: "logo_finishes", role_label: "Finisaje logo", module_template_code: "TPL-VOLUMETRIC-LOGO-FINISH_v1", module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 50, ui_hint: "Finisaje vizuale pentru logo.", status_label: "Modul intern activ" },
  { role_key: "logo_mounting", role_label: "Montaj logo", module_template_code: "TPL-VOLUMETRIC-LOGO-MOUNTING_v1", module_product_system_role: "internal_module", relation_type: "required_module", is_required: true, sort_order: 60, ui_hint: "Montaj/suport pentru logo.", status_label: "Modul intern activ" },
];

function makeTemplate(id: number, templateCode: string): ProductTemplateEntity {
  return {
    id,
    template_code: templateCode,
    family_id: "litere_volumetrice",
    family_name: "Litere volumetrice",
    description: `Fixture ${templateCode}`,
    components_json: "[]",
    operations_json: "[]",
    required_materials_json: "[]",
    active: true,
    created_at: "2026-07-01T00:00:00Z",
    updated_at: "2026-07-01T00:00:00Z",
  };
}

function makeAvailability(
  template: ProductTemplateEntity,
  overrides: Partial<ProductTemplateAvailabilityItem>
): ProductTemplateAvailabilityItem {
  return {
    template_id: template.id,
    template_code: template.template_code,
    family_id: template.family_id ?? null,
    family_name: template.family_name,
    description: template.description ?? null,
    db_active: true,
    quote_offerable: false,
    runtime_module: false,
    is_parent: false,
    has_modules: false,
    parent_codes: [],
    module_codes: [],
    status: "not_offerable",
    status_reason: "fixture",
    product_system_role: "archived_experimental",
    display_group: "archived_experimental",
    importance_rank: 50,
    owner_decision_required: false,
    readiness_reason: "Fixture",
    ui_label: "Arhivat / experimental",
    ui_description: "Scos din flow activ sau experimental.",
    parent_product_codes: [],
    child_module_codes: [],
    shared_with_product_codes: [],
    composition_modules: [],
    shared_component_contracts: [],
    ...overrides,
  };
}

function createCatalogFixture() {
  const templates = [
    makeTemplate(1, LETTERS),
    makeTemplate(15, LOGO),
    makeTemplate(3, VOLUM_ALUMINUM),
    makeTemplate(4, FACE),
    makeTemplate(16, LOGO_FACE),
  ];
  const [letters, logo, volumAluminum, face, logoFace] = templates;
  const availabilityItems = [
    makeAvailability(letters, {
      quote_offerable: true,
      is_parent: true,
      has_modules: true,
      module_codes: [VOLUM_ALUMINUM, FACE],
      child_module_codes: [VOLUM_ALUMINUM, FACE],
      status: "offerable",
      status_reason: "owner_valid_parent_template",
      product_system_role: "offerable_product",
      display_group: "active_products",
      importance_rank: 10,
      readiness_reason: "Produs valid pentru ofertare in Work Intake.",
      ui_label: "Produs activ pentru ofertare",
      ui_description: "Poate fi ales ca produs initial in Work Intake.",
      composition_modules: LETTER_COMPOSITION,
      shared_component_contracts: LETTER_SHARED_CONTRACTS,
    }),
    makeAvailability(logo, {
      quote_offerable: false,
      is_parent: true,
      has_modules: true,
      module_codes: [LOGO_FACE],
      child_module_codes: [LOGO_FACE],
      status: "not_offerable",
      status_reason: "candidate_linked_child_only",
      product_system_role: "candidate_product",
      display_group: "candidate_products",
      importance_rank: 20,
      owner_decision_required: true,
      readiness_reason: "Logo ramane candidate / linked child in compozitia Letters; nu este root ofertabil separat.",
      ui_label: "Produs candidat / linked child",
      ui_description: "Participa in compozitie cu Letters. Nu se alege direct in Work Intake.",
      composition_modules: LOGO_COMPOSITION,
      shared_component_contracts: LOGO_SHARED_CONTRACTS,
    }),
    makeAvailability(volumAluminum, {
      runtime_module: true,
      parent_codes: [LETTERS],
      parent_product_codes: [LETTERS],
      status: "runtime_module",
      status_reason: "runtime_module_only",
      product_system_role: "internal_module",
      display_group: "internal_modules",
      importance_rank: 30,
      readiness_reason: `Modul intern activ folosit de ${LETTERS}.`,
      ui_label: "Modul intern activ",
      ui_description: "Folosit de produse parinte. Nu se alege direct in Work Intake.",
    }),
    makeAvailability(face, {
      runtime_module: true,
      parent_codes: [LETTERS],
      parent_product_codes: [LETTERS],
      status: "runtime_module",
      status_reason: "runtime_module_only",
      product_system_role: "internal_module",
      display_group: "internal_modules",
      importance_rank: 30,
      readiness_reason: `Modul intern activ folosit de ${LETTERS}.`,
      ui_label: "Modul intern activ",
      ui_description: "Folosit de produse parinte. Nu se alege direct in Work Intake.",
    }),
    makeAvailability(logoFace, {
      runtime_module: true,
      parent_codes: [LOGO],
      parent_product_codes: [LOGO],
      status: "runtime_module",
      status_reason: "runtime_module_only",
      product_system_role: "internal_module",
      display_group: "internal_modules",
      importance_rank: 30,
      readiness_reason: `Modul intern activ folosit de ${LOGO}.`,
      ui_label: "Modul intern activ",
      ui_description: "Folosit de produse parinte. Nu se alege direct in Work Intake.",
    }),
  ];

  return {
    templates,
    availabilityItems,
    summaries: new Map<number, TemplateLibraryRowSummary>([
      [1, { components: 6, operations: 14, materials: 13, validationPassed: 6, validationTotal: 6 }],
      [15, { components: 6, operations: 22, materials: 20, validationPassed: 2, validationTotal: 6 }],
    ]),
  };
}

function CatalogHarness({ simulateEditor = false }: { simulateEditor?: boolean }) {
  const fixture = createCatalogFixture();
  const [catalogView, setCatalogView] = useState<ProductSystemCatalogView>("overview");
  const [density, setDensity] = useState<CatalogDensity>("compact");
  const [editorTemplateCode, setEditorTemplateCode] = useState<string | null>(null);

  if (simulateEditor && editorTemplateCode) {
    return (
      <div>
        <p>Editor {editorTemplateCode}</p>
        <button type="button" onClick={() => setEditorTemplateCode(null)}>Înapoi la șabloane</button>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <TemplateLibraryView
        templates={fixture.templates}
        availabilityItems={fixture.availabilityItems}
        tab="all"
        onTabChange={() => {}}
        search=""
        onSearchChange={() => {}}
        catalogView={catalogView}
        onCatalogViewChange={setCatalogView}
        density={density}
        onDensityChange={setDensity}
        summaries={fixture.summaries}
        recommendedTemplateId={null}
        activeCount={1}
        archivedCount={0}
        loading={false}
        onOpenTemplate={(template) => {
          if (simulateEditor) setEditorTemplateCode(template.template_code);
        }}
      />
    </TooltipProvider>
  );
}

function renderCatalog() {
  render(<CatalogHarness />);
}

function renderCatalogWithEditorBack() {
  render(<CatalogHarness simulateEditor />);
}

describe("TemplateLibraryView scalable Product System navigation", () => {
  it("keeps Products view and detailed density after editor back remount", () => {
    renderCatalogWithEditorBack();

    fireEvent.click(screen.getByRole("tab", { name: /Produse/i }));
    fireEvent.click(screen.getByTestId("product-system-density-detailed"));
    fireEvent.click(screen.getByTestId(`product-system-template-${LETTERS}`));

    expect(screen.getByText(`Editor ${LETTERS}`)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Înapoi la șabloane/i }));

    expect(screen.getByTestId("product-system-view-products")).toBeInTheDocument();
    expect(screen.queryByTestId("product-system-view-overview")).not.toBeInTheDocument();
    expect(screen.getByTestId("product-system-catalog-shell")).toHaveAttribute("data-density", "detailed");
    expect(screen.getByText(LETTERS)).toBeInTheDocument();
  });

  it("keeps Products view after opening Logo candidate and returning", () => {
    renderCatalogWithEditorBack();

    fireEvent.click(screen.getByRole("tab", { name: /Produse/i }));
    fireEvent.click(screen.getByTestId(`product-system-template-${LOGO}`));

    expect(screen.getByText(`Editor ${LOGO}`)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Înapoi la șabloane/i }));

    const products = screen.getByTestId("product-system-products-list");
    expect(screen.getByTestId("product-system-view-products")).toBeInTheDocument();
    expect(within(products).getByText(LOGO)).toBeInTheDocument();
    expect(screen.queryByTestId("product-system-view-overview")).not.toBeInTheDocument();
  });

  it("renders Overview in compact density by default with count cards and no long component list", () => {
    renderCatalog();

    expect(screen.getByTestId("product-system-catalog-shell")).toHaveAttribute("data-density", "compact");
    expect(screen.getByTestId("product-system-density-compact")).toHaveTextContent("Compact");
    expect(screen.getByTestId("product-system-density-detailed")).toHaveTextContent("Detaliat");
    expect(screen.getByTestId("product-system-view-overview")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Overview/i })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByTestId("product-system-overview-card-products")).toHaveTextContent("Produse");
    expect(screen.getByTestId("product-system-overview-card-products")).toHaveTextContent("2");
    expect(screen.getByTestId("product-system-overview-card-components")).toHaveTextContent("Shared modules");
    expect(screen.getByTestId("product-system-overview-card-components")).toHaveTextContent("6");
    expect(screen.getByTestId("product-system-overview-card-composition")).toHaveTextContent("2");
    expect(screen.getByTestId("product-system-overview-card-archived")).toHaveTextContent("5");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Shared Volumetric Modules");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Letters si Logo consuma aceleasi 6 componente comune");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("2 produse conectate");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("6 componente comune");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("12 product usages");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Lighting shared module: TPL-VOLUMETRIC-LED_v1");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Letters strategy source: TPL-VOLUMETRIC-LED_v1");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Logo strategy source: TPL-VOLUMETRIC-LOGO-LIGHTING_v1");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Logo lighting profile is not a duplicated primary module");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Lighting profile needs Product Truth/runtime validation");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Letters: offerable");
    expect(screen.getByTestId("product-system-overview-shared-foundation")).toHaveTextContent("Logo: candidate / not Work Intake");
    expect(screen.queryByTestId("product-system-components-list")).not.toBeInTheDocument();
    expect(screen.queryByTestId(`product-system-component-row-${VOLUM_ALUMINUM}`)).not.toBeInTheDocument();
  });

  it("switches to Products view and shows only offerable/candidate products as primary items", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Produse/i }));

    const products = screen.getByTestId("product-system-products-list");
    expect(screen.getByTestId("product-system-view-products")).toBeInTheDocument();
    expect(products).toHaveClass("grid");
    expect(products).toHaveClass("xl:grid-cols-3");
    expect(within(products).getByText(LETTERS)).toBeInTheDocument();
    expect(within(products).getByText(LOGO)).toBeInTheDocument();
    expect(within(products).queryByText(VOLUM_ALUMINUM)).not.toBeInTheDocument();
    expect(products.textContent).not.toContain("Work Intake: DA");
    expect(within(products).queryByText("GO owner")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Ofertabile/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /In pregatire/i })).toBeInTheDocument();
    expect(within(products).getByTestId(`product-system-template-icon-${LETTERS}`)).toHaveAttribute("data-icon-size", "large");
    expect(within(products).getByTestId(`product-system-template-icon-${LETTERS}`)).toHaveClass("h-16");
    expect(within(products).getByTestId(`product-system-template-bottom-actions-${LETTERS}`)).toBeInTheDocument();
    expect(within(products).getByTestId(`product-system-template-bottom-actions-${LOGO}`)).toBeInTheDocument();
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LETTERS}`)).toHaveTextContent("Shared base: 6/6");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LETTERS}`)).toHaveTextContent("Shared modules: 6/6");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LETTERS}`)).toHaveTextContent("Profile letters");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LETTERS}`)).toHaveTextContent("Work Intake DA");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LETTERS}`)).toHaveTextContent("Lighting strategy source: TPL-VOLUMETRIC-LED_v1");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LETTERS}`)).toHaveTextContent("TPL-METAL-PREMOUNT-STRUCTURE_v1");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LOGO}`)).toHaveTextContent("Shared base: 6/6");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LOGO}`)).toHaveTextContent("Shared modules: 6/6");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LOGO}`)).toHaveTextContent("Profile logo");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LOGO}`)).toHaveTextContent("Work Intake NU");
    expect(within(products).getByTestId(`product-system-template-compact-foundation-${LOGO}`)).toHaveTextContent("Lighting strategy/profile source: TPL-VOLUMETRIC-LOGO-LIGHTING_v1");
    for (const hiddenCode of OLD_LOGO_BACKING_TEMPLATE_CODES) {
      expect(products).not.toHaveTextContent(hiddenCode);
    }
    for (const hiddenLabel of OLD_LOGO_BACKING_LABELS) {
      expect(products).not.toHaveTextContent(hiddenLabel);
    }
    expect(within(products).getByTestId(`product-system-template-meta-trigger-${LETTERS}`)).toBeInTheDocument();
    expect(within(products).getByTestId(`product-system-template-meta-trigger-${LOGO}`)).toBeInTheDocument();
    expect(screen.queryByTestId(`product-system-template-shared-foundation-${LETTERS}`)).not.toBeInTheDocument();
    expect(screen.queryByTestId(`product-system-template-shared-foundation-${LOGO}`)).not.toBeInTheDocument();
    expect(screen.queryByText("Nu apare in Work Intake.")).not.toBeInTheDocument();
    expect(screen.queryByText("Necesita GO owner pentru ofertare.")).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-view-overview")).not.toBeInTheDocument();
  });

  it("shows secondary product metadata from the compact info trigger", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Produse/i }));
    const products = screen.getByTestId("product-system-products-list");
    fireEvent.click(within(products).getByTestId(`product-system-template-meta-trigger-${LETTERS}`));

    const lettersMeta = screen.getByTestId(`product-system-template-meta-popover-${LETTERS}`);
    expect(within(lettersMeta).getByText("Module")).toBeInTheDocument();
    expect(within(lettersMeta).getAllByText("6").length).toBeGreaterThanOrEqual(1);
    expect(within(lettersMeta).getByText("Validare")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("6/6")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("Work Intake")).toBeInTheDocument();
    expect(within(lettersMeta).getAllByText("Da").length).toBeGreaterThan(0);
    expect(within(lettersMeta).getByText("GO owner")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("Shared foundation")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("6 contracte")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("Profile")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("letters")).toBeInTheDocument();
    expect(within(lettersMeta).getAllByText("Nu").length).toBeGreaterThan(0);

    fireEvent.click(within(products).getByTestId(`product-system-template-meta-trigger-${LOGO}`));
    const logoMeta = screen.getByTestId(`product-system-template-meta-popover-${LOGO}`);
    expect(within(logoMeta).getByText("Work Intake")).toBeInTheDocument();
    expect(within(logoMeta).getByText("Shared foundation")).toBeInTheDocument();
    expect(within(logoMeta).getByText("6 contracte")).toBeInTheDocument();
    expect(within(logoMeta).getByText("Profile")).toBeInTheDocument();
    expect(within(logoMeta).getByText("logo")).toBeInTheDocument();
    expect(within(logoMeta).getAllByText("Nu").length).toBeGreaterThan(0);
  });

  it("uses specific and fallback template icons with controlled color", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Produse/i }));

    const lettersIcon = screen.getByTestId(`product-system-template-icon-${LETTERS}`);
    const logoIcon = screen.getByTestId(`product-system-template-icon-${LOGO}`);
    const lettersConfig = getProductTemplateIconConfig(LETTERS, "offerable_product");
    const logoConfig = getProductTemplateIconConfig(LOGO, "candidate_product");

    expect(lettersIcon).toHaveAttribute("data-icon-source", "specific");
    expect(lettersIcon).toHaveAttribute("data-icon-color", lettersConfig.color);
    expect(logoIcon).toHaveAttribute("data-icon-source", "fallback");
    expect(logoIcon).toHaveAttribute("data-icon-color", logoConfig.color);
    expect(lettersConfig.color).not.toEqual(logoConfig.color);
  });

  it("keeps product composition expand available in Products view", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Produse/i }));
    const products = screen.getByTestId("product-system-products-list");
    const lettersTrigger = within(products).getByTestId(`product-system-template-composition-trigger-${LETTERS}`);
    expect(lettersTrigger).toHaveAccessibleName("Afiseaza baza comuna volumetrica, 6 module comune");
    expect(lettersTrigger).toHaveAttribute("aria-expanded", "false");
    expect(lettersTrigger).not.toHaveTextContent("Module");
    expect(lettersTrigger).not.toHaveTextContent("Module (6)");

    fireEvent.click(lettersTrigger);

    expect(lettersTrigger).toHaveAttribute("aria-expanded", "true");
    const lettersSharedComposition = within(products).getByTestId(`product-system-template-shared-composition-${LETTERS}`);
    expect(lettersSharedComposition).toHaveTextContent("Shared volumetric base: 6 module comune");
    expect(lettersSharedComposition).toHaveTextContent("Fata comuna");
    expect(lettersSharedComposition).toHaveTextContent("Spate comuna");
    expect(lettersSharedComposition).toHaveTextContent("Lighting / LED comun -> TPL-VOLUMETRIC-LED_v1");
    expect(lettersSharedComposition).toHaveTextContent("Lighting strategy source: TPL-VOLUMETRIC-LED_v1");
    expect(lettersSharedComposition).toHaveTextContent("Work Intake: DA");
  });

  it("shows detailed copy and dates only after switching density", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Produse/i }));
    expect(screen.queryByText("Apare in Work Intake")).not.toBeInTheDocument();
    expect(screen.queryByText("Actualizat: 01.07.2026")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("product-system-density-detailed"));

    expect(screen.getByTestId("product-system-catalog-shell")).toHaveAttribute("data-density", "detailed");
    expect(screen.getByTestId(`product-system-template-composition-trigger-${LETTERS}`)).toHaveTextContent("Shared base (6 comune)");
    expect(screen.getByTestId(`product-system-template-shared-foundation-${LETTERS}`)).toHaveTextContent("Profile letters");
    expect(screen.getByTestId(`product-system-template-shared-foundation-${LETTERS}`)).toHaveTextContent("Shared modules: 6/6");
    expect(screen.getByTestId(`product-system-template-shared-foundation-${LETTERS}`)).toHaveTextContent("Lighting strategy source: TPL-VOLUMETRIC-LED_v1");
    expect(screen.getByTestId(`product-system-template-shared-foundation-${LOGO}`)).toHaveTextContent("Profile logo");
    expect(screen.getByTestId(`product-system-template-shared-foundation-${LOGO}`)).toHaveTextContent("Lighting strategy/profile source: TPL-VOLUMETRIC-LOGO-LIGHTING_v1");
    expect(screen.getByTestId("product-system-products-list").textContent).toContain("Work Intake: DA");
    expect(screen.getAllByText("GO owner").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Apare in Work Intake").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Actualizat: 01.07.2026 · Creat: 01.07.2026")).toHaveLength(2);
    expect(screen.getByText(/Necesita GO owner/)).toBeInTheDocument();
  });

  it("switches to Components view and shows compact shared component cards with usage popovers", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Module produs/i }));

    const sharedContracts = screen.getByTestId("product-system-shared-contracts-list");
    expect(screen.getByTestId("product-system-view-components")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-view-tab-components")).toHaveTextContent("Module produs 6");
    expect(screen.getAllByTestId(/product-system-shared-contract-row-/)).toHaveLength(6);
    const faceContract = screen.getByTestId("product-system-shared-contract-row-volumetric_face");
    expect(within(faceContract).getByText("volumetric_face")).toBeInTheDocument();
    expect(within(faceContract).getByText("Volumetric face")).toBeInTheDocument();
    expect(faceContract).toHaveTextContent(`Module produs principal: ${FACE}`);
    expect(faceContract).toHaveTextContent("shared");
    expect(faceContract).toHaveTextContent("used by 2 products");
    expect(faceContract).not.toHaveTextContent(LOGO_FACE);
    expect(faceContract).not.toHaveTextContent("Profile letters");
    expect(faceContract).not.toHaveTextContent("Profile logo");
    expect(faceContract).not.toHaveTextContent("Letters strategy source");
    expect(faceContract).not.toHaveTextContent("Logo strategy source");
    fireEvent.mouseEnter(screen.getByTestId("product-system-shared-usage-trigger-volumetric_face"));
    const faceUsage = screen.getByTestId("product-system-shared-usage-popover-volumetric_face");
    expect(faceUsage).toHaveTextContent("Module produs");
    expect(faceUsage).toHaveTextContent("Module produs: TPL-VOLUMETRIC-FACE_v1");
    expect(faceUsage).toHaveTextContent(`${LETTERS}rădăcină ofertabilă — Work Intake DA`);
    expect(faceUsage).toHaveTextContent(`${LOGO}copil legat / candidate — Work Intake NU`);
    fireEvent.mouseLeave(screen.getByTestId("product-system-shared-usage-trigger-volumetric_face"));
    const lightingContract = screen.getByTestId("product-system-shared-contract-row-volumetric_lighting");
    expect(lightingContract).toHaveTextContent("Module produs principal: TPL-VOLUMETRIC-LED_v1");
    expect(lightingContract).not.toHaveTextContent("Letters strategy source: TPL-VOLUMETRIC-LED_v1");
    expect(lightingContract).not.toHaveTextContent("Logo strategy source: TPL-VOLUMETRIC-LOGO-LIGHTING_v1");
    fireEvent.mouseEnter(screen.getByTestId("product-system-shared-usage-trigger-volumetric_lighting"));
    const lightingUsage = screen.getByTestId("product-system-shared-usage-popover-volumetric_lighting");
    expect(lightingUsage).toHaveTextContent("Module produs: TPL-VOLUMETRIC-LED_v1");
    expect(lightingUsage).toHaveTextContent(`${LETTERS}rădăcină ofertabilă — Work Intake DA — strategy: TPL-VOLUMETRIC-LED_v1`);
    expect(lightingUsage).toHaveTextContent(`${LOGO}copil legat / candidate — Work Intake NU — strategy: TPL-VOLUMETRIC-LOGO-LIGHTING_v1`);
    fireEvent.mouseLeave(screen.getByTestId("product-system-shared-usage-trigger-volumetric_lighting"));
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_return_side")).toHaveTextContent(`Module produs principal: ${VOLUM_ALUMINUM}`);
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_finish")).toHaveTextContent("Volumetric finish");
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_mounting_structure")).toHaveTextContent("Volumetric mounting / structure");
    expect(screen.queryByTestId("product-system-components-list")).not.toBeInTheDocument();
    expect(screen.queryByTestId(`product-system-component-row-${LETTERS}`)).not.toBeInTheDocument();
    expect(screen.queryByTestId(`product-system-template-icon-${VOLUM_ALUMINUM}`)).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-products-list")).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /Module tehnice/i }));

    const components = screen.getByTestId("product-system-components-list");
    expect(within(components).getByText(VOLUM_ALUMINUM)).toBeInTheDocument();
    expect(within(components).getByText(FACE)).toBeInTheDocument();
    expect(within(components).queryByText(LOGO_FACE)).not.toBeInTheDocument();
    expect(screen.getByTestId(`product-system-component-row-${VOLUM_ALUMINUM}`)).toBeInTheDocument();
    for (const hiddenCode of OLD_LOGO_BACKING_TEMPLATE_CODES) {
      expect(components).not.toHaveTextContent(hiddenCode);
    }
  });

  it("keeps Components compact dense and adds owner details only in detailed density", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Module produs/i }));

    expect(screen.getByTestId("product-system-catalog-shell")).toHaveAttribute("data-density", "compact");
    expect(screen.queryByText("Modulele produs partajate sunt unitățile principale; Product Template-urile care le folosesc sunt sumarizate în iconul shared.")).not.toBeInTheDocument();
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_lighting")).not.toHaveTextContent("PARTIAL");
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_lighting")).not.toHaveTextContent("Logo lighting profile is strategy only");

    fireEvent.click(screen.getByTestId("product-system-density-detailed"));

    expect(screen.getByTestId("product-system-catalog-shell")).toHaveAttribute("data-density", "detailed");
    expect(screen.getByText("Modulele produs partajate sunt unitățile principale; Product Template-urile care le folosesc sunt sumarizate în iconul shared.")).toBeInTheDocument();
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_lighting")).toHaveTextContent("PARTIAL");
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_lighting")).toHaveTextContent("Letters strategy source: TPL-VOLUMETRIC-LED_v1");
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_lighting")).toHaveTextContent("Logo strategy source: TPL-VOLUMETRIC-LOGO-LIGHTING_v1");
    expect(screen.getByTestId("product-system-shared-contract-row-volumetric_lighting")).toHaveTextContent("Logo lighting profile is strategy only, not a duplicated primary module.");
  });

  it("switches to Composition view and renders shared volumetric base as the primary model", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Compozitii/i }));

    const composition = screen.getByTestId("product-system-composition-list");
    expect(screen.getByTestId("product-system-view-composition")).toBeInTheDocument();
    expect(within(composition).getByText(LETTERS)).toBeInTheDocument();
    expect(within(composition).getByText(LOGO)).toBeInTheDocument();

    const lettersSharedBase = within(composition).getByTestId(`product-system-composition-shared-base-${LETTERS}`);
    expect(lettersSharedBase).toHaveTextContent("Shared volumetric base: 6 module comune");
    expect(lettersSharedBase).toHaveTextContent("Fata comuna -> TPL-VOLUMETRIC-FACE_v1");
    expect(lettersSharedBase).toHaveTextContent("Spate comuna -> TPL-VOLUMETRIC-BACK_v1");
    expect(lettersSharedBase).toHaveTextContent("Cant / volum din aluminiu -> TPL-VOLUM-ALUMINIU_v1");
    expect(lettersSharedBase).toHaveTextContent("Finisaj comun -> TPL-VOLUMETRIC-FINISH_v1");
    expect(lettersSharedBase).toHaveTextContent("Montaj / structura comuna -> TPL-METAL-PREMOUNT-STRUCTURE_v1");
    expect(lettersSharedBase).toHaveTextContent("Lighting / LED comun -> TPL-VOLUMETRIC-LED_v1");
    expect(lettersSharedBase).toHaveTextContent("Lighting strategy source: TPL-VOLUMETRIC-LED_v1");
    expect(lettersSharedBase).toHaveTextContent("Work Intake: DA");

    const logoSharedBase = within(composition).getByTestId(`product-system-composition-shared-base-${LOGO}`);
    expect(logoSharedBase).toHaveTextContent("Shared volumetric base: 6 module comune");
    expect(logoSharedBase).toHaveTextContent("Fata comuna -> TPL-VOLUMETRIC-FACE_v1");
    expect(logoSharedBase).toHaveTextContent("Spate comuna -> TPL-VOLUMETRIC-BACK_v1");
    expect(logoSharedBase).toHaveTextContent("Cant / volum din aluminiu -> TPL-VOLUM-ALUMINIU_v1");
    expect(logoSharedBase).toHaveTextContent("Finisaj comun -> TPL-VOLUMETRIC-FINISH_v1");
    expect(logoSharedBase).toHaveTextContent("Montaj / structura comuna -> TPL-METAL-PREMOUNT-STRUCTURE_v1");
    expect(logoSharedBase).toHaveTextContent("Lighting / LED comun -> TPL-VOLUMETRIC-LED_v1");
    expect(logoSharedBase).toHaveTextContent("Lighting strategy source: TPL-VOLUMETRIC-LOGO-LIGHTING_v1");
    expect(logoSharedBase).toHaveTextContent("Work Intake: NU");
    expect(logoSharedBase).toHaveTextContent("copil legat / candidate / Work Intake NU");
    expect(logoSharedBase).toHaveTextContent("Logo uses the same shared volumetric modules as Letters. Logo lighting profile is strategy only.");
    for (const hiddenCode of OLD_LOGO_BACKING_TEMPLATE_CODES) {
      expect(composition).not.toHaveTextContent(hiddenCode);
    }
    for (const hiddenLabel of OLD_LOGO_BACKING_LABELS) {
      expect(composition).not.toHaveTextContent(hiddenLabel);
    }

    fireEvent.click(screen.getByTestId("product-system-density-detailed"));
    expect(within(composition).queryByText("Technical backing / historical bindings")).not.toBeInTheDocument();
  });

  it("switches to Archived view and shows empty state when none exist", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Arhivate/i }));

    expect(screen.getByTestId("product-system-view-archived")).toBeInTheDocument();
    expect(screen.getByText("Nu exista template-uri arhivate sau experimentale in catalogul curent.")).toBeInTheDocument();
    expect(screen.queryByText(VOLUM_ALUMINUM)).not.toBeInTheDocument();
  });

  it("does not render blocked archive restore wording", () => {
    renderCatalog();
    const blockedRo = "dez" + "arhivat";
    const blockedEn = "un" + "archived";
    const blockedPhrase = "restored from " + "archive";

    expect(document.body.textContent?.toLowerCase()).not.toContain(blockedRo);
    expect(document.body.textContent?.toLowerCase()).not.toContain(blockedEn);
    expect(document.body.textContent?.toLowerCase()).not.toContain(blockedPhrase);
  });
});
