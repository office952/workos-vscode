import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { confirmAllSuggestedLayerRoles } from "./intakeV6LayerRoleBridge";
import {
  buildSupportPanelConfirmationPath,
  confirmationIncludesConfirmedSupportPanel,
} from "./intakeV6SupportPanelConfirmationPath";

const ACM = path.join(
  process.env.USERPROFILE || process.env.HOME || "",
  "Desktop",
  "fisiere-teste-svg",
  "litere-cu-fundal-acm-segmentat.svg",
);

describe("support panel confirmation path (Confirm All parity)", () => {
  it("proposes segmented_background with distinct panels when support confirmed", () => {
    const text = readFileSync(ACM, "utf8");
    const { report } = analyzeSvgString(text, "litere-cu-fundal-acm-segmentat.svg", text.length);
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    expect(confirmationIncludesConfirmedSupportPanel(confirmed)).toBe(true);

    const pathResult = buildSupportPanelConfirmationPath({
      report,
      confirmation: confirmed,
      finishSetup: null,
      bindables: [
        {
          component_template_code: "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
          owner_label: "Panou Alucobond casetat",
          geometry_role: "SUPPORT_CONTOUR",
          available: true,
        } as never,
      ],
      svgSourceHash: "test-hash",
    });

    expect(pathResult.ok).toBe(true);
    expect(pathResult.segmentedProposal).not.toBeNull();
    expect(pathResult.segmentedProposal?.status).toBe("PROPOSED");
    expect((pathResult.segmentedProposal?.panels ?? []).length).toBeGreaterThanOrEqual(2);
  });
});
