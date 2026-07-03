import type {
  GeometrySource,
  PreviewLayerSpec,
  ReturnDepthMm,
  VolumetricLetterPreviewConfig,
} from "./volumetricLetterPreviewTypes";

export const PREVIEW_VIEWBOX = { width: 120, height: 120 } as const;

export const EXPLODED_LAYOUT = {
  /** Offset between consecutive layers in exploded view (front → back). */
  stepX: 22,
  stepY: 16,
  labelGap: 10,
  pad: 20,
} as const;

export const PREVIEW_COLORS = {
  faceFill: "rgba(96, 165, 250, 0.65)",
  faceStroke: "#60A5FA",
  vinylFill: "rgba(34, 211, 238, 0.32)",
  vinylStroke: "#0891B2",
  returnFill: "#CBD5E1",
  returnStroke: "#94A3B8",
  backingFill: "#334155",
  backingStroke: "#1E293B",
  ledFill: "#FBBF24",
  ledStroke: "#D97706",
  wiringStroke: "#94A3B8",
  spacerFill: "#22C55E",
  spacerStroke: "#15803D",
  supportFill: "#1E293B",
  supportStroke: "#0F172A",
  placeholderFill: "#1E293B",
  placeholderStroke: "#475569",
  returnBottomFill: "#94A3B8",
} as const;

const DEFAULT_LETTER_BOUNDS = { x: 24, y: 20, width: 72, height: 80 };

export function resolveGeometrySource(config: VolumetricLetterPreviewConfig): GeometrySource {
  if (config.artwork.svgPath?.trim()) return "real";
  if (config.artwork.text?.trim()) return "estimated";
  return "placeholder";
}

export function geometrySourceLabel(source: GeometrySource): string {
  switch (source) {
    case "real":
      return "Geometrie SVG importată";
    case "estimated":
      return "Geometrie estimată (text)";
    case "placeholder":
      return "Geometrie placeholder";
  }
}

export function geometrySourceShortLabel(source: GeometrySource): string {
  switch (source) {
    case "real":
      return "SVG";
    case "estimated":
      return "Estimat";
    case "placeholder":
      return "Placeholder";
  }
}

/** LED positions use bounding-box grid when geometry is not imported SVG. */
export function usesEstimatedLedPlacement(config: VolumetricLetterPreviewConfig): boolean {
  return resolveGeometrySource(config) !== "real";
}

function returnDepthStrokeWidth(depthMm?: ReturnDepthMm): number {
  if (!depthMm) return 0;
  return Math.round(4 + ((depthMm - 30) / 70) * 8);
}

function formatReturnFinish(config: VolumetricLetterPreviewConfig): string | undefined {
  const { returnSide } = config;
  if (!returnSide.finishType) return undefined;
  if (returnSide.finishType === "raw_aluminium") return "Aluminiu brut";
  if (returnSide.finishType === "ral") {
    const code = returnSide.ralCode?.trim();
    const name = returnSide.ralName?.trim();
    if (code && name) return `RAL ${code} — ${name}`;
    if (code) return `RAL ${code}`;
    return "RAL";
  }
  if (returnSide.finishType === "oracal") {
    const series = returnSide.oracalSeries?.trim();
    const code = returnSide.oracalCode?.trim();
    const name = returnSide.oracalName?.trim();
    if (series && code && name) return `Oracal ${series}-${code} — ${name}`;
    if (series && code) return `Oracal ${series}-${code}`;
    return "Oracal";
  }
  return undefined;
}

function formatFaceDetail(config: VolumetricLetterPreviewConfig): string | undefined {
  const parts: string[] = [];
  if (config.face.material) parts.push(config.face.material);
  if (config.face.thicknessMm) parts.push(`${config.face.thicknessMm} mm`);
  return parts.length ? parts.join(" · ") : undefined;
}

function formatVinylDetail(config: VolumetricLetterPreviewConfig): string | undefined {
  if (!config.face.hasVinyl) return undefined;
  const series = config.face.vinylSeries?.trim();
  const code = config.face.vinylCode?.trim();
  const name = config.face.vinylName?.trim();
  if (series && code && name) return `${series}-${code} — ${name}`;
  if (series && code) return `${series}-${code}`;
  return "Folie față activă";
}

function formatBackingDetail(config: VolumetricLetterPreviewConfig): string | undefined {
  const parts: string[] = [];
  if (config.backing.material) parts.push(config.backing.material);
  if (config.backing.thicknessMm) parts.push(`${config.backing.thicknessMm} mm`);
  return parts.length ? parts.join(" · ") : undefined;
}

/** Layer stack derived from config — only includes layers that are configured. */
export function buildPreviewLayerStack(
  config: VolumetricLetterPreviewConfig
): PreviewLayerSpec[] {
  const layers: PreviewLayerSpec[] = [];

  if (config.face.material || config.face.thicknessMm || config.artwork.text || config.artwork.svgPath) {
    layers.push({
      id: "face",
      label: "Față plexiglas",
      configured: Boolean(config.face.material || config.face.thicknessMm),
      fill: PREVIEW_COLORS.faceFill,
      stroke: PREVIEW_COLORS.faceStroke,
      detail: formatFaceDetail(config),
    });
  }

  if (config.face.hasVinyl) {
    layers.push({
      id: "vinyl",
      label: "Folie față",
      configured: Boolean(config.face.vinylSeries?.trim() && config.face.vinylCode?.trim()),
      fill: PREVIEW_COLORS.vinylFill,
      stroke: PREVIEW_COLORS.vinylStroke,
      detail: formatVinylDetail(config),
    });
  }

  if (config.returnSide.material || config.returnSide.depthMm) {
    layers.push({
      id: "return",
      label: "Cant / lateral",
      configured: Boolean(config.returnSide.depthMm),
      fill: PREVIEW_COLORS.returnFill,
      stroke: PREVIEW_COLORS.returnStroke,
      detail: [
        config.returnSide.depthMm ? `${config.returnSide.depthMm} mm` : undefined,
        formatReturnFinish(config),
      ]
        .filter(Boolean)
        .join(" · "),
    });
  }

  if (config.backing.material || config.backing.thicknessMm) {
    layers.push({
      id: "backing",
      label: "Spate / backing",
      configured: Boolean(config.backing.material),
      fill: PREVIEW_COLORS.backingFill,
      stroke: PREVIEW_COLORS.backingStroke,
      detail: formatBackingDetail(config),
    });
  }

  if (config.lighting.enabled) {
    layers.push({
      id: "led",
      label: "Module LED",
      configured: Boolean(config.lighting.estimatedModuleCount || config.lighting.ledModuleType),
      fill: PREVIEW_COLORS.ledFill,
      stroke: PREVIEW_COLORS.ledStroke,
      detail: [
        config.lighting.ledModuleType,
        config.lighting.estimatedModuleCount
          ? `${config.lighting.estimatedModuleCount} module`
          : undefined,
        config.lighting.powerSupplyW ? `${config.lighting.powerSupplyW} W PSU` : undefined,
      ]
        .filter(Boolean)
        .join(" · "),
    });

    layers.push({
      id: "wiring",
      label: "Cablare",
      configured: config.lighting.enabled,
      stroke: PREVIEW_COLORS.wiringStroke,
      detail: "Traseu cablare spate",
    });
  }

  if (
    config.mounting.spacerCount ||
    config.mounting.spacerType ||
    config.mounting.directWallMount
  ) {
    layers.push({
      id: "mounting",
      label: "Distanțieri / montaj",
      configured: Boolean(config.mounting.spacerCount || config.mounting.spacerType),
      fill: PREVIEW_COLORS.spacerFill,
      stroke: PREVIEW_COLORS.spacerStroke,
      detail: [
        config.mounting.spacerType,
        config.mounting.spacerCount ? `${config.mounting.spacerCount} buc` : undefined,
        config.mounting.directWallMount ? "Montaj direct perete" : undefined,
      ]
        .filter(Boolean)
        .join(" · "),
    });
  }

  if (config.mounting.supportPanel) {
    layers.push({
      id: "support",
      label: "Panou suport",
      configured: true,
      fill: PREVIEW_COLORS.supportFill,
      stroke: PREVIEW_COLORS.supportStroke,
      detail: "Suport / cadru configurat",
    });
  }

  return layers;
}

export function getLetterBounds() {
  return { ...DEFAULT_LETTER_BOUNDS };
}

export function getReturnBandOffset(config: VolumetricLetterPreviewConfig): number {
  return returnDepthStrokeWidth(config.returnSide.depthMm);
}

/** Schematic isometric extrusion vector from return depth (channel-letter 3/4 view). */
export function getIsometricDepthVector(depthMm?: ReturnDepthMm): {
  dx: number;
  dy: number;
  depth: number;
} {
  const depth = depthMm ? Math.round(16 + ((depthMm - 30) / 70) * 24) : 16;
  return { dx: depth * 0.92, dy: depth * 0.54, depth };
}

export function getCompactSplitPlaneX(): number {
  const bounds = getLetterBounds();
  return bounds.x + bounds.width * 0.48;
}

export function computeCompactViewBox(config: VolumetricLetterPreviewConfig) {
  const bounds = getLetterBounds();
  const iso = getIsometricDepthVector(config.returnSide.depthMm);
  return {
    width: Math.ceil(bounds.x + bounds.width + iso.dx + 26),
    height: Math.ceil(bounds.y + bounds.height + iso.dy + 16),
  };
}

export type LedModulePlacement = { x: number; y: number; w: number; h: number };

/** Distributes LED module rectangles inside letter bounds from config count. */
export function buildLedModulePlacements(config: VolumetricLetterPreviewConfig): LedModulePlacement[] {
  if (!config.lighting.enabled) return [];

  const count = Math.max(1, Math.min(config.lighting.estimatedModuleCount ?? 4, 12));
  const { x, y, width, height } = DEFAULT_LETTER_BOUNDS;
  const cols = count <= 4 ? 2 : count <= 6 ? 3 : 4;
  const rows = Math.ceil(count / cols);
  const padX = 8;
  const padY = 10;
  const cellW = (width - padX * 2) / cols;
  const cellH = (height - padY * 2) / rows;
  const modW = Math.min(14, cellW * 0.55);
  const modH = Math.min(8, cellH * 0.45);

  const placements: LedModulePlacement[] = [];
  for (let i = 0; i < count; i += 1) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    placements.push({
      x: x + padX + col * cellW + (cellW - modW) / 2,
      y: y + padY + row * cellH + (cellH - modH) / 2,
      w: modW,
      h: modH,
    });
  }
  return placements;
}

export type SpacerPlacement = { cx: number; cy: number; r: number };

export function buildSpacerPlacements(config: VolumetricLetterPreviewConfig): SpacerPlacement[] {
  const count = config.mounting.spacerCount ?? 0;
  if (count <= 0) return [];

  const { x, y, width, height } = DEFAULT_LETTER_BOUNDS;
  const anchors = [
    { cx: x + 10, cy: y + 10 },
    { cx: x + width - 10, cy: y + 10 },
    { cx: x + 10, cy: y + height - 10 },
    { cx: x + width - 10, cy: y + height - 10 },
    { cx: x + width / 2, cy: y + height / 2 },
  ];
  return anchors.slice(0, Math.min(count, anchors.length)).map((a) => ({ ...a, r: 4 }));
}

export function buildMaterialBadges(config: VolumetricLetterPreviewConfig): string[] {
  const badges: string[] = [];
  if (config.face.material) badges.push(`Față: ${config.face.material}`);
  if (config.face.hasVinyl) badges.push("Folie față");
  if (config.returnSide.depthMm) badges.push(`Cant ${config.returnSide.depthMm} mm`);
  if (config.backing.material) badges.push(`Backing: ${config.backing.material}`);
  if (config.lighting.enabled) badges.push("LED");
  return badges;
}

/** Exploded offset per layer index (front → back). */
export function explodedLayerOffset(layerIndex: number): { dx: number; dy: number } {
  return {
    dx: layerIndex * EXPLODED_LAYOUT.stepX,
    dy: layerIndex * EXPLODED_LAYOUT.stepY,
  };
}

export function getLayerBoundsWithOffset(offsetX: number, offsetY: number) {
  const bounds = getLetterBounds();
  const returnPad = 12;
  return {
    x: bounds.x + offsetX,
    y: bounds.y + offsetY,
    width: bounds.width + returnPad,
    height: bounds.height + returnPad,
    cx: bounds.x + bounds.width / 2 + offsetX,
    cy: bounds.y + bounds.height / 2 + offsetY,
  };
}

export function computeExpandedViewBox(layerCount: number) {
  const bounds = getLetterBounds();
  const spread = Math.max(0, layerCount - 1);
  const stackW = bounds.width + spread * EXPLODED_LAYOUT.stepX + 16;
  const stackH = bounds.height + spread * EXPLODED_LAYOUT.stepY + 16;
  const labelColumn = 92;
  return {
    width: EXPLODED_LAYOUT.pad * 2 + stackW + labelColumn,
    height: EXPLODED_LAYOUT.pad * 2 + stackH + 8,
  };
}
