import { describe, expect, it } from "vitest";
import {
  formatEmployeeMobileV2MachineLabel,
  formatEmployeeMobileV2ProcessLabel,
} from "@/lib/employeeMobileV2Labels";

describe("employeeMobileV2Labels", () => {
  it("maps known process slugs to human labels", () => {
    expect(formatEmployeeMobileV2ProcessLabel("volumetric_letter_assembly")).toBe(
      "Asamblare litere volumetrice",
    );
    expect(formatEmployeeMobileV2ProcessLabel("cnc_cutting")).toBe("Debitare CNC");
    expect(formatEmployeeMobileV2ProcessLabel("led_assembly")).toBe("Montaj LED");
  });

  it("hides unknown process slugs instead of showing snake_case", () => {
    expect(formatEmployeeMobileV2ProcessLabel("unknown_internal_step")).toBeNull();
    expect(formatEmployeeMobileV2ProcessLabel("")).toBeNull();
  });

  it("maps known machine codes to human labels", () => {
    expect(formatEmployeeMobileV2MachineLabel("ASSEMBLY_TABLE")).toBe("Masă asamblare");
  });

  it("hides unknown machine slugs", () => {
    expect(formatEmployeeMobileV2MachineLabel("MYSTERY_STATION")).toBeNull();
  });

  it("allows already human-readable values without spaces requirement breach", () => {
    expect(formatEmployeeMobileV2ProcessLabel("Montaj manual")).toBe("Montaj manual");
  });
});
