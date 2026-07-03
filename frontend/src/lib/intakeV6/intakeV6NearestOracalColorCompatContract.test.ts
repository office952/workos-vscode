import { describe, expect, it } from "vitest";
import {
  applyNearestOracal651ToLetterGroup,
  findNearestOracal651Color,
} from "./intakeV6NearestOracalColor";

describe("intakeV6NearestOracalColor compat contract", () => {
  it("finds a nearest Oracal 651 entry for a hex SVG fill", () => {
    const match = findNearestOracal651Color("#FF0000");
    expect(match).not.toBeNull();
    expect(match?.system).toBe("ORACAL");
    expect(match?.series).toBe("651");
    expect(match?.code).toBeTruthy();
  });

  it("applies nearest Oracal to letter group without existing code", () => {
    const next = applyNearestOracal651ToLetterGroup({
      source_fill_color: "#FF0000",
      face_finish_type: "none",
      face_oracal_code: null,
      face_oracal_name: null,
    });
    expect(next.face_finish_type).toBe("oracal_651");
    expect(next.face_oracal_code).toBeTruthy();
    expect(next.face_oracal_name).toBeTruthy();
  });

  it("does not override an existing Oracal selection", () => {
    const next = applyNearestOracal651ToLetterGroup({
      source_fill_color: "#FF0000",
      face_finish_type: "oracal_651",
      face_oracal_code: "010",
      face_oracal_name: "White",
    });
    expect(next.face_oracal_code).toBe("010");
  });
});