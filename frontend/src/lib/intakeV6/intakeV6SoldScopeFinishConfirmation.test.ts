import { describe, expect, it } from "vitest";

import {
  countIncompleteArtworkFinishesForScope,
  countIncompleteLetterGroupsForScope,
  invalidateFinishConfirmationsForDeselectedModules,
  soldModulesRemoved,
} from "./intakeV6SoldScopeFinishConfirmation";
import { resolveSoldScopeFieldVisibility } from "./intakeV6SoldScopeVisibility";

const letterGroup = {
  group_key: "g1",
  layer_name: "A",
  face_finish_type: "oracal_851",
  face_oracal_code: "G001",
  return_finish_type: "ral_paint",
  return_oracal_code: "RAL9005",
  return_depth_mm: 80,
  confirmed: true,
};

const artworkRow = {
  layer_key: "logo",
  layer_name: "Logo",
  execution_type: "vinyl",
  return_depth_mm: 80,
  confirmed: true,
};

describe("intakeV6SoldScopeFinishConfirmation", () => {
  it("detects removed sold modules", () => {
    expect(soldModulesRemoved(["FACE", "BACK"], ["FACE"])).toEqual(["BACK"]);
  });

  it("invalidates confirmations once when modules are deselected", () => {
    const result = invalidateFinishConfirmationsForDeselectedModules({
      letterGroups: [letterGroup],
      artworkFinishes: [artworkRow],
      finishSetupConfirmed: true,
      deselectedModules: ["FACE"],
    });
    expect(result.letterGroups[0].confirmed).toBe(false);
    expect(result.letterGroups[0].face_oracal_code).toBe("G001");
    expect(result.finishSetupConfirmed).toBe(false);
  });

  it("does not count hidden modules toward readiness", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["BACK"] },
    });
    expect(countIncompleteLetterGroupsForScope([letterGroup], visibility)).toBe(0);
    expect(countIncompleteArtworkFinishesForScope([artworkRow], visibility)).toBe(0);
  });

  it("counts only visible module requirements", () => {
    const visibility = resolveSoldScopeFieldVisibility({
      offer_scope: { mode: "component_subset", sold_modules: ["FACE"] },
    });
    expect(
      countIncompleteLetterGroupsForScope(
        [{ ...letterGroup, face_finish_type: "oracal_651", face_oracal_code: null, confirmed: false }],
        visibility,
      ),
    ).toBe(1);
  });
});
