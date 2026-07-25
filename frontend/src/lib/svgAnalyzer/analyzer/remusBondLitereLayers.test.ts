import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { analyzeSvgString } from "@/lib/svgAnalyzer";

const FIXTURE = path.join(
  process.cwd(),
  "..",
  "docs",
  "worklog",
  "realignment",
  "audit_assets",
  "remus_acm_letters_svg_v1",
  "test-bond-litere.svg",
);

describe("Remus test-bond-litere — both Corel layers visible", () => {
  it("keeps Alucobond stroke as support_panel and Litere as face", () => {
    const text = readFileSync(FIXTURE, "utf8");
    const { report } = analyzeSvgString(text, "test-bond-litere.svg", text.length);

    expect(report.layers.length).toBeGreaterThanOrEqual(2);
    const support = report.layers.find(
      (layer) =>
        /alucobond|casetat/i.test(layer.name) ||
        /alucobond|casetat/i.test(layer.id) ||
        layer.autoRole === "support_panel",
    );
    const letters = report.layers.find(
      (layer) =>
        /litere|volumetr/i.test(layer.name) ||
        /litere|volumetr/i.test(layer.id) ||
        layer.autoRole === "face",
    );
    expect(support).toBeTruthy();
    expect(support?.autoRole).toBe("support_panel");
    expect(letters).toBeTruthy();
    expect(letters?.autoRole).toBe("face");
  });
});
