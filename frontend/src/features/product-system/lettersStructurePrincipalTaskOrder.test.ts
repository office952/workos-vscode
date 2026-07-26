import { describe, expect, it } from "vitest";
import {
  LETTERS_STRUCTURE_STEP_CAPAC_SPATE,
  LETTERS_STRUCTURE_STEP_SISTEM_LED,
  LETTERS_STRUCTURE_STEP_VIZUAL_FATA,
  LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU,
} from "./lettersStructureDetailRoutes";
import {
  getLettersComponentObtainDoc,
  isTaskOwnedByComponent,
  LETTERS_COMPONENT_OBTAIN_DOCS,
  LETTERS_PRINCIPAL_TASK_CHAIN,
  LETTERS_STRUCTURE_CARD_NOT_TASK_HELPER_RO,
  listObtainTasksForComponent,
} from "./lettersStructurePrincipalTaskOrder";

describe("lettersStructurePrincipalTaskOrder", () => {
  it("keeps a stable principal chain without inventing EUR", () => {
    expect(LETTERS_PRINCIPAL_TASK_CHAIN.map((task) => task.id)).toEqual([
      "prep_vector",
      "prep_cnc_file",
      "cut_face",
      "cut_forex_back",
      "prep_cant_path",
      "apply_cant_vinyl",
      "form_cant",
      "bond_face_cant",
      "paint_cant_ral",
      "install_led",
      "wire_test_led",
      "attach_body_to_back",
      "face_finish_after_assembly",
      "pack_with_psu",
    ]);
    const prose = LETTERS_PRINCIPAL_TASK_CHAIN.map((task) => task.labelRo + task.meaningRo).join(
      " ",
    );
    expect(prose).not.toMatch(/\d+(?:[.,]\d+)?\s*€|\d+\.\d+\s*EUR/i);
  });

  it("shares vector + CNC file prep between face and Forex obtain paths", () => {
    const face = listObtainTasksForComponent(LETTERS_STRUCTURE_STEP_VIZUAL_FATA).map((t) => t.id);
    const back = listObtainTasksForComponent(LETTERS_STRUCTURE_STEP_CAPAC_SPATE).map((t) => t.id);
    expect(face).toEqual(["prep_vector", "prep_cnc_file", "cut_face"]);
    expect(back).toEqual(["prep_vector", "prep_cnc_file", "cut_forex_back"]);
  });

  it("covers all four structure components and excludes emblem from LED obtain", () => {
    expect(LETTERS_COMPONENT_OBTAIN_DOCS.map((doc) => doc.stepId)).toEqual([
      LETTERS_STRUCTURE_STEP_VIZUAL_FATA,
      LETTERS_STRUCTURE_STEP_VOLUM_ALUMINIU,
      LETTERS_STRUCTURE_STEP_CAPAC_SPATE,
      LETTERS_STRUCTURE_STEP_SISTEM_LED,
    ]);
    const led = getLettersComponentObtainDoc(LETTERS_STRUCTURE_STEP_SISTEM_LED);
    expect(led?.notesRo.join(" ")).toMatch(/emblem/i);
    expect(led?.principalTaskIds).not.toContain("cut_face");
  });

  it("highlights ownership: cut_face belongs to face, install_led to LED", () => {
    const cutFace = LETTERS_PRINCIPAL_TASK_CHAIN.find((task) => task.id === "cut_face");
    const installLed = LETTERS_PRINCIPAL_TASK_CHAIN.find((task) => task.id === "install_led");
    expect(cutFace && isTaskOwnedByComponent(cutFace, LETTERS_STRUCTURE_STEP_VIZUAL_FATA)).toBe(
      true,
    );
    expect(cutFace && isTaskOwnedByComponent(cutFace, LETTERS_STRUCTURE_STEP_SISTEM_LED)).toBe(
      false,
    );
    expect(
      installLed && isTaskOwnedByComponent(installLed, LETTERS_STRUCTURE_STEP_SISTEM_LED),
    ).toBe(true);
  });

  it("states card is not a task on the structure helper", () => {
    expect(LETTERS_STRUCTURE_CARD_NOT_TASK_HELPER_RO).toMatch(/card ≠ task|card != task/i);
  });
});
