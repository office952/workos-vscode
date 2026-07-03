import { describe, expect, it } from "vitest";
import {
  deriveFastAskFromSpec,
  emptyVectorFastAskAnswers,
  isVectorFastAskComplete,
  mapVectorFastAskToProductSpec,
} from "./volumetricVectorFastAskMapping";

describe("volumetricVectorFastAskMapping", () => {
  it("maps depth 60 mm to depth_mm and return_depth_mm", () => {
    const { spec, prefilledSectionNumbers } = mapVectorFastAskToProductSpec(
      {},
      {
        ...emptyVectorFastAskAnswers(),
        vectorFileName: "logo.svg",
        layerAlignment: "aligned",
        faceWrap: "yes",
        faceColantareType: "oracal_colored",
        returnEdgeColor: "black",
        letterDepth: 60,
      }
    );
    expect(spec.depth_mm).toBe(60);
    expect(spec.return_depth_mm).toBe(60);
    expect(prefilledSectionNumbers).toContain(2);
  });

  it("maps face wrap to face_finish_type", () => {
    const { spec } = mapVectorFastAskToProductSpec(
      {},
      {
        ...emptyVectorFastAskAnswers(),
        vectorFileName: "a.svg",
        faceWrap: "yes",
        faceColantareType: "print_laminated",
        layerAlignment: "unknown",
        letterDepth: 60,
      }
    );
    expect(spec.face_vinyl_enabled).toBe(true);
    expect(spec.face_finish_type).toBe("printed_laminated_vinyl");
  });

  it("maps return edge color without paint volume finish", () => {
    const { spec } = mapVectorFastAskToProductSpec(
      {},
      {
        ...emptyVectorFastAskAnswers(),
        vectorFileName: "a.svg",
        returnEdgeColor: "white",
        layerAlignment: "unknown",
        faceWrap: "unknown",
        letterDepth: 60,
      }
    );
    expect(spec.return_color).toBe("white");
    expect(spec.volume_finish).toBe("none");
    expect(spec.face_miter_chamfer).toBe(true);
  });

  it("preserves existing spec unless overwrite", () => {
    const { spec } = mapVectorFastAskToProductSpec(
      { text: "HOTELEXIA", depth_mm: 80, face_finish_type: "none", face_wrap_enabled: false },
      {
        ...emptyVectorFastAskAnswers(),
        vectorFileName: "new.svg",
        letterDepth: 60,
        faceWrap: "yes",
        faceColantareType: "oracal_colored",
        layerAlignment: "unknown",
      }
    );
    expect(spec.text).toBe("HOTELEXIA");
    expect(spec.depth_mm).toBe(80);
    expect(spec.face_finish_type).toBe("none");
    expect(spec.vector_file_name).toBe("new.svg");
  });

  it("does not fake geometry metrics", () => {
    const { spec } = mapVectorFastAskToProductSpec(
      {},
      {
        ...emptyVectorFastAskAnswers(),
        vectorFileName: "a.svg",
        layerAlignment: "aligned",
        letterDepth: 60,
      }
    );
    expect(spec.letter_face_area_m2).toBeUndefined();
    expect(spec.letter_perimeter_m).toBeUndefined();
    expect(spec.letter_count).toBeUndefined();
  });

  it("always applies frontlit defaults on apply", () => {
    const { spec } = mapVectorFastAskToProductSpec(
      {},
      {
        ...emptyVectorFastAskAnswers(),
        vectorFileName: "a.svg",
        layerAlignment: "unknown",
        letterDepth: 60,
      }
    );
    expect(spec.illumination_type).toBe("frontlit");
    expect(spec.lighting_system_type).toBe("led_modules");
    expect(spec.led_module_wattage).toBe(1.44);
  });

  it("sets vector_fast_ask_applied_at on apply", () => {
    const { spec } = mapVectorFastAskToProductSpec(
      {},
      {
        ...emptyVectorFastAskAnswers(),
        vectorFileName: "a.svg",
        layerAlignment: "unknown",
        letterDepth: 60,
      }
    );
    expect(spec.vector_fast_ask_applied_at).toBeTruthy();
  });

  it("isVectorFastAskComplete for legacy smoke-like spec", () => {
    expect(
      isVectorFastAskComplete({
        vector_file_name: "test.svg",
        depth_mm: 60,
        return_edge_color: "white",
      })
    ).toBe(true);
  });

  it("deriveFastAskFromSpec round-trips depth and wrap", () => {
    const derived = deriveFastAskFromSpec({
      depth_mm: 60,
      return_depth_mm: 60,
      face_wrap_enabled: true,
      face_finish_type: "oracal_651",
      return_edge_color: "black",
    });
    expect(derived.letterDepth).toBe(60);
    expect(derived.faceWrap).toBe("yes");
    expect(derived.returnEdgeColor).toBe("black");
  });
});
