import { describe, expect, it } from "vitest";
import {
  analyzeSvgVectorFile,
  parseSvgVectorText,
} from "@/lib/svgVectorAnalysis";

const MULTI_LAYER_SVG = `<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg"
  xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
  width="100mm" height="50mm" viewBox="0 0 100 50">
  <g inkscape:groupmode="layer" inkscape:label="LITERE" id="layer-litere">
    <path d="M0 0 L10 0"/>
  </g>
  <g inkscape:groupmode="layer" inkscape:label="DIBOND" id="layer-dibond">
    <rect width="10" height="5"/>
  </g>
  <g id="CADRU">
    <title>Cadru metalic</title>
    <line x1="0" y1="0" x2="1" y2="1"/>
  </g>
</svg>`;

const GROUPS_ONLY_SVG = `<svg viewBox="0 0 10 10">
  <g id="group_a"><path d="M0 0"/></g>
  <g id="group_b"><circle cx="1" cy="1" r="1"/></g>
</svg>`;

describe("svgVectorAnalysis", () => {
  it("extracts viewBox and inkscape layer labels", () => {
    const result = parseSvgVectorText("test.svg", MULTI_LAYER_SVG);
    expect(result.parse_ok).toBe(true);
    expect(result.view_box).toBe("0 0 100 50");
    expect(result.width).toBe("100mm");
    expect(result.layers.length).toBeGreaterThanOrEqual(3);
    const litere = result.layers.find((l) => l.label === "LITERE");
    expect(litere?.suggested_role).toBe("volumetric_letters");
    const dibond = result.layers.find((l) => l.label === "DIBOND");
    expect(dibond?.suggested_role).toBe("support_panel");
  });

  it("handles groups without inkscape labels", () => {
    const result = parseSvgVectorText("plain.svg", GROUPS_ONLY_SVG);
    expect(result.parse_ok).toBe(true);
    expect(result.layers.length).toBe(2);
    expect(result.layers[0].suggested_role).toBe("unknown");
  });

  it("rejects invalid SVG with clear error", () => {
    const result = parseSvgVectorText("bad.svg", "<not-svg>broken</not-svg>");
    expect(result.parse_ok).toBe(false);
    expect(result.parse_error).toBeTruthy();
  });

  it("rejects SVG with script tags", () => {
    const result = parseSvgVectorText(
      "evil.svg",
      '<svg><script>alert(1)</script><path/></svg>'
    );
    expect(result.parse_ok).toBe(false);
  });

  it("analyzeSvgVectorFile reads file via FileReader", async () => {
    const file = new File([MULTI_LAYER_SVG], "layers.svg", { type: "image/svg+xml" });
    const result = await analyzeSvgVectorFile(file);
    expect(result.parse_ok).toBe(true);
    expect(result.file_name).toBe("layers.svg");
    expect(result.layers.length).toBeGreaterThan(0);
  });

  it("does not store raw SVG in analysis result", async () => {
    const file = new File([MULTI_LAYER_SVG], "layers.svg", { type: "image/svg+xml" });
    const result = await analyzeSvgVectorFile(file);
    expect(JSON.stringify(result)).not.toContain("<path d=");
  });
});
