import type { SvgVectorDetectedLayer } from "@/lib/svgVectorAnalysis";

export const SVG_MM_VIEWBOX = `<svg xmlns="http://www.w3.org/2000/svg" width="400mm" height="50mm" viewBox="0 0 400 50">
  <g id="LITERE" inkscape:label="LITERE" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
    <rect x="10" y="5" width="380" height="40"/>
  </g>
</svg>`;

export const SVG_MULTI_LAYER = `<svg xmlns="http://www.w3.org/2000/svg" width="1000mm" height="200mm" viewBox="0 0 1000 200">
  <g id="LITERE"><rect x="50" y="20" width="400" height="160"/><path d="M500 20 L550 180"/></g>
  <g id="DIBOND"><rect x="0" y="0" width="1000" height="200"/></g>
  <g id="CADRU"><rect x="10" y="10" width="980" height="180"/></g>
</svg>`;

/** Letters + horizontal bar rectangles on a separate structural layer. */
export const SVG_LETTERS_AND_STRUCTURE_LAYERS = `<svg xmlns="http://www.w3.org/2000/svg" width="1200mm" height="400mm" viewBox="0 0 1200 400">
  <g id="LITERE"><path d="M20 20 L120 20 L120 120 L20 120 Z M200 20 L300 20 L300 120 L200 120 Z"/></g>
  <g id="BARE_MONTAJ"><rect x="0" y="350" width="1200" height="30"/><rect x="0" y="20" width="1200" height="30"/></g>
</svg>`;

/** Bar-like rectangles mixed with letter paths in the same layer. */
export const SVG_LETTERS_WITH_INLINE_BARS = `<svg xmlns="http://www.w3.org/2000/svg" width="800mm" height="200mm" viewBox="0 0 800 200">
  <g id="LITERE">
    <path d="M50 50 L150 50 L150 150 L50 150 Z"/>
    <rect x="0" y="0" width="800" height="20"/>
    <rect x="0" y="180" width="800" height="20"/>
  </g>
</svg>`;

export const SVG_RECT_POLYGON = `<svg width="200mm" height="100mm" viewBox="0 0 200 100">
  <g id="LITERE"><polygon points="10,10 190,10 190,90 10,90"/></g>
</svg>`;

export const SVG_PATH_LAYER = `<svg width="300mm" height="80mm" viewBox="0 0 300 80">
  <g id="LITERE"><path d="M10 10 L100 10 L100 70 L10 70 Z"/></g>
</svg>`;

export const SVG_VIEWBOX_ONLY = `<svg viewBox="0 0 500 100">
  <g id="LITERE"><rect width="500" height="100"/></g>
</svg>`;

export const SVG_PX_UNITS = `<svg width="960px" height="480px" viewBox="0 0 960 480">
  <g id="LITERE"><rect x="0" y="0" width="960" height="480"/></g>
</svg>`;

export const SVG_UNSUPPORTED_TRANSFORM = `<svg width="100mm" height="50mm" viewBox="0 0 100 50">
  <g id="LITERE"><rect x="0" y="0" width="50" height="50" transform="rotate(45 25 25)"/></g>
</svg>`;

export const SVG_HIDDEN_ELEMENTS = `<svg width="100mm" height="50mm" viewBox="0 0 100 50">
  <g id="LITERE">
    <rect x="0" y="0" width="100" height="50"/>
    <rect x="0" y="0" width="50" height="50" display="none"/>
    <rect x="0" y="0" width="30" height="30" opacity="0"/>
  </g>
</svg>`;

export function layer(
  id: string,
  label: string,
  role: SvgVectorDetectedLayer["confirmed_role"]
): SvgVectorDetectedLayer {
  return {
    id,
    label,
    element_count: 1,
    suggested_role: role,
    confirmed_role: role,
    is_inkscape_layer: false,
  };
}
