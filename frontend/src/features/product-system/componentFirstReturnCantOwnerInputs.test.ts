import { describe, expect, it } from "vitest";
import {
  buildReturnCantOwnerInputSummary,
  formatReturnCantOwnerInputDisplayValue,
  RETURN_CANT_OWNER_INPUTS,
  RETURN_CANT_OWNER_INPUT_DISPLAY_UNKNOWN,
  workshopFieldAlignedWithOwnerInputs,
} from "./componentFirstReturnCantOwnerInputs";
import { FINISH_TYPE_VALUES, RETURN_CANT_WORKSHOP_FIELDS } from "./componentFirstLettersProductTruthWorkshop";

describe("componentFirstReturnCantOwnerInputs", () => {
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

  it("confirms RAL material/labor separation as model not price", () => {
    const ralSep = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "ral_material_labor_separation");
    expect(ralSep?.status).toBe("owner_confirmed");
    expect(String(ralSep?.value)).toMatch(/separate/i);
    expect(String(ralSep?.value)).not.toMatch(/\d+\s*(lei|eur)/i);
  });

  it("marks missing pricing-critical inputs as owner_input_required with null value", () => {
    const pendingKeys = [
      "oracal_code_list",
      "oracal_pricing_mode",
      "ral_input_mode",
      "return_depths_standard",
      "return_material",
      "return_material_unit",
      "return_labor_unit",
      "ral_material_price_rule",
      "ral_labor_price_rule",
    ];
    for (const key of pendingKeys) {
      const input = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === key);
      expect(input?.status).toBe("owner_input_required");
      expect(input?.value).toBeNull();
      expect(input?.mustNotInvent).toBe(true);
    }
  });

  it("does not contain fake Oracal codes, RAL lists, or prices", () => {
    for (const input of RETURN_CANT_OWNER_INPUTS) {
      const serialized = JSON.stringify(input.value ?? "");
      expect(serialized).not.toMatch(/ORACAL-\d+/i);
      expect(serialized).not.toMatch(/RAL\s*\d{4}/i);
      expect(serialized).not.toMatch(/\b\d+(\.\d+)?\s*(lei|eur|ron)\b/i);
    }
  });

  it("formats unknown values as OWNER INPUT REQUIRED not dash or zero", () => {
    const pending = RETURN_CANT_OWNER_INPUTS.find((i) => i.key === "oracal_code_list")!;
    expect(formatReturnCantOwnerInputDisplayValue(pending)).toBe(RETURN_CANT_OWNER_INPUT_DISPLAY_UNKNOWN);
    expect(formatReturnCantOwnerInputDisplayValue(pending)).not.toBe("-");
    expect(formatReturnCantOwnerInputDisplayValue(pending)).not.toBe("0");
    expect(formatReturnCantOwnerInputDisplayValue(pending)).not.toBe("null");
  });

  it("reports global OWNER INPUT REQUIRED summary", () => {
    const summary = buildReturnCantOwnerInputSummary();
    expect(summary.globalStatus).toBe("OWNER_INPUT_REQUIRED");
    expect(summary.confirmedCount).toBeGreaterThan(0);
    expect(summary.pendingCount).toBeGreaterThan(0);
  });

  it("aligns with workshop field contract keys", () => {
    expect(workshopFieldAlignedWithOwnerInputs()).toBe(true);
  });
});
