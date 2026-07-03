/**
 * Client-side SVG metadata + layer detection for volumetric vector intake.
 * Parses text only — no geometry calculation, no raw SVG persistence, no DOM injection.
 */

import { suggestLayerRole, type VectorLayerRole } from "@/lib/svgLayerRoleSuggestion";

const SCRIPT_TAG_RE = /<script\b[^>]*>[\s\S]*?<\/script>/gi;
const INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape";

export interface SvgVectorDetectedLayer {
  id: string;
  label: string;
  element_count: number;
  suggested_role: VectorLayerRole;
  confirmed_role: VectorLayerRole;
  is_inkscape_layer: boolean;
}

export interface SvgVectorAnalysis {
  file_name: string;
  parse_ok: boolean;
  parse_error?: string;
  width?: string;
  height?: string;
  view_box?: string;
  layers: SvgVectorDetectedLayer[];
  warnings: string[];
  has_embedded_raster: boolean;
  vector_svg_analyzed: boolean;
}

export const VECTOR_LAYER_ROLE_OPTIONS: {
  value: VectorLayerRole;
  label: string;
}[] = [
  { value: "volumetric_letters", label: "Litere volumetrice" },
  { value: "letter_face", label: "Față litere" },
  { value: "side_return", label: "Cant / lateral" },
  { value: "support_panel", label: "Suport Dibond / ACM" },
  { value: "metal_frame", label: "Cadru metalic" },
  { value: "guide_reference", label: "Ghidaj / cotă / referință" },
  { value: "ignore", label: "De ignorat" },
  { value: "unknown", label: "Necunoscut" },
];

function sanitizeSvgText(raw: string): { text: string; warnings: string[] } {
  const warnings: string[] = [];
  let text = raw.trim();
  if (!text) {
    return { text: "", warnings: ["Fișierul SVG este gol."] };
  }
  if (SCRIPT_TAG_RE.test(text) || text.toLowerCase().includes("<script")) {
    return { text: "", warnings: ["SVG conține script — respins din motive de securitate."] };
  }
  if (/<!entity/i.test(text)) {
    return { text: "", warnings: ["SVG conține entități externe — respins."] };
  }
  if (/<!doctype/i.test(text)) {
    text = text.replace(/<!doctype[^>]*>/i, "").trim();
    warnings.push("DOCTYPE eliminat pentru analiză (fișierul sursă rămâne neschimbat).");
  }
  return { text, warnings };
}

function countDrawableElements(group: Element): number {
  let count = 0;
  for (const child of Array.from(group.children)) {
    const tag = child.tagName.toLowerCase();
    if (tag === "g") {
      count += countDrawableElements(child);
    } else if (
      tag === "path" ||
      tag === "rect" ||
      tag === "circle" ||
      tag === "ellipse" ||
      tag === "line" ||
      tag === "polyline" ||
      tag === "polygon" ||
      tag === "text" ||
      tag === "use" ||
      tag === "image"
    ) {
      count += 1;
    }
  }
  return count;
}

function decodeXmlLayerName(raw: string): string {
  return raw
    .replace(/_x([0-9a-fA-F]{4})_/g, (_, hex) =>
      String.fromCharCode(parseInt(hex, 16))
    )
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function layerLabelFromGroup(g: Element): string {
  const inkscapeLabel =
    g.getAttributeNS(INKSCAPE_NS, "label") ?? g.getAttribute("inkscape:label");
  if (inkscapeLabel?.trim()) return decodeXmlLayerName(inkscapeLabel.trim());

  const dataName = g.getAttribute("data-name")?.trim();
  if (dataName) return decodeXmlLayerName(dataName);

  const titleEl = g.querySelector("title");
  if (titleEl?.textContent?.trim()) return decodeXmlLayerName(titleEl.textContent.trim());

  const id = g.getAttribute("id")?.trim();
  if (id) return decodeXmlLayerName(id);

  return "Layer fără nume";
}

function isInkscapeLayer(g: Element): boolean {
  const mode =
    g.getAttributeNS(INKSCAPE_NS, "groupmode") ?? g.getAttribute("inkscape:groupmode");
  return mode === "layer";
}

function collectTopLevelGroups(svgRoot: Element): Element[] {
  const direct = Array.from(svgRoot.children).filter(
    (el) => el.tagName.toLowerCase() === "g"
  );
  if (direct.length > 0) return direct;

  const inkscapeLayers = Array.from(svgRoot.querySelectorAll("g")).filter((g) =>
    isInkscapeLayer(g)
  );
  if (inkscapeLayers.length > 0) return inkscapeLayers;

  const allGroups = Array.from(svgRoot.querySelectorAll("g"));
  const leafGroups = allGroups.filter(
    (g) => !Array.from(g.querySelectorAll("g")).some((child) => child.parentNode === g)
  );
  return leafGroups.length > 0 ? leafGroups : allGroups.slice(0, 20);
}

function hasEmbeddedRaster(svgRoot: Element): boolean {
  return svgRoot.querySelector("image") != null;
}

export function parseSvgVectorText(
  fileName: string,
  rawText: string
): SvgVectorAnalysis {
  const base: SvgVectorAnalysis = {
    file_name: fileName,
    parse_ok: false,
    layers: [],
    warnings: [],
    has_embedded_raster: false,
    vector_svg_analyzed: false,
  };

  const { text, warnings: sanitizeWarnings } = sanitizeSvgText(rawText);
  base.warnings.push(...sanitizeWarnings);
  if (!text) {
    base.parse_error = sanitizeWarnings[0] ?? "SVG invalid.";
    return base;
  }

  const doc = new DOMParser().parseFromString(text, "image/svg+xml");
  const parseError = doc.querySelector("parsererror");
  if (parseError) {
    base.parse_error = "SVG invalid sau corupt — nu poate fi parsat.";
    base.warnings.push(base.parse_error);
    return base;
  }

  const svgRoot = doc.documentElement;
  if (svgRoot.tagName.toLowerCase() !== "svg") {
    base.parse_error = "Rădăcina documentului nu este <svg>.";
    return base;
  }

  base.parse_ok = true;
  base.vector_svg_analyzed = true;
  base.width = svgRoot.getAttribute("width") ?? undefined;
  base.height = svgRoot.getAttribute("height") ?? undefined;
  base.view_box = svgRoot.getAttribute("viewBox") ?? svgRoot.getAttribute("viewbox") ?? undefined;

  if (!base.view_box) {
    base.warnings.push("viewBox lipsește — dimensiunile pot fi relative.");
  }
  if (base.width && /cm|in|pt|px/i.test(base.width)) {
    base.warnings.push(`Unități detectate în width: ${base.width}`);
  }

  base.has_embedded_raster = hasEmbeddedRaster(svgRoot);
  if (base.has_embedded_raster) {
    base.warnings.push("Imagine raster încorporată detectată — verificați manual.");
  }

  const groups = collectTopLevelGroups(svgRoot);
  if (groups.length === 0) {
    base.warnings.push("Nu au fost detectate layere/grupuri SVG.");
    return base;
  }

  const seen = new Set<string>();
  for (const g of groups) {
    const id = g.getAttribute("id")?.trim() ?? "";
    const label = layerLabelFromGroup(g);
    const dedupeKey = `${id}::${label}`;
    if (seen.has(dedupeKey)) continue;
    seen.add(dedupeKey);

    const suggested = suggestLayerRole(label);
    base.layers.push({
      id: id || label,
      label,
      element_count: countDrawableElements(g),
      suggested_role: suggested,
      confirmed_role: suggested === "unknown" ? "unknown" : suggested,
      is_inkscape_layer: isInkscapeLayer(g),
    });
  }

  if (base.layers.length === 0) {
    base.warnings.push("Nu au fost detectate layere SVG.");
  }

  return base;
}

export function readSvgFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        resolve(reader.result);
      } else {
        reject(new Error("Nu s-a putut citi fișierul ca text."));
      }
    };
    reader.onerror = () => reject(new Error("Citire fișier eșuată."));
    reader.readAsText(file);
  });
}

export async function analyzeSvgVectorFile(file: File): Promise<SvgVectorAnalysis> {
  const ext = file.name.split(".").pop()?.toLowerCase();
  if (ext !== "svg") {
    return {
      file_name: file.name,
      parse_ok: false,
      parse_error: "Analiza layere este disponibilă doar pentru fișiere SVG.",
      layers: [],
      warnings: [],
      has_embedded_raster: false,
      vector_svg_analyzed: false,
    };
  }

  try {
    const text = await readSvgFileAsText(file);
    return parseSvgVectorText(file.name, text);
  } catch (err) {
    return {
      file_name: file.name,
      parse_ok: false,
      parse_error: err instanceof Error ? err.message : "Citire SVG eșuată.",
      layers: [],
      warnings: [],
      has_embedded_raster: false,
      vector_svg_analyzed: false,
    };
  }
}

export function layerRoleLabel(role: VectorLayerRole): string {
  return VECTOR_LAYER_ROLE_OPTIONS.find((o) => o.value === role)?.label ?? role;
}

export function allLayersMappingConfirmed(layers: SvgVectorDetectedLayer[]): boolean {
  if (layers.length === 0) return false;
  return layers.every((l) => l.confirmed_role !== "unknown");
}
