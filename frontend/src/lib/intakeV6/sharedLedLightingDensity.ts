/** Shared LED area rules for emblem / lightbox / area-lit surfaces. */

export const LED_AREA_MODULE_LENGTH_MM = 75;
export const LED_AREA_MODULE_WIDTH_MM = 15;
export const LED_AREA_MODULE_INLINE_GAP_MM = 40;
export const LED_AREA_MODULE_ROW_GAP_MM = 80;
export const LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM = 70;
export const LED_AREA_MODULE_BASE_DEPTH_MM = 60;
export const LED_AREA_MODULE_DEPTH_STEP_MM = 20;
export const LED_AREA_MODULE_GAP_STEP_MM = 20;

export const LED_AREA_MODULE_PITCH_X_MM =
  LED_AREA_MODULE_LENGTH_MM + LED_AREA_MODULE_INLINE_GAP_MM;
export const LED_AREA_MODULE_PITCH_Y_MM =
  LED_AREA_MODULE_WIDTH_MM + LED_AREA_MODULE_ROW_GAP_MM;

export const LED_AREA_REFERENCE_WIDTH_MM = 1000;
export const LED_AREA_REFERENCE_HEIGHT_MM = 1000;

export interface LedAreaLitBox {
  width_mm?: number | null;
  height_mm?: number | null;
  area_m2?: number | null;
  depth_mm?: number | null;
}

export interface LedAreaModuleLayoutRule {
  depthMm: number;
  inlineGapMm: number;
  rowGapMm: number;
  pitchXmm: number;
  pitchYmm: number;
}

export function resolveLedAreaModuleLayoutRule(
  depthMm: number | null | undefined,
): LedAreaModuleLayoutRule {
  const normalizedDepth =
    depthMm != null && Number.isFinite(depthMm) && depthMm > 0
      ? Math.max(LED_AREA_MODULE_BASE_DEPTH_MM, depthMm)
      : LED_AREA_MODULE_BASE_DEPTH_MM;
  const depthSteps = Math.max(
    0,
    Math.floor((normalizedDepth - LED_AREA_MODULE_BASE_DEPTH_MM) / LED_AREA_MODULE_DEPTH_STEP_MM),
  );
  const gapIncreaseMm = depthSteps * LED_AREA_MODULE_GAP_STEP_MM;
  const inlineGapMm = LED_AREA_MODULE_INLINE_GAP_MM + gapIncreaseMm;
  const rowGapMm = LED_AREA_MODULE_ROW_GAP_MM + gapIncreaseMm;
  return {
    depthMm: LED_AREA_MODULE_BASE_DEPTH_MM + depthSteps * LED_AREA_MODULE_DEPTH_STEP_MM,
    inlineGapMm,
    rowGapMm,
    pitchXmm: LED_AREA_MODULE_LENGTH_MM + inlineGapMm,
    pitchYmm: LED_AREA_MODULE_WIDTH_MM + rowGapMm,
  };
}

function countAxisModulesForMaxEdgeDistance(
  spanMm: number | null | undefined,
  moduleMm: number,
  gapMm: number,
  maxEdgeDistanceMm: number,
): number | null {
  if (spanMm == null || !Number.isFinite(spanMm) || spanMm <= 0) return null;
  const pitchMm = moduleMm + gapMm;
  const uncoveredSpanMm = spanMm - 2 * maxEdgeDistanceMm + gapMm;
  return Math.max(1, Math.ceil(uncoveredSpanMm / pitchMm));
}

export function calculateLedModuleGridForAreaLitBox(args: {
  widthMm: number | null | undefined;
  heightMm: number | null | undefined;
  depthMm?: number | null | undefined;
}): { columns: number; rows: number; modules: number } | null {
  const layout = resolveLedAreaModuleLayoutRule(args.depthMm);
  const columns = countAxisModulesForMaxEdgeDistance(
    args.widthMm,
    LED_AREA_MODULE_LENGTH_MM,
    layout.inlineGapMm,
    LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM,
  );
  const rows = countAxisModulesForMaxEdgeDistance(
    args.heightMm,
    LED_AREA_MODULE_WIDTH_MM,
    layout.rowGapMm,
    LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM,
  );
  if (columns == null || rows == null) return null;
  return { columns, rows, modules: columns * rows };
}

const LED_AREA_REFERENCE_GRID = calculateLedModuleGridForAreaLitBox({
  widthMm: LED_AREA_REFERENCE_WIDTH_MM,
  heightMm: LED_AREA_REFERENCE_HEIGHT_MM,
  depthMm: LED_AREA_MODULE_BASE_DEPTH_MM,
});

export const LED_AREA_DENSITY_MODULES_PER_SQM =
  (LED_AREA_REFERENCE_GRID?.modules ?? 80) /
  ((LED_AREA_REFERENCE_WIDTH_MM * LED_AREA_REFERENCE_HEIGHT_MM) / 1_000_000);

export function ledAreaDensityModulesPerSqm(depthMm?: number | null): number {
  const grid = calculateLedModuleGridForAreaLitBox({
    widthMm: LED_AREA_REFERENCE_WIDTH_MM,
    heightMm: LED_AREA_REFERENCE_HEIGHT_MM,
    depthMm,
  });
  return (
    (grid?.modules ?? LED_AREA_DENSITY_MODULES_PER_SQM) /
    ((LED_AREA_REFERENCE_WIDTH_MM * LED_AREA_REFERENCE_HEIGHT_MM) / 1_000_000)
  );
}

export function formatLedAreaDensity(value = LED_AREA_DENSITY_MODULES_PER_SQM): string {
  return `${value.toFixed(1)} module/m2`;
}

export function ledAreaLayoutRuleLabel(depthMm?: number | null): string {
  const layout = resolveLedAreaModuleLayoutRule(depthMm);
  return `Module ${LED_AREA_MODULE_LENGTH_MM}x${LED_AREA_MODULE_WIDTH_MM} mm, volum ${layout.depthMm} mm: gol ${layout.inlineGapMm} mm pe linie si ${layout.rowGapMm} mm pe coloana, margine max. ${LED_AREA_MODULE_MAX_EDGE_DISTANCE_MM} mm`;
}

export function calculateLedModulesByArea(
  areaSqm: number | null | undefined,
  depthMm?: number | null,
): number | null {
  if (areaSqm == null || !Number.isFinite(areaSqm) || areaSqm <= 0) return 0;
  return Math.ceil(areaSqm * ledAreaDensityModulesPerSqm(depthMm));
}

export function calculateLedModulesForAreaLitBoxes(
  boxes: LedAreaLitBox[] | null | undefined,
  fallbackAreaSqm?: number | null,
  depthMm?: number | null,
): number | null {
  if (Array.isArray(boxes) && boxes.length > 0) {
    let total = 0;
    let usedAny = false;
    for (const box of boxes) {
      const grid = calculateLedModuleGridForAreaLitBox({
        widthMm: box.width_mm,
        heightMm: box.height_mm,
        depthMm: box.depth_mm ?? depthMm,
      });
      if (grid) {
        total += grid.modules;
        usedAny = true;
        continue;
      }
      const fallback = calculateLedModulesByArea(box.area_m2, box.depth_mm ?? depthMm);
      if (fallback != null) {
        total += fallback;
        usedAny = true;
      }
    }
    if (usedAny) return total;
  }
  return calculateLedModulesByArea(fallbackAreaSqm, depthMm);
}

export const LED_STRIP_AREA_ROW_SPACING_MM = 40;
export const LED_STRIP_AREA_LENGTH_M_PER_SQM = 1000 / LED_STRIP_AREA_ROW_SPACING_MM;

export function calculateLedStripLengthByArea(areaSqm: number | null | undefined): number | null {
  if (areaSqm == null || !Number.isFinite(areaSqm) || areaSqm <= 0) return 0;
  return Math.round(areaSqm * LED_STRIP_AREA_LENGTH_M_PER_SQM * 1000) / 1000;
}

export function ledStripAreaLayoutRuleLabel(): string {
  return `Banda LED continua, randuri la ${LED_STRIP_AREA_ROW_SPACING_MM} mm (${LED_STRIP_AREA_LENGTH_M_PER_SQM.toFixed(1)} ml/m2)`;
}
