import { describe, expect, it } from "vitest";
import {
  applySvgPreviewLayerHighlight,
  clearSvgPreviewLayerHighlight,
  SVG_PREVIEW_LAYER_ACTIVE_CLASS,
  SVG_PREVIEW_LAYER_BBOX_CLASS,
  SVG_PREVIEW_LAYER_DIM_CLASS,
} from "./intakeV6SvgPreviewLayerHighlight";

const SAMPLE_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20">
  <g id="Layer_x0020_1">
    <path id="maria" fill="#00A0E3" d="M20 2 L28 2 L28 18 L20 18 Z"/>
    <path id="soare" fill="#E31E24" d="M35 2 L43 2 L43 18 L35 18 Z"/>
    <path fill="none" stroke="#2B2A29" d="M2 4 L12 4 L12 16 L2 16 Z"/>
  </g>
</svg>
`;

function renderSvg(source: string): SVGSVGElement {
  const host = document.createElement("div");
  host.innerHTML = source.trim();
  const svg = host.querySelector("svg");
  if (!svg) throw new Error("missing svg");
  document.body.appendChild(host);
  return svg;
}

describe("intakeV6SvgPreviewLayerHighlight", () => {
  it("highlights paths by fill color for pseudo layers", () => {
    const svg = renderSvg(SAMPLE_SVG);
    applySvgPreviewLayerHighlight(svg, {
      id: "pseudo:maria",
      name: "pseudo maria (blue)",
      layerKind: "pseudo",
      colors: ["#00A0E3"],
    });

    const maria = svg.querySelector("#maria");
    const soare = svg.querySelector("#soare");
    expect(maria).toHaveClass(SVG_PREVIEW_LAYER_ACTIVE_CLASS);
    expect(soare).toHaveClass(SVG_PREVIEW_LAYER_DIM_CLASS);
    expect(svg).toHaveAttribute("data-intake-v6-layer-highlight", "pseudo:maria");

    clearSvgPreviewLayerHighlight(svg);
    expect(maria).not.toHaveClass(SVG_PREVIEW_LAYER_ACTIVE_CLASS);
    expect(soare).not.toHaveClass(SVG_PREVIEW_LAYER_DIM_CLASS);
    svg.parentElement?.remove();
  });

  it("highlights drawable elements inside a real layer group", () => {
    const svg = renderSvg(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20">
        <g id="maria">
          <path fill="#00A0E3" d="M20 2 L28 18 Z"/>
        </g>
        <g id="soare">
          <path fill="#E31E24" d="M35 2 L43 18 Z"/>
        </g>
      </svg>
    `);

    applySvgPreviewLayerHighlight(svg, {
      id: "maria",
      name: "maria",
      layerKind: "real",
      colors: ["#00A0E3"],
    });

    const paths = svg.querySelectorAll("path");
    expect(paths[0]).toHaveClass(SVG_PREVIEW_LAYER_ACTIVE_CLASS);
    expect(paths[1]).toHaveClass(SVG_PREVIEW_LAYER_DIM_CLASS);
    svg.parentElement?.remove();
  });

  it("boosts stroke-only logo outlines with bbox overlay", () => {
    const svg = renderSvg(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20">
        <g id="logo-stanga">
          <path fill="none" stroke="#2B2A29" stroke-width="0.02" d="M2 4 L12 4 L12 16 L2 16 Z"/>
        </g>
        <path fill="#00A0E3" d="M40 2 L48 18 Z"/>
      </svg>
    `);

    applySvgPreviewLayerHighlight(svg, {
      id: "logo-stanga",
      name: "logo stanga",
      layerKind: "raster_artwork",
      colors: ["#2B2A29"],
    });

    const logoPath = svg.querySelector("#logo-stanga path");
    expect(logoPath).toHaveClass(SVG_PREVIEW_LAYER_ACTIVE_CLASS);
    expect(logoPath?.getAttribute("stroke")).toBe("#0891b2");
    expect(Number.parseFloat(logoPath?.getAttribute("stroke-width") ?? "0")).toBeGreaterThan(0.02);
    expect(svg.querySelector(`.${SVG_PREVIEW_LAYER_BBOX_CLASS}`)).toBeTruthy();

    clearSvgPreviewLayerHighlight(svg);
    expect(logoPath?.getAttribute("stroke")).toBe("#2B2A29");
    expect(svg.querySelector(`.${SVG_PREVIEW_LAYER_BBOX_CLASS}`)).toBeNull();
    svg.parentElement?.remove();
  });

  it("disambiguates twin logo stroke outlines by left/right side", () => {
    const svg = renderSvg(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 20">
        <path id="logo-left" fill="none" stroke="#2B2A29" stroke-width="0.02" d="M2 4 L12 4 L12 16 L2 16 Z"/>
        <path id="logo-right" fill="none" stroke="#2B2A29" stroke-width="0.02" d="M88 4 L98 4 L98 16 L88 16 Z"/>
        <path fill="#00A0E3" d="M40 2 L48 18 Z"/>
      </svg>
    `);

    applySvgPreviewLayerHighlight(svg, {
      id: "logo-stanga",
      name: "logo stanga",
      layerKind: "raster_artwork",
      colors: ["#2B2A29"],
    });

    expect(svg.querySelector("#logo-left")).toHaveClass(SVG_PREVIEW_LAYER_ACTIVE_CLASS);
    expect(svg.querySelector("#logo-right")).toHaveClass(SVG_PREVIEW_LAYER_DIM_CLASS);

    clearSvgPreviewLayerHighlight(svg);

    applySvgPreviewLayerHighlight(svg, {
      id: "logo-dreapta",
      name: "logo dreapta",
      layerKind: "raster_artwork",
      colors: ["#2B2A29"],
    });

    expect(svg.querySelector("#logo-left")).toHaveClass(SVG_PREVIEW_LAYER_DIM_CLASS);
    expect(svg.querySelector("#logo-right")).toHaveClass(SVG_PREVIEW_LAYER_ACTIVE_CLASS);
    svg.parentElement?.remove();
  });
});
