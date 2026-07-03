import { describe, expect, it } from "vitest";
import {
  INTAKE_V6_LETTERS_TEMPLATE_CODE,
  INTAKE_V6_LOGO_TEMPLATE_CODE,
  resolveIntakeV6LayerTargetTemplate,
} from "./intakeV6LayerTargetTemplate";

describe("resolveIntakeV6LayerTargetTemplate", () => {
  it("keeps face layers on the active letters template", () => {
    const target = resolveIntakeV6LayerTargetTemplate({
      layer: {
        id: "pseudo:maria",
        name: "pseudo maria (blue)",
        layerKind: "pseudo",
      } as never,
      selectedRole: "face",
      workspaceTemplateCode: INTAKE_V6_LETTERS_TEMPLATE_CODE,
    });

    expect(target.templateCode).toBe(INTAKE_V6_LETTERS_TEMPLATE_CODE);
    expect(target.templateLabel).toBe("Litere volumetrice");
  });

  it("routes printed artwork logo layers to the volumetric logo template", () => {
    const target = resolveIntakeV6LayerTargetTemplate({
      layer: {
        id: "logo-stanga",
        name: "logo stanga",
        layerKind: "pseudo",
      } as never,
      selectedRole: "printed_artwork",
      workspaceTemplateCode: INTAKE_V6_LETTERS_TEMPLATE_CODE,
    });

    expect(target.templateCode).toBe(INTAKE_V6_LOGO_TEMPLATE_CODE);
    expect(target.statusLabel).toContain(INTAKE_V6_LOGO_TEMPLATE_CODE);
  });
});