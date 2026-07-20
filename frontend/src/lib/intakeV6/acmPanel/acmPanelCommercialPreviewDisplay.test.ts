import { describe, expect, it } from "vitest";
import {
  acmPanelPreviewIsVisible,
  formatAcmPanelMmPair,
  formatAcmPanelPathSource,
  formatAcmPanelQty,
  humanizeAcmPanelPreviewWarning,
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
    expect(formatAcmPanelPathSource("proxy_rectangular", "proxy_rectangular")).toContain("proxy");
    expect(formatAcmPanelPathSource("unavailable", "unavailable")).toContain("indisponibil");
  });
});
