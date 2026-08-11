import { describe, expect, it } from "vitest";
import {
  INTAKE_V6_STEP2_OFFER_CRITICAL_GROUPS,
  INTAKE_V6_STEP2_PRODUCTION_DIAGNOSTIC_GROUPS,
  resolveIntakeV6ReviewRefetchGroups,
  type IntakeV6ReviewDirtyDomain,
  type IntakeV6ReviewRefetchGroup,
} from "./intakeV6ReviewRefetchDomains";

const STEP2_CRITICAL: IntakeV6ReviewRefetchGroup[] = [...INTAKE_V6_STEP2_OFFER_CRITICAL_GROUPS];

describe("resolveIntakeV6ReviewRefetchGroups — Step 2 GET diet", () => {
  it.each([
    "lighting",
    "face_finish",
    "artwork_finish",
    "backing",
    "mounting",
    "template",
    "sheet_footprint",
  ] as IntakeV6ReviewDirtyDomain[])(
    "%s refreshes only Step 2 offer-critical groups",
    (domain) => {
      expect(resolveIntakeV6ReviewRefetchGroups([domain])).toEqual(STEP2_CRITICAL);
    },
  );

  it("limits commercial input changes to pricing + pricedQuote", () => {
    expect(resolveIntakeV6ReviewRefetchGroups(["commercial_preview"])).toEqual([
      "pricing",
      "pricedQuote",
    ]);
  });

  it("preserves offer-critical groups on face_finish (pricedQuote + quoteHandoff)", () => {
    const groups = resolveIntakeV6ReviewRefetchGroups(["face_finish"]);
    expect(groups).toContain("pricedQuote");
    expect(groups).toContain("pricing");
    expect(groups).toContain("breakdown");
    expect(groups).toContain("quoteHandoff");
  });

  it("removes production / task diagnostic groups from ordinary configure domains", () => {
    const domains: IntakeV6ReviewDirtyDomain[] = [
      "face_finish",
      "backing",
      "lighting",
      "artwork_finish",
      "mounting",
      "template",
      "sheet_footprint",
    ];
    const groups = new Set(resolveIntakeV6ReviewRefetchGroups(domains));
    for (const productionGroup of INTAKE_V6_STEP2_PRODUCTION_DIAGNOSTIC_GROUPS) {
      expect(groups.has(productionGroup)).toBe(false);
    }
  });

  it("does not expand commercial_preview into production diagnostics", () => {
    const groups = resolveIntakeV6ReviewRefetchGroups(["commercial_preview"]);
    for (const productionGroup of INTAKE_V6_STEP2_PRODUCTION_DIAGNOSTIC_GROUPS) {
      expect(groups).not.toContain(productionGroup);
    }
  });

  it("unions multiple dirty domains without reintroducing production fan-out", () => {
    expect(
      resolveIntakeV6ReviewRefetchGroups(["face_finish", "backing", "lighting", "commercial_preview"]),
    ).toEqual(STEP2_CRITICAL);
  });
});
