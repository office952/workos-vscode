import { describe, expect, it } from "vitest";

import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import {
  extractQuoteGeometryFromAnalyzer,
  findOutOfScopeLayerWarnings,
  resolveQuoteGeometryForWorkspace,
} from "./intakeV6QuoteGeometry";

function mockReport(layers: SvgAnalysisCoreReport["layers"]): SvgAnalysisCoreReport {
  return {
    document: {
      widthMm: 3000,
      heightMm: 1000,
      boundingAreaSqm: 3,
      filledAreaSqm: 2.5,
    } as SvgAnalysisCoreReport["document"],
    geometry: { perimeterMl: 99, perimeterMm: 99000 } as SvgAnalysisCoreReport["geometry"],
    layers,
    parts: { count: 12, nestableCount: 10 } as SvgAnalysisCoreReport["parts"],
  } as SvgAnalysisCoreReport;
}

function mockConfirmation(layers: LayerRoleConfirmation["layers"]): LayerRoleConfirmation {
  return {
    confirmationStatus: "complete",
    layers,
    warnings: [],
  };
}

describe("extractQuoteGeometryFromAnalyzer", () => {
  it("sums face layer perimeters from nest2", () => {
    const report = mockReport([
      {
        id: "litere-1",
        name: "litere-volumetrice-1",
        autoRole: "face",
        perimeterMl: 12.5,
        boundingAreaSqm: 1.2,
      } as SvgAnalysisCoreReport["layers"][number],
      {
        id: "litere-2",
        name: "litere-volumetrice-2",
        autoRole: "face",
        perimeterMl: 8.3,
        boundingAreaSqm: 0.9,
      } as SvgAnalysisCoreReport["layers"][number],
    ]);
    const confirmation = mockConfirmation([
      {
        layerKey: "litere-1",
        layerId: "litere-1",
        layerName: "litere-volumetrice-1",
        autoRole: "face",
        autoConfidence: "high",
        confirmedRole: "face",
        confirmationState: "confirmed",
      },
      {
        layerKey: "litere-2",
        layerId: "litere-2",
        layerName: "litere-volumetrice-2",
        autoRole: "face",
        autoConfidence: "high",
        confirmedRole: "face",
        confirmationState: "confirmed",
      },
    ]);

    const result = extractQuoteGeometryFromAnalyzer(report, confirmation);
    expect(result.letter_perimeter_m).toBeCloseTo(20.8, 2);
    expect(result.face_area_m2).toBeCloseTo(2.1, 2);
    expect(result.geometry_source).toBe("nest2_face_layers");
    expect(result.letter_count).toBe(10);
  });

  it("excludes artwork layer area from face totals", () => {
    const report = mockReport([
      {
        id: "litere-1",
        name: "litere-volumetrice-1",
        autoRole: "face",
        perimeterMl: 12.5,
        boundingAreaSqm: 1.2,
      } as SvgAnalysisCoreReport["layers"][number],
      {
        id: "logo",
        name: "logo",
        autoRole: "printed_artwork",
        perimeterMl: 99,
        boundingAreaSqm: 0.45,
      } as SvgAnalysisCoreReport["layers"][number],
    ]);
    const confirmation = mockConfirmation([
      {
        layerKey: "litere-1",
        layerId: "litere-1",
        layerName: "litere-volumetrice-1",
        autoRole: "face",
        autoConfidence: "high",
        confirmedRole: "face",
        confirmationState: "confirmed",
      },
      {
        layerKey: "logo",
        layerId: "logo",
        layerName: "logo",
        autoRole: "printed_artwork",
        autoConfidence: "high",
        confirmedRole: "printed_artwork",
        confirmationState: "confirmed",
      },
    ]);

    const result = extractQuoteGeometryFromAnalyzer(report, confirmation);
    expect(result.face_area_m2).toBeCloseTo(1.2, 2);
    expect(result.artwork_area_m2).toBeCloseTo(0.45, 2);
    expect(result.letter_perimeter_m).toBeCloseTo(12.5, 2);
  });
});

describe("findOutOfScopeLayerWarnings", () => {
  const acmLayerConfirmation = mockConfirmation([
    {
      layerKey: "fundal",
      layerName: "fundal-acm",
      autoRole: "support_panel",
      autoConfidence: "high",
      confirmedRole: "support_panel",
      confirmationState: "confirmed",
    },
    {
      layerKey: "slogan",
      layerName: "slogan-texte-decupate",
      autoRole: "inner_hole",
      autoConfidence: "medium",
      confirmedRole: "inner_hole",
      confirmationState: "confirmed",
    },
  ]);

  it("warns on ACM and slogan layers when no payload is provided (conservative default)", () => {
    const warnings = findOutOfScopeLayerWarnings(acmLayerConfirmation);
    expect(warnings.length).toBe(2);
  });

  it("still warns on ACM layer when the payload does not price it into the offer (F7E F1/B-F005)", () => {
    const warnings = findOutOfScopeLayerWarnings(acmLayerConfirmation, {
      finish_setup: { mounting_solution: { template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" } },
    });
    expect(warnings.some((w) => w.includes("ACM/casetat"))).toBe(true);
  });

  it("does not warn ACM 'standby' when the payload actually prices it into the offer (F7E F1/B-F005)", () => {
    const warnings = findOutOfScopeLayerWarnings(acmLayerConfirmation, {
      finish_setup: {
        mounting_solution: { template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" },
        applied_content: "letters",
      },
    });
    expect(warnings.some((w) => w.includes("ACM/casetat"))).toBe(false);
    // Unrelated slogan warning is untouched by ACM inclusion state.
    expect(warnings.some((w) => w.includes("litere slogan"))).toBe(true);
    expect(warnings.length).toBe(1);
  });
});

describe("resolveQuoteGeometryForWorkspace", () => {
  it("uses finish_setup to enrich cant/volum perimeter on Layers path", () => {
    const report = mockReport([
      {
        id: "Layer_x0020_2",
        name: "Layer_x0020_2",
        autoRole: "face",
        perimeterMl: 6.17,
        boundingAreaSqm: 0.33,
      } as SvgAnalysisCoreReport["layers"][number],
      {
        id: "Layer_x0020_3",
        name: "Layer_x0020_3",
        autoRole: "face",
        perimeterMl: 7.45,
        boundingAreaSqm: 0.36,
      } as SvgAnalysisCoreReport["layers"][number],
      {
        id: "Layer_x0020_1",
        name: "Layer_x0020_1",
        autoRole: "printed_artwork",
        perimeterMl: 1.85,
        boundingAreaSqm: 0.2,
      } as SvgAnalysisCoreReport["layers"][number],
    ]);

    const confirmation = mockConfirmation([
      {
        layerKey: "Layer_x0020_1",
        layerId: "Layer_x0020_1",
        layerName: "Layer_x0020_1",
        autoRole: "printed_artwork",
        autoConfidence: "high",
        confirmedRole: "printed_artwork",
        confirmationState: "confirmed",
      },
      {
        layerKey: "Layer_x0020_2",
        layerId: "Layer_x0020_2",
        layerName: "Layer_x0020_2",
        autoRole: "face",
        autoConfidence: "medium",
        confirmedRole: "face",
        confirmationState: "confirmed",
      },
      {
        layerKey: "Layer_x0020_3",
        layerId: "Layer_x0020_3",
        layerName: "Layer_x0020_3",
        autoRole: "face",
        autoConfidence: "medium",
        confirmedRole: "face",
        confirmationState: "confirmed",
      },
    ]);

    const bare = resolveQuoteGeometryForWorkspace({
      payload: {},
      analyzerReport: report,
      layerRoleConfirmation: confirmation,
      localFileHash: null,
    });

    const enriched = resolveQuoteGeometryForWorkspace({
      payload: {
        finish_setup: {
          return_finish_type: "oracal_wrapped",
          letter_group_finishes: [
            {
              group_key: "Layer_x0020_2",
              layer_name: "Layer_x0020_2",
              return_finish_type: "oracal_wrapped",
              element_count: 1,
            },
          ],
          artwork_finishes: [
            {
              layer_key: "Layer_x0020_1",
              layer_name: "Layer_x0020_1",
              execution_type: "needs_decision",
              return_finish_type: "standard_aluminum",
              element_count: 1,
            },
          ],
        },
      },
      analyzerReport: report,
      layerRoleConfirmation: confirmation,
      localFileHash: null,
    });

    expect(bare.return_material_perimeter_ml).toBeCloseTo(13.62, 2);
    expect(enriched.return_material_perimeter_ml).toBeGreaterThan(bare.return_material_perimeter_ml ?? 0);
    expect(enriched.return_material_perimeter_ml).toBeCloseTo(15.47, 1);
  });

  it("keeps persisted quote geometry when the local SVG hash matches the workspace SVG", () => {
    const report = mockReport([
      {
        id: "local",
        name: "local-reanalysis",
        autoRole: "face",
        perimeterMl: 12,
        boundingAreaSqm: 0.7,
      } as SvgAnalysisCoreReport["layers"][number],
    ]);
    const confirmation = mockConfirmation([
      {
        layerKey: "local",
        layerId: "local",
        layerName: "local-reanalysis",
        autoRole: "face",
        autoConfidence: "high",
        confirmedRole: "face",
        confirmationState: "confirmed",
      },
    ]);

    const geometry = resolveQuoteGeometryForWorkspace({
      payload: {
        svg_source: {
          file_hash: "same-svg",
        },
        quote_geometry: {
          letter_perimeter_m: 21.1675,
          return_material_perimeter_ml: 31.6373,
          face_area_m2: 1.2638,
          geometry_source: "nest2_face_parts_outer",
          confirmed: true,
        },
      },
      analyzerReport: report,
      layerRoleConfirmation: confirmation,
      localFileHash: "same-svg",
    });

    expect(geometry.letter_perimeter_m).toBeCloseTo(21.1675, 4);
    expect(geometry.return_material_perimeter_ml).toBeCloseTo(31.6373, 4);
  });

  it("uses the local analyzer when the uploaded SVG hash differs from persisted workspace geometry", () => {
    const report = mockReport([
      {
        id: "local",
        name: "local-reanalysis",
        autoRole: "face",
        perimeterMl: 12,
        boundingAreaSqm: 0.7,
      } as SvgAnalysisCoreReport["layers"][number],
    ]);
    const confirmation = mockConfirmation([
      {
        layerKey: "local",
        layerId: "local",
        layerName: "local-reanalysis",
        autoRole: "face",
        autoConfidence: "high",
        confirmedRole: "face",
        confirmationState: "confirmed",
      },
    ]);

    const geometry = resolveQuoteGeometryForWorkspace({
      payload: {
        svg_source: {
          file_hash: "old-svg",
        },
        quote_geometry: {
          letter_perimeter_m: 21.1675,
          return_material_perimeter_ml: 31.6373,
          face_area_m2: 1.2638,
          geometry_source: "nest2_face_parts_outer",
          confirmed: true,
        },
      },
      analyzerReport: report,
      layerRoleConfirmation: confirmation,
      localFileHash: "new-svg",
    });

    expect(geometry.letter_perimeter_m).toBeCloseTo(12, 2);
    expect(geometry.return_material_perimeter_ml).toBeCloseTo(12, 2);
  });
});