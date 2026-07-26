import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { parseSvg } from "./parseSvg";
import { shouldPreserveExistingLayerStructure } from "./pseudoLayerExpansionGuard";

const fixtureDir = join(dirname(fileURLToPath(import.meta.url)), "../fixtures");

describe("pseudoLayerExpansionGuard", () => {
  it("preserves PBL multi-layer Corel export", () => {
    const source = readFileSync(join(fixtureDir, "pbl-layere.svg"), "utf8");
    const doc = parseSvg(source, "pbl-layere.svg", source.length);
    expect(shouldPreserveExistingLayerStructure(doc)).toBe(true);
  });

  it("does not preserve ana-maria unlayered single generic bucket", () => {
    const source = readFileSync(join(fixtureDir, "ana-maria-gradinita-fara-layere.svg"), "utf8");
    const doc = parseSvg(source, "ana-maria-gradinita-fara-layere.svg", source.length);
    expect(shouldPreserveExistingLayerStructure(doc)).toBe(false);
  });

  it("preserves Remus named Alucobond + Litere Corel layers", () => {
    const remus = join(
      process.cwd(),
      "..",
      "docs",
      "worklog",
      "realignment",
      "audit_assets",
      "remus_acm_letters_svg_v1",
      "test-bond-litere.svg",
    );
    const source = readFileSync(remus, "utf8");
    const doc = parseSvg(source, "test-bond-litere.svg", source.length);
    expect(shouldPreserveExistingLayerStructure(doc)).toBe(true);
  });
});
