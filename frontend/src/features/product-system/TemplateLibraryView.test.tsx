import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ProductAggregate } from "@/api/productAggregate";
import type { ProductFamily } from "@/api/productFamilies";
import type { TemplateCatalogEntry } from "@/features/product-system/templateCatalog";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { ProductTemplateEntity } from "@/lib/api";
import { TemplateLibraryView, type TemplateLibraryRowSummary } from "./TemplateLibraryView";

function makeTemplate(id: number, templateCode: string): ProductTemplateEntity {
  return {
    id,
    template_code: templateCode,
    family_id: "litere_volumetrice",
    family_name: "Litere volumetrice",
    status: "active",
    components_json: [],
    operations_json: [],
    materials_json: [],
    created_at: "2026-07-01T00:00:00Z",
    updated_at: "2026-07-01T00:00:00Z",
  } as ProductTemplateEntity;
}

function makeCatalogEntry(
  templateCode: string,
  overrides: Partial<TemplateCatalogEntry> = {},
): TemplateCatalogEntry {
  return {
    templateCode,
    kind: "standalone",
    label: "Standalone",
    description: "Standalone",
    relationshipKind: "standalone",
    relationshipLabel: "Standalone",
    relationshipDescription: "Standalone",
    incomingParentCodes: [],
    outgoingModuleCodes: [],
    incomingRelationTypes: [],
    outgoingRelationTypes: {},
    offerPolicyKind: "standalone_individual",
    offerPolicyLabel: "Standalone",
    offerPolicyDescription: "Standalone",
    ...overrides,
  };
}

const families: ProductFamily[] = [
  {
    family_id: "litere_volumetrice",
    label: "Litere volumetrice",
  } as ProductFamily,
];

function makeSummary(id: number): [number, TemplateLibraryRowSummary] {
  return [
    id,
    {
      components: 1,
      operations: 1,
      materials: 1,
      validationPassed: 6,
      validationTotal: 6,
    },
  ];
}

function buildLogoLibraryFixture() {
  const parent = makeTemplate(15, "TPL-VOLUMETRIC-LOGO_v1");
  const face = makeTemplate(16, "TPL-VOLUMETRIC-LOGO-FACE_v1");
  const finish = makeTemplate(17, "TPL-VOLUMETRIC-LOGO-FINISH_v1");
  const back = makeTemplate(18, "TPL-VOLUMETRIC-LOGO-BACK_v1");
  const templates = [parent, face, finish, back];

  const aggregate: ProductAggregate = {
    aggregate_version: "1.0.0",
    template_code: parent.template_code,
    template_id: parent.id,
    family_id: "litere_volumetrice",
    family_name: "Litere volumetrice",
    status: "active",
    business_name_ro: "Litere volumetrice",
    modules: {
      required: [
        {
          module_code: back.template_code,
          child_template_code: back.template_code,
          child_template_id: back.id,
          display_order: null,
          relation_type: "required_module",
        },
        {
          module_code: face.template_code,
          child_template_code: face.template_code,
          child_template_id: face.id,
          display_order: null,
          relation_type: "required_module",
        },
        {
          module_code: finish.template_code,
          child_template_code: finish.template_code,
          child_template_id: finish.id,
          display_order: null,
          relation_type: "required_module",
        },
      ],
      optional: [],
    },
    components: [
      {
        component_id: "comp_logo_face",
        display_order: 1,
        provenance: "linked_module",
        source_template_code: face.template_code,
      },
      {
        component_id: "comp_logo_finish",
        display_order: 2,
        provenance: "linked_module",
        source_template_code: finish.template_code,
      },
      {
        component_id: "comp_logo_back",
        display_order: 3,
        provenance: "linked_module",
        source_template_code: back.template_code,
      },
    ],
    materials: [],
    operations: [],
    conflicts: [],
    warnings: [],
    provenance_summary: {},
  };

  const catalog = new Map<string, TemplateCatalogEntry>([
    [
      parent.template_code.toUpperCase(),
      makeCatalogEntry(parent.template_code, {
        kind: "assembly",
        relationshipKind: "parent_assembly",
        relationshipLabel: "Ansamblu părinte",
        relationshipDescription: "Are module",
        outgoingModuleCodes: [back.template_code, face.template_code, finish.template_code].map((code) => code.toUpperCase()),
        outgoingRelationTypes: {
          [back.template_code.toUpperCase()]: "required_module",
          [face.template_code.toUpperCase()]: "required_module",
          [finish.template_code.toUpperCase()]: "required_module",
        },
        offerPolicyKind: "assembly_minimum_component",
        offerPolicyLabel: "Minim 1 componentă",
        offerPolicyDescription: "Minim 1 componentă",
      }),
    ],
    [face.template_code.toUpperCase(), makeCatalogEntry(face.template_code, { incomingParentCodes: [parent.template_code.toUpperCase()] })],
    [finish.template_code.toUpperCase(), makeCatalogEntry(finish.template_code, { incomingParentCodes: [parent.template_code.toUpperCase()] })],
    [back.template_code.toUpperCase(), makeCatalogEntry(back.template_code, { incomingParentCodes: [parent.template_code.toUpperCase()] })],
  ]);

  return { aggregate, back, catalog, face, finish, parent, templates };
}

function renderLibraryView() {
  const fixture = buildLogoLibraryFixture();

  render(
    <TooltipProvider>
      <TemplateLibraryView
        templates={fixture.templates}
        families={families}
        selectedFamilyId={null}
        onFamilyChange={() => {}}
        tab="all"
        onTabChange={() => {}}
        search=""
        onSearchChange={() => {}}
        summaries={new Map<number, TemplateLibraryRowSummary>(fixture.templates.map((template) => makeSummary(template.id)))}
        catalogByTemplateCode={fixture.catalog}
        aggregateByTemplateCode={new Map([[fixture.parent.template_code.toUpperCase(), fixture.aggregate]])}
        recommendedTemplateId={null}
        activeCount={fixture.templates.length}
        archivedCount={0}
        loading={false}
        onOpenTemplate={() => {}}
      />
    </TooltipProvider>,
  );

  return fixture;
}

function buildWorkflowPreviewFixture() {
  const letters = makeTemplate(30, "TPL-VOLUMETRIC-LETTERS_v2");
  const lettersFace = makeTemplate(31, "TPL-VOLUMETRIC-FACE_v1");
  const lettersReturn = makeTemplate(32, "TPL-VOLUM-ALUMINIU_v1");
  const lettersBack = makeTemplate(33, "TPL-VOLUMETRIC-BACK_v1");
  const lettersLighting = makeTemplate(34, "TPL-VOLUMETRIC-LED_v1");
  const lettersFinish = makeTemplate(35, "TPL-VOLUMETRIC-FINISH_v1");

  const logoFixture = buildLogoLibraryFixture();
  const templates = [
    letters,
    lettersFace,
    lettersReturn,
    lettersBack,
    lettersLighting,
    lettersFinish,
    ...logoFixture.templates,
  ];

  const lettersAggregate: ProductAggregate = {
    aggregate_version: "1.0.0",
    template_code: letters.template_code,
    template_id: letters.id,
    family_id: "litere_volumetrice",
    family_name: "Litere volumetrice",
    status: "active",
    business_name_ro: "Litere volumetrice",
    modules: {
      required: [
        {
          module_code: lettersFace.template_code,
          child_template_code: lettersFace.template_code,
          child_template_id: lettersFace.id,
          display_order: 1,
          relation_type: "required_module",
        },
        {
          module_code: lettersFinish.template_code,
          child_template_code: lettersFinish.template_code,
          child_template_id: lettersFinish.id,
          display_order: 2,
          relation_type: "required_module",
        },
        {
          module_code: lettersReturn.template_code,
          child_template_code: lettersReturn.template_code,
          child_template_id: lettersReturn.id,
          display_order: 3,
          relation_type: "required_module",
        },
        {
          module_code: lettersBack.template_code,
          child_template_code: lettersBack.template_code,
          child_template_id: lettersBack.id,
          display_order: 4,
          relation_type: "required_module",
        },
        {
          module_code: lettersLighting.template_code,
          child_template_code: lettersLighting.template_code,
          child_template_id: lettersLighting.id,
          display_order: 5,
          relation_type: "required_module",
        },
      ],
      optional: [],
    },
    components: [
      { component_id: "comp_face_litere", display_order: 1, provenance: "linked_module", source_template_code: lettersFace.template_code },
      { component_id: "comp_finisaj_litere", display_order: 2, provenance: "linked_module", source_template_code: lettersFinish.template_code },
      { component_id: "comp_lateral_litere", display_order: 3, provenance: "linked_module", source_template_code: lettersReturn.template_code },
      { component_id: "comp_spate_litere", display_order: 4, provenance: "linked_module", source_template_code: lettersBack.template_code },
      { component_id: "comp_led_litere", display_order: 5, provenance: "linked_module", source_template_code: lettersLighting.template_code },
    ],
    materials: [],
    operations: [],
    conflicts: [],
    warnings: [],
    provenance_summary: {},
  };

  const catalog = new Map<string, TemplateCatalogEntry>([
    [
      letters.template_code.toUpperCase(),
      makeCatalogEntry(letters.template_code, {
        kind: "assembly",
        relationshipKind: "parent_assembly",
        relationshipLabel: "Ansamblu părinte",
        relationshipDescription: "Are module",
        outgoingModuleCodes: [lettersFace, lettersFinish, lettersReturn, lettersBack, lettersLighting].map((row) => row.template_code.toUpperCase()),
        outgoingRelationTypes: {
          [lettersFace.template_code.toUpperCase()]: "required_module",
          [lettersFinish.template_code.toUpperCase()]: "required_module",
          [lettersReturn.template_code.toUpperCase()]: "required_module",
          [lettersBack.template_code.toUpperCase()]: "required_module",
          [lettersLighting.template_code.toUpperCase()]: "required_module",
        },
        offerPolicyKind: "assembly_minimum_component",
        offerPolicyLabel: "Minim 1 componentă",
        offerPolicyDescription: "Minim 1 componentă",
      }),
    ],
    [lettersFace.template_code.toUpperCase(), makeCatalogEntry(lettersFace.template_code, { incomingParentCodes: [letters.template_code.toUpperCase()] })],
    [lettersFinish.template_code.toUpperCase(), makeCatalogEntry(lettersFinish.template_code, { incomingParentCodes: [letters.template_code.toUpperCase()] })],
    [lettersReturn.template_code.toUpperCase(), makeCatalogEntry(lettersReturn.template_code, { incomingParentCodes: [letters.template_code.toUpperCase()] })],
    [lettersBack.template_code.toUpperCase(), makeCatalogEntry(lettersBack.template_code, { incomingParentCodes: [letters.template_code.toUpperCase()] })],
    [lettersLighting.template_code.toUpperCase(), makeCatalogEntry(lettersLighting.template_code, { incomingParentCodes: [letters.template_code.toUpperCase()] })],
    ...logoFixture.catalog.entries(),
  ]);

  const aggregates = new Map<string, ProductAggregate>([
    [letters.template_code.toUpperCase(), lettersAggregate],
    [logoFixture.parent.template_code.toUpperCase(), logoFixture.aggregate],
  ]);

  return { aggregates, catalog, letters, logo: logoFixture.parent, templates };
}

function buildSharedAssemblyModuleFixture() {
  const productA = makeTemplate(50, "TPL-PRODUCT-A_v1");
  const productB = makeTemplate(51, "TPL-PRODUCT-B_v1");
  const sharedAssemblyModule = makeTemplate(52, "TPL-SHARED-ASSEMBLY-MODULE_v1");
  const sharedLeaf = makeTemplate(53, "TPL-SHARED-LEAF_v1");
  const templates = [productA, productB, sharedAssemblyModule, sharedLeaf];

  const productAAggregate: ProductAggregate = {
    aggregate_version: "1.0.0",
    template_code: productA.template_code,
    template_id: productA.id,
    family_id: "litere_volumetrice",
    family_name: "Litere volumetrice",
    status: "active",
    business_name_ro: "Produs A",
    modules: {
      required: [
        {
          module_code: sharedAssemblyModule.template_code,
          child_template_code: sharedAssemblyModule.template_code,
          child_template_id: sharedAssemblyModule.id,
          display_order: 1,
          relation_type: "required_module",
        },
      ],
      optional: [],
    },
    components: [
      {
        component_id: "comp_shared_assembly_module",
        display_order: 1,
        provenance: "linked_module",
        source_template_code: sharedAssemblyModule.template_code,
      },
    ],
    materials: [],
    operations: [],
    conflicts: [],
    warnings: [],
    provenance_summary: {},
  };

  const productBAggregate: ProductAggregate = {
    aggregate_version: "1.0.0",
    template_code: productB.template_code,
    template_id: productB.id,
    family_id: "litere_volumetrice",
    family_name: "Litere volumetrice",
    status: "active",
    business_name_ro: "Produs B",
    modules: {
      required: [
        {
          module_code: sharedAssemblyModule.template_code,
          child_template_code: sharedAssemblyModule.template_code,
          child_template_id: sharedAssemblyModule.id,
          display_order: 1,
          relation_type: "required_module",
        },
      ],
      optional: [],
    },
    components: [
      {
        component_id: "comp_shared_assembly_module",
        display_order: 1,
        provenance: "linked_module",
        source_template_code: sharedAssemblyModule.template_code,
      },
    ],
    materials: [],
    operations: [],
    conflicts: [],
    warnings: [],
    provenance_summary: {},
  };

  const sharedAssemblyAggregate: ProductAggregate = {
    aggregate_version: "1.0.0",
    template_code: sharedAssemblyModule.template_code,
    template_id: sharedAssemblyModule.id,
    family_id: "litere_volumetrice",
    family_name: "Litere volumetrice",
    status: "active",
    business_name_ro: "Shared assembly module",
    modules: {
      required: [
        {
          module_code: sharedLeaf.template_code,
          child_template_code: sharedLeaf.template_code,
          child_template_id: sharedLeaf.id,
          display_order: 1,
          relation_type: "required_module",
        },
      ],
      optional: [],
    },
    components: [
      {
        component_id: "comp_shared_leaf",
        display_order: 1,
        provenance: "linked_module",
        source_template_code: sharedLeaf.template_code,
      },
    ],
    materials: [],
    operations: [],
    conflicts: [],
    warnings: [],
    provenance_summary: {},
  };

  const catalog = new Map<string, TemplateCatalogEntry>([
    [
      productA.template_code.toUpperCase(),
      makeCatalogEntry(productA.template_code, {
        kind: "assembly",
        relationshipKind: "parent_assembly",
        relationshipLabel: "Ansamblu părinte",
        relationshipDescription: "Are module",
        outgoingModuleCodes: [sharedAssemblyModule.template_code.toUpperCase()],
        outgoingRelationTypes: {
          [sharedAssemblyModule.template_code.toUpperCase()]: "required_module",
        },
        offerPolicyKind: "assembly_minimum_component",
        offerPolicyLabel: "Minim 1 componentă",
        offerPolicyDescription: "Minim 1 componentă",
      }),
    ],
    [
      productB.template_code.toUpperCase(),
      makeCatalogEntry(productB.template_code, {
        kind: "assembly",
        relationshipKind: "parent_assembly",
        relationshipLabel: "Ansamblu părinte",
        relationshipDescription: "Are module",
        outgoingModuleCodes: [sharedAssemblyModule.template_code.toUpperCase()],
        outgoingRelationTypes: {
          [sharedAssemblyModule.template_code.toUpperCase()]: "required_module",
        },
        offerPolicyKind: "assembly_minimum_component",
        offerPolicyLabel: "Minim 1 componentă",
        offerPolicyDescription: "Minim 1 componentă",
      }),
    ],
    [
      sharedAssemblyModule.template_code.toUpperCase(),
      makeCatalogEntry(sharedAssemblyModule.template_code, {
        kind: "assembly_module",
        relationshipKind: "required_module",
        relationshipLabel: "Ansamblu modular",
        relationshipDescription: "Este reutilizat și are module proprii",
        incomingParentCodes: [productA.template_code.toUpperCase(), productB.template_code.toUpperCase()],
        outgoingModuleCodes: [sharedLeaf.template_code.toUpperCase()],
        outgoingRelationTypes: {
          [sharedLeaf.template_code.toUpperCase()]: "required_module",
        },
        offerPolicyKind: "required_auto_included",
        offerPolicyLabel: "Componentă auto-inclusă",
        offerPolicyDescription: "Intră automat când este ofertat ansamblul părinte",
      }),
    ],
    [
      sharedLeaf.template_code.toUpperCase(),
      makeCatalogEntry(sharedLeaf.template_code, {
        kind: "reusable_module",
        incomingParentCodes: [sharedAssemblyModule.template_code.toUpperCase()],
      }),
    ],
  ]);

  const aggregates = new Map<string, ProductAggregate>([
    [productA.template_code.toUpperCase(), productAAggregate],
    [productB.template_code.toUpperCase(), productBAggregate],
    [sharedAssemblyModule.template_code.toUpperCase(), sharedAssemblyAggregate],
  ]);

  return { productA, productB, sharedAssemblyModule, sharedLeaf, templates, catalog, aggregates };
}

function renderSharedAssemblyModuleLibrary() {
  const fixture = buildSharedAssemblyModuleFixture();

  render(
    <TooltipProvider>
      <TemplateLibraryView
        templates={fixture.templates}
        families={families}
        selectedFamilyId={null}
        onFamilyChange={() => {}}
        tab="all"
        onTabChange={() => {}}
        search=""
        onSearchChange={() => {}}
        summaries={new Map<number, TemplateLibraryRowSummary>(fixture.templates.map((template) => makeSummary(template.id)))}
        catalogByTemplateCode={fixture.catalog}
        aggregateByTemplateCode={fixture.aggregates}
        recommendedTemplateId={null}
        activeCount={fixture.templates.length}
        archivedCount={0}
        loading={false}
        onOpenTemplate={() => {}}
      />
    </TooltipProvider>,
  );

  return fixture;
}

function renderWorkflowPreviewLibrary() {
  const fixture = buildWorkflowPreviewFixture();
  render(
    <TooltipProvider>
      <TemplateLibraryView
        templates={fixture.templates}
        families={families}
        selectedFamilyId={null}
        onFamilyChange={() => {}}
        tab="all"
        onTabChange={() => {}}
        search=""
        onSearchChange={() => {}}
        summaries={new Map<number, TemplateLibraryRowSummary>(fixture.templates.map((template) => makeSummary(template.id)))}
        catalogByTemplateCode={fixture.catalog}
        aggregateByTemplateCode={fixture.aggregates}
        recommendedTemplateId={null}
        activeCount={fixture.templates.length}
        archivedCount={0}
        loading={false}
        onOpenTemplate={() => {}}
      />
    </TooltipProvider>,
  );

  return fixture;
}

describe("TemplateLibraryView", () => {
  it("uses aggregate component order for compact component chips when module display order is missing", () => {
    const fixture = renderLibraryView();

    const chipOrder = [fixture.face, fixture.finish, fixture.back].map((child) =>
      screen.getByTestId(`template-chip-${fixture.parent.template_code}-${child.template_code}`).textContent,
    );

    expect(chipOrder).toEqual(["Face", "Finish", "Back"]);
  });

  it("keeps child modules out of product templates and switches to components on chip click", () => {
    const fixture = renderLibraryView();

    expect(screen.getByTestId(`template-library-row-0-${fixture.parent.template_code}`)).toBeInTheDocument();
    expect(screen.queryByTestId(`template-library-row-0-${fixture.face.template_code}`)).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId(`template-chip-${fixture.parent.template_code}-${fixture.face.template_code}`));

    expect(screen.getByRole("button", { name: /Componente \/ module reutilizabile/i })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByTestId(`template-library-row-0-${fixture.face.template_code}`)).toBeInTheDocument();
    expect(
      screen
        .getAllByTestId(/template-library-row-0-TPL-VOLUMETRIC-LOGO-/)
        .map((node) => node.getAttribute("data-testid"))
        .at(0),
    ).toBe(`template-library-row-0-${fixture.face.template_code}`);
  });

  it("keeps only discrete active and archived status filters visible", () => {
    renderLibraryView();

    expect(screen.getByTestId("template-status-filter-active")).toBeInTheDocument();
    expect(screen.getByTestId("template-status-filter-archived")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Toate \(/i })).not.toBeInTheDocument();
  });

  it("uses short surface labels and opens search only on demand", () => {
    renderLibraryView();

    expect(screen.getByTestId("template-surface-product_templates")).toHaveTextContent(/^Produse \(1\)$/i);
    expect(screen.getByTestId("template-surface-components")).toHaveTextContent(/^Componente \(3\)$/i);
    expect(screen.getByTestId("template-search-open")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/Caută cod șablon, familie/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("template-search-open"));

    expect(screen.getByPlaceholderText(/Caută cod șablon, familie/i)).toBeInTheDocument();

    fireEvent.click(screen.getByTestId("template-search-close"));

    expect(screen.queryByPlaceholderText(/Caută cod șablon, familie/i)).not.toBeInTheDocument();
  });

  it("uses coherent Romanian component filters without overlapping specific and orphan buckets", () => {
    renderLibraryView();

    fireEvent.click(screen.getByTestId("template-surface-components"));

    expect(screen.getByRole("button", { name: /Toate \(3\)/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Dedicat \(3\)/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Reutilizate \(0\)/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Fără părinte \(0\)/i })).toBeInTheDocument();
  });

  it("shows a reused assembly module in components when it is consumed by multiple product templates", () => {
    const fixture = renderSharedAssemblyModuleLibrary();

    fireEvent.click(screen.getByTestId("template-surface-components"));

    expect(screen.getByRole("button", { name: /Reutilizate \(1\)/i })).toBeInTheDocument();
    expect(screen.getByTestId(`template-library-row-0-${fixture.sharedAssemblyModule.template_code}`)).toBeInTheDocument();
    expect(screen.getAllByText(/Reutilizat/i).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: /Reutilizate \(1\)/i }));

    expect(screen.getByTestId(`template-library-row-0-${fixture.sharedAssemblyModule.template_code}`)).toBeInTheDocument();
    expect(screen.queryByTestId(`template-library-row-0-${fixture.productA.template_code}`)).not.toBeInTheDocument();
    expect(screen.queryByTestId(`template-library-row-0-${fixture.productB.template_code}`)).not.toBeInTheDocument();
  });

  it("keeps product template cards slim and hides inline child module sections by default", () => {
    const fixture = renderWorkflowPreviewLibrary();

    expect(screen.queryByText("Verificare fisiere si layere")).not.toBeInTheDocument();
    expect(screen.queryByText("Verificare logo si zone artwork")).not.toBeInTheDocument();
    expect(screen.queryByTestId(`workflow-panel-steps-${fixture.logo.template_code}`)).not.toBeInTheDocument();
    expect(screen.queryByText(/Blueprint vertical/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Module obligatorii/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Layer 01/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/^TPL-VOLUMETRIC-LOGO-FACE_v1$/i)).not.toBeInTheDocument();

    expect(screen.getByTestId(`workflow-summary-${fixture.letters.template_code}`)).toBeInTheDocument();
    expect(screen.getByTestId(`workflow-summary-${fixture.logo.template_code}`)).toBeInTheDocument();
    expect(screen.getByTestId(`workflow-step-count-${fixture.letters.template_code}`)).toHaveTextContent("12 pasi");
    expect(screen.getByTestId(`workflow-step-count-${fixture.logo.template_code}`)).toHaveTextContent("13 pasi");
    expect(screen.getByTestId(`workflow-status-${fixture.logo.template_code}`)).toHaveTextContent(/Recomandat/i);
    expect(screen.getByTestId(`workflow-warning-count-${fixture.logo.template_code}`)).toHaveTextContent(/Workflow valid/i);
    expect(screen.getByTestId(`workflow-configure-${fixture.logo.template_code}`)).toBeInTheDocument();
    expect(screen.getByTestId(`workflow-configure-${fixture.logo.template_code}`)).toHaveTextContent(/^Workflow$/i);
    expect(screen.getByTestId(`view-components-${fixture.logo.template_code}`)).toBeInTheDocument();
    expect(screen.getByTestId(`view-components-${fixture.logo.template_code}`)).toHaveTextContent(/^Componente$/i);
    expect(screen.getByTestId(`template-chip-${fixture.logo.template_code}-TPL-VOLUMETRIC-LOGO-FACE_v1`)).toHaveTextContent("Face");
    expect(screen.getByTestId(`template-chip-${fixture.logo.template_code}-TPL-VOLUMETRIC-LOGO-FINISH_v1`)).toHaveTextContent("Finish");
    expect(screen.getByTestId(`template-chip-${fixture.logo.template_code}-TPL-VOLUMETRIC-LOGO-BACK_v1`)).toHaveTextContent("Back");
  });

  it("opens a dedicated workflow panel with full step list and local-only notice", () => {
    const fixture = renderWorkflowPreviewLibrary();

    fireEvent.click(screen.getByTestId(`workflow-configure-${fixture.logo.template_code}`));

    expect(screen.getByTestId(`workflow-panel-title-${fixture.logo.template_code}`)).toHaveTextContent(
      `Workflow productie — ${fixture.logo.template_code}`,
    );
    expect(screen.getByText(/Acest workflow este draft local. Nu afecteaza executia reala si nu creeaza taskuri/i)).toBeInTheDocument();
    expect(screen.getByTestId(`workflow-panel-steps-${fixture.logo.template_code}`)).toBeInTheDocument();
    expect(screen.getByText("Verificare logo si zone artwork")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Save$/i })).not.toBeInTheDocument();
    expect(screen.getByText(/Salvare persistenta va fi disponibila in Phase 3/i)).toBeInTheDocument();
  });

  it("opens the components tab from the slim product card and keeps technical modules accessible", () => {
    const fixture = renderWorkflowPreviewLibrary();

    fireEvent.click(screen.getByTestId(`view-components-${fixture.logo.template_code}`));

    expect(screen.getByRole("button", { name: /Componente \/ module reutilizabile/i })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByTestId("focused-parent-template-label")).toHaveTextContent(
      `Componente folosite de ${fixture.logo.template_code.toUpperCase()}`,
    );
    expect(screen.getByText(/Focus: TPL-VOLUMETRIC-LOGO-FACE_v1/i)).toBeInTheDocument();
    expect(screen.queryByTestId(`template-library-row-0-${fixture.logo.template_code}`)).not.toBeInTheDocument();
    expect(screen.getByTestId("template-library-row-0-TPL-VOLUMETRIC-LOGO-FACE_v1")).toBeInTheDocument();
  });

  it("keeps draft ordering and warnings isolated per template code and does not call backend", () => {
    const fetchSpy = vi.spyOn(globalThis, "fetch");
    const fixture = renderWorkflowPreviewLibrary();

    fireEvent.click(screen.getByTestId(`workflow-configure-${fixture.logo.template_code}`));

    fireEvent.dragStart(screen.getByTestId("workflow-step-logo-light-test"));
    fireEvent.dragOver(screen.getByTestId("workflow-step-logo-face-nesting"));
    fireEvent.drop(screen.getByTestId("workflow-step-logo-face-nesting"));

    let logoStepOrder = screen
      .getAllByTestId(/workflow-step-logo-/)
      .map((node) => node.getAttribute("data-testid"));
    expect(logoStepOrder.slice(0, 3)).toEqual([
      "workflow-step-logo-artwork-review",
      "workflow-step-logo-artwork-print",
      "workflow-step-logo-light-test",
    ]);

    expect(screen.getByTestId(`workflow-preview-status-${fixture.logo.template_code}`)).toHaveTextContent(/Draft local/i);
    expect(screen.getByTestId(`workflow-validation-${fixture.logo.template_code}`)).toHaveTextContent(/1 validari necesita atentie/i);
    expect(screen.getAllByText(/Test lumina trebuie dupa Cablare si sursa/i).length).toBeGreaterThan(1);
    expect(screen.getByTestId(`workflow-warning-count-${fixture.logo.template_code}`)).toHaveTextContent(/1 avertizari/i);

    fireEvent.click(screen.getByRole("button", { name: /Inchide/i }));

    expect(screen.queryByTestId(`workflow-panel-title-${fixture.logo.template_code}`)).not.toBeInTheDocument();
    expect(screen.getByTestId(`workflow-status-${fixture.logo.template_code}`)).toHaveTextContent(/Draft local/i);
    expect(screen.getByTestId(`workflow-warning-count-${fixture.logo.template_code}`)).toHaveTextContent(/1 avertizari/i);
    expect(screen.getByTestId(`workflow-status-${fixture.letters.template_code}`)).toHaveTextContent(/Recomandat/i);
    expect(screen.getByTestId(`workflow-warning-count-${fixture.letters.template_code}`)).toHaveTextContent(/Workflow valid/i);

    fireEvent.click(screen.getByTestId(`workflow-configure-${fixture.letters.template_code}`));

    expect(screen.getByTestId(`workflow-panel-title-${fixture.letters.template_code}`)).toHaveTextContent(
      `Workflow productie — ${fixture.letters.template_code}`,
    );
    const lettersStepOrder = screen
      .getAllByTestId(/workflow-step-letters-/)
      .map((node) => node.getAttribute("data-testid"));
    expect(lettersStepOrder.slice(0, 4)).toEqual([
      "workflow-step-letters-artwork-review",
      "workflow-step-letters-face-nesting",
      "workflow-step-letters-face-cut",
      "workflow-step-letters-back-cut",
    ]);
    expect(screen.getByTestId(`workflow-preview-status-${fixture.letters.template_code}`)).toHaveTextContent(/Recomandat/i);
    expect(screen.getByTestId(`workflow-validation-${fixture.letters.template_code}`)).toHaveTextContent(/respecta dependintele declarate/i);

    fireEvent.click(screen.getByRole("button", { name: /Inchide/i }));
    fireEvent.click(screen.getByTestId(`workflow-configure-${fixture.logo.template_code}`));

    logoStepOrder = screen
      .getAllByTestId(/workflow-step-logo-/)
      .map((node) => node.getAttribute("data-testid"));
    expect(logoStepOrder.slice(0, 3)).toEqual([
      "workflow-step-logo-artwork-review",
      "workflow-step-logo-artwork-print",
      "workflow-step-logo-light-test",
    ]);
    expect(screen.getByTestId(`workflow-preview-status-${fixture.logo.template_code}`)).toHaveTextContent(/Draft local/i);

    expect(fetchSpy).not.toHaveBeenCalled();
    fetchSpy.mockRestore();
  });

  it("resets only the active template workflow from the dedicated panel", () => {
    const fixture = renderWorkflowPreviewLibrary();

    fireEvent.click(screen.getByTestId(`workflow-configure-${fixture.logo.template_code}`));

    fireEvent.dragStart(screen.getByTestId("workflow-step-logo-light-test"));
    fireEvent.dragOver(screen.getByTestId("workflow-step-logo-face-nesting"));
    fireEvent.drop(screen.getByTestId("workflow-step-logo-face-nesting"));

    fireEvent.click(screen.getByRole("button", { name: /Inchide/i }));
    fireEvent.click(screen.getByTestId(`workflow-configure-${fixture.letters.template_code}`));

    expect(screen.getAllByText(/Optional ·/i).length).toBeGreaterThan(0);

    fireEvent.dragStart(screen.getByTestId("workflow-step-letters-electrical-test"));
    fireEvent.dragOver(screen.getByTestId("workflow-step-letters-face-nesting"));
    fireEvent.drop(screen.getByTestId("workflow-step-letters-face-nesting"));

    expect(screen.getByTestId(`workflow-preview-status-${fixture.letters.template_code}`)).toHaveTextContent(/Draft local/i);
    expect(screen.getByTestId(`workflow-warning-count-${fixture.letters.template_code}`)).toHaveTextContent(/1 avertizari/i);

    fireEvent.click(screen.getByTestId(`workflow-reset-${fixture.letters.template_code}`));

    const lettersStepOrder = screen
      .getAllByTestId(/workflow-step-letters-/)
      .map((node) => node.getAttribute("data-testid"));
    expect(lettersStepOrder.slice(0, 3)).toEqual([
      "workflow-step-letters-artwork-review",
      "workflow-step-letters-face-nesting",
      "workflow-step-letters-face-cut",
    ]);

    expect(screen.getByTestId(`workflow-preview-status-${fixture.letters.template_code}`)).toHaveTextContent(/Recomandat/i);
    expect(screen.getByTestId(`workflow-validation-${fixture.letters.template_code}`)).toHaveTextContent(/respecta dependintele declarate/i);

    fireEvent.click(screen.getByRole("button", { name: /Inchide/i }));
    fireEvent.click(screen.getByTestId(`workflow-configure-${fixture.logo.template_code}`));

    const logoStepOrder = screen
      .getAllByTestId(/workflow-step-logo-/)
      .map((node) => node.getAttribute("data-testid"));
    expect(logoStepOrder.slice(0, 3)).toEqual([
      "workflow-step-logo-artwork-review",
      "workflow-step-logo-artwork-print",
      "workflow-step-logo-light-test",
    ]);
    expect(screen.getByTestId(`workflow-preview-status-${fixture.logo.template_code}`)).toHaveTextContent(/Draft local/i);
  });
});
