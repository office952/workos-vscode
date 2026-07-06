import { describe, expect, it } from "vitest";
import {
  buildIntakeLegacyPath,
  buildIntakeV6Path,
  findIntakeByRouteParam,
  hasIntakeStatusReadinessConflict,
  isIntakeV6CapableTemplateCode,
  intakeEditUsesVolumetricWorkspace,
  intakePrimaryEditLabel,
  resolveIntakeEditPath,
  shouldUseVolumetricIntakePage,
  TPL_VOLUMETRIC_LOGO_V1,
} from "@/lib/volumetricIntakeRoute";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

describe("volumetricIntakeRoute", () => {
  it("routes confirmed TPL-VOLUMETRIC-LETTERS to volumetric page", () => {
    expect(
      shouldUseVolumetricIntakePage(TPL_VOLUMETRIC_LETTERS, "totem")
    ).toBe(true);
  });

  it("keeps confirmed TPL-VOLUMETRIC-LOGO_v1 on non-direct root routing", () => {
    expect(isIntakeV6CapableTemplateCode(TPL_VOLUMETRIC_LOGO_V1)).toBe(false);
    expect(
      shouldUseVolumetricIntakePage(TPL_VOLUMETRIC_LOGO_V1, "totem")
    ).toBe(false);
    expect(
      resolveIntakeEditPath({
        id: "IR-LOGO",
        confirmedTemplateCode: TPL_VOLUMETRIC_LOGO_V1,
        productFamily: "litere_volumetrice",
        workspaceId: "workspace-logo",
      })
    ).toBe("/intake/IR-LOGO");
  });

  it("routes litere_volumetrice family before template confirmation", () => {
    expect(shouldUseVolumetricIntakePage(null, "litere_volumetrice")).toBe(
      true
    );
  });

  it("does not route unrelated families", () => {
    expect(
      shouldUseVolumetricIntakePage(null, "Totemuri / Pyloni")
    ).toBe(false);
  });

  it("detects status ahead of computed readiness", () => {
    expect(
      hasIntakeStatusReadinessConflict(
        "ready_for_quote",
        ["Template neconfirmat"],
        false,
        true
      )
    ).toBe(true);
  });

  it("does not flag conflict when ready and prerequisites met", () => {
    expect(
      hasIntakeStatusReadinessConflict("ready_for_quote", [], true, true)
    ).toBe(false);
  });

  it("findIntakeByRouteParam matches intake code or numeric db id", () => {
    const rows = [
      { id: "WI-E2E-COMMERCIAL-WARN-001", dbId: 24 },
      { id: "WI-OTHER", dbId: 25 },
    ];
    expect(findIntakeByRouteParam(rows, "WI-E2E-COMMERCIAL-WARN-001")?.dbId).toBe(24);
    expect(findIntakeByRouteParam(rows, "24")?.id).toBe(
      "WI-E2E-COMMERCIAL-WARN-001"
    );
    expect(findIntakeByRouteParam(rows, "missing")).toBeUndefined();
  });

  it("routes volumetric edit to Intake V6 by intake code", () => {
    expect(
      resolveIntakeEditPath({
        id: "IR-MQ47AGDG",
        confirmedTemplateCode: TPL_VOLUMETRIC_LETTERS,
        productFamily: "litere_volumetrice",
      })
    ).toBe("/intake-v6/IR-MQ47AGDG/operator");
    expect(buildIntakeV6Path("IR-MQ47AGDG")).toBe("/intake-v6/IR-MQ47AGDG/operator");
  });

  it("routes non-volumetric edit to legacy intake path", () => {
    expect(
      resolveIntakeEditPath({
        id: "WI-3321",
        confirmedTemplateCode: null,
        productFamily: "Casete Luminoase",
      })
    ).toBe("/intake/WI-3321");
    expect(buildIntakeLegacyPath("WI-3321")).toBe("/intake/WI-3321");
  });

  it("routes litere_volumetrice family before template confirmation to V6", () => {
    expect(
      intakeEditUsesVolumetricWorkspace(null, "litere_volumetrice")
    ).toBe(true);
    expect(
      resolveIntakeEditPath({
        id: "IR-NEW",
        productFamily: "litere_volumetrice",
      })
    ).toBe("/intake-v6/IR-NEW/operator");
  });

  it("routes analyzer-first requests by ensured workspace id before template truth exists", () => {
    expect(
      resolveIntakeEditPath({
        id: "IR-ANALYZER",
        confirmedTemplateCode: null,
        productFamily: "",
        workspaceId: "workspace-analyzer-first",
      })
    ).toBe("/intake-v6/workspace-analyzer-first/operator");
  });

  it("uses Intake V6 primary label only for volumetric intakes", () => {
    expect(
      intakePrimaryEditLabel(TPL_VOLUMETRIC_LETTERS, "litere_volumetrice")
    ).toBe("Deschide Intake V6");
    expect(
      intakePrimaryEditLabel(TPL_VOLUMETRIC_LOGO_V1, "litere_volumetrice")
    ).toBe("Instrumentează Comanda");
    expect(intakePrimaryEditLabel(null, "Totemuri / Pyloni")).toBe(
      "Instrumentează Comanda"
    );
  });
});
