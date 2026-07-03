import { describe, expect, it } from "vitest";
import {
  deriveVectorLayerMappingStatus,
  updateSvgLayerMapping,
} from "@/lib/intakeVectorLayerMapping";

describe("intakeVectorLayerMapping", () => {
  it("derives pending when no mappings", () => {
    expect(deriveVectorLayerMappingStatus(undefined)).toBe("pending");
  });

  it("derives mapped when letters layer mapped", () => {
    expect(
      deriveVectorLayerMappingStatus({ Layer_x0020_1: "TPL-VOLUMETRIC-LETTERS" })
    ).toBe("mapped");
  });

  it("stays pending when only support_bars mapped", () => {
    expect(deriveVectorLayerMappingStatus({ Layer_Bare: "support_bars" })).toBe("pending");
  });

  it("updates mappings without inventing geometry fields", () => {
    const next = updateSvgLayerMapping(
      { text: "HOTELEXIA", vector_file_type: "svg" },
      "Layer_x0020_1",
      "TPL-VOLUMETRIC-LETTERS"
    );
    expect(next.svg_layer_mappings).toEqual({
      Layer_x0020_1: "TPL-VOLUMETRIC-LETTERS",
    });
    expect(next.vector_layer_mapping_status).toBe("mapped");
    expect(next.letter_count).toBeUndefined();
    expect(next.letter_face_area_m2).toBeUndefined();
  });
});
