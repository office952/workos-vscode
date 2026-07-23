import { describe, expect, it } from "vitest";
import {
  buildReturnCantOwnerInputSummary,
  formatReturnCantOwnerInputDisplayValue,
  RETURN_CANT_OWNER_INPUTS,
  RETURN_CANT_OWNER_INPUT_DISPLAY_UNKNOWN,
  workshopFieldAlignedWithOwnerInputs,
} from "./candidateModuleProdusReturnCantOwnerInputs";
import { FINISH_TYPE_VALUES, RETURN_CANT_WORKSHOP_FIELDS } from "./candidateModuleProdusLettersProductTruthWorkshop";

describe("candidateModuleProdusReturnCantOwnerInputs", () => {
  it("confirms finish variants exactly as Culoare Stock, Oracal, Vopsit RAL", () => {
    const finish = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "finish_type_variants");
    expect(finish?.status).toBe("owner_confirmed");
    expect(finish?.value).toEqual([...FINISH_TYPE_VALUES]);
    expect(FINISH_TYPE_VALUES).toEqual(["Culoare Stock", "Oracal", "Vopsit RAL"]);
  });

  it("confirms stock color note mode without price assumption", () => {
    const stock = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "stock_color_note_mode");
    expect(stock?.status).toBe("owner_confirmed");
    expect(stock?.notesRo).toMatch(/Cost diferit NU/i);
    const workshopStock = RETURN_CANT_WORKSHOP_FIELDS.find((f) => f.fieldKey === "stock_color_note");
    expect(workshopStock?.status).toBe("confirmed");
  });

  it("confirms Oracal selector mode as lista completa without fake catalog", () => {
    const selector = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "oracal_selector_mode");
    expect(selector?.status).toBe("owner_confirmed");
    expect(selector?.value).toBe("listă completă Oracal");
    const catalog = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "oracal_code_list");
    expect(catalog?.status).toBe("owner_confirmed");
    expect(String(catalog?.value)).toMatch(/Intake V6 colorRegistry/i);
    expect(String(catalog?.value)).toMatch(/oracal651\.ts/i);
  });

  it("confirms Oracal pricing mode as pret pe cod/familie", () => {
    const pricing = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "oracal_pricing_mode");
    expect(pricing?.status).toBe("owner_confirmed");
    expect(pricing?.value).toBe("preț pe cod/familie");
  });

  it("confirms RAL input mode as selector standard without fake RAL table", () => {
    const ralMode = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "ral_input_mode");
    expect(ralMode?.status).toBe("owner_confirmed");
    expect(ralMode?.value).toBe("selector standard RAL");
    const ralSource = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "ral_selector_source");
    expect(ralSource?.status).toBe("owner_confirmed");
    expect(String(ralSource?.value)).toMatch(/RAL Classic/i);
  });

  it("confirms return depths as 30 / 60 / 80 / 100 mm", () => {
    const depths = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "return_depths_standard");
    expect(depths?.status).toBe("owner_confirmed");
    expect(depths?.value).toEqual(["30", "60", "80", "100"]);
    expect(formatReturnCantOwnerInputDisplayValue(depths!)).toMatch(/30 mm.*60 mm.*80 mm.*100 mm/);
  });

  it("confirms return material as aluminiu 0.6 mm", () => {
    const material = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "return_material");
    expect(material?.status).toBe("owner_confirmed");
    expect(material?.value).toBe("aluminiu 0.6 mm");
  });

  it("confirms material and labor units as ml", () => {
    expect(RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "return_material_unit")?.value).toBe("ml");
    expect(RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "return_labor_unit")?.value).toBe("ml");
  });

  it("confirms stock color does not affect price", () => {
    const stockPrice = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "stock_color_affects_price");
    expect(stockPrice?.status).toBe("owner_confirmed");
    expect(stockPrice?.value).toBe(false);
    expect(formatReturnCantOwnerInputDisplayValue(stockPrice!)).toMatch(/Nu — doar informație atelier/i);
  });

  it("confirms material-depth compatibility and RAL selector source", () => {
    const compat = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "material_depth_compatibility");
    const ralSource = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "ral_selector_source");
    expect(compat?.status).toBe("owner_confirmed");
    expect(ralSource?.status).toBe("owner_confirmed");
    expect(String(ralSource?.value)).toMatch(/RAL Classic/i);
  });

  it("confirms perimeter geometry source as perimetru/contur real", () => {
    const perimeter = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "perimeter_geometry_source");
    expect(perimeter?.status).toBe("owner_confirmed");
    expect(perimeter?.value).toBe("perimetru/contur real al literelor");
  });

  it("marks RAL material/labor price rules as owner_confirmed with Pricing Registry key references", () => {
    const materialRule = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "ral_material_price_rule");
    const laborRule = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "ral_labor_price_rule");
    expect(materialRule?.status).toBe("owner_confirmed");
    expect(laborRule?.status).toBe("owner_confirmed");
    expect(String(materialRule?.value)).toMatch(/MAT-VOPSEA-RAL-CANT-30MM/i);
    expect(String(materialRule?.value)).toMatch(/\/inventory\/pricing/i);
    expect(String(materialRule?.value)).not.toMatch(/2\.00 EUR\/ml/i);
    expect(String(laborRule?.value)).toMatch(/RETURN_CANT_RAL_PAINT_LABOR/i);
    expect(String(laborRule?.value)).toMatch(/\/inventory\/pricing/i);
    expect(String(laborRule?.value)).not.toMatch(/1\.00 EUR\/ml/i);
  });

  it("confirms RAL material/labor separation as model not price", () => {
    const ralSep = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "ral_material_labor_separation");
    expect(ralSep?.status).toBe("owner_confirmed");
    expect(String(ralSep?.value)).toMatch(/separate/i);
    expect(String(ralSep?.value)).not.toMatch(/\d+\s*(lei|eur)/i);
  });

  it("does not contain fake Oracal codes or uninvented catalog entries", () => {
    const catalogPending = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "oracal_code_list")!;
    expect(JSON.stringify(catalogPending.value)).not.toMatch(/ORACAL-\d+/i);
    expect(JSON.stringify(catalogPending.value)).not.toMatch(/RAL\s*\d{4}/i);
  });

  it("allows owner-confirmed RAL registry keys and minimum lei per color on material plus labor", () => {
    const material = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "ral_material_price_rule");
    const minimum = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "minimum_price_rule");
    expect(String(material?.value)).toMatch(/MAT-VOPSEA-RAL-CANT-30MM/i);
    expect(String(material?.value)).not.toMatch(/2\.00 EUR\/ml/i);
    expect(minimum?.status).toBe("owner_confirmed");
    expect(String(minimum?.value)).toMatch(/100 lei/i);
    expect(String(minimum?.value)).toMatch(/pe culoare RAL/i);
    expect(String(minimum?.value)).toMatch(/total material \+ manoperă/i);
    expect(String(minimum?.value)).toMatch(/fără conversie automată/i);
  });

  it("formats partial catalog values with target not dash or zero", () => {
    const catalog = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "oracal_code_list")!;
    expect(formatReturnCantOwnerInputDisplayValue(catalog)).toMatch(/Intake V6 colorRegistry/i);
    expect(formatReturnCantOwnerInputDisplayValue(catalog)).not.toBe("-");
    expect(formatReturnCantOwnerInputDisplayValue(catalog)).not.toBe("0");
  });

  it("reports global OWNER INPUT REQUIRED summary with partial count", () => {
    const summary = buildReturnCantOwnerInputSummary();
    expect(summary.globalStatus).toBe("OWNER_INPUT_REQUIRED");
    expect(summary.confirmedCount).toBeGreaterThan(10);
    expect(summary.partialCount).toBe(0);
  });

  it("aligns with workshop field contract keys", () => {
    expect(workshopFieldAlignedWithOwnerInputs()).toBe(true);
  });
});
