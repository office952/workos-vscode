import { describe, expect, it } from "vitest";
import {
  CNC_ACM_BOXED_SERVICES_RO,
  CNC_LETTERS_FACE_SERVICES_RO,
  CNC_PROCESS_ELEMENTS_RO,
} from "./cncProcessTaxonomyRo";
import { CNC_PROCESSABLE_LETTER_FACE_SERVICES } from "./cncProcessableBadge";

describe("cncProcessTaxonomyRo", () => {
  it("locks three separate CNC elements", () => {
    expect([...CNC_PROCESS_ELEMENTS_RO]).toEqual([
      "Decupare",
      "Canal / Șanfren",
      "V-groove",
    ]);
  });

  it("maps letters to Decupare + Canal/Șanfren (not V-groove)", () => {
    expect([...CNC_LETTERS_FACE_SERVICES_RO]).toEqual(["Decupare", "Canal / Șanfren"]);
    expect([...CNC_PROCESSABLE_LETTER_FACE_SERVICES]).toEqual([...CNC_LETTERS_FACE_SERVICES_RO]);
    expect(CNC_LETTERS_FACE_SERVICES_RO).not.toContain("V-groove");
  });

  it("maps ACM/Dibond to Decupare + V-groove (not Canal/Șanfren)", () => {
    expect([...CNC_ACM_BOXED_SERVICES_RO]).toEqual(["Decupare", "V-groove"]);
    expect(CNC_ACM_BOXED_SERVICES_RO).not.toContain("Canal / Șanfren");
  });
});
