import { describe, expect, it } from "vitest";
import {
  formatPublicationBlocker,
  formatReadinessFindingMessage,
  humanTemplateName,
  relationTypeLabelRo,
} from "./productSystemAdminDisplay";

describe("productSystemAdminDisplay", () => {
  it("prefers human name for known templates", () => {
    expect(humanTemplateName("TPL-VOLUM-ALUMINIU_v1")).toBe("Cant / volum din aluminiu");
    expect(humanTemplateName("TPL-VOLUMETRIC-LETTERS_v2")).toBe("Litere volumetrice");
    expect(humanTemplateName("TPL-ACM-BOXED-MOUNTING-SUPPORT_v1")).toBe("Alucobond casetat");
    expect(humanTemplateName("TPL-ACM-CASSETTED-PANEL")).toBe("Alucobond casetat");
  });

  it("formats known_conflict blockers with human name primary", () => {
    const d = formatPublicationBlocker("known_conflict:TPL-VOLUM-ALUMINIU_v1");
    expect(d.primary).toMatch(/Cant \/ volum din aluminiu/);
    expect(d.secondary).toBe("TPL-VOLUM-ALUMINIU_v1");
  });

  it("humanizes readiness finding messages", () => {
    const d = formatReadinessFindingMessage(
      "Required child template TPL-VOLUM-ALUMINIU_v1 is inactive",
    );
    expect(d.primary).toContain("Cant / volum din aluminiu");
    expect(d.secondary).toBe("TPL-VOLUM-ALUMINIU_v1");
  });

  it("labels relation types in Romanian when known", () => {
    expect(relationTypeLabelRo("required_child")).toBe("Copil obligatoriu");
    expect(relationTypeLabelRo("custom_x")).toBe("custom_x");
  });
});
