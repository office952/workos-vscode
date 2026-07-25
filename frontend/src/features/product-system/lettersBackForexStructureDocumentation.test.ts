import { describe, expect, it } from "vitest";
import {
  LETTERS_BACK_CALC_CARDS,
  LETTERS_BACK_DOC_DIRECTION_RO,
  LETTERS_BACK_DOC_ROLE_RO,
  LETTERS_BACK_DOC_SECTIONS,
  LETTERS_BACK_DOC_SOURCES,
} from "./lettersBackForexStructureDocumentation";
import { LETTERS_BACK_FOREX_10MM_DISPLAY_NAME } from "@/lib/materials/lettersBackForexMaterialDisplay";

describe("lettersBackForexStructureDocumentation", () => {
  it("covers role, material, process, geometry, boundary, direction", () => {
    expect(LETTERS_BACK_DOC_SECTIONS.map((section) => section.id)).toEqual([
      "role",
      "material",
      "process",
      "geometry",
      "boundary",
      "direction",
    ]);
    expect(LETTERS_BACK_DOC_ROLE_RO).toMatch(/Pasul 3/);
    expect(LETTERS_BACK_DOC_DIRECTION_RO).toMatch(/Composer|Sistem LED/i);
  });

  it("locks Forex 10 mm without hardcoded EUR amounts", () => {
    const material = LETTERS_BACK_DOC_SECTIONS.find((section) => section.id === "material");
    const process = LETTERS_BACK_DOC_SECTIONS.find((section) => section.id === "process");
    expect(material?.bodyRo).toContain(LETTERS_BACK_FOREX_10MM_DISPLAY_NAME);
    expect(material?.bodyRo).toContain("MAT-SPATE-PVC-LITERE");
    expect(material?.bulletsRo?.some((line) => /\d+(?:[.,]\d+)?\s*€/.test(line))).toBe(false);
    expect(material?.bulletsRo?.some((line) => /Pricing Registry/i.test(line))).toBe(true);
    expect(process?.bodyRo).toMatch(/BADGE-CNC-PROCESSABLE/i);
    expect(process?.bulletsRo?.some((line) => /opțional|fără/i.test(line))).toBe(true);
  });

  it("lists canonical owner source paths", () => {
    expect(LETTERS_BACK_DOC_SOURCES.length).toBeGreaterThanOrEqual(3);
    expect(
      LETTERS_BACK_DOC_SOURCES.some((source) =>
        source.path.includes("TPL_VOLUMETRIC_FACE_BACK_PREP"),
      ),
    ).toBe(true);
  });

  it("documents material consumption and CNC cutting as primary calc cards", () => {
    expect(LETTERS_BACK_CALC_CARDS.map((card) => card.id)).toEqual([
      "material_consumption",
      "cnc_cutting",
    ]);
    const material = LETTERS_BACK_CALC_CARDS[0];
    const cutting = LETTERS_BACK_CALC_CARDS[1];
    expect(material?.formulaRo).toMatch(/backing_area|mp/i);
    expect(cutting?.formulaRo).toMatch(/3 sau 5|3.*5/i);
    expect(cutting?.stepsRo.join(" ")).toMatch(/3 treceri/);
    expect(cutting?.stepsRo.join(" ")).toMatch(/5 treceri/);
    expect(material?.formulaRo + cutting?.formulaRo).not.toMatch(/\d+\.\d+\s*EUR/);
  });
});
