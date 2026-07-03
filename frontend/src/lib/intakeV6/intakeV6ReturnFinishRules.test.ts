import { describe, expect, it } from "vitest";
import {
  buildIntakeV6ReturnCantForUiOption,
  formatIntakeV6ReturnFinishLabel,
  INTAKE_V6_RETURN_FINISH_UI_OPTIONS,
  intakeV6InternalReturnFinishToUi,
  resolveIntakeV6ReturnFinishUiOption,
} from "./intakeV6ReturnFinishRules";

describe("intakeV6ReturnFinishRules", () => {
  it("exposes only operator-facing cant options", () => {
    expect(INTAKE_V6_RETURN_FINISH_UI_OPTIONS.map((row) => row.label)).toEqual([
      "Alb",
      "Negru",
      "Auriu",
      "Argintiu",
      "Vopsit RAL",
      "Oracal 651",
    ]);
  });

  it("maps Oracal 651 UI option to oracal_wrapped with series 651", () => {
    const next = buildIntakeV6ReturnCantForUiOption("oracal_wrapped", {
      finishType: "standard_aluminum",
      depthMm: 60,
    });
    expect(next.finishType).toBe("oracal_wrapped");
    expect(next.materialCode).toBe("651");
  });

  it("maps legacy standard_aluminum to Argintiu UI option", () => {
    expect(intakeV6InternalReturnFinishToUi("standard_aluminum")).toBe("silver");
    expect(resolveIntakeV6ReturnFinishUiOption("standard_aluminum")).toBe("silver");
  });

  it("defaults missing finish to Alb UI option", () => {
    expect(resolveIntakeV6ReturnFinishUiOption(null)).toBe("white");
    expect(resolveIntakeV6ReturnFinishUiOption("")).toBe("white");
  });

  it("formats user-friendly labels for summary", () => {
    expect(
      formatIntakeV6ReturnFinishLabel({
        finishType: "standard_aluminum",
      }),
    ).toBe("Argintiu");
    expect(
      formatIntakeV6ReturnFinishLabel({
        finishType: "oracal_wrapped",
        colorCode: "070",
        colorName: "White",
      }),
    ).toBe("Oracal 651 White");
    expect(
      formatIntakeV6ReturnFinishLabel({
        finishType: "ral_paint",
        colorCode: "9005",
        colorName: "Jet black",
      }),
    ).toContain("Vopsit RAL 9005");
  });
});