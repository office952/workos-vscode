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
  "doar-panou.svg",
);

describe("Remus doar-panou — Contur suport auto-role", () => {
  it("proposes support_panel for Alucobond Casetat stroke layer, not Vector Logo", () => {
    const text = readFileSync(FIXTURE, "utf8");
    const { report } = analyzeSvgString(text, "doar-panou.svg", text.length);

    expect(report.layers.length).toBeGreaterThanOrEqual(1);
    const support = report.layers.find(
      (layer) =>
        /alucobond|casetat/i.test(layer.name) ||
        /alucobond|casetat/i.test(layer.id) ||
        layer.autoRole === "support_panel",
    );
    expect(support).toBeTruthy();
    expect(support?.autoRole).toBe("support_panel");
    expect(report.layers.every((layer) => layer.autoRole !== "printed_artwork")).toBe(true);
    expect(report.closedContourCandidates?.closed_contour_count ?? 0).toBeGreaterThanOrEqual(1);
  });
});
