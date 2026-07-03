import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";

export type SvgPreviewLayerHighlightTarget = {
  id: string;
  name: string;
  layerKind?: string | null;
  colors?: string[];
};

export function resolveSvgPreviewLayerHighlightTarget(
  report: SvgAnalysisCoreReport,
  confirmation: LayerRoleConfirmation,
  hoveredLayerKey: string | null,
): SvgPreviewLayerHighlightTarget | null {
  if (!hoveredLayerKey) return null;
  for (const layer of report.layers) {
    const entry =
      confirmation.layers.find(
        (item) => item.layerKey === layer.id || item.layerKey === layer.name,
      ) ?? confirmation.layers.find((item) => item.layerName === layer.name);
    const layerKey = entry?.layerKey ?? layer.id ?? layer.name;
    if (layerKey !== hoveredLayerKey) continue;
    return {
      id: layer.id,
      name: layer.name,
      layerKind: layer.layerKind,
      colors: layer.colors,
    };
  }
  return null;
}

export const SVG_PREVIEW_LAYER_DIM_CLASS = "intake-v6-svg-layer-dim";
export const SVG_PREVIEW_LAYER_ACTIVE_CLASS = "intake-v6-svg-layer-active";
export const SVG_PREVIEW_LAYER_BBOX_CLASS = "intake-v6-svg-layer-bbox-highlight";

const DRAWABLE_SELECTOR =
  "path,rect,circle,ellipse,line,polyline,polygon,text,image";

const HL_STROKE = "data-intake-v6-hl-stroke";
const HL_STROKE_WIDTH = "data-intake-v6-hl-stroke-width";
const HL_FILL = "data-intake-v6-hl-fill";

function normalizePaint(value: string | null | undefined): string | null {
  if (!value) return null;
  const token = value.trim().toLowerCase();
  if (!token || token === "none" || token === "transparent") return null;
  if (token.startsWith("#") && token.length > 7) return token.slice(0, 7);
  return token;
}

function collectNormalizedColors(target: SvgPreviewLayerHighlightTarget): Set<string> {
  const colors = new Set<string>();
  for (const raw of target.colors ?? []) {
    const normalized = normalizePaint(raw);
    if (normalized) colors.add(normalized);
  }
  return colors;
}

function isDrawableElement(element: Element): boolean {
  const tag = element.tagName.toLowerCase();
  return tag !== "g" && tag !== "svg" && tag !== "defs";
}

function isLogoLikeTarget(target: SvgPreviewLayerHighlightTarget): boolean {
  const name = target.name.toLowerCase();
  return (
    target.layerKind === "raster_artwork" ||
    name.includes("logo") ||
    name.includes("emblem") ||
    name.includes("artwork")
  );
}

type LogoSide = "left" | "right";

function resolveLogoSide(target: SvgPreviewLayerHighlightTarget): LogoSide | null {
  const token = `${target.id} ${target.name}`
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  if (token.includes("stanga") || token.includes("left")) return "left";
  if (token.includes("dreapta") || token.includes("right")) return "right";
  return null;
}

function resolveSvgCenterX(svgRoot: SVGSVGElement): number {
  const viewBox = svgRoot.viewBox.baseVal;
  if (viewBox.width > 0) return viewBox.x + viewBox.width / 2;
  try {
    const box = svgRoot.getBBox();
    return box.x + box.width / 2;
  } catch {
    return 0;
  }
}

function elementCenterX(element: SVGGraphicsElement): number | null {
  try {
    const box = element.getBBox();
    if (Number.isFinite(box.width) && Number.isFinite(box.height) && (box.width > 0 || box.height > 0)) {
      return box.x + box.width / 2;
    }
  } catch {
    // getBBox fails when element is not rendered
  }
  return pathAnchorXFromD(element);
}

function pathAnchorXFromD(element: Element): number | null {
  const d = element.getAttribute("d");
  if (!d) return null;
  const match = /^[\s]*[Mm]\s*(-?\d*\.?\d+(?:e[-+]?\d+)?)/i.exec(d.trim());
  if (!match?.[1]) return null;
  const anchorX = Number.parseFloat(match[1]);
  return Number.isFinite(anchorX) ? anchorX : null;
}

function isStrokeOutlinePath(element: Element): boolean {
  const fill = normalizePaint(element.getAttribute("fill"));
  const stroke = normalizePaint(element.getAttribute("stroke"));
  return !fill && Boolean(stroke);
}

function isOnLogoSide(centerX: number, svgCenterX: number, side: LogoSide): boolean {
  return side === "left" ? centerX < svgCenterX : centerX >= svgCenterX;
}

function filterMatchedByLogoSide(
  svgRoot: SVGSVGElement,
  matched: Set<Element>,
  side: LogoSide,
): Set<Element> {
  const svgCenterX = resolveSvgCenterX(svgRoot);
  const filtered = new Set<Element>();
  for (const element of matched) {
    if (!(element instanceof SVGGraphicsElement)) continue;
    const centerX = elementCenterX(element);
    if (centerX == null) continue;
    if (isOnLogoSide(centerX, svgCenterX, side)) filtered.add(element);
  }
  return filtered;
}

function collectLogoSideStrokeDrawables(
  svgRoot: SVGSVGElement,
  side: LogoSide,
  colors: Set<string>,
): Set<Element> {
  const svgCenterX = resolveSvgCenterX(svgRoot);
  const matched = new Set<Element>();
  for (const element of svgRoot.querySelectorAll(DRAWABLE_SELECTOR)) {
    if (!isStrokeOutlinePath(element)) continue;
    if (colors.size > 0) {
      const stroke = normalizePaint(element.getAttribute("stroke"));
      if (!stroke || !colors.has(stroke)) continue;
    }
    if (!(element instanceof SVGGraphicsElement)) continue;
    const centerX = elementCenterX(element);
    if (centerX == null) continue;
    if (isOnLogoSide(centerX, svgCenterX, side)) matched.add(element);
  }
  return matched;
}

function resolveGroupCandidates(target: SvgPreviewLayerHighlightTarget): string[] {
  const candidates = new Set<string>();
  if (target.id) candidates.add(target.id);
  if (target.name) candidates.add(target.name);
  if (target.name.includes(" ")) candidates.add(target.name.replace(/\s+/g, "-"));
  if (target.name.includes(" ")) candidates.add(target.name.replace(/\s+/g, "_"));
  return Array.from(candidates);
}

function findGroupElement(svgRoot: SVGSVGElement, groupId: string): Element | null {
  if (!groupId) return null;
  try {
    const byId = svgRoot.querySelector(`#${CSS.escape(groupId)}`);
    if (byId) return byId;
  } catch {
    // ignore invalid selector
  }
  return svgRoot.querySelector(`[id="${groupId.replace(/"/g, '\\"')}"]`);
}

function collectMatchedDrawables(
  svgRoot: SVGSVGElement,
  target: SvgPreviewLayerHighlightTarget,
): Set<Element> {
  const matched = new Set<Element>();
  const allDrawables = Array.from(svgRoot.querySelectorAll(DRAWABLE_SELECTOR));
  const logoSide = resolveLogoSide(target);
  const colors = collectNormalizedColors(target);

  for (const groupId of resolveGroupCandidates(target)) {
    const group = findGroupElement(svgRoot, groupId);
    if (!group) continue;
    if (isDrawableElement(group)) matched.add(group);
    group.querySelectorAll(DRAWABLE_SELECTOR).forEach((element) => matched.add(element));
  }

  if (matched.size > 0) return matched;

  if (logoSide) {
    const sideMatched = collectLogoSideStrokeDrawables(svgRoot, logoSide, colors);
    if (sideMatched.size > 0) return sideMatched;
  }

  if (colors.size === 0) return matched;

  for (const element of allDrawables) {
    const fill = normalizePaint(element.getAttribute("fill"));
    const stroke = normalizePaint(element.getAttribute("stroke"));
    if ((fill && colors.has(fill)) || (stroke && colors.has(stroke))) {
      matched.add(element);
    }
  }

  if (logoSide && matched.size > 1) {
    const filtered = filterMatchedByLogoSide(svgRoot, matched, logoSide);
    if (filtered.size > 0) return filtered;
  }

  return matched;
}

function parseStrokeWidth(value: string | null | undefined): number {
  const parsed = Number.parseFloat(value ?? "");
  return Number.isFinite(parsed) ? parsed : 0;
}

function backupPaintAttributes(element: SVGElement): void {
  if (element.hasAttribute(HL_STROKE)) return;
  element.setAttribute(HL_STROKE, element.getAttribute("stroke") ?? "");
  element.setAttribute(HL_STROKE_WIDTH, element.getAttribute("stroke-width") ?? "");
  element.setAttribute(HL_FILL, element.getAttribute("fill") ?? "");
}

function restorePaintAttributes(element: Element): void {
  if (!(element instanceof SVGElement) || !element.hasAttribute(HL_STROKE)) return;
  const stroke = element.getAttribute(HL_STROKE);
  const strokeWidth = element.getAttribute(HL_STROKE_WIDTH);
  const fill = element.getAttribute(HL_FILL);
  if (stroke) element.setAttribute("stroke", stroke);
  else element.removeAttribute("stroke");
  if (strokeWidth) element.setAttribute("stroke-width", strokeWidth);
  else element.removeAttribute("stroke-width");
  if (fill) element.setAttribute("fill", fill);
  else element.removeAttribute("fill");
  element.removeAttribute(HL_STROKE);
  element.removeAttribute(HL_STROKE_WIDTH);
  element.removeAttribute(HL_FILL);
}

function enhanceActiveElement(element: Element, logoLike: boolean): void {
  if (!(element instanceof SVGElement)) return;
  const tag = element.tagName.toLowerCase();
  if (tag === "image") return;

  backupPaintAttributes(element);
  const fill = normalizePaint(element.getAttribute("fill"));
  const stroke = normalizePaint(element.getAttribute("stroke"));
  const strokeWidth = parseStrokeWidth(element.getAttribute("stroke-width"));

  if (!fill) {
    element.setAttribute("fill", logoLike ? "rgba(6, 182, 212, 0.28)" : "rgba(6, 182, 212, 0.18)");
  }

  if (stroke || (!fill && tag === "path")) {
    element.setAttribute("stroke", "#0891b2");
    const boosted = Math.max(strokeWidth * (logoLike ? 8 : 5), logoLike ? 0.12 : 0.06);
    element.setAttribute("stroke-width", String(boosted));
  }
}

function mergeBBox(
  bounds: { minX: number; minY: number; maxX: number; maxY: number },
  element: SVGGraphicsElement,
): void {
  try {
    const box = element.getBBox();
    if (!Number.isFinite(box.width) || !Number.isFinite(box.height)) return;
    bounds.minX = Math.min(bounds.minX, box.x);
    bounds.minY = Math.min(bounds.minY, box.y);
    bounds.maxX = Math.max(bounds.maxX, box.x + box.width);
    bounds.maxY = Math.max(bounds.maxY, box.y + box.height);
  } catch {
    // getBBox fails when element is not rendered
  }
}

function addBoundingBoxOverlay(
  svgRoot: SVGSVGElement,
  matched: Set<Element>,
  logoLike: boolean,
): void {
  const bounds = {
    minX: Number.POSITIVE_INFINITY,
    minY: Number.POSITIVE_INFINITY,
    maxX: Number.NEGATIVE_INFINITY,
    maxY: Number.NEGATIVE_INFINITY,
  };

  for (const element of matched) {
    if (element instanceof SVGGraphicsElement) {
      mergeBBox(bounds, element);
    }
  }

  if (!Number.isFinite(bounds.minX) || !Number.isFinite(bounds.maxY)) return;

  const width = bounds.maxX - bounds.minX;
  const height = bounds.maxY - bounds.minY;
  const pad = Math.max(Math.max(width, height) * (logoLike ? 0.06 : 0.03), logoLike ? 0.8 : 0.35);

  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("x", String(bounds.minX - pad));
  rect.setAttribute("y", String(bounds.minY - pad));
  rect.setAttribute("width", String(width + pad * 2));
  rect.setAttribute("height", String(height + pad * 2));
  rect.setAttribute("fill", logoLike ? "rgba(6, 182, 212, 0.16)" : "rgba(6, 182, 212, 0.08)");
  rect.setAttribute("stroke", "#06b6d4");
  rect.setAttribute("stroke-width", logoLike ? "0.18" : "0.1");
  rect.setAttribute("rx", "0.5");
  rect.setAttribute("pointer-events", "none");
  rect.classList.add(SVG_PREVIEW_LAYER_BBOX_CLASS);
  svgRoot.appendChild(rect);
}

export function clearSvgPreviewLayerHighlight(svgRoot: SVGSVGElement): void {
  svgRoot.querySelectorAll(`.${SVG_PREVIEW_LAYER_DIM_CLASS}`).forEach((element) => {
    element.classList.remove(SVG_PREVIEW_LAYER_DIM_CLASS);
  });
  svgRoot.querySelectorAll(`.${SVG_PREVIEW_LAYER_ACTIVE_CLASS}`).forEach((element) => {
    element.classList.remove(SVG_PREVIEW_LAYER_ACTIVE_CLASS);
    restorePaintAttributes(element);
  });
  svgRoot.querySelectorAll(`.${SVG_PREVIEW_LAYER_BBOX_CLASS}`).forEach((element) => {
    element.remove();
  });
  svgRoot.removeAttribute("data-intake-v6-layer-highlight");
}

export function applySvgPreviewLayerHighlight(
  svgRoot: SVGSVGElement,
  target: SvgPreviewLayerHighlightTarget | null,
): void {
  clearSvgPreviewLayerHighlight(svgRoot);
  if (!target) return;

  const matched = collectMatchedDrawables(svgRoot, target);
  if (matched.size === 0) return;

  const logoLike = isLogoLikeTarget(target);
  const drawables = svgRoot.querySelectorAll(DRAWABLE_SELECTOR);
  drawables.forEach((element) => {
    if (matched.has(element)) {
      element.classList.add(SVG_PREVIEW_LAYER_ACTIVE_CLASS);
      enhanceActiveElement(element, logoLike);
    } else {
      element.classList.add(SVG_PREVIEW_LAYER_DIM_CLASS);
    }
  });

  addBoundingBoxOverlay(svgRoot, matched, logoLike);
  svgRoot.setAttribute("data-intake-v6-layer-highlight", target.id || target.name);
}
