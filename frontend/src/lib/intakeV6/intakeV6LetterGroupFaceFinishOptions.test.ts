import { describe, expect, it } from "vitest";
import { resolveLetterGroupFaceFinishOptions } from "./intakeV6LetterGroupFaceFinishOptions";

describe("resolveLetterGroupFaceFinishOptions", () => {
  const templateWithPrint = [
    { value: "none", label: "Fără finisaj — plexiglas brut" },
    { value: "oracal_641", label: "Oracal 641" },
    { value: "oracal_651", label: "Oracal 651" },
    { value: "oracal_8500", label: "Oracal 8500" },
    { value: "printed_vinyl", label: "Print pe vinyl" },
    { value: "printed_laminated_vinyl", label: "Printat / Laminat" },
  ];

  it("includes allowed letter face finishes with none option", () => {
    const options = resolveLetterGroupFaceFinishOptions(templateWithPrint);
    expect(options.map((o) => o.value)).toEqual(["none", "oracal_641", "oracal_651", "oracal_8500", "print_laminate"]);
    expect(options.find((o) => o.value === "none")?.label).toBe("Fără finisaj — plexiglas brut");
    expect(options.find((o) => o.value === "print_laminate")?.label).toBe("Printat / Laminat");
    expect(options.find((o) => o.value === "oracal_8500")?.label).toBe("Oracal 8500");
  });

  it("excludes legacy print-only vinyl option from letter groups", () => {
    const options = resolveLetterGroupFaceFinishOptions(templateWithPrint);
    const labels = options.map((o) => o.label);
    expect(labels).not.toContain("Print pe vinyl");
  });
});
