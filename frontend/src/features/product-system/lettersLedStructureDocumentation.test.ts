import { describe, expect, it } from "vitest";
import {
  LETTERS_LED_CALC_CARDS,
  LETTERS_LED_DOC_DIRECTION_RO,
  LETTERS_LED_DOC_ROLE_RO,
  LETTERS_LED_DOC_SECTIONS,
  LETTERS_LED_DOC_SOURCES,
  LETTERS_LED_LIGHT_COLOR_DEFAULT,
  LETTERS_LED_MODULE_WATTAGE_DEFAULT_W,
  LETTERS_LED_MODULE_WATTAGE_OPTIONS_W,
  LETTERS_LED_PITCH_MM,
  LETTERS_LED_PSU_RESERVE_PERCENT,
} from "./lettersLedStructureDocumentation";
import { LETTERS_LED_MODULE_DISPLAY_NAME } from "@/lib/materials/lettersLedMaterialDisplay";

describe("lettersLedStructureDocumentation", () => {
  it("covers role, material, psu, process, boundary, direction", () => {
    expect(LETTERS_LED_DOC_SECTIONS.map((section) => section.id)).toEqual([
      "role",
      "material",
      "psu",
      "process",
      "boundary",
      "direction",
    ]);
    expect(LETTERS_LED_DOC_ROLE_RO).toMatch(/Pasul 4/);
    expect(LETTERS_LED_DOC_DIRECTION_RO).toMatch(/Composer|Finisaj/i);
  });

  it("locks module identity, wattage, light color and 250 mm pitch without hardcoded EUR", () => {
    const material = LETTERS_LED_DOC_SECTIONS.find((section) => section.id === "material");
    expect(material?.bodyRo).toContain(LETTERS_LED_MODULE_DISPLAY_NAME);
    expect(material?.bodyRo).toContain("MAT-LED-MODULE");
    expect(LETTERS_LED_PITCH_MM).toBe(250);
    expect(LETTERS_LED_MODULE_WATTAGE_OPTIONS_W).toEqual([0.75, 1.0, 1.44]);
    expect(LETTERS_LED_MODULE_WATTAGE_DEFAULT_W).toBe(0.75);
    expect(LETTERS_LED_LIGHT_COLOR_DEFAULT).toBe("warm");
    expect(material?.bulletsRo?.join(" ")).toMatch(/0\.75/);
    expect(material?.bulletsRo?.join(" ")).toMatch(/warm/);
    expect(material?.bulletsRo?.some((line) => /\d+(?:[.,]\d+)?\s*€/.test(line))).toBe(false);
  });

  it("lists canonical owner source paths including PSU allocation", () => {
    expect(LETTERS_LED_DOC_SOURCES.length).toBeGreaterThanOrEqual(3);
    expect(
      LETTERS_LED_DOC_SOURCES.some((source) =>
        source.path.includes("intake_v4_led_lighting"),
      ),
    ).toBe(true);
    expect(
      LETTERS_LED_DOC_SOURCES.some((source) => source.path.includes("psuAllocation")),
    ).toBe(true);
  });

  it("documents letter LED formula and automatic PSU allocation as primary calc cards", () => {
    expect(LETTERS_LED_CALC_CARDS.map((card) => card.id)).toEqual([
      "module_count",
      "psu_selection",
    ]);
    const modules = LETTERS_LED_CALC_CARDS[0];
    const psu = LETTERS_LED_CALC_CARDS[1];
    expect(modules?.titleRo).toMatch(/Formula LED/i);
    expect(modules?.formulaRo).toMatch(/ceil.*250/i);
    expect(modules?.formulaRo).toMatch(/estimated_led_watts/i);
    expect(modules?.notThisRo.join(" ")).toMatch(/emblem/i);
    expect(psu?.formulaRo).toMatch(/required_psu_watts/i);
    expect(psu?.formulaRo).toMatch(/psu_configuration/i);
    expect(psu?.stepsRo.join(" ")).toMatch(/fără emblemă|fără emblema/i);
    expect(LETTERS_LED_PSU_RESERVE_PERCENT).toBe(30);
    expect(psu?.stepsRo.join(" ")).toMatch(/30%/);
    expect(modules?.formulaRo + psu?.formulaRo).not.toMatch(/\d+\.\d+\s*EUR/);
  });

  it("keeps emblem lighting out of letters Sistem LED scope", () => {
    const boundary = LETTERS_LED_DOC_SECTIONS.find((section) => section.id === "boundary");
    expect(boundary?.bulletsRo?.join(" ")).toMatch(/emblem/i);
    expect(LETTERS_LED_DOC_ROLE_RO).toMatch(/Emblem/i);
  });
});
