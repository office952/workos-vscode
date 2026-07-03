import { describe, expect, it } from "vitest";
import { resolveIntakeV6DisabledCtaSummary } from "./intakeV6DisabledCtaSummary";

describe("intakeV6DisabledCtaSummary", () => {
  it("maps layer_roles_incomplete to Product Truth blocker summary", () => {
    const summary = resolveIntakeV6DisabledCtaSummary({
      currentStep: "layers",
      disabled: true,
      reason: "layer_roles_incomplete",
      layersTotal: 6,
      layersConfirmed: 0,
    });

    expect(summary).toMatchObject({
      badges: ["BLOCKED", "NEEDS_CONFIRMATION"],
      title: "Product Truth incomplet",
      kind: "product_truth",
    });
    expect(summary?.message).toMatch(/Rolurile layerelor\/grupurilor/i);
    expect(summary?.submessage).toMatch(/Pricing Registry este pregătit/i);
    expect(summary?.submessage).toMatch(/6 grupuri\/straturi detectate/i);
    expect(summary?.submessage).not.toMatch(/pricing not ready|mergi la Pricing Registry|lipseste pret/i);
    expect(`${summary?.message} ${summary?.submessage} ${summary?.nextAction}`).not.toMatch(/ora|minut/i);
  });

  it("maps missing selected layer and finish target to Product Truth form input", () => {
    expect(
      resolveIntakeV6DisabledCtaSummary({
        currentStep: "review",
        disabled: true,
        reason: "missing selected layer",
      })?.badges,
    ).toEqual(["BLOCKED", "NEEDS_FORM_INPUT"]);

    expect(
      resolveIntakeV6DisabledCtaSummary({
        currentStep: "review",
        disabled: true,
        reason: "missing finish target",
      })?.badges,
    ).toEqual(["BLOCKED", "NEEDS_FORM_INPUT"]);
  });

  it("keeps real pricing coverage as pricing issue", () => {
    const summary = resolveIntakeV6DisabledCtaSummary({
      currentStep: "confirm",
      disabled: true,
      reason: "Calculul live conține linii fără tarif configurat.",
    });

    expect(summary).toMatchObject({
      badges: ["WARNING", "NEEDS_FORM_INPUT"],
      title: "Pricing coverage de verificat",
      kind: "pricing",
    });
    expect(summary?.message).toMatch(/tarif\/preț neconfigurat/i);
  });

  it("does not show a summary when CTA is enabled", () => {
    expect(
      resolveIntakeV6DisabledCtaSummary({
        currentStep: "layers",
        disabled: false,
        reason: "layer_roles_incomplete",
      }),
    ).toBeNull();
  });
});
