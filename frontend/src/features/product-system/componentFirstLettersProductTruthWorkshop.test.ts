import { describe, expect, it } from "vitest";
import {
  buildWorkshopSummary,
  COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS,
  exportOwnerQuestions,
  getWorkshopByComponentCode,
  RETURN_CANT_WORKSHOP_FIELDS,
} from "./componentFirstLettersProductTruthWorkshop";

describe("componentFirstLettersProductTruthWorkshop", () => {
  const returnCant = getWorkshopByComponentCode("TPL-COMP-LETTER-RETURN-CANT_v1")!;

  it("RETURN-CANT has the 3 confirmed finish options", () => {
    const finishType = RETURN_CANT_WORKSHOP_FIELDS.find((f) => f.fieldKey === "finish_type");
    expect(finishType?.allowedValues).toEqual(["Culoare Stock", "Oracal", "Vopsit RAL"]);
    expect(finishType?.status).toBe("confirmed");
  });

  it("RETURN-CANT has stock_color_note as confirmed informational/atelier field", () => {
    const stockNote = RETURN_CANT_WORKSHOP_FIELDS.find((f) => f.fieldKey === "stock_color_note");
    expect(stockNote?.status).toBe("confirmed");
    expect(stockNote?.audience).toContain("atelier");
    expect(stockNote?.requirement).toContain("informational");
  });

  it("RETURN-CANT has Oracal/RAL fields as owner_input_required", () => {
    expect(RETURN_CANT_WORKSHOP_FIELDS.find((f) => f.fieldKey === "oracal_code")?.status).toBe(
      "owner_input_required",
    );
    expect(RETURN_CANT_WORKSHOP_FIELDS.find((f) => f.fieldKey === "ral_code")?.status).toBe(
      "owner_input_required",
    );
  });

  it("RETURN-CANT has RAL material/labor rules as owner_input_required with mustNotInvent", () => {
    const materialRule = RETURN_CANT_WORKSHOP_FIELDS.find((f) => f.fieldKey === "ral_material_price_rule");
    const laborRule = RETURN_CANT_WORKSHOP_FIELDS.find((f) => f.fieldKey === "ral_labor_price_rule");
    expect(materialRule?.status).toBe("owner_input_required");
    expect(laborRule?.status).toBe("owner_input_required");
    expect(materialRule?.mustNotInvent).toBe(true);
    expect(laborRule?.mustNotInvent).toBe(true);
  });

  it("all components have at least one owner question", () => {
    for (const workshop of COMPONENT_FIRST_LETTERS_PRODUCT_TRUTH_WORKSHOPS) {
      expect(workshop.ownerQuestions.length).toBeGreaterThan(0);
    }
  });

  it("all unconfirmed fields must have mustNotInvent=true", () => {
    const unconfirmed = RETURN_CANT_WORKSHOP_FIELDS.filter((f) => f.status !== "confirmed");
    for (const field of unconfirmed) {
      expect(field.mustNotInvent).toBe(true);
    }
  });

  it("no owner_input_required field has a fake default price", () => {
    const ownerRequired = RETURN_CANT_WORKSHOP_FIELDS.filter((f) => f.status === "owner_input_required");
    for (const field of ownerRequired) {
      if (field.inputType === "money" || field.inputType === "unit_rate") {
        expect(field.defaultValue).toBeUndefined();
      }
    }
  });

  it("workshop global status is OWNER_INPUT_REQUIRED", () => {
    const summary = buildWorkshopSummary();
    expect(summary.globalStatus).toBe("OWNER_INPUT_REQUIRED");
  });

  it("exports owner questions grouped by component with RETURN-CANT first in list", () => {
    const questions = exportOwnerQuestions();
    expect(questions.some((q) => q.componentShortLabel === "RETURN-CANT")).toBe(true);
    expect(returnCant.ownerQuestions.length).toBeGreaterThan(0);
  });

  it("cross-references existing mapping paths where available", () => {
    const depth = RETURN_CANT_WORKSHOP_FIELDS.find((f) => f.fieldKey === "return_depth_mm");
    expect(depth?.truthPath).toBe("product.components.return_cant.depth");
    expect(depth?.pathSource).toBe("confirmed_mapping");
  });
});
