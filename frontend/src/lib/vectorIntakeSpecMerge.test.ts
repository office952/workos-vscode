import { describe, expect, it } from "vitest";
import {
  mergeLocalVectorSpecFields,
  shouldKeepLocalVectorSpec,
} from "@/lib/vectorIntakeSpecMerge";

describe("vectorIntakeSpecMerge", () => {
  it("keeps local vector when file timestamp is newer or equal", () => {
    expect(
      shouldKeepLocalVectorSpec({
        localFileAt: "2026-06-07T12:00:00.000Z",
        localPathwayIsVector: true,
        syncedFileAt: "2026-06-07T11:00:00.000Z",
      })
    ).toBe(true);
    expect(
      shouldKeepLocalVectorSpec({
        localFileAt: "2026-06-07T12:00:00.000Z",
        localPathwayIsVector: true,
        syncedFileAt: "2026-06-07T12:00:00.000Z",
      })
    ).toBe(true);
  });

  it("prefers prev layers when server has fewer", () => {
    const merged = mergeLocalVectorSpecFields(
      {
        vector_file_name: "lleexxaa.svg",
        vector_detected_layers: [
          {
            id: "a",
            label: "Litere",
            element_count: 1,
            suggested_role: "volumetric_letters",
            confirmed_role: "volumetric_letters",
          },
          {
            id: "b",
            label: "Cadru",
            element_count: 2,
            suggested_role: "metal_frame",
            confirmed_role: "metal_frame",
          },
        ],
        vector_svg_analyzed: true,
      },
      {
        vector_file_name: "lleexxaa.svg",
        vector_detected_layers: [],
      }
    );
    expect(merged.vector_detected_layers).toHaveLength(2);
    expect(merged.vector_svg_analyzed).toBe(true);
  });

  it("does not preserve prev geometry when vector file identity changes", () => {
    const merged = mergeLocalVectorSpecFields(
      {
        vector_file_name: "hotel_lexa.svg",
        vector_file_selected_at: "2026-06-07T10:00:00.000Z",
        vector_suggested_letter_perimeter_m: 185.797,
        letter_perimeter_m: 185.797,
        geometry_confirmed_for_file_name: "hotel_lexa.svg",
        vector_layer_mapping_confirmed: true,
      },
      {
        vector_file_name: "lleexxaa.svg",
        vector_file_selected_at: "2026-06-07T11:00:00.000Z",
        vector_layer_mapping_confirmed: false,
        geometry_stale: true,
      }
    );
    expect(merged.vector_file_name).toBe("lleexxaa.svg");
    expect(merged.letter_perimeter_m).toBeUndefined();
    expect(merged.vector_suggested_letter_perimeter_m).toBeUndefined();
    expect(merged.geometry_stale).toBe(true);
    expect(merged.vector_layer_mapping_confirmed).toBe(false);
  });
});
