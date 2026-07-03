import { describe, expect, it } from "vitest";
import {
  resolveIntakeWorkspaceShell,
  INTAKE_WORKSPACE_SHELL_LABELS,
} from "./intakeDetailRouting";
import { TPL_VOLUMETRIC_LETTERS } from "./volumetricQuoteInput";

describe("intakeDetailRouting", () => {
  it("routes empty product_family to generic unresolved", () => {
    expect(resolveIntakeWorkspaceShell(null, "")).toBe("generic_unresolved");
    expect(resolveIntakeWorkspaceShell(null, "   ")).toBe("generic_unresolved");
  });

  it("routes volumetric template or family to modular shell", () => {
    expect(
      resolveIntakeWorkspaceShell(TPL_VOLUMETRIC_LETTERS, "litere_volumetrice")
    ).toBe("volumetric_modular");
    expect(resolveIntakeWorkspaceShell(null, "litere_volumetrice")).toBe(
      "volumetric_modular"
    );
  });

  it("routes other families to generic legacy", () => {
    expect(resolveIntakeWorkspaceShell(null, "Casete Luminoase")).toBe(
      "generic_legacy"
    );
  });

  it("labels all shells", () => {
    expect(INTAKE_WORKSPACE_SHELL_LABELS.volumetric_modular).toContain(
      "volumetric"
    );
    expect(INTAKE_WORKSPACE_SHELL_LABELS.generic_unresolved).toContain(
      "unresolved"
    );
    expect(INTAKE_WORKSPACE_SHELL_LABELS.generic_legacy).toContain("legacy");
  });
});
