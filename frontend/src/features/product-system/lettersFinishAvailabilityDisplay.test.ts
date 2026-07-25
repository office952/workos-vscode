import { describe, expect, it } from "vitest";
import { LETTERS_FACE_FINISH_LABOR_STEPS } from "@/lib/materials/lettersAutocolantDisplay";
import {
  isLettersFinisajStructureComponent,
  listLettersCantFinishChips,
  listLettersFaceFinishChips,
} from "./lettersFinishAvailabilityDisplay";

describe("lettersFinishAvailabilityDisplay", () => {
  it("lists face finish option badges in owner order", () => {
    const face = listLettersFaceFinishChips();
    expect(face.map((chip) => chip.labelRo)).toEqual([
      "Oracal 8500",
      "Oracal 641",
      "Oracal 651",
      "Printat / Laminat",
    ]);
    expect(face.every((chip) => chip.group === "face")).toBe(true);
  });

  it("shares two labor steps for any face finish option", () => {
    expect(LETTERS_FACE_FINISH_LABOR_STEPS.map((step) => step.labelRo)).toEqual([
      "Aplicare față",
      "Decupare contur",
    ]);
  });

  it("lists cant finish modes Stock / Autocolant / RAL", () => {
    const cant = listLettersCantFinishChips();
    const labels = cant.map((chip) => chip.labelRo).join(" | ");
    expect(labels).toMatch(/Stock/i);
    expect(labels).toMatch(/Autocolant/i);
    expect(labels).toMatch(/RAL/i);
  });

  it("detects FINISAJ structure component", () => {
    expect(
      isLettersFinisajStructureComponent({
        type: "FINISAJ",
        component_id: "comp_finisaj_litere",
        name: "Finisaj",
      }),
    ).toBe(true);
    expect(
      isLettersFinisajStructureComponent({
        type: "LITERE_3D",
        component_id: "comp_face_litere",
        name: "Vizual față",
      }),
    ).toBe(false);
  });
});
