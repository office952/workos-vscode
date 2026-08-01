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
    version: "ops_graph_frozen_technical_materials/v1",
    source: "order_snapshot_v2.product_aggregate_snapshot.materials",
    title: "Materiale tehnice conform comenzii",
    semantic_note:
      "Lista provine din definiția tehnică înghețată a comenzii. Nu reprezintă stoc, rezervare sau consum.",
    status: "present",
    entry_count: 2,
    entries: [
      {
        entry_index: 0,
        material_code: "MAT-A",
        label: "Alpha",
        unit: "mp",
        quantity: null,
        provenance: "parent",
        component_ref: "comp_face",
      },
      {
        entry_index: 1,
        material_code: "MAT-A",
        label: "Alpha module",
        unit: "mp",
        quantity: null,
        provenance: "linked_module",
        component_ref: "comp_lateral",
      },
    ],
    warnings: [],
    ...overrides,
  };
}

describe("formatFrozenMaterialQuantity", () => {
  it("renders honest labels for null statuses and never zero-coerces", () => {
    expect(formatFrozenMaterialQuantity(null)).toBe("Nespecificată");
    expect(formatFrozenMaterialQuantity(undefined)).toBe("Nespecificată");
    expect(formatFrozenMaterialQuantity(null, "legacy_unspecified")).toBe(
      "Nespecificată",
    );
    expect(formatFrozenMaterialQuantity(null, "reference_only")).toBe(
      "Referință (fără cantitate)",
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
  it("shows semantic title, note, count; expands duplicates without merging", () => {
    render(<OpsGraphFrozenTechnicalMaterials projection={projection()} />);
    expect(screen.getByTestId("ops-graph-frozen-materials-title")).toHaveTextContent(
      "Materiale tehnice conform comenzii",
    );
    expect(screen.getByTestId("ops-graph-frozen-materials-note")).toHaveTextContent(
      /Nu reprezintă stoc, rezervare sau consum/,
    );
    expect(screen.getByTestId("ops-graph-frozen-materials-count")).toHaveTextContent(
      "2 intrări",
    );
    expect(screen.queryByTestId("ops-graph-frozen-materials-list")).not.toBeInTheDocument();

    fireEvent.click(screen.getByTestId("ops-graph-frozen-materials-toggle"));
    expect(screen.getByTestId("ops-graph-frozen-materials-list")).toBeInTheDocument();
    expect(screen.getAllByText("MAT-A")).toHaveLength(2);
    expect(screen.getByTestId("ops-graph-frozen-material-qty-0")).toHaveTextContent(
      "Nespecificată",
    );
    expect(screen.getByTestId("ops-graph-frozen-material-qty-0")).toHaveAttribute(
      "data-quantity-null",
      "true",
    );
    expect(screen.queryByText(/consum/i)).toBeInTheDocument(); // semantic note only
    expect(screen.queryByText(/rezervat/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/disponibil/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/EUR/)).not.toBeInTheDocument();
    expect(screen.queryByText(/preț/i)).not.toBeInTheDocument();
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
