/**
 * MVP SVG geometry parser — suggestions only, never quote-critical auto-fill.
 * Parses text via DOMParser; does not store raw SVG or inject into live DOM.
 */

import {
  geometryRoleBucket,
  STRUCTURE_IN_LETTERS_LAYER_WARNING,
} from "@/lib/svgGeometryLayerRoles";
import type { VectorLayerRole } from "@/lib/svgLayerRoleSuggestion";
import type { SvgVectorDetectedLayer } from "@/lib/svgVectorAnalysis";
import {
  areaScale,
  averageScale,
  estimateLetterCountFromSubpaths,
  mm2ToM2,
  mmToM,
  parsePathMetrics,
  userUnitsToMm,
} from "@/lib/svgPathMetrics";

export const SVG_GEOMETRY_PARSER_VERSION = "mvp-2-path-metrics";

const SCRIPT_TAG_RE = /<script\b[^>]*>[\s\S]*?<\/script>/gi;
const INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape";
const PX_PER_MM = 96 / 25.4;

export type GeometryConfidence = "high" | "medium" | "low";

export interface SvgGeometryBBox {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export interface SvgGeometryUnits {
  widthUnit: string;
  heightUnit: string;
  scaleSource: "physical" | "viewbox_only" | "mixed";
  pxToMm: number;
  confidence: GeometryConfidence;
}

export interface SvgGeometryLayerResult {
  layerId: string;
  label: string;
  confirmedRole: VectorLayerRole;
  elementCount: number;
  bbox: SvgGeometryBBox | null;
  bboxMm: SvgGeometryBBox | null;
  warnings: string[];
  confidence: GeometryConfidence;
}

export interface SvgGeometrySuggestions {
  assemblyWidthMm?: number;
  assemblyHeightMm?: number;
  letterLayerWidthMm?: number;
  letterLayerHeightMm?: number;
  supportWidthMm?: number;
  supportHeightMm?: number;
  supportAreaM2?: number;
  frameWidthMm?: number;
  frameHeightMm?: number;
  letterElementCount?: number;
  /** Total cut path length for letter layer(s), metres. */
  letterPerimeterM?: number;
  /** Sum of closed subpath areas for letter layer(s), m². */
  letterFaceAreaM2?: number;
  /** Estimated letter count from path subpaths. */
  letterCount?: number;
}

export interface SvgGeometryParseResult {
  parseOk: boolean;
  parseError?: string;
  units: SvgGeometryUnits | null;
  layers: SvgGeometryLayerResult[];
  suggestions: SvgGeometrySuggestions;
  warnings: string[];
  unsupported: string[];
  confidence: GeometryConfidence;
}

export const PERIMETER_AREA_UNSUPPORTED_MSG =
  "Perimetrul și aria nu au putut fi extrase din contururile SVG.";

function emptyResult(error?: string): SvgGeometryParseResult {
  return {
    parseOk: false,
    parseError: error,
    units: null,
    layers: [],
    suggestions: {},
    warnings: error ? [error] : [],
    unsupported: [PERIMETER_AREA_UNSUPPORTED_MSG],
    confidence: "low",
  };
}

function sanitizeSvgText(raw: string): { text: string; ok: boolean; error?: string } {
  let text = raw.trim();
  if (!text) return { text: "", ok: false, error: "Fișierul SVG este gol." };
  if (SCRIPT_TAG_RE.test(text) || text.toLowerCase().includes("<script")) {
    return { text: "", ok: false, error: "SVG conține script — respins." };
  }
  if (/<!entity/i.test(text)) {
    return { text: "", ok: false, error: "SVG conține entități externe — respins." };
  }
  if (/<!doctype/i.test(text)) {
    text = text.replace(/<!doctype[^>]*>/i, "").trim();
  }
  return { text, ok: true };
}

function parseLengthToken(raw: string | null | undefined): { value: number; unit: string } | null {
  if (!raw?.trim()) return null;
  const m = raw.trim().match(/^([+-]?\d*\.?\d+(?:e[+-]?\d+)?)\s*(mm|cm|in|px|pt|%)?$/i);
  if (!m) return null;
  return { value: Number(m[1]), unit: (m[2] ?? "").toLowerCase() || "user" };
}

function lengthToMm(value: number, unit: string): { mm: number; confidence: GeometryConfidence } {
  switch (unit) {
    case "mm":
      return { mm: value, confidence: "high" };
    case "cm":
      return { mm: value * 10, confidence: "high" };
    case "in":
      return { mm: value * 25.4, confidence: "high" };
    case "pt":
      return { mm: (value * 25.4) / 72, confidence: "medium" };
    case "px":
      return { mm: value / PX_PER_MM, confidence: "low" };
    default:
      return { mm: value, confidence: "low" };
  }
}

function parseViewBox(raw: string | null | undefined): SvgGeometryBBox | null {
  if (!raw?.trim()) return null;
  const parts = raw.trim().split(/[\s,]+/).map(Number);
  if (parts.length !== 4 || parts.some((n) => Number.isNaN(n))) return null;
  const [minX, minY, w, h] = parts;
  return { minX, minY, maxX: minX + w, maxY: minY + h };
}

function mergeBbox(a: SvgGeometryBBox | null, b: SvgGeometryBBox | null): SvgGeometryBBox | null {
  if (!a) return b;
  if (!b) return a;
  return {
    minX: Math.min(a.minX, b.minX),
    minY: Math.min(a.minY, b.minY),
    maxX: Math.max(a.maxX, b.maxX),
    maxY: Math.max(a.maxY, b.maxY),
  };
}

function bboxWidth(b: SvgGeometryBBox): number {
  return Math.max(0, b.maxX - b.minX);
}

function bboxHeight(b: SvgGeometryBBox): number {
  return Math.max(0, b.maxY - b.minY);
}

function getStyleProp(el: Element, prop: string): string | null {
  const style = el.getAttribute("style");
  if (!style) return null;
  const re = new RegExp(`${prop}\\s*:\\s*([^;]+)`, "i");
  const m = style.match(re);
  return m?.[1]?.trim() ?? null;
}

function isElementHidden(el: Element, ancestors: Element[]): boolean {
  const chain = [...ancestors, el];
  for (const node of chain) {
    const display = node.getAttribute("display") ?? getStyleProp(node, "display");
    if (display === "none") return true;
    const visibility = node.getAttribute("visibility") ?? getStyleProp(node, "visibility");
    if (visibility === "hidden" || visibility === "collapse") return true;
    const opacity = node.getAttribute("opacity") ?? getStyleProp(node, "opacity");
    if (opacity === "0") return true;
  }
  return false;
}

function parseTransform(
  transform: string | null | undefined
): {
  apply: (x: number, y: number) => { x: number; y: number };
  warnings: string[];
} {
  const warnings: string[] = [];
  if (!transform?.trim()) {
    return { apply: (x, y) => ({ x, y }), warnings };
  }

  let fn = (x: number, y: number) => ({ x, y });
  const parts = transform.match(/(\w+)\([^)]*\)/g) ?? [];

  for (const part of parts) {
    const m = part.match(/^(\w+)\((.+)\)$/);
    if (!m) continue;
    const [, name, argsRaw] = m;
    const args = argsRaw.split(/[\s,]+/).map(Number).filter((n) => !Number.isNaN(n));
    const prev = fn;

    switch (name) {
      case "translate": {
        const tx = args[0] ?? 0;
        const ty = args[1] ?? 0;
        fn = (x, y) => {
          const p = prev(x, y);
          return { x: p.x + tx, y: p.y + ty };
        };
        break;
      }
      case "scale": {
        const sx = args[0] ?? 1;
        const sy = args[1] ?? sx;
        fn = (x, y) => {
          const p = prev(x, y);
          return { x: p.x * sx, y: p.y * sy };
        };
        break;
      }
      case "matrix": {
        if (args.length >= 6) {
          const [a, b, c, d, e, f] = args;
          fn = (x, y) => {
            const p = prev(x, y);
            return { x: a * p.x + c * p.y + e, y: b * p.x + d * p.y + f };
          };
        }
        break;
      }
      case "rotate":
      case "skewX":
      case "skewY":
        warnings.push(`Transform nesuportat: ${name}`);
        break;
      default:
        warnings.push(`Transform nesuportat: ${name}`);
        break;
    }
  }

  return { apply: fn, warnings };
}

function expandPoint(
  bbox: SvgGeometryBBox | null,
  x: number,
  y: number
): SvgGeometryBBox {
  if (!bbox) return { minX: x, minY: y, maxX: x, maxY: y };
  return {
    minX: Math.min(bbox.minX, x),
    minY: Math.min(bbox.minY, y),
    maxX: Math.max(bbox.maxX, x),
    maxY: Math.max(bbox.maxY, y),
  };
}

function elementLocalBbox(el: Element): { bbox: SvgGeometryBBox | null; warnings: string[] } {
  const tag = el.tagName.toLowerCase();
  const warnings: string[] = [];
  const num = (attr: string, fallback = 0) => {
    const v = el.getAttribute(attr);
    return v != null && v !== "" ? Number(v) : fallback;
  };

  switch (tag) {
    case "rect": {
      const x = num("x");
      const y = num("y");
      const w = num("width");
      const h = num("height");
      if (w <= 0 || h <= 0) return { bbox: null, warnings };
      return { bbox: { minX: x, minY: y, maxX: x + w, maxY: y + h }, warnings };
    }
    case "circle": {
      const cx = num("cx");
      const cy = num("cy");
      const r = num("r");
      if (r <= 0) return { bbox: null, warnings };
      return {
        bbox: { minX: cx - r, minY: cy - r, maxX: cx + r, maxY: cy + r },
        warnings,
      };
    }
    case "ellipse": {
      const cx = num("cx");
      const cy = num("cy");
      const rx = num("rx");
      const ry = num("ry", rx);
      if (rx <= 0 || ry <= 0) return { bbox: null, warnings };
      return {
        bbox: { minX: cx - rx, minY: cy - ry, maxX: cx + rx, maxY: cy + ry },
        warnings,
      };
    }
    case "line": {
      const x1 = num("x1");
      const y1 = num("y1");
      const x2 = num("x2");
      const y2 = num("y2");
      return {
        bbox: {
          minX: Math.min(x1, x2),
          minY: Math.min(y1, y2),
          maxX: Math.max(x1, x2),
          maxY: Math.max(y1, y2),
        },
        warnings,
      };
    }
    case "polyline":
    case "polygon": {
      const pts = el.getAttribute("points");
      if (!pts?.trim()) return { bbox: null, warnings };
      const coords = pts.trim().split(/[\s,]+/).map(Number);
      let bbox: SvgGeometryBBox | null = null;
      for (let i = 0; i + 1 < coords.length; i += 2) {
        bbox = expandPoint(bbox, coords[i], coords[i + 1]);
      }
      return { bbox, warnings };
    }
    case "path": {
      const d = el.getAttribute("d");
      if (!d?.trim()) return { bbox: null, warnings };
      return pathCoordinateBounds(d);
    }
    default:
      return { bbox: null, warnings };
  }
}

function pathCoordinateBounds(d: string): { bbox: SvgGeometryBBox | null; warnings: string[] } {
  const warnings: string[] = [];
  const tokens =
    d
      .replace(/([MmLlHhVvCcSsQqTtAaZz])/g, " $1 ")
      .replace(/,/g, " ")
      .match(/[a-zA-Z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g) ?? [];
  let i = 0;
  let cmd = "";
  let cx = 0;
  let cy = 0;
  let startX = 0;
  let startY = 0;
  let bbox: SvgGeometryBBox | null = null;

  const readNum = () => Number(tokens[i++]);

  const track = (x: number, y: number) => {
    bbox = expandPoint(bbox, x, y);
    cx = x;
    cy = y;
  };

  while (i < tokens.length) {
    const t = tokens[i];
    if (/^[a-zA-Z]$/.test(t)) {
      cmd = t;
      i++;
      continue;
    }

    const rel = cmd === cmd.toLowerCase();
    const C = cmd.toUpperCase();

    try {
      switch (C) {
        case "M": {
          const x = readNum();
          const y = readNum();
          const ax = rel ? cx + x : x;
          const ay = rel ? cy + y : y;
          startX = ax;
          startY = ay;
          track(ax, ay);
          cmd = rel ? "l" : "L";
          break;
        }
        case "L": {
          const x = readNum();
          const y = readNum();
          track(rel ? cx + x : x, rel ? cy + y : y);
          break;
        }
        case "H": {
          const x = readNum();
          track(rel ? cx + x : x, cy);
          break;
        }
        case "V": {
          const y = readNum();
          track(cx, rel ? cy + y : y);
          break;
        }
        case "C": {
          readNum();
          readNum();
          readNum();
          readNum();
          const x = readNum();
          const y = readNum();
          track(rel ? cx + x : x, rel ? cy + y : y);
          break;
        }
        case "S":
        case "Q":
        case "T": {
          const arity = C === "Q" || C === "T" ? 2 : 4;
          for (let k = 0; k < arity - 2; k++) readNum();
          const x = readNum();
          const y = readNum();
          track(rel ? cx + x : x, rel ? cy + y : y);
          break;
        }
        case "A": {
          readNum();
          readNum();
          readNum();
          readNum();
          readNum();
          const x = readNum();
          const y = readNum();
          track(rel ? cx + x : x, rel ? cy + y : y);
          warnings.push("Arc path — limite estimate conservator.");
          break;
        }
        case "Z": {
          track(startX, startY);
          break;
        }
        default:
          warnings.push(`Comandă path nesuportată: ${C}`);
          i++;
      }
    } catch {
      warnings.push("Path complex — limite estimate conservator.");
      break;
    }
  }

  return { bbox, warnings };
}

function computeElementBbox(
  el: Element,
  ancestors: Element[]
): { bbox: SvgGeometryBBox | null; warnings: string[] } {
  if (isElementHidden(el, ancestors)) return { bbox: null, warnings: [] };

  const { bbox: local, warnings: localWarnings } = elementLocalBbox(el);
  if (!local) return { bbox: null, warnings: localWarnings };

  const { apply, warnings: transformWarnings } = parseTransform(el.getAttribute("transform"));
  const corners = [
    apply(local.minX, local.minY),
    apply(local.maxX, local.minY),
    apply(local.minX, local.maxY),
    apply(local.maxX, local.maxY),
  ];
  let bbox: SvgGeometryBBox | null = null;
  for (const p of corners) {
    bbox = expandPoint(bbox, p.x, p.y);
  }
  return { bbox, warnings: [...localWarnings, ...transformWarnings] };
}

function traverseDrawableBbox(
  root: Element,
  ancestors: Element[] = []
): { bbox: SvgGeometryBBox | null; elementCount: number; warnings: string[] } {
  let bbox: SvgGeometryBBox | null = null;
  let elementCount = 0;
  const warnings: string[] = [];

  for (const child of Array.from(root.children)) {
    const tag = child.tagName.toLowerCase();
    if (tag === "g") {
      const nested = traverseDrawableBbox(child, [...ancestors, root]);
      bbox = mergeBbox(bbox, nested.bbox);
      elementCount += nested.elementCount;
      warnings.push(...nested.warnings);
      continue;
    }
    if (
      tag === "path" ||
      tag === "rect" ||
      tag === "circle" ||
      tag === "ellipse" ||
      tag === "line" ||
      tag === "polyline" ||
      tag === "polygon"
    ) {
      const { bbox: elBbox, warnings: w } = computeElementBbox(child, [...ancestors, root]);
      if (elBbox) {
        bbox = mergeBbox(bbox, elBbox);
        elementCount += 1;
      }
      warnings.push(...w);
    }
  }

  return { bbox, elementCount, warnings };
}

function layerLabelFromGroup(g: Element): string {
  const inkscapeLabel =
    g.getAttributeNS(INKSCAPE_NS, "label") ?? g.getAttribute("inkscape:label");
  if (inkscapeLabel?.trim()) return inkscapeLabel.trim();
  const titleEl = g.querySelector("title");
  if (titleEl?.textContent?.trim()) return titleEl.textContent.trim();
  return g.getAttribute("id")?.trim() ?? "Layer fără nume";
}

function findLayerGroup(svgRoot: Element, layer: SvgVectorDetectedLayer): Element | null {
  const groups = Array.from(svgRoot.querySelectorAll("g"));
  for (const g of groups) {
    const id = g.getAttribute("id")?.trim() ?? "";
    const label = layerLabelFromGroup(g);
    if (layer.id && id === layer.id) return g;
    if (label === layer.label) return g;
  }
  return null;
}

function resolveUnits(
  svgRoot: Element
): { units: SvgGeometryUnits; warnings: string[]; scaleX: number; scaleY: number } {
  const warnings: string[] = [];
  const widthRaw = svgRoot.getAttribute("width");
  const heightRaw = svgRoot.getAttribute("height");
  const viewBox = parseViewBox(
    svgRoot.getAttribute("viewBox") ?? svgRoot.getAttribute("viewbox")
  );

  const wParsed = parseLengthToken(widthRaw);
  const hParsed = parseLengthToken(heightRaw);

  let scaleX = 1;
  let scaleY = 1;
  let confidence: GeometryConfidence = "low";
  let scaleSource: SvgGeometryUnits["scaleSource"] = "viewbox_only";
  const widthUnit = wParsed?.unit ?? "user";
  const heightUnit = hParsed?.unit ?? "user";

  if (wParsed && hParsed && viewBox) {
    const wMm = lengthToMm(wParsed.value, wParsed.unit);
    const hMm = lengthToMm(hParsed.value, hParsed.unit);
    const vbW = bboxWidth(viewBox);
    const vbH = bboxHeight(viewBox);
    if (vbW > 0 && vbH > 0) {
      scaleX = wMm.mm / vbW;
      scaleY = hMm.mm / vbH;
      scaleSource = "physical";
      confidence =
        wMm.confidence === "high" && hMm.confidence === "high"
          ? "high"
          : wMm.confidence === "low" || hMm.confidence === "low"
            ? "low"
            : "medium";
      if (wParsed.unit === "px" || hParsed.unit === "px") {
        warnings.push("Dimensiuni în px — conversie la 96 DPI, încredere redusă.");
        confidence = "low";
      }
      const ratioDiff = Math.abs(scaleX - scaleY) / Math.max(scaleX, scaleY);
      if (ratioDiff > 0.02) {
        warnings.push("Scări width/height diferite — verifică manual.");
        confidence = confidence === "high" ? "medium" : "low";
        scaleSource = "mixed";
      }
    }
  } else if (wParsed && !viewBox) {
    const wMm = lengthToMm(wParsed.value, wParsed.unit);
    scaleX = scaleY = wMm.mm / wParsed.value;
    scaleSource = "physical";
    confidence = wParsed.unit === "px" ? "low" : wMm.confidence;
    warnings.push("viewBox lipsește — scalare limitată.");
  } else if (viewBox) {
    warnings.push("Doar viewBox — dimensiuni fizice estimate cu încredere redusă.");
    confidence = "low";
  } else {
    warnings.push("Dimensiuni fizice indisponibile — sugestii în unități SVG.");
  }

  return {
    units: {
      widthUnit,
      heightUnit,
      scaleSource,
      pxToMm: 1 / PX_PER_MM,
      confidence,
    },
    warnings,
    scaleX,
    scaleY,
  };
}

function bboxToMm(bbox: SvgGeometryBBox, scaleX: number, scaleY: number): SvgGeometryBBox {
  return {
    minX: bbox.minX * scaleX,
    minY: bbox.minY * scaleY,
    maxX: bbox.maxX * scaleX,
    maxY: bbox.maxY * scaleY,
  };
}

function collectPathElements(group: Element): Element[] {
  const paths: Element[] = [];
  const walk = (node: Element) => {
    for (const child of Array.from(node.children)) {
      const tag = child.tagName.toLowerCase();
      if (tag === "path") {
        paths.push(child);
      } else if (tag === "g") {
        walk(child);
      }
    }
  };
  walk(group);
  return paths;
}

function computeLetterPathMetrics(
  group: Element,
  scaleX: number,
  scaleY: number
): {
  perimeterM: number;
  areaM2: number;
  letterCount: number;
  warnings: string[];
} {
  const warnings: string[] = [];
  const paths = collectPathElements(group);
  if (paths.length === 0) {
    return { perimeterM: 0, areaM2: 0, letterCount: 0, warnings: ["Nu există elemente path în layer litere."] };
  }

  let totalLengthUser = 0;
  let totalAreaUser = 0;
  const allSubpaths = [];
  for (const pathEl of paths) {
    const d = pathEl.getAttribute("d");
    if (!d?.trim()) continue;
    const pm = parsePathMetrics(d);
    warnings.push(...pm.warnings);
    totalLengthUser += pm.totalLength;
    totalAreaUser += pm.totalClosedArea;
    allSubpaths.push(...pm.subpaths);
  }

  const avgScale = averageScale(scaleX, scaleY);
  const perimeterMm = userUnitsToMm(totalLengthUser, avgScale);
  const areaMm2 = totalAreaUser * areaScale(scaleX, scaleY);
  const letterCount = estimateLetterCountFromSubpaths(allSubpaths);

  return {
    perimeterM: Math.round(mmToM(perimeterMm) * 1000) / 1000,
    areaM2: Math.round(mm2ToM2(areaMm2) * 10000) / 10000,
    letterCount,
    warnings,
  };
}

/** Bar-like rectangle aspect ratio threshold (long side / short side). */
const BAR_LIKE_ASPECT_RATIO = 8;

function collectBarLikeRectWarnings(group: Element): string[] {
  const warnings: string[] = [];
  const walk = (node: Element) => {
    for (const child of Array.from(node.children)) {
      const tag = child.tagName.toLowerCase();
      if (tag === "g") {
        walk(child);
        continue;
      }
      if (tag !== "rect") continue;
      const w = Number(child.getAttribute("width") ?? 0);
      const h = Number(child.getAttribute("height") ?? 0);
      if (w <= 0 || h <= 0) continue;
      const longSide = Math.max(w, h);
      const shortSide = Math.min(w, h);
      if (shortSide > 0 && longSide / shortSide >= BAR_LIKE_ASPECT_RATIO) {
        warnings.push(STRUCTURE_IN_LETTERS_LAYER_WARNING);
        return;
      }
    }
  };
  walk(group);
  return warnings;
}

function lowerConfidence(
  a: GeometryConfidence,
  b: GeometryConfidence
): GeometryConfidence {
  const order = { high: 3, medium: 2, low: 1 };
  return order[a] <= order[b] ? a : b;
}

export function parseSvgGeometryFromText(
  svgText: string,
  confirmedLayers: SvgVectorDetectedLayer[]
): SvgGeometryParseResult {
  const unsupported: string[] = [];
  const { text, ok, error } = sanitizeSvgText(svgText);
  if (!ok) return emptyResult(error);

  const doc = new DOMParser().parseFromString(text, "image/svg+xml");
  if (doc.querySelector("parsererror")) {
    return emptyResult("SVG invalid sau corupt.");
  }

  const svgRoot = doc.documentElement;
  if (svgRoot.tagName.toLowerCase() !== "svg") {
    return emptyResult("Rădăcina documentului nu este <svg>.");
  }

  const mappedLayers = confirmedLayers.filter((l) => l.confirmed_role !== "unknown");
  if (mappedLayers.length === 0) {
    return {
      parseOk: true,
      units: null,
      layers: [],
      suggestions: {},
      warnings: ["Confirmă rolurile layerelor înainte de sugestii geometrice."],
      unsupported,
      confidence: "low",
    };
  }

  const { units, warnings: unitWarnings, scaleX, scaleY } = resolveUnits(svgRoot);
  const warnings = [...unitWarnings];
  let confidence = units.confidence;

  const layerResults: SvgGeometryLayerResult[] = [];
  let assemblyBbox: SvgGeometryBBox | null = null;
  let letterBbox: SvgGeometryBBox | null = null;
  let supportBbox: SvgGeometryBBox | null = null;
  let frameBbox: SvgGeometryBBox | null = null;
  let letterElementCount = 0;

  let letterGroupForMetrics: Element | null = null;

  for (const layer of mappedLayers) {
    let group = findLayerGroup(svgRoot, layer);
    const layerWarnings: string[] = [];
    let layerConfidence: GeometryConfidence = units.confidence;

    if (
      !group &&
      mappedLayers.length === 1 &&
      geometryRoleBucket(layer.confirmed_role) === "letter"
    ) {
      group = svgRoot;
      layerWarnings.push(
        "Layer fără grup dedicat — se folosește întregul SVG pentru estimare bbox."
      );
    }

    if (!group) {
      layerResults.push({
        layerId: layer.id,
        label: layer.label,
        confirmedRole: layer.confirmed_role,
        elementCount: 0,
        bbox: null,
        bboxMm: null,
        warnings: ["Layer negăsit în SVG pentru bbox."],
        confidence: "low",
      });
      confidence = lowerConfidence(confidence, "low");
      continue;
    }

    const { bbox, elementCount, warnings: traverseWarnings } = traverseDrawableBbox(group);
    layerWarnings.push(...traverseWarnings);
    if (traverseWarnings.some((w) => w.includes("nesuportat"))) {
      layerConfidence = lowerConfidence(layerConfidence, "medium");
    }

    const bboxMm =
      bbox && units.scaleSource !== "viewbox_only" ? bboxToMm(bbox, scaleX, scaleY) : null;

    layerResults.push({
      layerId: layer.id,
      label: layer.label,
      confirmedRole: layer.confirmed_role,
      elementCount,
      bbox,
      bboxMm,
      warnings: layerWarnings,
      confidence: layerConfidence,
    });

    if (bboxMm) {
      assemblyBbox = mergeBbox(assemblyBbox, bboxMm);
    } else if (bbox) {
      assemblyBbox = mergeBbox(assemblyBbox, bbox);
    }

    const bucket = geometryRoleBucket(layer.confirmed_role);
    if (bucket === "letter" && group && !letterGroupForMetrics) {
      letterGroupForMetrics = group;
    }
    if (bucket === "letter") {
      letterElementCount += elementCount;
      if (bboxMm) letterBbox = mergeBbox(letterBbox, bboxMm);
      else if (bbox) letterBbox = mergeBbox(letterBbox, bbox);
    } else if (bucket === "support") {
      if (bboxMm) supportBbox = mergeBbox(supportBbox, bboxMm);
      else if (bbox) supportBbox = mergeBbox(supportBbox, bbox);
    } else if (bucket === "frame") {
      if (bboxMm) frameBbox = mergeBbox(frameBbox, bboxMm);
      else if (bbox) frameBbox = mergeBbox(frameBbox, bbox);
    }

    confidence = lowerConfidence(confidence, layerConfidence);
    warnings.push(...layerWarnings);
  }

  const suggestions: SvgGeometrySuggestions = {};
  const useMm = units.scaleSource !== "viewbox_only";

  // Assembly dimensions for quote must exclude support/structure layers.
  const quoteAssemblyBbox = letterBbox ?? assemblyBbox;
  if (quoteAssemblyBbox && useMm) {
    suggestions.assemblyWidthMm = Math.round(bboxWidth(quoteAssemblyBbox) * 10) / 10;
    suggestions.assemblyHeightMm = Math.round(bboxHeight(quoteAssemblyBbox) * 10) / 10;
  }
  if (
    letterBbox &&
    assemblyBbox &&
    useMm &&
    (Math.abs(bboxWidth(letterBbox) - bboxWidth(assemblyBbox)) > 1 ||
      Math.abs(bboxHeight(letterBbox) - bboxHeight(assemblyBbox)) > 1)
  ) {
    warnings.push(
      "Dimensiunile ansamblului pentru ofertare folosesc doar layerul litere — structura suport este exclusă."
    );
  }
  if (letterBbox && useMm) {
    suggestions.letterLayerWidthMm = Math.round(bboxWidth(letterBbox) * 10) / 10;
    suggestions.letterLayerHeightMm = Math.round(bboxHeight(letterBbox) * 10) / 10;
  }
  if (supportBbox && useMm) {
    suggestions.supportWidthMm = Math.round(bboxWidth(supportBbox) * 10) / 10;
    suggestions.supportHeightMm = Math.round(bboxHeight(supportBbox) * 10) / 10;
    const areaMm2 = bboxWidth(supportBbox) * bboxHeight(supportBbox);
    suggestions.supportAreaM2 = Math.round((areaMm2 / 1_000_000) * 10000) / 10000;
    warnings.push("Aria suportului este estimare bounding-box, nu contur real.");
  }
  if (frameBbox && useMm) {
    suggestions.frameWidthMm = Math.round(bboxWidth(frameBbox) * 10) / 10;
    suggestions.frameHeightMm = Math.round(bboxHeight(frameBbox) * 10) / 10;
  }
  if (letterElementCount > 0) {
    suggestions.letterElementCount = letterElementCount;
  }

  if (letterGroupForMetrics && useMm) {
    warnings.push(...collectBarLikeRectWarnings(letterGroupForMetrics));
    const pathMetrics = computeLetterPathMetrics(letterGroupForMetrics, scaleX, scaleY);
    warnings.push(...pathMetrics.warnings);
    if (pathMetrics.perimeterM > 0) {
      suggestions.letterPerimeterM = pathMetrics.perimeterM;
    }
    if (pathMetrics.areaM2 > 0) {
      suggestions.letterFaceAreaM2 = pathMetrics.areaM2;
    }
    if (pathMetrics.letterCount > 0) {
      suggestions.letterCount = pathMetrics.letterCount;
      if (pathMetrics.letterCount !== letterElementCount) {
        warnings.push(
          `Număr contururi detectate: ${pathMetrics.letterCount} (elemente path: ${letterElementCount}).`
        );
      }
    } else if (letterElementCount > 0) {
      warnings.push("Număr elemente ≠ număr litere — verifică manual.");
    }
  }

  if (
    !suggestions.letterPerimeterM &&
    !suggestions.letterFaceAreaM2 &&
    mappedLayers.some((l) => geometryRoleBucket(l.confirmed_role) === "letter")
  ) {
    unsupported.push(PERIMETER_AREA_UNSUPPORTED_MSG);
    warnings.push(PERIMETER_AREA_UNSUPPORTED_MSG);
  }

  if (!useMm) {
    warnings.push("Dimensiuni fizice indisponibile — sugestiile mm nu sunt calculate.");
    confidence = "low";
  }

  return {
    parseOk: true,
    units,
    layers: layerResults,
    suggestions,
    warnings: [...new Set(warnings)],
    unsupported,
    confidence,
  };
}

export async function parseSvgGeometryFromFile(
  file: File,
  confirmedLayers: SvgVectorDetectedLayer[]
): Promise<SvgGeometryParseResult> {
  if (file.name.split(".").pop()?.toLowerCase() !== "svg") {
    return emptyResult("Parser geometrie disponibil doar pentru SVG.");
  }
  try {
    const text = await file.text();
    return parseSvgGeometryFromText(text, confirmedLayers);
  } catch (err) {
    return emptyResult(err instanceof Error ? err.message : "Citire SVG eșuată.");
  }
}
