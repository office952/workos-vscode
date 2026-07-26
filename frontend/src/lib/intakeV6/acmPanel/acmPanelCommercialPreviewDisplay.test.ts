import { describe, expect, it } from "vitest";
import {
  acmPanelPreviewIsVisible,
  formatAcmPanelMmPair,
  formatAcmPanelMultiPanelDeductionNote,
  formatAcmPanelPanelCountLabel,
  formatAcmPanelPathSource,
  formatAcmPanelQty,
  humanizeAcmPanelPreviewWarning,
  prepareAcmPanelPreviewWarnings,
} from "./acmPanelCommercialPreviewDisplay";

describe("acmPanelCommercialPreviewDisplay", () => {
  it("formats assembly pair", () => {
    expect(formatAcmPanelMmPair(2000, 350)).toBe("2000 × 350 mm");
  });

  it("formats face area", () => {
    expect(formatAcmPanelQty(0.7, "mp")).toBe("0.7 mp");
    expect(formatAcmPanelQty(5.4, "ml")).toBe("5.4 ml");
  });

  it("humanizes warnings", () => {
    expect(humanizeAcmPanelPreviewWarning("segmentation_proposed")).toContain("PROPOSED");
    expect(humanizeAcmPanelPreviewWarning("acm_panel:technical_configuration_unconfirmed")).toContain(
      "tehnică",
    );
  });

  it("visibility requires lines or total", () => {
    expect(acmPanelPreviewIsVisible(null)).toBe(false);
    expect(acmPanelPreviewIsVisible({ status: "unavailable" })).toBe(false);
    expect(
      acmPanelPreviewIsVisible({
        status: "provisional_with_warnings",
        estimated_total: 64,
        lines: [{ code: "acm_panel_cut" }],
      }),
    ).toBe(true);
  });

  it("formats path quantity source", () => {
    expect(formatAcmPanelPathSource("measured", "imported_dxf")).toContain("măsurat");
    expect(formatAcmPanelPathSource("commercial_deduced", "commercial_deduced")).toContain(
      "Deducere comercială",
    );
    expect(formatAcmPanelPathSource("proxy_rectangular", "proxy_rectangular")).toContain("proxy");
    expect(formatAcmPanelPathSource("unavailable", "unavailable")).toContain("indisponibil");
  });

  it("notes multi-panel commercial deduction", () => {
    expect(
      formatAcmPanelMultiPanelDeductionNote(2, "commercial_deduced", "commercial_deduced"),
    ).toBe("Calculat separat pentru 2 panouri");
    expect(formatAcmPanelMultiPanelDeductionNote(1, "commercial_deduced", "commercial_deduced")).toBeNull();
    expect(formatAcmPanelMultiPanelDeductionNote(2, "measured", "imported_dxf")).toBeNull();
  });

  it("never shows 0 panouri when assembly dims exist", () => {
    expect(formatAcmPanelPanelCountLabel(0, 2000, 500)).toBe("1 panou");
    expect(formatAcmPanelPanelCountLabel(null, 2000, 500)).toBe("1 panou");
    expect(formatAcmPanelPanelCountLabel(2, 2000, 500)).toBe("2 panouri");
  });

  it("humanizes quantity_source and drops path-source duplicates", () => {
    expect(humanizeAcmPanelPreviewWarning("quantity_source=commercial_deduction")).toMatch(
      /deducere comercială/i,
    );
    const prepared = prepareAcmPanelPreviewWarnings(
      [
        "quantity_source=commercial_deduction",
        "cut_v_quantity_source=commercial_deduction",
        "technical_configuration_unconfirmed",
      ],
      true,
    );
    expect(prepared).toEqual(["Configurație tehnică neconfirmată"]);
  });
});
