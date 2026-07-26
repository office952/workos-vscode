import { describe, expect, it } from "vitest";
import {
  isLettersFaceStructureComponent,
  LETTERS_FACE_CNC_SERVICES,
  LETTERS_FACE_CNC_TOOLTIP_TITLE,
  LETTERS_FACE_PLEXI_3MM_PROCESS,
} from "./lettersFaceProcessDisplay";

describe("lettersFaceProcessDisplay", () => {
  it("documents only Plexi 3mm → CNC cut → CNC bevel for FACE substrate", () => {
    expect(LETTERS_FACE_PLEXI_3MM_PROCESS.map((step) => step.id)).toEqual([
      "material_plexi_3mm",
      "cnc_debitare",
      "cnc_sanfren",
    ]);
    expect(LETTERS_FACE_PLEXI_3MM_PROCESS.every((step) => step.sourceNote.length > 0)).toBe(true);
  });

  it("lists CNC hover title and numbered services", () => {
    expect(LETTERS_FACE_CNC_TOOLTIP_TITLE).toBe("Procesare CNC");
    expect([...LETTERS_FACE_CNC_SERVICES]).toEqual(["Decupare", "Canal / Șanfren"]);
  });

  it("detects Vizual față structure row", () => {
    expect(
      isLettersFaceStructureComponent({
        type: "LITERE_3D",
        component_id: "comp_face_litere",
        name: "Vizual față — plexi/acrilic",
      }),
    ).toBe(true);
    expect(
      isLettersFaceStructureComponent({
        type: "FINISAJ",
        component_id: "comp_finisaj_litere",
        name: "Finisaj",
      }),
    ).toBe(false);
  });
});
