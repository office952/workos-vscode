import { describe, expect, it } from "vitest";
import {
  LETTERS_FACE_CALC_CARDS,
  LETTERS_FACE_DOC_DIRECTION_RO,
  LETTERS_FACE_DOC_ROLE_RO,
  LETTERS_FACE_DOC_SECTIONS,
  LETTERS_FACE_DOC_SOURCES,
} from "./lettersFaceStructureDocumentation";
import { LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME } from "@/lib/materials/lettersFacePlexiMaterialDisplay";

describe("lettersFaceStructureDocumentation", () => {
  it("covers role, material, CNC, finish, boundary, direction", () => {
    expect(LETTERS_FACE_DOC_SECTIONS.map((section) => section.id)).toEqual([
      "role",
      "material",
      "cnc",
      "finish",
      "boundary",
      "direction",
    ]);
    expect(LETTERS_FACE_DOC_ROLE_RO).toMatch(/Pasul 1/);
    expect(LETTERS_FACE_DOC_DIRECTION_RO).toMatch(/Composer/i);
  });

  it("locks plexiglas display name and CNC badge references in prose", () => {
    const material = LETTERS_FACE_DOC_SECTIONS.find((section) => section.id === "material");
    const cnc = LETTERS_FACE_DOC_SECTIONS.find((section) => section.id === "cnc");
    const finish = LETTERS_FACE_DOC_SECTIONS.find((section) => section.id === "finish");
    expect(material?.bodyRo).toContain(LETTERS_FACE_PLEXI_3MM_OPAL_DISPLAY_NAME);
    expect(material?.bodyRo).toContain("MAT-ACP-FATA-LITERE");
    expect(cnc?.bodyRo).toContain("BADGE-CNC-PROCESSABLE");
    expect(cnc?.bulletsRo?.some((line) => /Decupare|Debitare/i.test(line))).toBe(true);
    expect(cnc?.bulletsRo?.some((line) => /Șanfren/i.test(line))).toBe(true);
    expect(finish?.bulletsRo?.some((line) => /€\/mp|EUR\/mp|\d+\.\d/.test(line))).toBe(false);
    expect(finish?.bulletsRo?.some((line) => /Pricing Registry/i.test(line))).toBe(true);
  });

  it("lists canonical owner source paths", () => {
    expect(LETTERS_FACE_DOC_SOURCES.length).toBeGreaterThanOrEqual(4);
    expect(
      LETTERS_FACE_DOC_SOURCES.some((source) =>
        source.path.includes("face_component_truth_owner_decision_v1"),
      ),
    ).toBe(true);
  });

  it("documents material consumption and CNC cutting as primary calc cards", () => {
    expect(LETTERS_FACE_CALC_CARDS.map((card) => card.id)).toEqual([
      "material_consumption",
      "cnc_cutting",
    ]);
    const material = LETTERS_FACE_CALC_CARDS[0];
    const cutting = LETTERS_FACE_CALC_CARDS[1];
    expect(material?.formulaRo).toMatch(/bounding|out-of-box/i);
    expect(cutting?.formulaRo).toMatch(/face_perimeter|2 treceri/i);
    expect(cutting?.stepsRo.join(" ")).toMatch(/2.*= 1 Decupare|2 treceri|Decupare contur/i);
    expect(material?.formulaRo + cutting?.formulaRo).not.toMatch(/\d+\.\d+\s*EUR/);
  });
});

