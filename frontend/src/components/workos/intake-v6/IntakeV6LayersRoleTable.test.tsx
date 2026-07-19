import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import IntakeV6LayersRoleTable from "./IntakeV6LayersRoleTable";
import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";

function buildReport(): SvgAnalysisCoreReport {
  return {
    schemaName: "svg-analyzer-analysis",
    schemaVersion: "1.11.0",
    engineVersion: "test",
    createdAt: "2026-07-01T00:00:00Z",
    sourceFileName: "gradi-curat.svg",
    sourceFileSize: 123,
    file: {
      name: "gradi-curat.svg",
      sizeBytes: 123,
      detectedUnits: null,
      conversionConfidence: "high",
      physicalSizeSource: "svg width/height",
    },
    document: {
      widthMm: 5087,
      heightMm: 600,
      viewBox: "0 0 519.77 61.30",
      viewBoxWidth: 519.77,
      viewBoxHeight: 61.3,
      scaleX: 1,
      scaleY: 1,
      mmPerViewBoxUnit: 1,
      boundingAreaSqm: 1,
      filledAreaSqm: 1,
      areaConfidence: "high",
      areaEstimated: false,
    },
    geometry: {
      perimeterMm: 1000,
      perimeterMl: 1,
      perimeterConfidence: "high",
      pathElementCount: 1,
      subPathCount: 1,
      closedSubPathCount: 1,
      openSubPathCount: 0,
      shapeCount: 1,
      transformCount: 0,
    },
    layers: [
      {
        id: "pseudo:maria",
        name: "pseudo maria (blue)",
        layerKind: "pseudo",
        layerOrigin: "solid_fill_cluster",
        roleReason: "Pseudo-layer generated from solid vector fill color cluster.",
        autoRole: "face",
        autoConfidence: "high",
        autoRoleCandidates: [],
        paintEvidence: {
          fills: ["#00A0E3"],
          strokes: [],
          gradientRefs: [],
          hasGradient: false,
          hasPattern: false,
          hasImage: false,
          isMulticolor: false,
          fillCount: 1,
          textElementCount: 0,
          paintKind: "solid",
        },
        productionHint: "cnc_cut",
        roleGuess: "face",
        elementCount: 1,
        pathElementCount: 1,
        subPathCount: 1,
        closedSubPathCount: 1,
        openSubPathCount: 0,
        widthMm: 10,
        heightMm: 10,
        boundingAreaSqm: 1,
        filledAreaSqm: 1,
        areaConfidence: "high",
        perimeterMm: 100,
        perimeterMl: 0.1,
        colors: ["#00A0E3"],
        warnings: [],
      },
      {
        id: "logo-stanga",
        name: "logo stanga",
        layerKind: "pseudo",
        layerOrigin: "stroke_vector_outline",
        roleReason: "Stroke-only vector isolated as logo/artwork candidate.",
        autoRole: "printed_artwork",
        autoConfidence: "high",
        autoRoleCandidates: [],
        paintEvidence: {
          fills: [],
          strokes: ["#2B2A29"],
          gradientRefs: [],
          hasGradient: false,
          hasPattern: false,
          hasImage: false,
          isMulticolor: false,
          fillCount: 0,
          textElementCount: 0,
          paintKind: "none",
        },
        productionHint: "print_vinyl",
        roleGuess: "printed_artwork",
        elementCount: 1,
        pathElementCount: 1,
        subPathCount: 1,
        closedSubPathCount: 1,
        openSubPathCount: 0,
        widthMm: 10,
        heightMm: 10,
        boundingAreaSqm: 1,
        filledAreaSqm: null,
        areaConfidence: "low",
        perimeterMm: 100,
        perimeterMl: 0.1,
        colors: ["#2B2A29"],
        warnings: [],
      },
    ],
    layerRoleConfirmation: {
      schemaVersion: "layer_role_confirmation_v1",
      confirmationStatus: "partial",
      layers: [],
    },
    colors: {
      unique: ["#00A0E3", "#2B2A29"],
      dominant: ["#00A0E3"],
      fills: ["#00A0E3"],
      strokes: ["#2B2A29"],
      byLayer: {
        "pseudo maria (blue)": ["#00A0E3"],
        "logo stanga": ["#2B2A29"],
      },
    },
    warnings: [],
    errors: [],
    confidence: {
      dimensions: "high",
      perimeter: "high",
      area: "high",
      layers: "high",
      colors: "high",
    },
    benchmark: {
      status: "NO_REFERENCE",
      referenceSource: null,
      referencePerimeterMm: null,
      analyzerPerimeterMm: null,
      deltaMm: null,
      deltaPercent: null,
      passThresholdPercent: null,
    },
    exportMeta: {
      exportedAt: "2026-07-01T00:00:00Z",
      exportedBy: "test",
      appName: "test",
      schemaVersion: "1.11.0",
      notes: [],
    },
  } as SvgAnalysisCoreReport;
}

function buildSixLayerReport(): SvgAnalysisCoreReport {
  const base = buildReport();
  const variants = [
    { id: "pseudo:soare", name: "pseudo soare (red)", color: "#E31E24" },
    { id: "pseudo:ana", name: "pseudo ana (green)", color: "#009846" },
    { id: "pseudo:gradinita", name: "pseudo gradinita (orange)", color: "#EF7F1A" },
    { id: "logo-dreapta", name: "logo dreapta", color: "#2B2A29" },
  ];

  base.layers = [
    ...base.layers,
    ...variants.map((variant, index) => ({
      ...base.layers[Math.min(index, 1)],
      id: variant.id,
      name: variant.name,
      colors: [variant.color],
      paintEvidence:
        variant.id === "logo-dreapta"
          ? {
              ...base.layers[1].paintEvidence,
              strokes: [variant.color],
            }
          : {
              ...base.layers[0].paintEvidence,
              fills: [variant.color],
            },
    })),
  ];

  return base;
}

function buildLogoOnlyReport(): SvgAnalysisCoreReport {
  const base = buildReport();
  base.sourceFileName = "cerc100cm.svg";
  base.layers = [base.layers[1]!];
  base.colors = {
    unique: ["#2B2A29"],
    dominant: ["#2B2A29"],
    fills: [],
    strokes: ["#2B2A29"],
    byLayer: {
      "logo stanga": ["#2B2A29"],
    },
  };
  return base;
}

function buildConfirmation(): LayerRoleConfirmation {
  return {
    schemaVersion: "layer_role_confirmation_v1",
    confirmationStatus: "partial",
    layers: [
      {
        layerKey: "pseudo:maria",
        layerId: "pseudo:maria",
        layerName: "pseudo maria (blue)",
        autoRole: "face",
        autoConfidence: "high",
        autoRoleCandidates: [],
        confirmedRole: null,
        confirmationState: "pending",
        operatorNote: null,
        paintEvidence: {
          fills: ["#00A0E3"],
          strokes: [],
          gradientRefs: [],
          hasGradient: false,
          hasPattern: false,
          hasImage: false,
          isMulticolor: false,
          fillCount: 1,
          textElementCount: 0,
          paintKind: "solid",
        },
        productionHint: "cnc_cut",
      },
      {
        layerKey: "logo-stanga",
        layerId: "logo-stanga",
        layerName: "logo stanga",
        autoRole: "printed_artwork",
        autoConfidence: "high",
        autoRoleCandidates: [],
        confirmedRole: null,
        confirmationState: "pending",
        operatorNote: null,
        paintEvidence: {
          fills: [],
          strokes: ["#2B2A29"],
          gradientRefs: [],
          hasGradient: false,
          hasPattern: false,
          hasImage: false,
          isMulticolor: false,
          fillCount: 0,
          textElementCount: 0,
          paintKind: "none",
        },
        productionHint: "print_vinyl",
      },
    ],
  };
}

describe("IntakeV6LayersRoleTable display labels", () => {
  it("hides pseudo from main labels and shows detected group copy", () => {
    const onUpdateLayerRole = vi.fn();
    render(
      <IntakeV6LayersRoleTable
        report={buildReport()}
        confirmation={buildConfirmation()}
        onUpdateLayerRole={onUpdateLayerRole}
        layout="cards"
        workspaceTemplateCode="TPL-VOLUMETRIC-LETTERS_v2"
      />,
    );

    expect(screen.getByText("Element 1 — albastru")).toBeInTheDocument();
    expect(screen.getByText("Grup detectat: maria")).toBeInTheDocument();
    expect(screen.queryByText(/Țintă automată Product System/i)).not.toBeInTheDocument();
    expect(screen.getAllByText("Rol geometrie").length).toBeGreaterThan(0);
    expect(screen.getByText("Element 2 — contur negru")).toBeInTheDocument();
    expect(screen.getByText("Grup detectat: Logo 1")).toBeInTheDocument();
    expect(screen.queryByText(/pseudo maria/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/pseudo fill/i)).not.toBeInTheDocument();
  });

  it("shows Product System component on the same card as geometry role", () => {
    render(
      <IntakeV6LayersRoleTable
        report={buildReport()}
        confirmation={buildConfirmation()}
        onUpdateLayerRole={() => undefined}
        layout="cards"
        workspaceTemplateCode="TPL-VOLUMETRIC-LETTERS_v2"
        bindables={[
          {
            component_template_code: "TPL-VOLUMETRIC-FACE_v1",
            owner_label: "Vector litere",
            accepted_geometry_roles: ["LETTER_VECTOR_SET"],
            selection_mode: "LAYER_OR_GROUP",
            cardinality: "MULTI",
            required: true,
            available: true,
            active: true,
            active_by_default: true,
          },
          {
            component_template_code: "TPL-VOLUMETRIC-LOGO_v1",
            owner_label: "Vector logo",
            accepted_geometry_roles: ["LOGO_VECTOR_SET"],
            selection_mode: "LAYER_OR_GROUP",
            cardinality: "MULTI",
            required: false,
            available: true,
            active: false,
            active_by_default: false,
            guards: ["candidate_only"],
          },
        ]}
      />,
    );

    expect(screen.getAllByText("Față litere volumetrice").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Componentă logo volumetric").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Avertizare").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Componentă produs").length).toBeGreaterThan(0);
  });

  it("keeps role selection functional with display-only labels", () => {
    const onUpdateLayerRole = vi.fn();
    render(
      <IntakeV6LayersRoleTable
        report={buildReport()}
        confirmation={buildConfirmation()}
        onUpdateLayerRole={onUpdateLayerRole}
        layout="cards"
        workspaceTemplateCode="TPL-VOLUMETRIC-LETTERS_v2"
      />,
    );

    fireEvent.change(screen.getByTestId("intake-v6-layer-role-pseudo:maria"), {
      target: { value: "printed_artwork" },
    });

    expect(onUpdateLayerRole).toHaveBeenCalledWith("pseudo:maria", "printed_artwork");
  });

  it("renders owner-facing role labels for letters and atypical vectors", () => {
    render(
      <IntakeV6LayersRoleTable
        report={buildReport()}
        confirmation={buildConfirmation()}
        onUpdateLayerRole={() => undefined}
        layout="cards"
        workspaceTemplateCode="TPL-VOLUMETRIC-LETTERS_v2"
      />,
    );

    expect((screen.getByTestId("intake-v6-layer-role-pseudo:maria") as HTMLSelectElement).selectedOptions[0]?.textContent).toBe("Vector Litere");
    expect((screen.getByTestId("intake-v6-layer-role-logo-stanga") as HTMLSelectElement).selectedOptions[0]?.textContent).toBe("Vector Logo");
  });

  it("keeps all six layers visible without pagination", () => {
    render(
      <IntakeV6LayersRoleTable
        report={buildSixLayerReport()}
        confirmation={buildConfirmation()}
        onUpdateLayerRole={() => undefined}
        layout="cards"
        workspaceTemplateCode="TPL-VOLUMETRIC-LETTERS_v2"
      />,
    );

    expect(screen.queryByTestId("intake-v6-layer-card-pagination")).not.toBeInTheDocument();
    expect(screen.getByText("Element 6 — contur negru")).toBeInTheDocument();
  });

  it("shows owner-approved dropdown options for letters and logo layers", () => {
    render(
      <IntakeV6LayersRoleTable
        report={buildReport()}
        confirmation={buildConfirmation()}
        onUpdateLayerRole={() => undefined}
        layout="cards"
        workspaceTemplateCode="TPL-VOLUMETRIC-LETTERS_v2"
      />,
    );

    const lettersSelect = screen.getByTestId("intake-v6-layer-role-pseudo:maria");
    const logoSelect = screen.getByTestId("intake-v6-layer-role-logo-stanga");

    expect(lettersSelect.querySelector("optgroup")).toBeNull();
    expect(logoSelect.querySelector("optgroup")).toBeNull();
    const letterOptions = Array.from(lettersSelect.querySelectorAll("option")).map((option) => option.textContent);
    const logoOptions = Array.from(logoSelect.querySelectorAll("option")).map((option) => option.textContent);
    expect(letterOptions).toEqual([
      "Vector Litere",
      "Vector Logo",
      "Contur suport",
      "Text decupat",
      "Logo decupat",
      "Insert plexiglas",
      "Decorativ / Ignore",
    ]);
    expect(logoOptions).toEqual(letterOptions);
    expect(new Set(letterOptions).size).toBe(letterOptions.length);
    expect(lettersSelect.textContent).not.toContain("Vinil aplicat");
    expect(lettersSelect.textContent).not.toContain("Fundal / suport / bond / caseta");
    expect(lettersSelect.textContent).not.toContain("Cant / volum");
    expect(lettersSelect.textContent).not.toContain("Spate / backing");
    expect(lettersSelect.textContent).not.toContain("Vector Atipic");
    expect(lettersSelect.textContent).not.toContain("Ignora strat");
    expect(lettersSelect.textContent).not.toContain("Necesită confirmare");
  });

  it("uses the same owner taxonomy when the Letters+Logo context is detected from layer targets", () => {
    render(
      <IntakeV6LayersRoleTable
        report={buildReport()}
        confirmation={buildConfirmation()}
        onUpdateLayerRole={() => undefined}
        layout="cards"
      />,
    );

    const lettersSelect = screen.getByTestId("intake-v6-layer-role-pseudo:maria");
    const logoSelect = screen.getByTestId("intake-v6-layer-role-logo-stanga");
    const letterOptions = Array.from(lettersSelect.querySelectorAll("option")).map((option) => option.textContent);
    const logoOptions = Array.from(logoSelect.querySelectorAll("option")).map((option) => option.textContent);

    expect(letterOptions).toHaveLength(7);
    expect(logoOptions).toEqual(letterOptions);
    expect(logoSelect.querySelector("optgroup")).toBeNull();
    expect(logoSelect.textContent).not.toContain("Vector Atipic");
    expect(logoSelect.textContent).not.toContain("Cant / volum");
  });

  it("keeps the owner-only dropdown in a single-logo workspace", () => {
    render(
      <IntakeV6LayersRoleTable
        report={buildLogoOnlyReport()}
        confirmation={buildConfirmation()}
        onUpdateLayerRole={() => undefined}
        layout="cards"
      />,
    );

    const logoSelect = screen.getByTestId("intake-v6-layer-role-logo-stanga") as HTMLSelectElement;
    const logoOptions = Array.from(logoSelect.querySelectorAll("option")).map((option) => option.textContent);

    expect(screen.getByText("Grup detectat: Logo 1")).toBeInTheDocument();
    expect(logoSelect.selectedOptions[0]?.textContent).toBe("Vector Logo");
    expect(logoOptions).toHaveLength(7);
    expect(logoSelect.textContent).not.toContain("Vinil aplicat");
    expect(logoSelect.textContent).not.toContain("Ignora strat");
    expect(logoSelect.textContent).not.toContain("Necesită confirmare");
    expect(logoSelect.textContent).not.toContain("Fundal / suport / bond / caseta");
  });

  it("hides per-card status icons when all layers are confirmed", () => {
    const confirmation = buildConfirmation();
    confirmation.confirmationStatus = "complete";
    for (const layer of confirmation.layers) {
      layer.confirmationState = "confirmed";
      layer.confirmedRole = layer.autoRole;
    }

    render(
      <IntakeV6LayersRoleTable
        report={buildReport()}
        confirmation={confirmation}
        onUpdateLayerRole={() => undefined}
        layout="cards"
      />,
    );

    expect(screen.queryByTestId("intake-v6-layer-status-icon-pseudo:maria")).not.toBeInTheDocument();
    expect(screen.queryByTestId("intake-v6-layer-status-icon-logo-stanga")).not.toBeInTheDocument();
  });
});