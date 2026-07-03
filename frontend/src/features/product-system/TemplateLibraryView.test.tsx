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
    }),
    makeAvailability(logo, {
      is_parent: true,
      has_modules: true,
      module_codes: [LOGO_FACE],
      child_module_codes: [LOGO_FACE],
      status: "experimental",
      status_reason: "not_owner_valid",
      product_system_role: "candidate_product",
      display_group: "candidate_products",
      importance_rank: 20,
      owner_decision_required: true,
      readiness_reason: "Produs structural existent, dar necesita GO owner pentru ofertare.",
      ui_label: "Produs in pregatire",
      ui_description: "Nu apare in Work Intake pana la GO owner.",
      composition_modules: LOGO_COMPOSITION,
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
    expect(screen.getByTestId("product-system-overview-card-components")).toHaveTextContent("Componente / Module");
    expect(screen.getByTestId("product-system-overview-card-components")).toHaveTextContent("3");
    expect(screen.getByTestId("product-system-overview-card-composition")).toHaveTextContent("2");
    expect(screen.getByTestId("product-system-overview-card-archived")).toHaveTextContent("0");
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
    expect(within(products).getByText("Produs ofertabil")).toBeInTheDocument();
    expect(within(products).getByText("In pregatire")).toBeInTheDocument();
    expect(within(products).getByTestId(`product-system-template-icon-${LETTERS}`)).toHaveAttribute("data-icon-size", "large");
    expect(within(products).getByTestId(`product-system-template-icon-${LETTERS}`)).toHaveClass("h-16");
    expect(within(products).getByTestId(`product-system-template-bottom-actions-${LETTERS}`)).toBeInTheDocument();
    expect(within(products).getByTestId(`product-system-template-bottom-actions-${LOGO}`)).toBeInTheDocument();
    expect(within(products).getByTestId(`product-system-template-meta-trigger-${LETTERS}`)).toBeInTheDocument();
    expect(within(products).getByTestId(`product-system-template-meta-trigger-${LOGO}`)).toBeInTheDocument();
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
    expect(within(lettersMeta).getByText("6")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("Validare")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("6/6")).toBeInTheDocument();
    expect(within(lettersMeta).getByText("Work Intake")).toBeInTheDocument();
    expect(within(lettersMeta).getAllByText("Da").length).toBeGreaterThan(0);
    expect(within(lettersMeta).getByText("GO owner")).toBeInTheDocument();
    expect(within(lettersMeta).getAllByText("Nu").length).toBeGreaterThan(0);

    fireEvent.click(within(products).getByTestId(`product-system-template-meta-trigger-${LOGO}`));
    const logoMeta = screen.getByTestId(`product-system-template-meta-popover-${LOGO}`);
    expect(within(logoMeta).getByText("Work Intake")).toBeInTheDocument();
    expect(within(logoMeta).getByText("GO owner")).toBeInTheDocument();
    expect(within(logoMeta).getAllByText("Da").length).toBeGreaterThan(0);
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
    expect(lettersTrigger).toHaveAccessibleName("Afiseaza modulele produsului, 6 module");
    expect(lettersTrigger).toHaveAttribute("aria-expanded", "false");
    expect(lettersTrigger).not.toHaveTextContent("Module");
    expect(lettersTrigger).not.toHaveTextContent("Module (6)");

    fireEvent.click(lettersTrigger);

    expect(lettersTrigger).toHaveAttribute("aria-expanded", "true");
    expect(within(products).getByText("Fata litera")).toBeInTheDocument();
    expect(within(products).getByText(FACE)).toBeInTheDocument();
    expect(within(products).getByText("Optional / conditionat")).toBeInTheDocument();
  });

  it("shows detailed copy and dates only after switching density", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Produse/i }));
    expect(screen.queryByText("Apare in Work Intake")).not.toBeInTheDocument();
    expect(screen.queryByText("Actualizat: 01.07.2026")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("product-system-density-detailed"));

    expect(screen.getByTestId("product-system-catalog-shell")).toHaveAttribute("data-density", "detailed");
    expect(screen.getByTestId(`product-system-template-composition-trigger-${LETTERS}`)).toHaveTextContent("Module produs (6)");
    expect(screen.getByTestId("product-system-products-list").textContent).toContain("Work Intake: DA");
    expect(screen.getByText("GO owner")).toBeInTheDocument();
    expect(screen.getByText("Apare in Work Intake")).toBeInTheDocument();
    expect(screen.getAllByText("Actualizat: 01.07.2026 · Creat: 01.07.2026")).toHaveLength(2);
    expect(screen.getByText(/Necesita GO owner pentru ofertare/)).toBeInTheDocument();
  });

  it("switches to Components view and shows modules/components without product primary rows", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Componente/i }));

    const components = screen.getByTestId("product-system-components-list");
    expect(screen.getByTestId("product-system-view-components")).toBeInTheDocument();
    expect(within(components).getByText(VOLUM_ALUMINUM)).toBeInTheDocument();
    expect(within(components).getByText(FACE)).toBeInTheDocument();
    expect(screen.getByTestId(`product-system-component-row-${VOLUM_ALUMINUM}`)).toBeInTheDocument();
    expect(screen.queryByTestId(`product-system-component-row-${LETTERS}`)).not.toBeInTheDocument();
    expect(screen.queryByTestId(`product-system-template-icon-${VOLUM_ALUMINUM}`)).not.toBeInTheDocument();
    expect(screen.queryByTestId("product-system-products-list")).not.toBeInTheDocument();
  });

  it("switches to Composition view and renders product to module relations", () => {
    renderCatalog();

    fireEvent.click(screen.getByRole("tab", { name: /Compozitii/i }));

    const composition = screen.getByTestId("product-system-composition-list");
    expect(screen.getByTestId("product-system-view-composition")).toBeInTheDocument();
    expect(within(composition).getByText(LETTERS)).toBeInTheDocument();
    expect(within(composition).getByText(/Fata litera/)).toBeInTheDocument();
    expect(within(composition).queryByText(FACE)).not.toBeInTheDocument();
    expect(within(composition).getByText(LOGO)).toBeInTheDocument();
    expect(within(composition).getByText(/Fata logo/)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("product-system-density-detailed"));
    expect(within(composition).getByText(FACE)).toBeInTheDocument();
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
