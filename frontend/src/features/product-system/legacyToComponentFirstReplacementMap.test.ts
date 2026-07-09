import { describe, expect, it } from "vitest";
import {
  buildLegacyReplacementSummary,
  computeLegacyReplacementOverallVerdict,
  getLegacyReplacementEntry,
  LEGACY_TO_COMPONENT_FIRST_REPLACEMENT_MAP,
} from "./legacyToComponentFirstReplacementMap";

describe("legacyToComponentFirstReplacementMap", () => {
  it("maps core legacy modules to component-first targets with canDeleteNow=false", () => {
    const face = getLegacyReplacementEntry("TPL-VOLUMETRIC-FACE_v1");
    expect(face?.replacementTargetCode).toBe("TPL-COMP-LETTER-FACE_v1");
    expect(face?.canDeleteNow).toBe(false);

    const led = getLegacyReplacementEntry("TPL-VOLUMETRIC-LED_v1");
    expect(led?.replacementTargetCode).toBe("TPL-COMP-LETTER-LED_v1");
    expect(led?.canDeleteNow).toBe(false);

    const returnCant = getLegacyReplacementEntry("TPL-VOLUM-ALUMINIU_v1");
    expect(returnCant?.replacementTargetCode).toBe("TPL-COMP-LETTER-RETURN-CANT_v1");
    expect(returnCant?.canDeleteNow).toBe(false);

    for (const entry of LEGACY_TO_COMPONENT_FIRST_REPLACEMENT_MAP) {
      expect(entry.canDeleteNow).toBe(false);
    }
  });

  it("reports global not_ready_for_delete verdict with zero deletable entries", () => {
    const summary = buildLegacyReplacementSummary();
    expect(summary.deletableNowCount).toBe(0);
    expect(summary.overallVerdict).toBe("not_ready_for_delete");
    expect(computeLegacyReplacementOverallVerdict()).toBe("not_ready_for_delete");
  });
});
