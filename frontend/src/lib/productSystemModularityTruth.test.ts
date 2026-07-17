import { describe, expect, it } from "vitest";
import {
  ACM_BOXED_TEMPLATE_CODE,
  getProductModularityTruth,
  LETTERS_TEMPLATE_CODE,
  LOGO_TEMPLATE_CODE,
  MODULARITY_LAW_LINES_RO,
  SETTINGS_OWNERSHIP_CONFLICT_RO,
} from "@/lib/productSystemModularityTruth";

describe("productSystemModularityTruth", () => {
  it("exposes modularity law with Romanian diacritics", () => {
    expect(MODULARITY_LAW_LINES_RO.join(" ")).toMatch(/PROBLEMĂ/);
    expect(MODULARITY_LAW_LINES_RO.join(" ")).toMatch(/SUSȚINĂ/);
    expect(MODULARITY_LAW_LINES_RO.join(" ")).toMatch(/COMBINĂ/);
  });

  it("maps Letters multi-axis truth without bare ACTIVE as sole status", () => {
    const truth = getProductModularityTruth(LETTERS_TEMPLATE_CODE)!;
    expect(truth.commercialChipRo).toBe("Rădăcină folosită azi");
    expect(truth.summaryChipsRo).toEqual(
      expect.arrayContaining([
        "Rădăcină ofertabilă",
        "Slice 1 stabilizat",
        "Stabilizare generală parțială",
      ]),
    );
    expect(truth.commercialChipRo).not.toMatch(/^(ACTIVE|CONFIRMAT|PARTIAL|Pregătit)$/);
    const face = truth.modules.find((m) => m.moduleKey === "FACE");
    const finish = truth.modules.find((m) => m.moduleKey === "FINISH");
    const mounting = truth.modules.find((m) => m.moduleKey === "MOUNTING");
    expect(face?.independenceRo).toMatch(/de sine stătător/);
    expect(finish?.independenceRo).toMatch(/captiv/);
    expect(finish?.independenceRo).toMatch(/Activare neaprobată/);
    expect(mounting?.independenceRo).toMatch(/captiv/);
    expect(mounting?.independenceRo).toMatch(/Activare neaprobată/);
    expect(finish?.noteRo).toMatch(/modul FINISH/);
    expect(mounting?.noteRo).toMatch(/mounting_system/);
    expect(truth.falseGeneric.some((m) => m.moduleKey === "sistem_led")).toBe(true);
    expect(truth.compositionDependencies[0]?.classId).toBe("COMPOSITION_ONLY");
    expect(truth.compositionDependencies[0]?.meaningRo).toMatch(/nu este cerință standalone/i);
    expect(truth.settingsConflictVisible).toBe(true);
    expect(SETTINGS_OWNERSHIP_CONFLICT_RO).toMatch(/conflict nerezolvat/i);
  });

  it("keeps Logo root blocked and linked child partial", () => {
    const truth = getProductModularityTruth(LOGO_TEMPLATE_CODE)!;
    expect(truth.commercialChipRo).toBe("Candidat · rădăcină blocată");
    expect(truth.summaryChipsRo).toEqual(
      expect.arrayContaining(["Rădăcină blocată", "Copil legat parțial", "Independență neprobată"]),
    );
    expect(truth.headlineRo).not.toMatch(/ofertabil/i);
  });

  it("keeps ACM boxed partial without independent panel readiness", () => {
    const truth = getProductModularityTruth(ACM_BOXED_TEMPLATE_CODE)!;
    expect(truth.commercialChipRo).toBe("Montaj ACM · parțial");
    expect(truth.summaryChipsRo.join(" ")).toMatch(/Panou independent nepregătit/);
    expect(truth.summaryChipsRo.join(" ")).toMatch(/Casetat arhivat/);
    expect(truth.modules.some((m) => m.moduleKey === "ACM-PANEL" && /nepregătit/.test(m.independenceRo))).toBe(
      true,
    );
  });
});
