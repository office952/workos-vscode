import type { VolumetricLetterPreviewConfig } from "./volumetricLetterPreviewTypes";
import {
  buildLedModulePlacements,
  getIsometricDepthVector,
  getLetterBounds,
  resolveGeometrySource,
} from "./volumetricLetterPreviewGeometry";

/** Closed block-letter A (evenodd) — fillable silhouette for 3D preview. */
export const BLOCK_LETTER_A_PATH =
  "M 28 92 L 46 28 L 54 28 L 72 92 L 64 92 L 60 72 L 40 72 L 36 92 Z M 42 64 L 58 64 L 54 48 L 46 48 Z";

export const ISOMETRIC_VISUAL = {
  splitRatio: 0.48,
  trimWidth: 2.8,
  returnWallThickness: 4,
  backingInset: 6,
  canvasPadX: 8,
  canvasPadY: 6,
} as const;

export type IsometricPalette = {
  faceTop: string;
  faceBottom: string;
  trim: string;
  returnExterior: string;
  returnExteriorDark: string;
  returnInterior: string;
  returnBottom: string;
  backingTop: string;
  backingBottom: string;
  cavity: string;
  ledBody: string;
  ledDot: string;
  wiring: string;
  canvasTop: string;
  canvasBottom: string;
  shadow: string;
};

export function resolveIsometricPalette(config: VolumetricLetterPreviewConfig): IsometricPalette {
  const hasVinyl = config.face.hasVinyl;
  const faceTop = hasVinyl ? "#FB923C" : "#93C5FD";
  const faceBottom = hasVinyl ? "#EA580C" : "#2563EB";

  return {
    faceTop,
    faceBottom,
    trim: "#0F172A",
    returnExterior: "#374151",
    returnExteriorDark: "#1F2937",
    returnInterior: "#E5E7EB",
    returnBottom: "#111827",
    backingTop: "#F1F5F9",
    backingBottom: "#CBD5E1",
    cavity: "#0B1120",
    ledBody: "#F8FAFC",
    ledDot: "#FBBF24",
    wiring: "#9CA3AF",
    canvasTop: "#ECEFF3",
    canvasBottom: "#F8FAFC",
    shadow: "rgba(15, 23, 42, 0.18)",
  };
}

export function resolveLetterSilhouettePath(config: VolumetricLetterPreviewConfig): string | null {
  const source = resolveGeometrySource(config);
  if (source === "real") {
    const path = config.artwork.svgPath?.trim();
    if (path) return path;
  }
  if (source === "estimated" && config.artwork.text?.trim()) {
    return BLOCK_LETTER_A_PATH;
  }
  return null;
}

export function getCompactSplitPlaneX(): number {
  const bounds = getLetterBounds();
  return bounds.x + bounds.width * ISOMETRIC_VISUAL.splitRatio;
}

export function computeIsometricCompactViewBox(config: VolumetricLetterPreviewConfig) {
  const bounds = getLetterBounds();
  const iso = getIsometricDepthVector(config.returnSide.depthMm);
  const pad = ISOMETRIC_VISUAL;
  return {
    width: Math.ceil(bounds.x + bounds.width + iso.dx + pad.canvasPadX + 18),
    height: Math.ceil(bounds.y + bounds.height + iso.dy + pad.canvasPadY + 10),
  };
}

export function getIsometricShellPolygons(
  config: VolumetricLetterPreviewConfig,
  offsetX = 0,
  offsetY = 0
) {
  const bounds = getLetterBounds();
  const iso = getIsometricDepthVector(config.returnSide.depthMm ?? 30);
  const bx = bounds.x + offsetX;
  const by = bounds.y + offsetY;
  const bw = bounds.width;
  const bh = bounds.height;
  const { dx, dy } = iso;

  const rightSide = `${bx + bw},${by} ${bx + bw + dx},${by + dy} ${bx + bw + dx},${by + bh + dy} ${bx + bw},${by + bh}`;
  const bottom = `${bx},${by + bh} ${bx + bw},${by + bh} ${bx + bw + dx},${by + bh + dy} ${bx + dx * 0.28},${by + bh + dy * 0.95}`;

  return { rightSide, bottom, iso, bounds: { bx, by, bw, bh } };
}

export function getBackingIsometricQuad(
  config: VolumetricLetterPreviewConfig,
  offsetX = 0,
  offsetY = 0
) {
  const bounds = getLetterBounds();
  const iso = getIsometricDepthVector(config.returnSide.depthMm ?? 30);
  const inset = ISOMETRIC_VISUAL.backingInset;
  const bx = bounds.x - inset + offsetX;
  const by = bounds.y - inset + offsetY;
  const bw = bounds.width + inset * 2;
  const bh = bounds.height + inset * 2;
  const backDx = iso.dx * 0.95;
  const backDy = iso.dy * 0.95;

  return `${bx + backDx},${by + backDy} ${bx + bw + backDx},${by + backDy} ${bx + bw + backDx},${by + bh + backDy} ${bx + backDx},${by + bh + backDy}`;
}

export type IsometricCalloutSpec = {
  id: string;
  label: string;
  anchorX: number;
  anchorY: number;
  labelX: number;
  labelY: number;
  side: "interior" | "exterior";
};

export function buildIsometricCallouts(
  config: VolumetricLetterPreviewConfig,
  splitX: number
): IsometricCalloutSpec[] {
  const bounds = getLetterBounds();
  const iso = getIsometricDepthVector(config.returnSide.depthMm ?? 30);
  const items: IsometricCalloutSpec[] = [];

  if (config.backing.material || config.backing.thicknessMm) {
    items.push({
      id: "backing",
      label: "Spate",
      anchorX: bounds.x + bounds.width * 0.18,
      anchorY: bounds.y + bounds.height * 0.62,
      labelX: bounds.x - 2,
      labelY: bounds.y + bounds.height * 0.78,
      side: "interior",
    });
  }

  if (config.lighting.enabled) {
    items.push({
      id: "led",
      label: "Module LED",
      anchorX: bounds.x + bounds.width * 0.28,
      anchorY: bounds.y + bounds.height * 0.42,
      labelX: bounds.x + bounds.width * 0.08,
      labelY: bounds.y + bounds.height * 0.28,
      side: "interior",
    });
  }

  if (config.face.material || config.artwork.text || config.artwork.svgPath) {
    items.push({
      id: "face",
      label: "Față acrilic",
      anchorX: splitX + bounds.width * 0.22,
      anchorY: bounds.y + bounds.height * 0.22,
      labelX: splitX + bounds.width * 0.08,
      labelY: bounds.y - 2,
      side: "exterior",
    });
  }

  if (config.returnSide.depthMm || config.returnSide.material) {
    items.push({
      id: "return",
      label: "Cant aluminiu",
      anchorX: bounds.x + bounds.width + iso.dx * 0.42,
      anchorY: bounds.y + bounds.height * 0.38,
      labelX: bounds.x + bounds.width + iso.dx + 4,
      labelY: bounds.y + bounds.height * 0.22,
      side: "exterior",
    });
  }

  return items;
}

export function getLedModuleRenderData(config: VolumetricLetterPreviewConfig) {
  return buildLedModulePlacements(config).map((m) => ({
    ...m,
    dots: [
      { cx: m.x + m.w * 0.28, cy: m.y + m.h * 0.5 },
      { cx: m.x + m.w * 0.5, cy: m.y + m.h * 0.5 },
      { cx: m.x + m.w * 0.72, cy: m.y + m.h * 0.5 },
    ],
  }));
}

export function usesPlaceholderSilhouette(config: VolumetricLetterPreviewConfig): boolean {
  return resolveGeometrySource(config) === "placeholder";
}
