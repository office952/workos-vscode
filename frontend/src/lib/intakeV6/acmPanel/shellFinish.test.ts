import { describe, expect, it } from "vitest";
import {
  defaultAcmShellFinishContract,
  normalizeAcmShellFinish,
  shellNeedsFoil,
  summarizeAcmShellFinishOperatorRo,
  summarizeAcmShellFinishRo,
} from "./shellFinish";

describe("acmPanel shellFinish", () => {
  it("defaults to stock plate both zones and paint screws", () => {
    const d = defaultAcmShellFinishContract();
    expect(d.face.kind).toBe("stock_plate");
    expect(d.volume.kind).toBe("stock_plate");
    expect(shellNeedsFoil(d)).toBe(false);
    expect(d.paint_screws_if_no_foil).toBe(true);
    expect(d.apply_after_frame).toBe(true);
  });

  it("normalizes oracal face and sets foil strategy + no paint screws", () => {
    const n = normalizeAcmShellFinish({
      face: { kind: "oracal_651", color_code: "021", roll_width_mm: 1260 },
      volume: { kind: "stock_plate" },
      foil_strategy: { mode: "face_plus_first_fold" },
    });
    expect(n.face.kind).toBe("oracal_651");
    if (n.face.kind === "oracal_651") {
      expect(n.face.color_code).toBe("021");
      expect(n.face.roll_width_mm).toBe(1260);
    }
    expect(shellNeedsFoil(n)).toBe(true);
    expect(n.paint_screws_if_no_foil).toBe(false);
    expect(n.foil_strategy?.mode).toBe("face_plus_first_fold");
    expect(summarizeAcmShellFinishRo(n)).toMatch(/colant după cadru/i);
  });

  it("clears foil strategy when both zones are stock", () => {
    const n = normalizeAcmShellFinish({
      face: { kind: "stock_plate" },
      volume: { kind: "stock_plate" },
      foil_strategy: { mode: "face_multi_piece", piece_count: 3, client_informed: true },
    });
    expect(n.foil_strategy).toBeNull();
    expect(n.paint_screws_if_no_foil).toBe(true);
  });

  it("operator summary stays short for foil and no-foil", () => {
    expect(summarizeAcmShellFinishOperatorRo(defaultAcmShellFinishContract())).toBe(
      "Fără colant · vopsire șuruburi",
    );
    const withFoil = normalizeAcmShellFinish({
      face: { kind: "oracal_651", color_code: "021", roll_width_mm: 1000 },
      volume: { kind: "oracal_651", color_code: "", roll_width_mm: 1000 },
    });
    expect(summarizeAcmShellFinishOperatorRo(withFoil)).toBe("Colant față + cant · după cadru");
  });
});
