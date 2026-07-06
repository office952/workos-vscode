import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type {
  IntakeV6ArtworkFinish,
  IntakeV6LogicalListReadModelResponse,
  IntakeV6MaterialBreakdownResponse,
} from "@/lib/intakeV6/intakeV6Api";
import type { IntakeV6LetterGroupFinish } from "@/lib/intakeV6/intakeV6LetterGroups";
import IntakeV6LiveCalculationSummary from "./IntakeV6LiveCalculationSummary";

afterEach(() => cleanup());

const letterGroups: IntakeV6LetterGroupFinish[] = [{
  group_key: "letters",
  layer_name: "letters",
  face_area_m2: 1,
  face_finish_type: "none",
  return_finish_type: "white_aluminum",
  confirmed: true,
}];

const artworkFinishes: IntakeV6ArtworkFinish[] = [{
  layer_key: "logo",
  layer_name: "logo",
  execution_type: "print_laminate",
  color_mode: "polychrome",
  estimated_area_m2: 1,
  return_finish_type: "white_aluminum",
  confirmed: true,
}];

const baseBreakdown: IntakeV6MaterialBreakdownResponse = {
  workspace_id: "1",
  template_code: "TPL-VOLUMETRIC-LETTERS",
  breakdown_scope: "review",
  nesting_rows: [],
  material_rows: [
    {
      material_key: "plexiglas_face",
      display_name: "Plexiglas 3 mm / față litere",
      category: "material",
      quantity: 2,
      base_quantity: 2,
      unit: "m2",
      quantity_source: "nesting",
      quantity_quality: "calculated",
      quantity_with_waste: 2,
      priced_quantity: 2,
      unit_price: 16,
      price_source: "pricing_registry",
      estimated_cost: 32,
      material_cost: 32,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "forex_backing",
      display_name: "Forex 10 mm / spate litere",
      category: "material",
      quantity: 2,
      base_quantity: 2,
      unit: "m2",
      quantity_source: "backing",
      quantity_quality: "calculated",
      quantity_with_waste: 2,
      priced_quantity: 2,
      unit_price: 16,
      price_source: "pricing_registry",
      estimated_cost: 32,
      material_cost: 32,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "face_vinyl_651",
      display_name: "Vinil față Oracal 651",
      category: "material",
      quantity: 0.8,
      base_quantity: 0.8,
      unit: "m2",
      quantity_source: "letter_group_finishes",
      quantity_quality: "calculated",
      quantity_with_waste: 0.8,
      priced_quantity: 0.8,
      unit_price: 9,
      price_source: "intake_v6_owner_oracal_651",
      estimated_cost: 7.2,
      material_cost: 7.2,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "face_vinyl_8500",
      display_name: "Vinil față Oracal 8500",
      category: "material",
      quantity: 0.4,
      base_quantity: 0.4,
      unit: "m2",
      quantity_source: "letter_group_finishes",
      quantity_quality: "calculated",
      quantity_with_waste: 0.4,
      priced_quantity: 0.4,
      unit_price: 20,
      price_source: "intake_v6_owner_oracal_8500",
      estimated_cost: 8,
      material_cost: 8,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "return_material",
      display_name: "Cant / volum litere",
      category: "material",
      quantity: 20,
      base_quantity: 20,
      unit: "m",
      quantity_source: "quote_geometry.return_material",
      quantity_quality: "calculated",
      quantity_with_waste: 24,
      priced_quantity: 24,
      unit_price: 3,
      price_source: "registry",
      estimated_cost: 72,
      material_cost: 72,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "artwork_return_logo-stanga",
      display_name: "Cant / volum emblemă — logo stânga",
      category: "material",
      quantity: 2.5,
      base_quantity: 2.5,
      unit: "m",
      quantity_source: "artwork_finishes",
      quantity_quality: "calculated",
      quantity_with_waste: 3,
      priced_quantity: 3,
      unit_price: 3,
      price_source: "registry",
      estimated_cost: 9,
      material_cost: 9,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "artwork_logo-stanga_print_vinyl",
      display_name: "Material print Orafol — logo stânga",
      category: "material",
      quantity: 0.5,
      base_quantity: 0.5,
      unit: "m2",
      quantity_source: "artwork_finishes",
      quantity_quality: "calculated",
      quantity_with_waste: 0.6,
      priced_quantity: 0.6,
      unit_price: 1.5,
      price_source: "pricing_registry",
      estimated_cost: 0.9,
      material_cost: 0.9,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "artwork_logo-stanga_laminated_vinyl",
      display_name: "Material laminare Orafol — logo stânga",
      category: "material",
      quantity: 0.5,
      base_quantity: 0.5,
      unit: "m2",
      quantity_source: "artwork_finishes",
      quantity_quality: "calculated",
      quantity_with_waste: 0.6,
      priced_quantity: 0.6,
      unit_price: 2,
      price_source: "pricing_registry",
      estimated_cost: 1.2,
      material_cost: 1.2,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "edge_cant_oracal_651",
      display_name: "Oracal 651 / cant volum",
      category: "material",
      quantity: 0.25,
      base_quantity: 0.25,
      unit: "m2",
      quantity_source: "shared_edge_cant_rules",
      quantity_quality: "calculated",
      quantity_with_waste: 0.25,
      priced_quantity: 0.25,
      unit_price: 9,
      price_source: "shared_edge_cant_rules|intake_v6_owner_oracal_651",
      estimated_cost: 2.25,
      material_cost: 2.25,
      warnings: [],
      currency: "EUR",
    },
  ],
  consumable_rows: [
    {
      material_key: "led_modules",
      display_name: "Module LED (0.75 W / buc)",
      category: "consumable",
      quantity: 145,
      base_quantity: 145,
      unit: "buc",
      quantity_source: "finish_setup",
      quantity_quality: "calculated",
      quantity_with_waste: 174,
      priced_quantity: 174,
      unit_price: 0.5,
      price_source: "pricing_registry",
      estimated_cost: 87,
      material_cost: 87,
      warnings: [],
      currency: "EUR",
    },
    {
      material_key: "mounting_accessories_percent",
      display_name: "Accesorii montaj / conectori (5% cost confectie)",
      category: "consumable",
      quantity: 1,
      base_quantity: 1,
      unit: "job",
      quantity_source: "owner_policy",
      quantity_quality: "calculated",
      quantity_with_waste: 1,
      priced_quantity: 1,
      unit_price: 10,
      price_source: "intake_v6_owner_mounting_accessories_5pct",
      estimated_cost: 10,
      material_cost: 10,
      warnings: [],
      currency: "EUR",
    },
  ],
  operation_rows: [
    {
      key: "cnc_face_cutting_plexiglas_3mm",
      display_name: "Debitare CNC față Plexiglas 3 mm",
      operation_type: "cutting",
      quantity: 20,
      unit: "ml",
      operation_equivalent_quantity: 20,
      operation_equivalent_unit: "ml-pass",
      unit_price: 1.5,
      estimated_cost: 30,
      pricing_status: "pricing_registry",
    },
    {
      key: "artwork_logo-stanga_print_service",
      display_name: "Serviciu print — logo stânga",
      operation_type: "print_vinyl",
      quantity: 0.6,
      unit: "m2",
      operation_equivalent_quantity: 0.6,
      operation_equivalent_unit: "m2",
      unit_price: 8,
      estimated_cost: 4.8,
      pricing_status: "owner_confirmed",
    },
    {
      key: "artwork_logo-stanga_lamination_service",
      display_name: "Serviciu laminare X-PRO — logo stânga",
      operation_type: "lamination",
      quantity: 0.6,
      unit: "m2",
      operation_equivalent_quantity: 0.6,
      operation_equivalent_unit: "m2",
      unit_price: 2,
      estimated_cost: 1.2,
      pricing_status: "owner_confirmed",
    },
    {
      key: "artwork_logo-stanga_application_service",
      display_name: "Serviciu aplicare — logo stânga",
      operation_type: "vinyl_application",
      quantity: 0.6,
      unit: "m2",
      operation_equivalent_quantity: 0.6,
      operation_equivalent_unit: "m2",
      unit_price: 3,
      estimated_cost: 1.8,
      pricing_status: "owner_confirmed",
    },
  ],
  edge_cant_operation_rows: [
    {
      key: "edge_cant_oracal_wrap",
      display_name: "Aplicare Oracal 651 pe cant / volum",
      operation_type: "vinyl_application",
      quantity: 4,
      unit: "m",
      estimated_cost: null,
      pricing_status: "missing_rate",
    },
  ],
  totals: {
    material_cost_total: 298.45,
    estimated_cost_total: 298.45,
    currency: "EUR",
    contains_estimates: false,
    contains_missing_prices: true,
  },
  warnings: [],
};

const logicalList: IntakeV6LogicalListReadModelResponse = {
  read_only: true,
  source: "gradi_logical_list_read_model_v1",
  core_row_count: 21,
  target_core_row_count: 21,
  core_rows_complete: true,
  categories: ["TOATE", "MATERIALE", "SERVICII / OPERATII", "MANOPERA"],
  rows: [
    ["material.plexiglas_face", "MATERIALE", "MATCHED", "Plexiglas 3 mm / fata litere", 1.2638, "m2", "MATERIAL_PLEXI_FACE_BY_AREA_V1", "v1", "proposed_binding", [], [], 1],
    ["material.logo_plexiglas_face", "MATERIALE", "MATCHED", "Plexiglas 3 mm / embleme/logo", 0.8005, "m2", "MATERIAL_PLEXI_LOGO_FACE_BY_AREA_V1", "v1", "proposed_binding", [], [], 0],
    ["material.forex_backing", "MATERIALE", "PARTIAL", "Forex 10 mm / spate litere", 1.2638, "m2", "MATERIAL_FOREX_BACK_BY_AREA_V1", "v1", "proposed_binding", ["BACKING_AREA_FALLBACK_USED"], [], 1],
    ["material.face_oracal", "MATERIALE", "PARTIAL_TARIFF_CONFIRMATION_REQUIRED", "Vinil fata Oracal - consum pe serii 641 + 651", 1.3751, "m2", "MATERIAL_ORACAL_FACE_BY_NESTED_AREA_V1", "v1", "proposed_binding", [], ["ORACAL_ROLL_COLOR_SPLIT_MISSING"], 2],
    ["material.print", "MATERIALE", "SPLIT_IN_RUNTIME", "Material print Orafol", 0.996821, "m2", "MATERIAL_PRINT_BY_NESTED_AREA_V1", "v1", "proposed_binding", ["PRINT_ROWS_AGGREGATED_FOR_LOGICAL_LIST"], [], 3],
    ["material.lamination", "MATERIALE", "SPLIT_IN_RUNTIME", "Material laminare Orafol", 0.996821, "m2", "MATERIAL_LAMINATION_BY_NESTED_AREA_V1", "v1", "proposed_binding", ["LAMINATION_ROWS_AGGREGATED_FOR_LOGICAL_LIST"], [], 3],
    ["material.led_modules", "MATERIALE", "MATCHED", "Module LED", 144, "buc", "MATERIAL_LED_MODULES_BY_AREA_DENSITY_V1", "v1", "legacy_unversioned", ["FORMULA_TRACE_MISSING"], [], 1],
    ["material.led_psu", "MATERIALE", "MATCHED", "Sursa LED 12V", 1, "buc", "MATERIAL_PSU_BY_POWER_SAFETY_FACTOR_V1", "v1", "legacy_unversioned", [], [], 1],
    ["service.cnc_face", "SERVICII_OPERATII", "MATCHED", "Debitare CNC fata Plexiglas", 25.0188, "ml", "SERVICE_CNC_FACE_CUT_BY_CONTOUR_LENGTH_V1", "v1", "proposed_binding", [], [], 0],
    ["service.print", "SERVICII_OPERATII", "SPLIT_IN_RUNTIME", "Serviciu print", 1.1962, "m2", "SERVICE_PRINT_BY_AREA_V1", "v1", "proposed_binding", ["PRINT_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST"], [], 3],
    ["service.lamination", "SERVICII_OPERATII", "SPLIT_IN_RUNTIME", "Serviciu laminare X-PRO", 1.1962, "m2", "SERVICE_LAMINATION_BY_AREA_V1", "v1", "legacy_unversioned", ["LAMINATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST"], [], 3],
    ["service.application", "SERVICII_OPERATII", "SPLIT_IN_RUNTIME", "Serviciu aplicare", 1.1962, "m2", "SERVICE_APPLICATION_BY_AREA_V1", "v1", "legacy_unversioned", ["APPLICATION_SERVICE_ROWS_AGGREGATED_FOR_LOGICAL_LIST"], [], 3],
    ["labor.cant_glue", "MANOPERA", "MATCHED", "Lipire cant / volum pe fata litere", 31.6382, "m", "LABOR_CANT_GLUE_BY_PERIMETER_V1", "v1", "proposed_binding", [], [], 1],
  ].map(([line_id, category, status, display_label, quantity, unit, formula_code_proposed, formula_version_proposed, formula_status, gaps, warnings, childCount]) => ({
    line_id: String(line_id),
    category: String(category),
    status: String(status),
    display_label: String(display_label),
    quantity: Number(quantity),
    unit: String(unit),
    formula_code_proposed: String(formula_code_proposed),
    formula_version_proposed: String(formula_version_proposed),
    formula_status: String(formula_status),
    gaps: gaps as string[],
    warnings: warnings as string[],
    child_rows: Array.from({ length: Number(childCount) }, (_, index) => ({ index })),
  })),
  warnings: ["BACKING_AREA_FALLBACK_USED"],
  blockers: [],
  validation: { formula_trace_metadata_present: true },
};

describe("IntakeV6LiveCalculationSummary", () => {
  it("uses logical-list rows as the primary owner-facing list when available", () => {
    render(
      <IntakeV6LiveCalculationSummary
        breakdown={baseBreakdown}
        faceBackDraft={null}
        logicalList={logicalList}
      />,
    );

    expect(screen.getByTestId("intake-v6-logical-list-summary")).toHaveTextContent("21/21");
    expect(screen.getByTestId("intake-v6-live-material-used-material.plexiglas_face")).toHaveTextContent(
      /Plexiglas 3 mm \/ fata litere/,
    );
    expect(screen.getByTestId("intake-v6-live-material-used-material.logo_plexiglas_face")).toHaveTextContent(
      /Plexiglas 3 mm \/ embleme\/logo/,
    );
    expect(screen.getByTestId("intake-v6-live-material-used-material.forex_backing")).toHaveTextContent(
      /Forex 10 mm \/ spate litere/,
    );
    expect(screen.getByTestId("intake-v6-live-material-used-material.face_oracal")).toHaveTextContent(/Oracal/);
    expect(screen.getByTestId("intake-v6-live-material-used-material.led_modules")).toHaveTextContent(/Module LED/);
    expect(screen.getByTestId("intake-v6-live-material-used-service.cnc_face")).toHaveTextContent(/Debitare CNC/);
    expect(screen.getByTestId("intake-v6-live-material-used-labor.cant_glue")).toHaveTextContent(/Lipire cant/);
    expect(screen.queryByTestId("intake-v6-live-material-used-plexi_letters")).not.toBeInTheDocument();
  });

  it("shows logical-list formula metadata, gaps, categories, and child row counts", () => {
    render(<IntakeV6LiveCalculationSummary breakdown={baseBreakdown} faceBackDraft={null} logicalList={logicalList} />);

    expect(screen.getByTestId("intake-v6-logical-list-category-MATERIALE")).toHaveTextContent(/Materiale/);
    expect(screen.getByTestId("intake-v6-logical-list-category-SERVICII_OPERATII")).toHaveTextContent(/Servicii/);
    expect(screen.getByTestId("intake-v6-logical-list-category-MANOPERA")).toHaveTextContent(/Manoperă/);
    expect(screen.getByTestId("intake-v6-logical-formula-material.plexiglas_face")).toHaveTextContent(
      "MATERIAL_PLEXI_FACE_BY_AREA_V1 @ v1",
    );
    expect(screen.getByTestId("intake-v6-logical-gaps-material.forex_backing")).toHaveTextContent(
      "BACKING_AREA_FALLBACK_USED",
    );
    expect(screen.getByTestId("intake-v6-logical-children-material.face_oracal")).toHaveTextContent("child rows: 2");
  });

  it("renders one compact table with quantity and price columns", () => {
    render(
      <IntakeV6LiveCalculationSummary
        breakdown={baseBreakdown}
        faceBackDraft={null}
        letterGroups={letterGroups}
        artworkFinishes={artworkFinishes}
      />,
    );

    expect(screen.getByTestId("intake-v6-live-calculation-summary")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-live-totals-summary")).toBeInTheDocument();
    expect(screen.getByText("Linie")).toBeInTheDocument();
    expect(screen.getByText("Consum")).toBeInTheDocument();
    expect(screen.getByText("Preț")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-live-material-total")).toHaveTextContent(/298[,.]45\s*EUR/);
    expect(screen.getByTestId("intake-v6-live-missing-rates-banner")).toHaveTextContent(/Tarife lipsă/);
  });

  it("splits plexiglas between letters and emblems while keeping total price allocated", () => {
    render(
      <IntakeV6LiveCalculationSummary
        breakdown={baseBreakdown}
        faceBackDraft={null}
        letterGroups={letterGroups}
        artworkFinishes={artworkFinishes}
      />,
    );

    expect(screen.getByTestId("intake-v6-live-material-used-plexi_letters")).toHaveTextContent(
      /Plexiglas 3 mm \/ față litere/,
    );
    expect(screen.getByTestId("intake-v6-live-material-used-plexi_letters")).toHaveTextContent(/1\.000 m²/);
    expect(screen.getByTestId("intake-v6-live-material-cost-plexi_letters")).toHaveTextContent("16.00 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-plexi_emblems")).toHaveTextContent(
      /Plexiglas 3 mm \/ embleme\/logo/,
    );
    expect(screen.getByTestId("intake-v6-live-material-used-plexi_emblems")).toHaveTextContent(/1\.000 m²/);
    expect(screen.getByTestId("intake-v6-live-material-cost-plexi_emblems")).toHaveTextContent("16.00 EUR");
  });

  it("keeps Oracal series and cant Oracal separated with their own prices", () => {
    render(<IntakeV6LiveCalculationSummary breakdown={baseBreakdown} faceBackDraft={null} />);

    expect(screen.getByTestId("intake-v6-live-material-used-oracal_651")).toHaveTextContent(/Oracal 651/);
    expect(screen.getByTestId("intake-v6-live-material-cost-oracal_651")).toHaveTextContent("7.20 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-oracal_8500")).toHaveTextContent(/Oracal 8500/);
    expect(screen.getByTestId("intake-v6-live-material-cost-oracal_8500")).toHaveTextContent("8.00 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-oracal_cant_651")).toHaveTextContent(
      /Oracal 651 \/ cant volum/,
    );
    expect(screen.getByTestId("intake-v6-live-material-cost-oracal_cant_651")).toHaveTextContent("2.25 EUR");
  });

  it("shows print material, laminate material, service rows, CNC, and missing edge operation prices", () => {
    render(<IntakeV6LiveCalculationSummary breakdown={baseBreakdown} faceBackDraft={null} />);

    expect(screen.getByTestId("intake-v6-live-material-used-print_vinyl")).toHaveTextContent(
      /Material print Orafol/,
    );
    expect(screen.getByTestId("intake-v6-live-material-cost-print_vinyl")).toHaveTextContent("0.90 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-lamination_material")).toHaveTextContent(/Material laminare Orafol/);
    expect(screen.getByTestId("intake-v6-live-material-cost-lamination_material")).toHaveTextContent("1.20 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-print_service")).toHaveTextContent(/Serviciu print/);
    expect(screen.getByTestId("intake-v6-live-material-cost-print_service")).toHaveTextContent("4.80 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-lamination_service")).toHaveTextContent(/Serviciu laminare X-PRO/);
    expect(screen.getByTestId("intake-v6-live-material-cost-lamination_service")).toHaveTextContent("1.20 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-application_service")).toHaveTextContent(/Serviciu aplicare/);
    expect(screen.getByTestId("intake-v6-live-material-cost-application_service")).toHaveTextContent("1.80 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-cnc_face")).toHaveTextContent(/Debitare CNC față Plexiglas/);
    expect(screen.getByTestId("intake-v6-live-material-cost-cnc_face")).toHaveTextContent("30.00 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-edge_oracal_application")).toHaveTextContent(
      /Aplicare Oracal cant/,
    );
    expect(screen.getByTestId("intake-v6-live-material-cost-edge_oracal_application")).toHaveTextContent(
      /tarif lipsă/,
    );
    expect(screen.getByTestId("intake-v6-live-missing-rates-banner")).toHaveTextContent(/Tarife lipsă/i);
    expect(screen.getByTestId("intake-v6-live-missing-rates-list")).toHaveTextContent(/Aplicare Oracal cant/);
  });

  it("shows LED and mounting accessories as separate consumable rows", () => {
    render(<IntakeV6LiveCalculationSummary breakdown={baseBreakdown} faceBackDraft={null} />);

    expect(screen.getByTestId("intake-v6-live-material-used-led_modules")).toHaveTextContent(/Module LED/);
    expect(screen.getByTestId("intake-v6-live-material-used-led_modules")).toHaveTextContent(/145 buc/);
    expect(screen.getByTestId("intake-v6-live-material-cost-led_modules")).toHaveTextContent("87.00 EUR");

    expect(screen.getByTestId("intake-v6-live-material-used-mounting_accessories_percent")).toHaveTextContent(
      /Accesorii montaj/,
    );
    expect(screen.getByTestId("intake-v6-live-material-cost-mounting_accessories_percent")).toHaveTextContent(
      "10.00 EUR",
    );
  });

  it("shows pending save banner when local edits are unsaved", () => {
    render(<IntakeV6LiveCalculationSummary breakdown={baseBreakdown} faceBackDraft={null} pendingSave />);
    expect(screen.getByTestId("intake-v6-live-pending-save")).toHaveTextContent(/modificari in curs/i);
  });

  it("limits preview lines in right panel and links to details sheet", () => {
    render(
      <IntakeV6LiveCalculationSummary
        breakdown={baseBreakdown}
        faceBackDraft={null}
        layout="rightPanel"
      />,
    );

    expect(screen.getByTestId("intake-v6-review-calculator-panel")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-live-preview-more")).toHaveTextContent(/\+/);
    expect(screen.getByTestId("intake-v6-review-calculator-details")).toBeInTheDocument();
  });

  it("collapses details on mobile until toggled", () => {
    render(<IntakeV6LiveCalculationSummary breakdown={baseBreakdown} faceBackDraft={null} />);

    const toggle = screen.getByTestId("intake-v6-live-materials-used-toggle");
    const listShell = screen.getByTestId("intake-v6-live-materials-list").parentElement?.parentElement;
    expect(listShell).toHaveClass("hidden");
    fireEvent.click(toggle);
    expect(listShell).toHaveClass("block");
  });

  it("filters line rows by category chip", () => {
    render(
      <IntakeV6LiveCalculationSummary
        breakdown={baseBreakdown}
        faceBackDraft={null}
        letterGroups={letterGroups}
        artworkFinishes={artworkFinishes}
      />,
    );

    expect(screen.getByTestId("intake-v6-live-calc-filters")).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-live-filter-services_operations"));
    expect(screen.getByTestId("intake-v6-live-material-used-cnc_face")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-live-material-used-plexi_letters")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("intake-v6-live-filter-all"));
    expect(screen.getByTestId("intake-v6-live-material-used-plexi_letters")).toBeInTheDocument();
  });

  it("shows filter subtotal footer when a category filter is active", () => {
    render(
      <IntakeV6LiveCalculationSummary
        breakdown={baseBreakdown}
        faceBackDraft={null}
        letterGroups={letterGroups}
        artworkFinishes={artworkFinishes}
      />,
    );

    expect(screen.queryByTestId("intake-v6-live-filter-subtotal")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-live-filter-services_operations"));
    expect(screen.getByTestId("intake-v6-live-filter-subtotal")).toHaveTextContent(/Subtotal filtru:/);
    expect(screen.getByTestId("intake-v6-live-filter-line-count")).toHaveTextContent(/Nr\. linii: 5/);
    expect(screen.queryByTestId("intake-v6-live-filter-artwork")).not.toBeInTheDocument();
  });

  it("shows operator cant perimeter in details sheet", () => {
    render(
      <IntakeV6LiveCalculationSummary
        breakdown={baseBreakdown}
        faceBackDraft={null}
        layout="bar"
        operatorCantPerimeterM={20.8795}
        letterGroups={letterGroups}
        artworkFinishes={artworkFinishes}
      />,
    );

    fireEvent.click(screen.getByTestId("intake-v6-price-spine-details"));
    expect(screen.getByTestId("intake-v6-live-cant-metrics")).toHaveTextContent(/20\.88 m/);
  });
});