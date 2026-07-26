import { describe, expect, it } from "vitest";
import {
  misleadingCodeNoteRo,
  normalizePricingDisplayName,
} from "./pricingDisplayNaming";

describe("pricingDisplayNaming — Volum aluminiu", () => {
  it("locks four width SKUs and selector", () => {
    expect(normalizePricingDisplayName("MAT-PROFIL-LATERAL-LITERE-30MM", "x")).toBe(
      "Volum aluminiu 30 mm",
    );
    expect(normalizePricingDisplayName("MAT-PROFIL-LATERAL-LITERE-100MM", "x")).toBe(
      "Volum aluminiu 100 mm",
    );
    expect(normalizePricingDisplayName("MAT-PROFIL-LATERAL-LITERE", "x")).toBe(
      "Volum aluminiu — alege lățimea (30/60/80/100)",
    );
  });

  it("warns against confusing with ACM / premontaj / casetă", () => {
    expect(misleadingCodeNoteRo("MAT-PROFIL-LATERAL-LITERE-60MM")).toMatch(/Nu panou ACM/i);
    expect(misleadingCodeNoteRo("MAT-PROFIL-LATERAL-LITERE")).toMatch(/Selector/i);
  });
});

describe("pricingDisplayNaming — Capac spate Forex", () => {
  it("locks Forex 10 mm display for MAT-SPATE-PVC-LITERE", () => {
    expect(normalizePricingDisplayName("MAT-SPATE-PVC-LITERE", "PVC expandat 10 mm")).toBe(
      "Forex 10 mm",
    );
    expect(misleadingCodeNoteRo("MAT-SPATE-PVC-LITERE")).toMatch(/Capac spate/i);
  });
});

describe("pricingDisplayNaming — Sistem LED", () => {
  it("locks module, strip, PSU selector and wattage labels", () => {
    expect(normalizePricingDisplayName("MAT-LED-MODULE", "x")).toBe("Modul LED 12V");
    expect(normalizePricingDisplayName("MAT-LED-STRIP", "x")).toBe("Bandă LED 12V");
    expect(normalizePricingDisplayName("MAT-LED-PSU-12V", "x")).toBe(
      "Sursă LED 12V — alege puterea (60/100/160/200 W)",
    );
    expect(normalizePricingDisplayName("MAT-LED-PSU-12V-200W", "x")).toBe("Sursă LED 12V 200W");
  });

  it("warns against W-multiplication and strip-as-standard", () => {
    expect(misleadingCodeNoteRo("MAT-LED-PSU-12V")).toMatch(/Nu multiplica/i);
    expect(misleadingCodeNoteRo("MAT-LED-STRIP")).toMatch(/Alternativă/i);
  });
});


