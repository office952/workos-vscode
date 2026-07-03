import { describe, expect, it } from "vitest";
import {
  findMaterialFamilyMatches,
  findUsageTermWarnings,
  getCanonicalMaterialSuggestion,
  isSubstantiallyCanonicalMaterialName,
  normalizeMaterialSearchTerm,
} from "./materialCanonicalAnalysis";

describe("materialCanonicalAnalysis", () => {
  it("normalizes search terms", () => {
    expect(normalizeMaterialSearchTerm("  Bond_3mm  ")).toBe("bond 3mm");
    expect(normalizeMaterialSearchTerm("Țeavă 30×30")).toBe("teava 30 30");
  });

  it("maps bond to ACM/ACP family", () => {
    const suggestion = getCanonicalMaterialSuggestion("bond 3mm");
    expect(suggestion.families[0]?.family.material_family).toBe("acm_acp_panel");
    expect(suggestion.canonicalLabelSuggestion).toMatch(/ACM\/ACP/);
    expect(suggestion.messages.some((m) => /bond/i.test(m))).toBe(true);
  });

  it("maps dibond to ACM/ACP with brand hint", () => {
    const suggestion = getCanonicalMaterialSuggestion("dibond alb 3mm");
    expect(suggestion.families[0]?.family.material_family).toBe("acm_acp_panel");
    expect(suggestion.brandMatches.some((b) => b.term === "dibond")).toBe(true);
    expect(suggestion.messages.some((m) => /Dibond/i.test(m))).toBe(true);
  });

  it("maps alucobond to ACM/ACP", () => {
    const matches = findMaterialFamilyMatches("alucobond 4mm");
    expect(matches[0]?.family.material_family).toBe("acm_acp_panel");
  });

  it("maps forex to PVC expandat", () => {
    const suggestion = getCanonicalMaterialSuggestion("forex 10mm");
    expect(suggestion.families[0]?.family.material_family).toBe("pvc_expanded");
    expect(suggestion.canonicalLabelSuggestion).toBe("PVC expandat");
  });

  it("maps stiplex and plexiglas to PMMA", () => {
    expect(getCanonicalMaterialSuggestion("stiplex 3mm").families[0]?.family.material_family).toBe(
      "pmma_acrylic"
    );
    expect(
      getCanonicalMaterialSuggestion("plexiglas opal 3mm").families[0]?.family.material_family
    ).toBe("pmma_acrylic");
  });

  it("maps oracal 651 to vinyl film with brand and series", () => {
    const suggestion = getCanonicalMaterialSuggestion("oracal 651 galben");
    expect(suggestion.families[0]?.family.material_family).toBe("vinyl_film");
    expect(suggestion.families[0]?.matchedSeries).toContain("651");
    expect(suggestion.brandMatches.some((b) => b.term === "oracal")).toBe(true);
  });

  it("maps vinyl to folie autocolantă PVC", () => {
    const suggestion = getCanonicalMaterialSuggestion("vinyl print");
    expect(suggestion.families[0]?.family.material_family).toBe("vinyl_film");
  });

  it("warns on premontaj usage for steel profile input", () => {
    const suggestion = getCanonicalMaterialSuggestion("bare premontaj otel 30x30x1.5");
    expect(suggestion.families[0]?.family.material_family).toBe("steel_profile");
    expect(suggestion.usageWarnings.some((w) => /premontaj/i.test(w.term))).toBe(true);
    expect(suggestion.messages.some((m) => /utilizarea materialului/i.test(m))).toBe(true);
  });

  it("maps profil aluminiu caseta with usage warning", () => {
    const suggestion = getCanonicalMaterialSuggestion("profil aluminiu caseta");
    expect(suggestion.families[0]?.family.material_family).toBe("aluminium_profile");
    expect(suggestion.usageWarnings.length).toBeGreaterThan(0);
  });

  it("maps pvc expandat directly", () => {
    const suggestion = getCanonicalMaterialSuggestion("pvc expandat 5mm alb");
    expect(suggestion.families[0]?.family.material_family).toBe("pvc_expanded");
  });

  it("preserves ACM technical specs hint", () => {
    const suggestion = getCanonicalMaterialSuggestion("ACM 3 mm alu 0.30");
    expect(suggestion.families[0]?.family.material_family).toBe("acm_acp_panel");
    expect(suggestion.messages.some((m) => /Specificațiile tehnice/i.test(m))).toBe(true);
  });

  it("suppresses alias noise for already-canonical PVC expandat name", () => {
    const suggestion = getCanonicalMaterialSuggestion("PVC expandat 10 mm");
    expect(suggestion.families[0]?.family.material_family).toBe("pvc_expanded");
    expect(suggestion.messages.some((m) => /Termen detectat/i.test(m))).toBe(false);
  });

  it("UI smoke: bond 3mm shows alias hint", () => {
    expect(getCanonicalMaterialSuggestion("bond 3mm").messages.length).toBeGreaterThan(0);
  });

  it("UI smoke: dibond alb 3mm shows brand or alias", () => {
    const m = getCanonicalMaterialSuggestion("dibond alb 3mm").messages.join(" ");
    expect(/dibond|Dibond|ACM/i.test(m)).toBe(true);
  });

  it("UI smoke: bare premontaj shows usage warning", () => {
    expect(
      getCanonicalMaterialSuggestion("bare premontaj otel 30x30x1.5").usageWarnings.length
    ).toBeGreaterThan(0);
  });

  it("isSubstantiallyCanonicalMaterialName detects canonical PVC label", () => {
    expect(
      isSubstantiallyCanonicalMaterialName(
        "PVC expandat 10 mm",
        "PVC expandat"
      )
    ).toBe(true);
  });

  it("does not auto-rename — returns suggestions only", () => {
    const input = "Bare premontaj litere 30x30x1.5";
    const suggestion = getCanonicalMaterialSuggestion(input);
    expect(suggestion.normalizedInput).not.toBe(input);
    expect(suggestion.canonicalLabelSuggestion).toBeTruthy();
    expect(findUsageTermWarnings(input).length).toBeGreaterThan(0);
  });
});
