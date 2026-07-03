import { describe, expect, it } from "vitest";

import type { IntakeV6SheetQuoteMaterialCandidates } from "./intakeV6Api";
import {
  buildIntakeV6SheetFootprintSourceOptions,
  resolveDefaultSheetFootprintSource,
  resolveSelectedFootprintDisplay,
} from "./intakeV6SheetFootprintSource";

function sampleCandidates(): IntakeV6SheetQuoteMaterialCandidates {
  return {
    eligible_face_area_sqm: 1.2638,
    placement_footprint_face_sqm: 1.1469,
    face_union_bbox_sqm: 2.5238,
    layout_occupied_area_sqm: 2.5238,
    full_sheet_allocation_sqm: 6.0,
    selected_quote_sheet_area_source: "eligible_area_floor",
  };
}

describe("intakeV6SheetFootprintSource", () => {
  it("builds primary source options with areas from candidates", () => {
    const options = buildIntakeV6SheetFootprintSourceOptions({
      candidates: sampleCandidates(),
    });
    expect(options.map((option) => option.key)).toEqual([
      "eligible_area_floor",
      "face_union_bbox",
      "layout_occupied_area",
      "operator_manual_footprint",
    ]);
    expect(options[0]?.areaSqm).toBe(1.2638);
    expect(options[1]?.areaSqm).toBe(2.5238);
  });

  it("defaults to eligible when no override persisted", () => {
    expect(resolveDefaultSheetFootprintSource(sampleCandidates(), null)).toBe("eligible_area_floor");
  });

  it("restores persisted face union bbox source", () => {
    expect(
      resolveDefaultSheetFootprintSource(sampleCandidates(), {
        selectedFootprintSource: "face_union_bbox",
        useForQuoteEstimate: true,
      }),
    ).toBe("face_union_bbox");
  });

  it("formats selected footprint display", () => {
    const display = resolveSelectedFootprintDisplay({
      sourceKey: "face_union_bbox",
      candidates: sampleCandidates(),
    });
    expect(display.label).toBe("Face union bbox");
    expect(display.areaText).toBe("2.5238 m²");
  });
});