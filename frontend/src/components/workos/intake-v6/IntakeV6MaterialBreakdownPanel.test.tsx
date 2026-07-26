import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import IntakeV6MaterialBreakdownPanel from "@/components/workos/intake-v6/IntakeV6MaterialBreakdownPanel";
import type { IntakeV6MaterialBreakdownResponse } from "@/lib/intakeV6/intakeV6Api";

function breakdownWithOperations(): IntakeV6MaterialBreakdownResponse {
  return {
    workspace_id: "ws-1",
    template_code: "TPL-VOLUMETRIC-LETTERS",
    breakdown_scope: "quote_material_cost_estimate",
    nesting_rows: [],
    material_rows: [
      {
        material_key: "plexiglas_face",
        display_name: "plexiglas 3mm PMMA - opal",
        category: "material",
        quantity: 0.5834,
        unit: "m2",
        quantity_source: "nesting",
        quantity_quality: "calculated",
        quantity_with_waste: 0.5834,
        price_source: "missing",
        warnings: [],
        currency: "EUR",
      },
    ],
    consumable_rows: [],
    operation_rows: [
      {
        key: "cnc_face_cutting_plexiglas_3mm",
        display_name: "Debitare CNC față plexiglas 3mm PMMA - opal",
        operation_type: "cutting",
        material_name: "plexiglas 3mm PMMA - opal",
        thickness_mm: 3,
        quantity: 13.62,
        unit: "ml",
        passes: 1,
        pricing_status: "missing_rate",
        workstation_key: "cnc_router",
        required_skill_key: "cnc_operator",
        resource_mapping_status: "mapped",
      },
      {
        key: "cnc_face_bevel_plexiglas_3mm",
        display_name: "Șanfren CNC față plexiglas 3mm PMMA - opal",
        operation_type: "bevel",
        quantity: 13.62,
        unit: "ml",
        passes: 1,
        pricing_status: "missing_rate",
        workstation_key: "cnc_router",
        required_skill_key: "cnc_operator",
        resource_mapping_status: "pending_mapping",
      },
    ],
    edge_cant_operation_rows: [
      {
        key: "edge_cant_bond_to_face",
        display_name: "Lipire cant / volum pe față litere",
        operation_type: "assembly",
        quantity: 13.62,
        unit: "m",
        pricing_status: "missing_rate",
        workstation_key: "assembly_bench",
        required_skill_key: "assembly_operator",
        resource_mapping_status: "pending_mapping",
        source: "shared_edge_cant_rules",
      },
    ],
    totals: {
      material_cost_total: 0,
      estimated_cost_total: 0,
      currency: "EUR",
      contains_estimates: false,
      contains_missing_prices: true,
    },
    warnings: [],
  };
}

describe("IntakeV6MaterialBreakdownPanel CNC operations", () => {
  it("shows CNC operation rows separate from materials with missing rate label", () => {
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdownWithOperations()} loading={false} />);
    expect(screen.getByTestId("intake-v6-cnc-operation-rows")).toBeInTheDocument();
    expect(screen.getByText("Debitare CNC față plexiglas 3mm PMMA - opal")).toBeInTheDocument();
    expect(screen.getByText("Șanfren CNC față plexiglas 3mm PMMA - opal")).toBeInTheDocument();
    expect(screen.getAllByText(/Preț operație neconfigurat/).length).toBeGreaterThan(0);
    expect(screen.getByText("plexiglas 3mm PMMA - opal")).toBeInTheDocument();
  });

  it("shows edge cant operation rows separate from CNC", () => {
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdownWithOperations()} loading={false} />);
    expect(screen.getByTestId("intake-v6-edge-cant-operation-rows")).toBeInTheDocument();
    expect(screen.getByText("Operații cant / volum — preview ofertare")).toBeInTheDocument();
    expect(screen.getByText("Lipire cant / volum pe față litere")).toBeInTheDocument();
    expect(screen.queryByText(/^return$/i)).not.toBeInTheDocument();
  });

  it("shows Oracal 651 cant impact when wrapped material present", () => {
    const breakdown = breakdownWithOperations();
    breakdown.material_rows.push({
      material_key: "edge_cant_oracal_651",
      display_name: "Oracal 651 / cant volum",
      category: "material",
      quantity: 1.1442,
      base_quantity: 1.1442,
      priced_quantity: 1.1442,
      unit: "m2",
      quantity_source: "shared_edge_cant_rules",
      unit_price: 9,
      estimated_cost: 10.2978,
      currency: "EUR",
      price_source: "intake_v6_owner_oracal_651",
      quantity_quality: "calculated",
      quantity_with_waste: 1.1442,
      warnings: [],
    });
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdown} loading={false} />);
    expect(screen.getByTestId("intake-v6-oracal-cant-impact")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-oracal-cant-area").textContent).toContain("1.1442 m²");
    expect(screen.getByTestId("intake-v6-oracal-cant-unit-price").textContent).toContain("9");
  });

  it("shows analysis-bundle pending message when breakdown is unavailable", () => {
    render(<IntakeV6MaterialBreakdownPanel breakdown={null} loading={false} analysisBundlePending />);
    expect(screen.getByTestId("intake-v6-breakdown-analysis-bundle-pending")).toBeInTheDocument();
    expect(screen.getByText(/Salvează Review\/Setări/)).toBeInTheDocument();
  });

  it("shows eligible face area floor wording instead of high nesting precision when floor applied", () => {
    const breakdown = breakdownWithOperations();
    breakdown.material_rows[0] = {
      ...breakdown.material_rows[0],
      quantity: 0.6907,
      quantity_with_waste: 0.6907,
      quantity_basis: "sheet_nesting_role_split_quote_estimate",
      quantity_source: "svg_analysis_json.nesting|sheet_3000x2000|single_face",
      confidence: "estimate_from_nesting_high",
    };
    breakdown.warnings = [
      {
        code: "sheet_nesting_quantity_floor_applied",
        message:
          "Nesting placă — cantitatea estimată a fost ridicată la suma ariilor fețelor eligibile (footprint nesting sub aria pieselor).",
        source: "sheet_nesting|eligible_face_area_sum",
        severity: "info",
      },
    ];
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdown} loading={false} />);
    const basis = screen.getByTestId("intake-v6-basis-plexiglas_face");
    expect(basis.textContent).toContain("Estimare arie piese — floor arie eligibilă");
    expect(basis.textContent).not.toContain("Nesting — precizie ridicată");
    expect(screen.getByTestId("intake-v6-floor-hint-plexiglas_face")).toHaveTextContent(
      /Footprint-ul nesting era sub aria pieselor/,
    );
  });

  it("keeps high nesting precision wording when floor warning is absent", () => {
    const breakdown = breakdownWithOperations();
    breakdown.material_rows[0] = {
      ...breakdown.material_rows[0],
      quantity_basis: "sheet_nesting_role_split_quote_estimate",
      quantity_source: "svg_analysis_json.nesting|sheet_3000x2000|single_face",
      confidence: "estimate_from_nesting_high",
    };
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdown} loading={false} />);
    const basis = screen.getByTestId("intake-v6-basis-plexiglas_face");
    expect(basis.textContent).toContain("Nesting — precizie ridicată");
    expect(screen.queryByTestId("intake-v6-floor-hint-plexiglas_face")).not.toBeInTheDocument();
  });

  it("shows sheet quote review panel with status and candidates", () => {
    const breakdown = breakdownWithOperations();
    breakdown.sheet_quote_material_candidates = {
      eligible_face_area_sqm: 1.2638,
      placement_footprint_face_sqm: 1.1469,
      child_part_bbox_sum_sqm: 1.1469,
      semantic_group_bbox_sum_sqm: 1.2638,
      design_space_union_bbox_sqm: 2.1839,
      design_space_union_bbox_with_buffer_sqm: 2.2494,
      face_union_bbox_sqm: 2.5238,
      layout_occupied_area_sqm: 2.5238,
      nesting_shelf_occupied_sqm: 2.5238,
      full_sheet_allocation_sqm: 6.0,
      recommended_auto_candidate: {
        source: "child_part_bbox_sum_with_buffer",
        area_sqm: 1.2638,
        buffer_percent: 5,
        confidence: "low",
        reason: "preview",
      },
      requires_manual_review: true,
      manual_review_reason: "candidateSpread=2.20>1.35",
      selection: {
        selected_source: "eligible_area_floor",
        final_area_sqm: 1.2638,
        selection_mode: "current_floor",
        is_applied_to_quote: false,
      },
      selected_quote_sheet_area_sqm: 1.2638,
      selected_quote_sheet_area_source: "eligible_area_floor",
    };
    render(
      <IntakeV6MaterialBreakdownPanel breakdown={breakdown} loading={false} workspaceId="ws-ana" />,
    );
    expect(screen.getByTestId("intake-v6-sheet-quote-review")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-owner-review-banner").textContent).toContain(
      "Verificare operator obligatorie",
    );
    expect(screen.getByTestId("intake-v6-sheet-quote-status").textContent).toContain(
      "Verificare operator obligatorie",
    );
    expect(screen.getByTestId("intake-v6-sheet-quote-manual-review-cta")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-sheet-quote-selected-area-readable")).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId("intake-v6-sheet-quote-technical-toggle"));
    expect(screen.getByTestId("intake-v6-sheet-quote-selected-area-readable")).toHaveTextContent(
      "Arie selectată pentru review: 1.2638 m²",
    );
    expect(screen.getByTestId("intake-v6-sheet-quote-source-readable")).toHaveTextContent(
      "Sursă calcul: Floor arie eligibilă",
    );
    const panel = screen.getByTestId("intake-v6-sheet-quote-policy-table");
    expect(panel.textContent).toContain("Child part bbox sum");
    expect(panel.textContent).toContain("Recommended auto");
    expect(screen.getByTestId("intake-v6-sheet-quote-applied-readable")).toHaveTextContent(
      "Aplicat în ofertă finală: Nu",
    );
    expect(screen.getByTestId("intake-v6-sheet-quote-operator-decision")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Selectare sursă footprint (detaliu tehnic)"));
    expect(screen.getByText("Verificare footprint material")).toBeInTheDocument();
  });

  it("shows fresh snapshot note and hides stale warning after reanalysis", () => {
    const breakdown = breakdownWithOperations();
    breakdown.sheet_quote_material_candidates = {
      eligible_face_area_sqm: 1.2638,
      placement_footprint_face_sqm: 1.1469,
      layout_occupied_area_sqm: 2.5238,
      face_union_bbox_sqm: 2.5238,
      full_sheet_allocation_sqm: 6.0,
      requires_manual_review: true,
      manual_review_reason:
        "candidateSpread=2.20>1.35;pseudo_layer_or_unlayered_complexity;layoutOccupied/childPartBBox>1.75",
      selection: {
        selected_source: "eligible_area_floor",
        final_area_sqm: 1.2638,
        is_applied_to_quote: false,
      },
      selected_quote_sheet_area_sqm: 1.2638,
      selected_quote_sheet_area_source: "eligible_area_floor",
    };
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdown} loading={false} workspaceId="ws-ana" />);
    expect(screen.queryByTestId("intake-v6-stale-snapshot-warning")).not.toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-fresh-snapshot-note")).toBeInTheDocument();
    expect(screen.getByTestId("intake-v6-sheet-quote-applied-readable")).toHaveTextContent(
      "Aplicat în ofertă finală: Nu",
    );
  });

  it("shows stale warning before reanalysis when orphan defs present", () => {
    const breakdown = breakdownWithOperations();
    breakdown.sheet_quote_material_candidates = {
      eligible_face_area_sqm: 1.2638,
      orphan_defs_split_placement_sqm: 2.3211,
      layout_occupied_area_sqm: 5.36,
      requires_manual_review: true,
      manual_review_reason: "stale_orphan_defs_split_placement;orphan_defs_parts_in_analysis",
      selection: {
        selected_source: "eligible_area_floor",
        final_area_sqm: 1.2638,
        is_applied_to_quote: false,
      },
      selected_quote_sheet_area_sqm: 1.2638,
    };
    render(<IntakeV6MaterialBreakdownPanel breakdown={breakdown} loading={false} workspaceId="ws-ana" />);
    expect(screen.getByTestId("intake-v6-stale-snapshot-warning")).toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-fresh-snapshot-note")).not.toBeInTheDocument();
  });
});