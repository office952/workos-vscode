/**
 * Non-mutating preview overlay for closed-contour selection.
 * Appends a temporary <g> to the preview DOM only — never writes back to SVG source.
 */

export type SvgPreviewContourOverlayTarget = {
  contour_id: string;
  mode: "hover" | "selected";
  bbox: { x: number; y: number; width: number; height: number };
  overlay_d?: string | null;
  overlay_points?: string | null;
};

export const CONTOUR_OVERLAY_GROUP_ATTR = "data-intake-v6-contour-overlay";

export function clearSvgPreviewContourOverlay(svgRoot: SVGSVGElement): void {
  svgRoot.removeAttribute("data-intake-v6-contour-highlight");
  const existing = svgRoot.querySelectorAll(`[${CONTOUR_OVERLAY_GROUP_ATTR}]`);
  existing.forEach((node) => node.remove());
}

export function applySvgPreviewContourOverlay(
  svgRoot: SVGSVGElement,
  target: SvgPreviewContourOverlayTarget | null,
): void {
  clearSvgPreviewContourOverlay(svgRoot);
  if (!target) return;

  svgRoot.setAttribute("data-intake-v6-contour-highlight", target.contour_id);
  const ns = "http://www.w3.org/2000/svg";
  const g = document.createElementNS(ns, "g");
  g.setAttribute(CONTOUR_OVERLAY_GROUP_ATTR, target.mode);
  g.setAttribute("pointer-events", "none");

  const stroke = target.mode === "selected" ? "rgba(34, 211, 238, 0.95)" : "rgba(125, 211, 252, 0.75)";
  const width = target.mode === "selected" ? "3.5" : "2.5";

  let shape: SVGElement | null = null;
  if (target.overlay_d) {
    shape = document.createElementNS(ns, "path");
    shape.setAttribute("d", target.overlay_d);
  } else if (target.overlay_points) {
    shape = document.createElementNS(ns, "polygon");
    shape.setAttribute("points", target.overlay_points);
  } else {
    shape = document.createElementNS(ns, "rect");
    shape.setAttribute("x", String(target.bbox.x));
    shape.setAttribute("y", String(target.bbox.y));
    shape.setAttribute("width", String(target.bbox.width));
    shape.setAttribute("height", String(target.bbox.height));
  }

  shape.setAttribute("fill", "none");
  shape.setAttribute("stroke", stroke);
  shape.setAttribute("stroke-width", width);
  shape.setAttribute("vector-effect", "non-scaling-stroke");
  g.appendChild(shape);

  // Soft bbox halo so letters stay visible inside
  const halo = document.createElementNS(ns, "rect");
  halo.setAttribute("x", String(target.bbox.x));
  halo.setAttribute("y", String(target.bbox.y));
  halo.setAttribute("width", String(target.bbox.width));
  halo.setAttribute("height", String(target.bbox.height));
  halo.setAttribute("fill", "rgba(34, 211, 238, 0.06)");
  halo.setAttribute("stroke", "none");
  g.insertBefore(halo, shape);

  svgRoot.appendChild(g);
}
