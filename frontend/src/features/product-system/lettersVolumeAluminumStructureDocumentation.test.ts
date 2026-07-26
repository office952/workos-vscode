import { describe, expect, it } from "vitest";
import {
  LETTERS_VOLUME_CALC_CARDS,
  LETTERS_VOLUME_DOC_DIRECTION_RO,
  LETTERS_VOLUME_DOC_ROLE_RO,
  LETTERS_VOLUME_DOC_SECTIONS,
  LETTERS_VOLUME_DOC_SOURCES,
} from "./lettersVolumeAluminumStructureDocumentation";
import { LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO } from "@/lib/materials/lettersVolumeAluminumMaterialDisplay";

describe("lettersVolumeAluminumStructureDocumentation", () => {
  it("covers role, material, process, finish, boundary, direction", () => {
    expect(LETTERS_VOLUME_DOC_SECTIONS.map((section) => section.id)).toEqual([
      "role",
      "material",
      "process",
      "finish",
      "boundary",
      "direction",
    ]);
    expect(LETTERS_VOLUME_DOC_ROLE_RO).toMatch(/Pasul 2/);
    expect(LETTERS_VOLUME_DOC_DIRECTION_RO).toMatch(/Vizual față|Composer/i);
  });

  it("locks volume family and width SKUs without hardcoded EUR amounts", () => {
    const material = LETTERS_VOLUME_DOC_SECTIONS.find((section) => section.id === "material");
    const finish = LETTERS_VOLUME_DOC_SECTIONS.find((section) => section.id === "finish");
    expect(material?.bodyRo).toContain(LETTERS_VOLUME_ALUMINUM_FAMILY_LABEL_RO);
    expect(material?.bodyRo).toContain("MAT-PROFIL-LATERAL-LITERE");
    expect(material?.bulletsRo?.some((line) => /30MM/.test(line))).toBe(true);
    expect(material?.bulletsRo?.some((line) => /€\/ml|EUR\/ml|\d+\.\d/.test(line))).toBe(
      false,
    );
    expect(finish?.bulletsRo?.some((line) => /Pricing Registry|registry/i.test(line))).toBe(
      true,
    );
  });

  it("lists canonical owner source paths", () => {
    expect(LETTERS_VOLUME_DOC_SOURCES.length).toBeGreaterThanOrEqual(4);
    expect(
      LETTERS_VOLUME_DOC_SOURCES.some((source) =>
        source.path.includes("return_cant_owner_answers"),
      ),
    ).toBe(true);
    expect(
      LETTERS_VOLUME_DOC_SOURCES.some((source) =>
        source.path.includes("face_component_truth_owner_decision"),
      ),
    ).toBe(true);
  });

  it("documents profile consumption and cant finish as primary calc cards", () => {
    expect(LETTERS_VOLUME_CALC_CARDS.map((card) => card.id)).toEqual([
      "profile_consumption",
      "cant_finish",
    ]);
    const profile = LETTERS_VOLUME_CALC_CARDS[0];
    const finish = LETTERS_VOLUME_CALC_CARDS[1];
    expect(profile?.formulaRo).toMatch(/face_perimeter_length_m|quantity_ml/i);
    expect(finish?.formulaRo).toMatch(/Oracal|RAL|lățime_rolă/i);
    expect(profile?.formulaRo + finish?.formulaRo).not.toMatch(/\d+\.\d+\s*EUR/);
  });
});
