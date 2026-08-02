import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import OpsGraphFrozenTechnicalMaterials, {
  formatFrozenMaterialQuantity,
} from "./OpsGraphFrozenTechnicalMaterials";
import type { FrozenTechnicalMaterialsProjection } from "@/api/execution";

function projection(
  overrides: Partial<FrozenTechnicalMaterialsProjection> = {},
): FrozenTechnicalMaterialsProjection {
  return {
    version: "ops_graph_frozen_technical_materials/v2",
    source: "order_snapshot_v2.product_aggregate_snapshot.materials",
    title: "Materiale tehnice conform comenzii",
    semantic_note:
      "Necesar tehnic înghețat la acceptarea comenzii. Nu reprezintă stoc, rezervare sau recomandare de achiziție.",
    status: "present",
    entry_count: 3,
    entries: [
      {
        entry_index: 0,
        material_code: "MAT-ORACAL-651",
        label: "Folie Oracal wrap",
        unit: "mp",
        quantity: 0.84,
        quantity_status: "derived",
        quantity_status_label_ro: "Calculată",
        provenance: "linked_module",
        component_ref: "comp_volum_aluminiu_module",
      },
      {
        entry_index: 1,
        material_code: "MAT-VOPSEA-RAL",
        label: "Vopsea RAL",
        unit: "buc",
        quantity: null,
        quantity_status: "source_missing",
        quantity_status_label_ro: "Sursă lipsă",
        quantity_missing_reason_ro:
          "Cantitatea nu poate fi calculată încă deoarece lipsește sursa tehnică necesară.",
        provenance: "linked_module",
        component_ref: "comp_volum_aluminiu_module",
      },
      {
        entry_index: 2,
        material_code: "MAT-ORACAL-651",
        label: "Folie față",
        unit: "mp",
        quantity: null,
        quantity_status: "reference_only",
        quantity_status_label_ro: "De referință",
        provenance: "parent",
        component_ref: "comp_face",
      },
    ],
    warnings: [],
    ...overrides,
  };
}

describe("formatFrozenMaterialQuantity", () => {
  it("renders honest labels for null statuses and never zero-coerces", () => {
    expect(formatFrozenMaterialQuantity(null)).toBe("Legacy / nespecificată");
    expect(formatFrozenMaterialQuantity(undefined)).toBe("Legacy / nespecificată");
    expect(formatFrozenMaterialQuantity(null, "legacy_unspecified")).toBe(
      "Legacy / nespecificată",
    );
    expect(formatFrozenMaterialQuantity(null, "reference_only")).toBe(
      "De referință",
    );
    expect(formatFrozenMaterialQuantity(null, "source_missing")).toBe("Sursă lipsă");
    expect(
      formatFrozenMaterialQuantity(null, "source_missing", "Sursă lipsă"),
    ).toBe("Sursă lipsă");
    expect(formatFrozenMaterialQuantity(0)).toBe("0");
    expect(formatFrozenMaterialQuantity(3)).toBe("3");
  });
});

describe("OpsGraphFrozenTechnicalMaterials", () => {
  it("shows planning-hints columns, statuses, duplicates, no stock language", () => {
    render(<OpsGraphFrozenTechnicalMaterials projection={projection()} />);
    expect(screen.getByTestId("ops-graph-frozen-materials-title")).toHaveTextContent(
      "Materiale tehnice conform comenzii",
    );
    expect(screen.getByTestId("ops-graph-frozen-materials-note")).toHaveTextContent(
      /Nu reprezintă stoc, rezervare sau recomandare de achiziție/,
    );
    expect(screen.getByTestId("ops-graph-frozen-materials-count")).toHaveTextContent(
      "3 intrări",
    );

    fireEvent.click(screen.getByTestId("ops-graph-frozen-materials-toggle"));
    expect(screen.getByTestId("ops-graph-frozen-materials-list")).toBeInTheDocument();
    expect(screen.getAllByText("MAT-ORACAL-651")).toHaveLength(2);
    expect(screen.getByTestId("ops-graph-frozen-material-qty-0")).toHaveTextContent(
      "0.84 mp",
    );
    expect(screen.getByTestId("ops-graph-frozen-material-qty-0")).toHaveAttribute(
      "data-quantity-null",
      "false",
    );
    expect(screen.getByTestId("ops-graph-frozen-material-status-0")).toHaveTextContent(
      "Calculată",
    );
    expect(screen.getByTestId("ops-graph-frozen-material-qty-1")).toHaveAttribute(
      "data-quantity-null",
      "true",
    );
    expect(screen.getByTestId("ops-graph-frozen-material-status-1")).toHaveTextContent(
      "Sursă lipsă",
    );
    expect(
      screen.getByText(
        /Cantitatea nu poate fi calculată încă deoarece lipsește sursa tehnică necesară/,
      ),
    ).toBeInTheDocument();
    expect(screen.getByTestId("ops-graph-frozen-material-status-2")).toHaveTextContent(
      "De referință",
    );

    fireEvent.click(screen.getByTestId("ops-graph-frozen-materials-details-toggle"));
    expect(screen.getByTestId("ops-graph-frozen-materials-details")).toBeInTheDocument();

    expect(screen.queryByText(/disponibil/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/rezervat/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/EUR/)).not.toBeInTheDocument();
    expect(screen.queryByText(/preț/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/cumpăr/i)).not.toBeInTheDocument();
  });

  it("shows honest empty state when snapshot materials absent", () => {
    render(
      <OpsGraphFrozenTechnicalMaterials
        projection={projection({
          status: "materials_absent",
          entry_count: 0,
          entries: [],
        })}
      />,
    );
    expect(screen.getByTestId("ops-graph-frozen-materials-empty")).toBeInTheDocument();
    expect(
      screen.queryByTestId("ops-graph-frozen-materials-toggle"),
    ).not.toBeInTheDocument();
  });

  it("returns null when projection missing", () => {
    const { container } = render(
      <OpsGraphFrozenTechnicalMaterials projection={null} />,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
