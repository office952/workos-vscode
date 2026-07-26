/**
 * Deterministic closed-contour detection + panel candidate scoring.
 * Reuses ParsedSvgDocument + GeometrySummary; does not mutate SVG source.
 */

import type { GeometrySummary, ParsedSvgDocument } from "../analyzer/types";
import type {
  ClosedContourBBox,
  ClosedContourCandidate,
  ClosedContourDetectionReport,
  ClosedContourSourceType,
  ClosureMethod,
} from "./closedContourTypes";

const ABSURD_WIDTH_MM = 8000;
const ENDPOINT_TOL_VBU = 0.05;

function fnv1aHex(input: string): string {
  let h = 0x811c9dc5;
  for (let i = 0; i < input.length; i += 1) {
    h ^= input.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(16).padStart(8, "0");
}

function roundN(n: number, digits = 4): number {
  const f = 10 ** digits;
  return Math.round(n * f) / f;
}

function splitPathDataSubpaths(d: string): string[] {
  const starts = [...d.matchAll(/[Mm]/g)].map((m) => m.index ?? 0);
  if (starts.length === 0) return [];
  const segments: string[] = [];
  for (let i = 0; i < starts.length; i += 1) {
    const start = starts[i];
    const end = i + 1 < starts.length ? starts[i + 1] : d.length;
    const segment = d.slice(start, end).trim();
    if (segment.length > 0) segments.push(segment);
  }
  return segments;
}

function parsePoints(points: string | null): Array<[number, number]> {
  if (!points) return [];
  const nums = points
    .trim()
    .split(/[\s,]+/)
    .map(Number)
    .filter((n) => Number.isFinite(n));
  const out: Array<[number, number]> = [];
  for (let i = 0; i + 1 < nums.length; i += 2) {
    out.push([nums[i], nums[i + 1]]);
  }
  return out;
}

function bboxFromPoints(pts: Array<[number, number]>): ClosedContourBBox | null {
  if (pts.length === 0) return null;
  const xs = pts.map((p) => p[0]);
  const ys = pts.map((p) => p[1]);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const maxX = Math.max(...xs);
  const maxY = Math.max(...ys);
  return { x: minX, y: minY, width: maxX - minX, height: maxY - minY };
}

function perimeterFromPoints(pts: Array<[number, number]>, closed: boolean): number {
  if (pts.length < 2) return 0;
  let p = 0;
  for (let i = 1; i < pts.length; i += 1) {
    p += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  }
  if (closed && pts.length > 2) {
    p += Math.hypot(pts[0][0] - pts[pts.length - 1][0], pts[0][1] - pts[pts.length - 1][1]);
  }
  return p;
}

/** Lightweight path sampler for bbox / perimeter (reuse chord approximation). */
function samplePath(d: string): Array<[number, number]> {
  const tokens = d.match(/[a-zA-Z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g);
  if (!tokens?.length) return [];
  let x = 0;
  let y = 0;
  let startX = 0;
  let startY = 0;
  let cmd = "";
  let i = 0;
  const pts: Array<[number, number]> = [];
  const push = (nx: number, ny: number) => {
    x = nx;
    y = ny;
    pts.push([nx, ny]);
  };
  const num = (off: number): number | null => {
    const v = Number(tokens[i + off]);
    return Number.isFinite(v) ? v : null;
  };
  while (i < tokens.length) {
    const tok = tokens[i];
    if (/^[a-zA-Z]$/.test(tok)) {
      cmd = tok;
      i += 1;
      if (cmd === "Z" || cmd === "z") {
        push(startX, startY);
        continue;
      }
    }
    if (!cmd) {
      i += 1;
      continue;
    }
    const rel = cmd === cmd.toLowerCase();
    if (cmd === "M" || cmd === "m") {
      const nx = num(0);
      const ny = num(1);
      if (nx == null || ny == null) {
        i += 1;
        continue;
      }
      push(rel ? x + nx : nx, rel ? y + ny : ny);
      startX = x;
      startY = y;
      cmd = rel ? "l" : "L";
      i += 2;
      continue;
    }
    if (cmd === "L" || cmd === "l") {
      const nx = num(0);
      const ny = num(1);
      if (nx == null || ny == null) {
        i += 1;
        continue;
      }
      push(rel ? x + nx : nx, rel ? y + ny : ny);
      i += 2;
      continue;
    }
    if (cmd === "H" || cmd === "h") {
      const n = num(0);
      if (n == null) {
        i += 1;
        continue;
      }
      push(rel ? x + n : n, y);
      i += 1;
      continue;
    }
    if (cmd === "V" || cmd === "v") {
      const n = num(0);
      if (n == null) {
        i += 1;
        continue;
      }
      push(x, rel ? y + n : n);
      i += 1;
      continue;
    }
    if (cmd === "C" || cmd === "c") {
      const ex = num(4);
      const ey = num(5);
      if (ex == null || ey == null) {
        i += 1;
        continue;
      }
      push(rel ? x + ex : ex, rel ? y + ey : ey);
      i += 6;
      continue;
    }
    if (cmd === "S" || cmd === "s" || cmd === "Q" || cmd === "q") {
      const ex = num(2);
      const ey = num(3);
      if (ex == null || ey == null) {
        i += 1;
        continue;
      }
      push(rel ? x + ex : ex, rel ? y + ey : ey);
      i += 4;
      continue;
    }
    if (cmd === "T" || cmd === "t") {
      const ex = num(0);
      const ey = num(1);
      if (ex == null || ey == null) {
        i += 1;
        continue;
      }
      push(rel ? x + ex : ex, rel ? y + ey : ey);
      i += 2;
      continue;
    }
    if (cmd === "A" || cmd === "a") {
      const ex = num(5);
      const ey = num(6);
      if (ex == null || ey == null) {
        i += 1;
        continue;
      }
      push(rel ? x + ex : ex, rel ? y + ey : ey);
      i += 7;
      continue;
    }
    i += 1;
  }
  return pts;
}

function isGeometricallyClosed(pts: Array<[number, number]>, tol = ENDPOINT_TOL_VBU): boolean {
  if (pts.length < 3) return false;
  const a = pts[0];
  const b = pts[pts.length - 1];
  return Math.hypot(a[0] - b[0], a[1] - b[1]) <= tol;
}

function containsBBox(outer: ClosedContourBBox, inner: ClosedContourBBox, tol = 0.5): boolean {
  return (
    inner.x >= outer.x - tol &&
    inner.y >= outer.y - tol &&
    inner.x + inner.width <= outer.x + outer.width + tol &&
    inner.y + inner.height <= outer.y + outer.height + tol
  );
}

function rectangularity(bbox: ClosedContourBBox, areaVbu2: number): number {
  const boxArea = Math.max(bbox.width * bbox.height, 1e-9);
  const ratio = Math.min(1, Math.max(0, areaVbu2 / boxArea));
  const aspect = Math.min(bbox.width, bbox.height) / Math.max(bbox.width, bbox.height, 1e-9);
  // Prefer near-rectangular outer panels without using color.
  return roundN(0.65 * ratio + 0.35 * aspect, 4);
}

function orientationOf(w: number, h: number): ClosedContourCandidate["orientation"] {
  const r = Math.abs(w - h) / Math.max(w, h, 1e-9);
  if (r < 0.05) return "square";
  return w >= h ? "landscape" : "portrait";
}

function resolveMmPerVbu(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
): { mmPerVbu: number; raw: number; unitAmbiguity: boolean; correction: ClosedContourDetectionReport["scale_correction"]; warnings: string[] } {
  const raw = geometry.mmPerVbu > 0 ? geometry.mmPerVbu : 1;
  const warnings: string[] = [];
  const widthMm =
    doc.viewBox && raw > 0 ? doc.viewBox.width * raw : doc.width && doc.conversionToMm.factor
      ? doc.width.value * doc.conversionToMm.factor
      : null;
  const unit = doc.conversionToMm.detectedUnits;
  if (unit === "cm" && widthMm != null && widthMm > ABSURD_WIDTH_MM && doc.viewBox) {
    warnings.push(
      "UNIT_AMBIGUITY_COREL_CM: dimensiunile root în cm produc o lățime absurdă; pentru candidatul de panou se folosește viewBox ca mm (guard).",
    );
    return {
      mmPerVbu: 1,
      raw,
      unitAmbiguity: true,
      correction: "viewbox_as_mm_corel_cm_guard",
      warnings,
    };
  }
  return { mmPerVbu: raw, raw, unitAmbiguity: false, correction: "none", warnings };
}

interface RawContour {
  element_id: string;
  source_element_type: ClosedContourSourceType;
  source_index: number;
  source_subpath_index: number | null;
  closure_method: ClosureMethod;
  bbox: ClosedContourBBox;
  area_vbu2: number;
  perimeter_vbu: number;
  overlay_d: string | null;
  overlay_points: string | null;
  geometry_payload: string;
}

function collectRawContours(doc: ParsedSvgDocument): RawContour[] {
  const out: RawContour[] = [];
  for (const el of doc.elements) {
    if (el.type === "group" || el.type === "unknown" || el.excludeFromPartExtraction) continue;

    if (el.type === "path" && el.d) {
      const segments = splitPathDataSubpaths(el.d);
      segments.forEach((segment, localIdx) => {
        const explicitZ = /[Zz]\s*$/.test(segment.trim());
        const pts = samplePath(segment);
        const geometric = isGeometricallyClosed(pts);
        if (!explicitZ && !geometric) return;
        const bbox = bboxFromPoints(pts);
        if (!bbox || bbox.width <= 0 || bbox.height <= 0) return;
        const peri = perimeterFromPoints(pts, true);
        // shoelace absolute / 2
        let area = 0;
        for (let i = 0; i < pts.length - 1; i += 1) {
          area += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1];
        }
        area = Math.abs(area) / 2;
        out.push({
          element_id: el.elementId,
          source_element_type: segments.length > 1 ? "path_subpath" : "path",
          source_index: el.index,
          source_subpath_index: segments.length > 1 ? localIdx : null,
          closure_method: explicitZ ? "explicit_z" : "geometric_endpoints",
          bbox,
          area_vbu2: area > 0 ? area : bbox.width * bbox.height,
          perimeter_vbu: peri > 0 ? peri : 2 * (bbox.width + bbox.height),
          overlay_d: segment,
          overlay_points: null,
          geometry_payload: `path|${el.index}|${localIdx}|${segment.replace(/\s+/g, " ").trim()}`,
        });
      });
      continue;
    }

    if (el.type === "polygon" && el.points) {
      const pts = parsePoints(el.points);
      if (pts.length < 3) continue;
      const bbox = bboxFromPoints(pts);
      if (!bbox) continue;
      let area = 0;
      for (let i = 0; i < pts.length; i += 1) {
        const j = (i + 1) % pts.length;
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1];
      }
      area = Math.abs(area) / 2;
      out.push({
        element_id: el.elementId,
        source_element_type: "polygon",
        source_index: el.index,
        source_subpath_index: null,
        closure_method: "polygon",
        bbox,
        area_vbu2: area > 0 ? area : bbox.width * bbox.height,
        perimeter_vbu: perimeterFromPoints(pts, true),
        overlay_d: null,
        overlay_points: el.points,
        geometry_payload: `polygon|${el.index}|${el.points.replace(/\s+/g, " ").trim()}`,
      });
      continue;
    }

    if (el.type === "rect") {
      const x = Number(el.attributes.x ?? 0);
      const y = Number(el.attributes.y ?? 0);
      const w = Number(el.attributes.width ?? NaN);
      const h = Number(el.attributes.height ?? NaN);
      if (!Number.isFinite(w) || !Number.isFinite(h) || w <= 0 || h <= 0) continue;
      const bbox = { x, y, width: w, height: h };
      out.push({
        element_id: el.elementId,
        source_element_type: "rect",
        source_index: el.index,
        source_subpath_index: null,
        closure_method: "primitive_closed",
        bbox,
        area_vbu2: w * h,
        perimeter_vbu: 2 * (w + h),
        overlay_d: null,
        overlay_points: `${x},${y} ${x + w},${y} ${x + w},${y + h} ${x},${y + h}`,
        geometry_payload: `rect|${el.index}|${x},${y},${w},${h}`,
      });
      continue;
    }

    if (el.type === "circle") {
      const cx = Number(el.attributes.cx ?? 0);
      const cy = Number(el.attributes.cy ?? 0);
      const r = Number(el.attributes.r ?? NaN);
      if (!Number.isFinite(r) || r <= 0) continue;
      const bbox = { x: cx - r, y: cy - r, width: 2 * r, height: 2 * r };
      out.push({
        element_id: el.elementId,
        source_element_type: "circle",
        source_index: el.index,
        source_subpath_index: null,
        closure_method: "primitive_closed",
        bbox,
        area_vbu2: Math.PI * r * r,
        perimeter_vbu: 2 * Math.PI * r,
        overlay_d: null,
        overlay_points: null,
        geometry_payload: `circle|${el.index}|${cx},${cy},${r}`,
      });
      continue;
    }

    if (el.type === "ellipse") {
      const cx = Number(el.attributes.cx ?? 0);
      const cy = Number(el.attributes.cy ?? 0);
      const rx = Number(el.attributes.rx ?? NaN);
      const ry = Number(el.attributes.ry ?? NaN);
      if (!Number.isFinite(rx) || !Number.isFinite(ry) || rx <= 0 || ry <= 0) continue;
      const bbox = { x: cx - rx, y: cy - ry, width: 2 * rx, height: 2 * ry };
      out.push({
        element_id: el.elementId,
        source_element_type: "ellipse",
        source_index: el.index,
        source_subpath_index: null,
        closure_method: "primitive_closed",
        bbox,
        area_vbu2: Math.PI * rx * ry,
        perimeter_vbu: Math.PI * (3 * (rx + ry) - Math.sqrt((3 * rx + ry) * (rx + 3 * ry))),
        overlay_d: null,
        overlay_points: null,
        geometry_payload: `ellipse|${el.index}|${cx},${cy},${rx},${ry}`,
      });
      continue;
    }

    if (el.type === "polyline" && el.points) {
      const pts = parsePoints(el.points);
      if (!isGeometricallyClosed(pts)) continue;
      const bbox = bboxFromPoints(pts);
      if (!bbox) continue;
      out.push({
        element_id: el.elementId,
        source_element_type: "polyline_closed",
        source_index: el.index,
        source_subpath_index: null,
        closure_method: "polyline_endpoints",
        bbox,
        area_vbu2: bbox.width * bbox.height,
        perimeter_vbu: perimeterFromPoints(pts, true),
        overlay_d: null,
        overlay_points: el.points,
        geometry_payload: `polyline|${el.index}|${el.points.replace(/\s+/g, " ").trim()}`,
      });
    }
  }
  return out;
}

function scoreCandidate(
  c: Omit<ClosedContourCandidate, "confidence" | "reasons" | "is_outer_candidate">,
  totalArea: number,
  totalCount: number,
): Pick<ClosedContourCandidate, "confidence" | "reasons" | "is_outer_candidate"> {
  const reasons: string[] = ["contur închis"];
  let score = 0.35;
  if (c.area_mm2 >= totalArea * 0.35) {
    score += 0.2;
    reasons.push(`suprafață mare (${roundN((c.area_mm2 / Math.max(totalArea, 1)) * 100, 1)}% din compoziție)`);
  }
  if (c.contains_count >= Math.max(1, Math.floor(totalCount * 0.3))) {
    score += 0.2;
    reasons.push(`conține ${c.contains_count} elemente`);
  }
  if (c.rectangularity_score >= 0.75) {
    score += 0.15;
    reasons.push(`rectangularitate ${c.rectangularity_score}`);
  }
  if (c.contained_area_ratio >= 0.5) {
    score += 0.1;
    reasons.push(`acoperă ${roundN(c.contained_area_ratio * 100, 1)}% din aria conținută`);
  }
  // Demote tiny decorative / letter-hole sized relative to composition
  if (c.area_mm2 < totalArea * 0.05) {
    score -= 0.25;
    reasons.push("contur mic față de compoziție (probabil literă/decor)");
  }
  const confidence = Math.max(0, Math.min(1, roundN(score, 4)));
  const is_outer_candidate = confidence >= 0.55 && c.contains_count > 0;
  if (is_outer_candidate) reasons.unshift("candidat panou: probabil");
  return { confidence, reasons, is_outer_candidate };
}

export function detectClosedContourCandidates(
  doc: ParsedSvgDocument,
  geometry: GeometrySummary,
): ClosedContourDetectionReport {
  const scale = resolveMmPerVbu(doc, geometry);
  const raw = collectRawContours(doc);
  const mm = scale.mmPerVbu;

  const draft = raw.map((r) => {
    const geometry_hash = fnv1aHex(r.geometry_payload);
    const contour_id = `cc_${geometry_hash}`;
    const width_mm = r.bbox.width * mm;
    const height_mm = r.bbox.height * mm;
    const area_mm2 = r.area_vbu2 * mm * mm;
    const perimeter_mm = r.perimeter_vbu * mm;
    return {
      contour_id,
      element_id: r.element_id,
      source_element_type: r.source_element_type,
      source_index: r.source_index,
      source_subpath_index: r.source_subpath_index,
      is_closed: true as const,
      closure_method: r.closure_method,
      geometry_hash,
      bbox: r.bbox,
      width_mm: roundN(width_mm, 3),
      height_mm: roundN(height_mm, 3),
      area_mm2: roundN(area_mm2, 3),
      perimeter_mm: roundN(perimeter_mm, 3),
      centroid: {
        x: roundN(r.bbox.x + r.bbox.width / 2, 4),
        y: roundN(r.bbox.y + r.bbox.height / 2, 4),
      },
      orientation: orientationOf(width_mm, height_mm),
      contains_count: 0,
      contained_area_ratio: 0,
      rectangularity_score: rectangularity(r.bbox, r.area_vbu2),
      warnings: [] as string[],
      overlay_d: r.overlay_d,
      overlay_points: r.overlay_points,
      _area_vbu2: r.area_vbu2,
    };
  });

  const totalArea = draft.reduce((s, c) => s + c.area_mm2, 0);

  for (const c of draft) {
    let contains = 0;
    let containedArea = 0;
    for (const other of draft) {
      if (other.contour_id === c.contour_id) continue;
      if (containsBBox(c.bbox, other.bbox)) {
        contains += 1;
        containedArea += other.area_mm2;
      }
    }
    c.contains_count = contains;
    c.contained_area_ratio = roundN(containedArea / Math.max(totalArea, 1), 4);
  }

  const candidates: ClosedContourCandidate[] = draft
    .map((c) => {
      const scored = scoreCandidate(c, totalArea, draft.length);
      const { _area_vbu2: _, ...rest } = c;
      return { ...rest, ...scored };
    })
    .sort((a, b) => {
      if (b.confidence !== a.confidence) return b.confidence - a.confidence;
      if (b.area_mm2 !== a.area_mm2) return b.area_mm2 - a.area_mm2;
      return a.contour_id.localeCompare(b.contour_id);
    });

  return {
    schema: "closed_contour_candidates_v1",
    candidate_count: candidates.length,
    closed_contour_count: candidates.length,
    unit_ambiguity: scale.unitAmbiguity,
    mm_per_vbu_used: scale.mmPerVbu,
    mm_per_vbu_raw: scale.raw,
    scale_correction: scale.correction,
    warnings: scale.warnings,
    candidates,
  };
}

export function findCandidateById(
  report: ClosedContourDetectionReport,
  contourId: string | null | undefined,
): ClosedContourCandidate | null {
  if (!contourId) return null;
  return report.candidates.find((c) => c.contour_id === contourId) ?? null;
}

/** Re-run detection; used to prove identity stability. */
export function assertContourIdentityStable(
  a: ClosedContourDetectionReport,
  b: ClosedContourDetectionReport,
): boolean {
  if (a.candidates.length !== b.candidates.length) return false;
  const idsA = a.candidates.map((c) => c.contour_id).sort();
  const idsB = b.candidates.map((c) => c.contour_id).sort();
  return idsA.every((id, i) => id === idsB[i]);
}
