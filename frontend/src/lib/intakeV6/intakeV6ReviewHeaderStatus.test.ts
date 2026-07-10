import { describe, expect, it } from "vitest";
import { buildReviewHeaderStatus } from "./intakeV6ReviewHeaderStatus";

const clearSurfacing = { showBanner: false, reasons: [], actions: [] };

describe("buildReviewHeaderStatus", () => {
  it("returns Totul OK when no actions or problems", () => {
    const status = buildReviewHeaderStatus({
      analysisReady: true,
      svgReady: true,
      layersConfirmed: 6,
      layersTotal: 6,
      artworkTotal: 2,
      artworkConfigured: 2,
      operatorConfirmationMissing: false,
      surfacing: clearSurfacing,
      widthMm: 1200,
      heightMm: 400,
      perimeterM: 5.2,
    });

    expect(status.label).toBe("Totul OK");
    expect(status.tone).toBe("success");
    expect(status.actionCount).toBe(0);
    expect(status.details.find((row) => row.id === "svg")?.value).toBe("OK");
    expect(status.details.find((row) => row.id === "pricing")?.value).toBe("OK");
  });

  it("returns action count when operator confirmation is missing on confirm step", () => {
    const status = buildReviewHeaderStatus({
      analysisReady: true,
      svgReady: true,
      layersConfirmed: 6,
      layersTotal: 6,
      artworkTotal: 2,
      artworkConfigured: 2,
      operatorConfirmationMissing: true,
      currentStep: "confirm",
      surfacing: clearSurfacing,
    });

    expect(status.label).toBe("1 acțiune necesară");
    expect(status.tone).toBe("warning");
    expect(status.actions.some((action) => action.id === "confirm-step")).toBe(true);
    expect(status.details.find((row) => row.id === "operator")?.value).toBe("Lipsește");
  });

  it("returns Probleme when pricing rates are missing", () => {
    const status = buildReviewHeaderStatus({
      analysisReady: true,
      svgReady: true,
      containsMissingPrices: true,
      layersConfirmed: 6,
      layersTotal: 6,
      artworkTotal: 0,
      artworkConfigured: 0,
      surfacing: {
        showBanner: true,
        reasons: ["Calculul live conține linii fără tarif configurat."],
        actions: ["Verifică liniile cu tarif lipsă în Calcul live."],
      },
    });

    expect(status.label).toBe("Probleme");
    expect(status.tone).toBe("danger");
    expect(status.details.find((row) => row.id === "pricing")?.value).toBe("Lipsesc tarife");
    expect(status.actions.some((action) => action.id === "jump-live-calc")).toBe(true);
  });

  it("does not count final confirmation on review step", () => {
    const status = buildReviewHeaderStatus({
      analysisReady: true,
      svgReady: true,
      layersConfirmed: 6,
      layersTotal: 6,
      artworkTotal: 2,
      artworkConfigured: 2,
      operatorConfirmationMissing: true,
      currentStep: "review",
      surfacing: clearSurfacing,
    });

    expect(status.actionCount).toBe(0);
    expect(status.actions.some((action) => action.id === "confirm-step")).toBe(false);
    expect(status.details.find((row) => row.id === "operator")?.value).toBe("Pas 3");
  });

  it("includes layer and artwork detail rows", () => {
    const status = buildReviewHeaderStatus({
      analysisReady: true,
      svgReady: true,
      layersConfirmed: 4,
      layersTotal: 6,
      artworkTotal: 2,
      artworkConfigured: 1,
      pendingConfirmationCount: 1,
      surfacing: clearSurfacing,
    });

    expect(status.details.find((row) => row.id === "layers")?.value).toBe("4/6 confirmate");
    expect(status.details.find((row) => row.id === "artwork")?.value).toBe("Necesită decizie");
    expect(status.actions.some((action) => action.id === "jump-artwork")).toBe(true);
    expect(status.actions.some((action) => action.label === "Mergi la Artwork")).toBe(true);
    expect(status.actions.some((action) => action.id === "jump-layers")).toBe(true);
    expect(status.actions.some((action) => action.label === "Mergi la Straturi")).toBe(true);
  });
});
