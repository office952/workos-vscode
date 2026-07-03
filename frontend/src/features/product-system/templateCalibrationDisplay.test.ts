import { describe, it, expect } from "vitest";
import {
  formatComponentDisplayName,
  formatMaterialQuantityLabel,
  formatOperationCalibrationLabel,
  hasFormulaLineMetadata,
} from "@/features/product-system/templateCalibrationDisplay";

describe("templateCalibrationDisplay", () => {
  it("formats formula operations without misleading zero minutes", () => {
    expect(
      formatOperationCalibrationLabel({
        estimatedMinutes: 0,
        calculation_type: "formula_based",
        formula_id: "perimeter",
      })
    ).toBe("calculată la ofertare");
  });

  it("formats static operation calibration duration", () => {
    expect(
      formatOperationCalibrationLabel({
        estimatedMinutes: 45,
        calculation_type: "static",
      })
    ).toBe("durată internă de calibrare: 45 min");
  });

  it("formats formula materials without misleading zero quantity", () => {
    expect(
      formatMaterialQuantityLabel({
        quantity: 0,
        unit: "mp",
        formula_id: "face_area",
      })
    ).toBe("calculată la ofertare");
  });

  it("detects formula metadata on materials", () => {
    expect(
      hasFormulaLineMetadata({
        formula_id: "qty",
      })
    ).toBe(true);
  });

  it("softens QC in finisaj display names", () => {
    const label = formatComponentDisplayName("Finisare — vopsire, asamblare, QC");
    expect(label).toBe("Finisare — vopsire, asamblare");
  });
});
