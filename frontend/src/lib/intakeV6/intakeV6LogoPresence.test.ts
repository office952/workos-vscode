import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";
import { confirmAllSuggestedLayerRoles } from "./intakeV6LayerRoleBridge";
import { deriveArtworkFinishesFromAnalyzer } from "./intakeV4ArtworkFinish";
import { resolveLogoPresence } from "./intakeV6LogoPresence";

const DESKTOP = path.join(
  process.env.USERPROFILE || process.env.HOME || "",
  "Desktop",
  "fisiere-teste-svg",
);

describe("logo_presence + artwork finish gate", () => {
  it("ACM fixture: optional_absent and zero artwork finish rows after confirm", () => {
    const file = path.join(DESKTOP, "litere-cu-fundal-acm-segmentat.svg");
    const text = readFileSync(file, "utf8");
    const { report } = analyzeSvgString(text, "litere-cu-fundal-acm-segmentat.svg", text.length);
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    expect(resolveLogoPresence(report, confirmed)).toBe("optional_absent");
    expect(deriveArtworkFinishesFromAnalyzer(report, confirmed)).toHaveLength(0);
    expect(report.layers.some((l) => l.id === "pseudo:fill-c5c6c6")).toBe(true);
    const support = report.layers.find((l) => l.id === "pseudo:fill-c5c6c6");
    expect(support?.sourceGroupIds).toContain("gravare-cnc-135gr");
    expect((support?.elementIds ?? []).length).toBe(2);
    expect(support?.paintEvidence.paintKind).toBe("solid");
  });

  it("gradi fixture: logos stay artwork, not support_panel", () => {
    const file = path.join(DESKTOP, "gradi-curat.svg");
    const text = readFileSync(file, "utf8");
    const { report } = analyzeSvgString(text, "gradi-curat.svg", text.length);
    const logos = report.layers.filter((l) => l.id.startsWith("logo_instance_"));
    expect(logos).toHaveLength(2);
    expect(logos.every((l) => l.autoRole === "printed_artwork")).toBe(true);
    expect(logos.every((l) => l.autoRole !== "support_panel")).toBe(true);
    const confirmed = confirmAllSuggestedLayerRoles(report.layerRoleConfirmation, report);
    expect(resolveLogoPresence(report, confirmed)).toBe("detected_confirmed");
    const rows = deriveArtworkFinishesFromAnalyzer(report, confirmed);
    expect(rows.length).toBeGreaterThanOrEqual(2);
    expect(report.layers.some((l) => l.autoRole === "support_panel")).toBe(false);
  });
});
