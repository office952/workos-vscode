import { describe, expect, it } from "vitest";
import {
  describeOperatorStateBadge,
  resolveArtworkFinishBadges,
  resolveHydratedFinishBadge,
  resolveLayerConfirmationBadge,
} from "./intakeV6OperatorStateBadges";

describe("intake v6 operator state badges", () => {
  it("labels suggested and confirmed as different states", () => {
    expect(describeOperatorStateBadge("SUGGESTED")).toBe("Propunere");
    expect(resolveLayerConfirmationBadge("confirmed")).toBe("CONFIRMED");
    expect(describeOperatorStateBadge("CONFIRMED")).toBe("Confirmat");
  });

  it("does not label pending layer confirmation as confirmed", () => {
    expect(resolveLayerConfirmationBadge("pending")).toBe("NEEDS_CONFIRMATION");
    expect(resolveLayerConfirmationBadge(undefined)).toBe("NEEDS_CONFIRMATION");
  });

  it("labels hydrated finish values as fallback until operator confirmation", () => {
    expect(resolveHydratedFinishBadge(false)).toBe("FALLBACK");
    expect(describeOperatorStateBadge(resolveHydratedFinishBadge(false))).toBe("Fallback/hydrated din template");
    expect(resolveHydratedFinishBadge(true)).toBe("CONFIRMED");
  });

  it("keeps artwork suggested, fallback, and confirmed as separate states", () => {
    expect(resolveArtworkFinishBadges({ confirmed: false })).toEqual([
      "SUGGESTED",
      "NEEDS_CONFIRMATION",
      "FALLBACK",
    ]);
    expect(resolveArtworkFinishBadges({ confirmed: true })).toEqual(["SUGGESTED", "CONFIRMED"]);
    expect(resolveArtworkFinishBadges({ confirmed: false, hasTarget: false })).toEqual([
      "SUGGESTED",
      "BLOCKED",
      "NEEDS_FORM_INPUT",
    ]);
  });
});
