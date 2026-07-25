import { describe, expect, it } from "vitest";
import {
  getLettersFaceFinishMaterialByCode,
  LETTERS_FACE_FINISH_MATERIAL_CODES,
  LETTERS_FACE_FINISH_MATERIALS,
  lettersFaceFinishOptionLabel,
} from "./lettersFaceFinishMaterialDisplay";

describe("lettersFaceFinishMaterialDisplay", () => {
  it("locks four face finish materials with owner prices", () => {
    expect(LETTERS_FACE_FINISH_MATERIALS.map((entry) => entry.labelRo)).toEqual([
      "Oracal 8500",
      "Oracal 641",
      "Oracal 651",
      "Printat / Laminat",
    ]);
    expect(LETTERS_FACE_FINISH_MATERIAL_CODES).toEqual([
      "MAT-ORACAL-8500",
      "MAT-ORACAL-641",
      "MAT-ORACAL-651",
      "MAT-VINYL-PRINT-LAMINATED",
    ]);
    expect(
      LETTERS_FACE_FINISH_MATERIALS.map((entry) => entry.unitCostEurMp),
    ).toEqual([20.0, 6.5, 9.0, 10.0]);
  });

  it("maps intake tokens to display labels", () => {
    expect(lettersFaceFinishOptionLabel("oracal_8500")).toBe("Oracal 8500");
    expect(lettersFaceFinishOptionLabel("print_laminate")).toBe("Printat / Laminat");
    expect(lettersFaceFinishOptionLabel("printed_laminated_vinyl")).toBe("Printat / Laminat");
  });

  it("resolves materials by inventory/pricing code", () => {
    expect(getLettersFaceFinishMaterialByCode("MAT-ORACAL-651")?.labelRo).toBe("Oracal 651");
    expect(getLettersFaceFinishMaterialByCode("MAT-ACP-FATA-LITERE")).toBeNull();
    expect(getLettersFaceFinishMaterialByCode("MAT-VINYL-PRINT")).toBeNull();
  });

  it("does not invent BADGE-FACE capability codes", () => {
    for (const entry of LETTERS_FACE_FINISH_MATERIALS) {
      expect(JSON.stringify(entry)).not.toMatch(/BADGE-FACE/i);
      expect(entry.meaningRo.length).toBeGreaterThan(20);
    }
  });
});
