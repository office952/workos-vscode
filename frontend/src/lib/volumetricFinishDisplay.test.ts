import { describe, expect, it } from "vitest";
import { formatVolumetricFinishSummary } from "./volumetricFinishDisplay";

describe("formatVolumetricFinishSummary", () => {
  it("formats standard return finish", () => {
    const s = formatVolumetricFinishSummary({
      return_finish_system: "standard",
      return_color: "black",
    });
    expect(s.returnFinishLabel).toMatch(/Standard.*Negru/i);
    expect(s.returnFinishDetail).toMatch(/stoc/i);
    expect(s.returnApproximatePreview).toBeFalsy();
  });

  it("formats RAL return with code and name", () => {
    const s = formatVolumetricFinishSummary({
      return_finish_system: "RAL",
      return_ral_code: "9010",
      return_ral_name: "Alb pur",
      return_ral_preview_hex: "#F7F9EF",
      return_color: "white",
    });
    expect(s.returnFinishLabel).toBe("Vopsit RAL");
    expect(s.returnFinishCode).toBe("9010");
    expect(s.returnFinishName).toBe("Alb pur");
    expect(s.returnFinishDetail).toMatch(/9010/);
    expect(s.returnApproximatePreview).toBe(true);
    expect(s.returnFinishLabel).not.toMatch(/Standard/);
  });

  it("formats Oracal 651 return finish", () => {
    const s = formatVolumetricFinishSummary({
      return_finish_system: "ORACAL",
      return_oracal_series: "651",
      return_oracal_code: "010",
      return_oracal_name: "White",
      return_oracal_preview_hex: "#FFFFFF",
    });
    expect(s.returnFinishLabel).toBe("Colantat Oracal 651");
    expect(s.returnFinishDetail).toMatch(/651-010/);
    expect(s.returnPreviewHex).toBe("#FFFFFF");
  });

  it("face vinyl disabled shows Nu", () => {
    const s = formatVolumetricFinishSummary({
      face_vinyl_enabled: false,
    });
    expect(s.faceVinylLabel).toBe("Nu");
    expect(s.faceVinylDetail).toBeUndefined();
  });

  it("formats face vinyl Oracal 651", () => {
    const s = formatVolumetricFinishSummary({
      face_vinyl_enabled: true,
      face_vinyl_series: "651",
      face_vinyl_code: "070",
      face_vinyl_name: "Black",
      face_vinyl_preview_hex: "#111111",
    });
    expect(s.faceVinylLabel).toBe("Oracal 651");
    expect(s.faceVinylDetail).toMatch(/651-070/);
    expect(s.faceVinylTranslucent).toBe(false);
  });

  it("formats face vinyl Oracal 8500", () => {
    const s = formatVolumetricFinishSummary({
      face_vinyl_enabled: true,
      face_vinyl_series: "8500",
      face_vinyl_code: "010",
      face_vinyl_name: "White translucent",
      face_finish_type: "oracal_8500",
    });
    expect(s.faceVinylLabel).toBe("Oracal 8500");
    expect(s.faceVinylTranslucent).toBe(true);
    expect(s.faceVinylDetail).toMatch(/8500-010/);
  });

  it("legacy RAL fallback uses paint_ral fields", () => {
    const s = formatVolumetricFinishSummary({
      paint_ral_code: "3020",
      paint_ral_name: "Traffic red",
    });
    expect(s.returnFinishLabel).toBe("Vopsit RAL");
    expect(s.returnFinishCode).toBe("3020");
    expect(s.warnings.some((w) => w.includes("legacy"))).toBe(true);
  });

  it("legacy face vinyl uses face_vinyl_color_code", () => {
    const s = formatVolumetricFinishSummary({
      face_vinyl_enabled: true,
      face_vinyl_color_code: "8500-010",
      face_vinyl_color_name: "White translucent",
      face_finish_type: "oracal_8500",
    });
    expect(s.faceVinylCode).toBe("010");
    expect(s.faceVinylTranslucent).toBe(true);
    expect(s.warnings.some((w) => w.includes("legacy"))).toBe(true);
  });

  it("RAL does not use return_color as primary label", () => {
    const s = formatVolumetricFinishSummary({
      return_finish_system: "RAL",
      return_ral_code: "7016",
      return_ral_name: "Anthracite grey",
      return_color: "white",
    });
    expect(s.returnFinishLabel).toBe("Vopsit RAL");
    expect(s.returnFinishLabel).not.toContain("Alb");
    expect(s.returnFinishDetail).toMatch(/7016/);
  });

  it("warns when RAL return mode has no code selected", () => {
    const s = formatVolumetricFinishSummary({
      return_finish_system: "RAL",
    });
    expect(s.warnings.some((w) => w.includes("RAL"))).toBe(true);
  });

  it("warns when Oracal return mode has no code selected", () => {
    const s = formatVolumetricFinishSummary({
      return_finish_system: "ORACAL",
      return_oracal_series: "651",
    });
    expect(s.warnings.some((w) => w.includes("Oracal"))).toBe(true);
  });

  it("warns when face vinyl enabled without color code", () => {
    const s = formatVolumetricFinishSummary({
      face_vinyl_enabled: true,
      face_vinyl_series: "651",
      face_vinyl_roll_width_mm: 1260,
    });
    expect(s.warnings.some((w) => w.includes("față"))).toBe(true);
  });
});
