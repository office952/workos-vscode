/**
 * SVG path metrics — subpath length, closed area, subpath count.
 * Used for letter layer quote geometry (perimeter, face area, letter count).
 */

export interface PathPoint {
  x: number;
  y: number;
}

export interface PathSubpathMetrics {
  closed: boolean;
  length: number;
  area: number;
  pointCount: number;
}

export interface PathMetricsResult {
  subpaths: PathSubpathMetrics[];
  totalLength: number;
  totalClosedArea: number;
  subpathCount: number;
  warnings: string[];
}

function tokenizePath(d: string): string[] {
  const normalized = d.replace(/([MmLlHhVvCcSsQqTtAaZz])/g, " $1 ").replace(/,/g, " ");
  const tokens: string[] = [];
  for (const part of normalized.trim().split(/\s+/)) {
    if (!part) continue;
    if (/^[a-zA-Z]$/.test(part)) {
      tokens.push(part);
    } else if (/^-?\d/i.test(part)) {
      tokens.push(part);
    }
  }
  return tokens;
}

function dist(a: PathPoint, b: PathPoint): number {
  return Math.hypot(b.x - a.x, b.y - a.y);
}

function shoelaceArea(points: PathPoint[]): number {
  if (points.length < 3) return 0;
  let sum = 0;
  for (let i = 0; i < points.length; i++) {
    const j = (i + 1) % points.length;
    sum += points[i].x * points[j].y - points[j].x * points[i].y;
  }
  return Math.abs(sum) * 0.5;
}

function cubicAt(
  p0: PathPoint,
  p1: PathPoint,
  p2: PathPoint,
  p3: PathPoint,
  t: number
): PathPoint {
  const u = 1 - t;
  return {
    x: u * u * u * p0.x + 3 * u * u * t * p1.x + 3 * u * t * t * p2.x + t * t * t * p3.x,
    y: u * u * u * p0.y + 3 * u * u * t * p1.y + 3 * u * t * t * p2.y + t * t * t * p3.y,
  };
}

function flattenCubic(p0: PathPoint, p1: PathPoint, p2: PathPoint, p3: PathPoint, steps = 12): PathPoint[] {
  const pts: PathPoint[] = [];
  for (let i = 1; i <= steps; i++) {
    pts.push(cubicAt(p0, p1, p2, p3, i / steps));
  }
  return pts;
}

function flattenQuadratic(p0: PathPoint, p1: PathPoint, p2: PathPoint, steps = 10): PathPoint[] {
  const pts: PathPoint[] = [];
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const u = 1 - t;
    pts.push({
      x: u * u * p0.x + 2 * u * t * p1.x + t * t * p2.x,
      y: u * u * p0.y + 2 * u * t * p1.y + t * t * p2.y,
    });
  }
  return pts;
}

function appendPoints(subpath: PathPoint[], pts: PathPoint[]): number {
  let added = 0;
  for (const p of pts) {
    subpath.push(p);
    added += 1;
  }
  return added;
}

function polylineLength(points: PathPoint[], closed: boolean): number {
  if (points.length < 2) return 0;
  let len = 0;
  for (let i = 1; i < points.length; i++) {
    len += dist(points[i - 1], points[i]);
  }
  if (closed) {
    len += dist(points[points.length - 1], points[0]);
  }
  return len;
}

/** Parse SVG path `d` into subpath metrics in SVG user units. */
export function parsePathMetrics(d: string): PathMetricsResult {
  const warnings: string[] = [];
  const tokens = tokenizePath(d);
  let i = 0;
  let cmd = "";
  let cx = 0;
  let cy = 0;
  let subpathStart: PathPoint = { x: 0, y: 0 };
  let current: PathPoint[] = [];
  const subpaths: PathSubpathMetrics[] = [];

  const readNum = () => {
    const v = Number(tokens[i++]);
    return Number.isFinite(v) ? v : 0;
  };

  const finishSubpath = (closed: boolean) => {
    if (current.length < 2) {
      current = [];
      return;
    }
    const length = polylineLength(current, closed);
    const area = closed ? shoelaceArea(current) : 0;
    subpaths.push({
      closed,
      length,
      area,
      pointCount: current.length,
    });
    current = [];
  };

  const startSubpath = (x: number, y: number) => {
    finishSubpath(false);
    cx = x;
    cy = y;
    subpathStart = { x, y };
    current = [{ x, y }];
  };

  while (i < tokens.length) {
    const t = tokens[i];
    if (/^[a-zA-Z]$/.test(t)) {
      cmd = t;
      i++;
      if (cmd.toUpperCase() === "Z") {
        finishSubpath(true);
        cx = subpathStart.x;
        cy = subpathStart.y;
        cmd = "";
      }
      continue;
    }

    const rel = cmd === cmd.toLowerCase();
    const C = cmd.toUpperCase();

    try {
      switch (C) {
        case "M": {
          const x = readNum();
          const y = readNum();
          startSubpath(rel ? cx + x : x, rel ? cy + y : y);
          cmd = rel ? "l" : "L";
          break;
        }
        case "L": {
          const x = readNum();
          const y = readNum();
          const p = { x: rel ? cx + x : x, y: rel ? cy + y : y };
          current.push(p);
          cx = p.x;
          cy = p.y;
          break;
        }
        case "H": {
          const x = readNum();
          const p = { x: rel ? cx + x : x, y: cy };
          current.push(p);
          cx = p.x;
          break;
        }
        case "V": {
          const y = readNum();
          const p = { x: cx, y: rel ? cy + y : y };
          current.push(p);
          cy = p.y;
          break;
        }
        case "C": {
          const x1 = readNum();
          const y1 = readNum();
          const x2 = readNum();
          const y2 = readNum();
          const x = readNum();
          const y = readNum();
          const p0 = { x: cx, y: cy };
          const p1 = { x: rel ? cx + x1 : x1, y: rel ? cy + y1 : y1 };
          const p2 = { x: rel ? cx + x2 : x2, y: rel ? cy + y2 : y2 };
          const p3 = { x: rel ? cx + x : x, y: rel ? cy + y : y };
          appendPoints(current, flattenCubic(p0, p1, p2, p3));
          cx = p3.x;
          cy = p3.y;
          warnings.push("path_curve_metrics_approximate");
          break;
        }
        case "Q": {
          const x1 = readNum();
          const y1 = readNum();
          const x = readNum();
          const y = readNum();
          const p0 = { x: cx, y: cy };
          const p1 = { x: rel ? cx + x1 : x1, y: rel ? cy + y1 : y1 };
          const p2 = { x: rel ? cx + x : x, y: rel ? cy + y : y };
          appendPoints(current, flattenQuadratic(p0, p1, p2));
          cx = p2.x;
          cy = p2.y;
          warnings.push("path_curve_metrics_approximate");
          break;
        }
        case "S":
        case "T": {
          warnings.push(`Comandă path ${C} — aproximare liniară.`);
          const x = readNum();
          const y = readNum();
          const p = { x: rel ? cx + x : x, y: rel ? cy + y : y };
          current.push(p);
          cx = p.x;
          cy = p.y;
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
          const p = { x: rel ? cx + x : x, y: rel ? cy + y : y };
          current.push(p);
          cx = p.x;
          cy = p.y;
          warnings.push("Arc path — lungime aproximată ca segment.");
          break;
        }
        default:
          warnings.push(`Comandă path nesuportată: ${C}`);
          i++;
      }
    } catch {
      warnings.push("Path complex — metrici parțiale.");
      break;
    }
  }

  finishSubpath(false);

  const totalLength = subpaths.reduce((n, s) => n + s.length, 0);
  const totalClosedArea = subpaths.filter((s) => s.closed).reduce((n, s) => n + s.area, 0);

  return {
    subpaths,
    totalLength,
    totalClosedArea,
    subpathCount: subpaths.length,
    warnings,
  };
}

/** Minimum subpath length (user units) to count as a letter contour. */
export const MIN_LETTER_SUBPATH_LENGTH_USER = 5;

export function estimateLetterCountFromSubpaths(
  subpaths: PathSubpathMetrics[],
  minLength = MIN_LETTER_SUBPATH_LENGTH_USER
): number {
  return subpaths.filter((s) => s.length >= minLength && s.pointCount >= 3).length;
}

export function userUnitsToMm(value: number, scale: number): number {
  return value * scale;
}

export function mmToM(mm: number): number {
  return mm / 1000;
}

export function mm2ToM2(mm2: number): number {
  return mm2 / 1_000_000;
}

/** Average scale when scaleX ≈ scaleY. */
export function averageScale(scaleX: number, scaleY: number): number {
  return (scaleX + scaleY) / 2;
}

export function areaScale(scaleX: number, scaleY: number): number {
  return scaleX * scaleY;
}
