import { describe, expect, it } from "vitest";

import type { IntakeV6CncOperationRow } from "./intakeV6Api";
import {
  adaptBackingAbsentOperationLabel,
  buildOperatorLogoLabelMap,
  formatIntakeV6LinearQuantityDisplay,
  getOperatorLayerLabel,
  isInternalCorelLayerId,
  isPrintLaminationOperationRow,
  sanitizeOperatorDisplayText,
  splitIntakeV6MaterialBreakdownOperationRows,
} from "./intakeV6OperatorUiDisplay";

describe("intakeV6OperatorUiDisplay", () => {
  it("maps internal Corel ids to friendly logo labels", () => {
    const logoLabelMap = buildOperatorLogoLabelMap([
      { id: "logo-dreapta", name: "logo dreapta" },
      { id: "logo-stanga", name: "logo stanga" },
    ]);

    expect(isInternalCorelLayerId("_2209257786352")).toBe(true);
    expect(getOperatorLayerLabel("logo-dreapta", "logo dreapta", { logoLabelMap })).toBe("Logo 1");
    expect(getOperatorLayerLabel("logo-stanga", "logo stanga", { logoLabelMap })).toBe("Logo 2");
    expect(getOperatorLayerLabel("_2209257786352", "logo dreapta", { logoLabelMap })).toBe("Logo 1");
    expect(getOperatorLayerLabel("_2209257786352", "_2209257786352")).toBe("artwork layer");
  });

  it("numbers a single positional logo as Logo 1 regardless of side token", () => {
    const rightOnlyMap = buildOperatorLogoLabelMap([{ id: "logo-dreapta", name: "logo dreapta" }]);
    const centerOnlyMap = buildOperatorLogoLabelMap([{ id: "logo-centru", name: "logo centru" }]);

    expect(getOperatorLayerLabel("logo-dreapta", "logo dreapta", { logoLabelMap: rightOnlyMap })).toBe("Logo 1");
    expect(getOperatorLayerLabel("logo-centru", "logo centru", { logoLabelMap: centerOnlyMap })).toBe("Logo 1");
  });

  it("formats CNC linear quantity as meters not milliliters", () => {
    expect(formatIntakeV6LinearQuantityDisplay(25.02, "ml", "cnc")).toBe("25.02 m");
    expect(formatIntakeV6LinearQuantityDisplay(19, "ml", "cable")).toBe("19.00 m");
    expect(
      formatIntakeV6LinearQuantityDisplay(50.04, "ml", "adhesive", {
        materialKey: "adhesive_return_to_face",
      }),
    ).toBe("50.04 ml");
    expect(formatIntakeV6LinearQuantityDisplay(68.11, "ml-pass", "machine_pass")).toBe("68.11 m-pass");
  });

  it("splits CNC and print operation rows", () => {
    const rows: IntakeV6CncOperationRow[] = [
      {
        key: "cnc_face_cutting_plexiglas_3mm",
        display_name: "Debitare CNC față plexiglas 3mm PMMA - opal",
        operation_type: "cutting",
        quantity: 13.62,
        unit: "ml",
      },
      {
        key: "artwork_logo-dreapta_print_vinyl_op",
        display_name: "Imprimare autocolant — logo dreapta",
        operation_type: "print_vinyl",
        quantity: 0.45,
        unit: "m2",
      },
    ];
    const split = splitIntakeV6MaterialBreakdownOperationRows(rows);
    expect(split.cncRows).toHaveLength(1);
    expect(split.printRows).toHaveLength(1);
    expect(isPrintLaminationOperationRow(split.printRows[0])).toBe(true);
  });

  it("adapts backing-absent CNC task labels", () => {
    expect(
      adaptBackingAbsentOperationLabel(
        "Debitare față plexiglas și spate Forex la CNC",
        "none",
      ),
    ).toBe("Debitare față plexiglas la CNC");
  });

  it("sanitizes internal ids in operator strings", () => {
    expect(sanitizeOperatorDisplayText("Print față — _2209257786352")).toContain("artwork layer");
  });
});