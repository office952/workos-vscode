/**
 * Shared AcmPanel assembly extent contract (mm).
 * Explicit keys: assembly_width_mm / assembly_height_mm — never overload panel_*.
 * Mirror: backend/services/acm_assembly_extent.py
 */

export const ASSEMBLY_DIMENSION_TOLERANCE_MM = 1;

export type AcmAssemblyExtentSource =
  | "panel_extent"
  | "assembly_dimensions"
  | "single_panel"
  | "envelope"
  | "none";

export type AcmAssemblyPanelInput = {
  width_mm: number | null | undefined;
  height_mm: number | null | undefined;
  x_mm?: number | null;
  y_mm?: number | null;
  position?: { x_mm?: number | null; y_mm?: number | null } | null;
};

export type AcmAssemblyExtentResult = {
  assembly_width_mm: number | null;
  assembly_height_mm: number | null;
  source: AcmAssemblyExtentSource;
  warnings: string[];
  /** True when multi-panel and envelope differs from assembly (consumer must not use envelope as overall). */
  envelope_ignored_for_multi_panel: boolean;
};

function num(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim() !== "") {
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function formatMm(value: number): string {
  return Number.isInteger(value) ? String(value) : String(Math.round(value * 10) / 10);
}

function panelXY(p: AcmAssemblyPanelInput): { x: number; y: number } {
  return {
    x: num(p.position?.x_mm) ?? num(p.x_mm) ?? 0,
    y: num(p.position?.y_mm) ?? num(p.y_mm) ?? 0,
  };
}

function panelHasExplicitPosition(p: AcmAssemblyPanelInput): boolean {
  if (num(p.position?.x_mm) != null || num(p.position?.y_mm) != null) return true;
  if (num(p.x_mm) != null || num(p.y_mm) != null) return true;
  return false;
}

function panelExtent(
  panels: Array<{ x: number; y: number; w: number; h: number }>,
): { width: number; height: number } | null {
  if (!panels.length) return null;
  let minX = Infinity;
  let maxX = -Infinity;
  let minY = Infinity;
  let maxY = -Infinity;
  for (const p of panels) {
    minX = Math.min(minX, p.x);
    maxX = Math.max(maxX, p.x + p.w);
    minY = Math.min(minY, p.y);
    maxY = Math.max(maxY, p.y + p.h);
  }
  const width = maxX - minX;
  const height = maxY - minY;
  if (!(width > 0) || !(height > 0)) return null;
  return { width, height };
}

/**
 * Compute assembly_width_mm / assembly_height_mm from panels + optional assembly_dimensions.
 * Multi-panel: never use single-contour envelope as overall.
 */
export function computeAcmAssemblyExtent(args: {
  panels?: AcmAssemblyPanelInput[] | null;
  assembly_dimensions?: { width_mm?: number | null; height_mm?: number | null } | null;
  /** Contour / primary envelope — only used for warning when multi-panel. */
  envelope_width_mm?: number | null;
  envelope_height_mm?: number | null;
}): AcmAssemblyExtentResult {
  const warnings: string[] = [];
  const valid: Array<{ x: number; y: number; w: number; h: number }> = [];
  let positionedCount = 0;

  for (const raw of args.panels ?? []) {
    const w = num(raw.width_mm);
    const h = num(raw.height_mm);
    if (w == null || h == null || !(w > 0) || !(h > 0)) continue;
    if (panelHasExplicitPosition(raw)) positionedCount += 1;
    const { x, y } = panelXY(raw);
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    valid.push({ x, y, w, h });
  }

  const asmW = num(args.assembly_dimensions?.width_mm);
  const asmH = num(args.assembly_dimensions?.height_mm);

  if (!valid.length) {
    if (asmW != null && asmH != null && asmW > 0 && asmH > 0) {
      return {
        assembly_width_mm: asmW,
        assembly_height_mm: asmH,
        source: "assembly_dimensions",
        warnings,
        envelope_ignored_for_multi_panel: false,
      };
    }
    // Single-panel / panel-alone: geometry W×H when panels[] empty (legacy / unsynced).
    const envW = num(args.envelope_width_mm);
    const envH = num(args.envelope_height_mm);
    if (envW != null && envH != null && envW > 0 && envH > 0) {
      return {
        assembly_width_mm: envW,
        assembly_height_mm: envH,
        source: "envelope",
        warnings,
        envelope_ignored_for_multi_panel: false,
      };
    }
    return {
      assembly_width_mm: null,
      assembly_height_mm: null,
      source: "none",
      warnings,
      envelope_ignored_for_multi_panel: false,
    };
  }

  const extent = panelExtent(valid);
  if (!extent) {
    return {
      assembly_width_mm: null,
      assembly_height_mm: null,
      source: "none",
      warnings: ["Geometrie panouri insuficientă pentru assembly extent."],
      envelope_ignored_for_multi_panel: false,
    };
  }

  let assemblyWidth = extent.width;
  let assemblyHeight = extent.height;
  let source: AcmAssemblyExtentSource =
    valid.length > 1 ? "panel_extent" : "single_panel";

  const positionsUnreliable = valid.length > 1 && positionedCount < 2;
  if (
    positionsUnreliable &&
    asmW != null &&
    asmH != null &&
    asmW > 0 &&
    asmH > 0
  ) {
    warnings.push(
      "Poziții panouri lipsă/incomplete — folosesc assembly_dimensions pentru ansamblu.",
    );
    assemblyWidth = asmW;
    assemblyHeight = asmH;
    source = "assembly_dimensions";
  } else if (valid.length > 1) {
    if (asmW != null && asmH != null && asmW > 0 && asmH > 0) {
      const dw = Math.abs(asmW - extent.width);
      const dh = Math.abs(asmH - extent.height);
      if (
        dw <= ASSEMBLY_DIMENSION_TOLERANCE_MM &&
        dh <= ASSEMBLY_DIMENSION_TOLERANCE_MM
      ) {
        assemblyWidth = asmW;
        assemblyHeight = asmH;
        source = "assembly_dimensions";
      } else {
        warnings.push(
          `assembly_dimensions (${formatMm(asmW)}×${formatMm(asmH)}) diferă de extent panouri (${formatMm(extent.width)}×${formatMm(extent.height)}) — folosesc extent panouri.`,
        );
        source = "panel_extent";
      }
    }
  } else {
    const only = valid[0]!;
    if (asmW != null && asmH != null && asmW > 0 && asmH > 0) {
      const dw = Math.abs(asmW - only.w);
      const dh = Math.abs(asmH - only.h);
      if (
        dw <= ASSEMBLY_DIMENSION_TOLERANCE_MM &&
        dh <= ASSEMBLY_DIMENSION_TOLERANCE_MM
      ) {
        assemblyWidth = asmW;
        assemblyHeight = asmH;
        source = "assembly_dimensions";
      } else {
        assemblyWidth = only.w;
        assemblyHeight = only.h;
        source = "single_panel";
      }
    } else {
      assemblyWidth = only.w;
      assemblyHeight = only.h;
      source = "single_panel";
    }
  }

  let envelopeIgnored = false;
  const envelopeW = num(args.envelope_width_mm);
  const envelopeH = num(args.envelope_height_mm);
  if (
    valid.length > 1 &&
    envelopeW != null &&
    Math.abs(envelopeW - assemblyWidth) > ASSEMBLY_DIMENSION_TOLERANCE_MM
  ) {
    envelopeIgnored = true;
    warnings.push(
      `Envelope contour (${formatMm(envelopeW)}×${formatMm(envelopeH ?? 0)}) nu este overall assembly — ignorat pentru ansamblu.`,
    );
  }

  return {
    assembly_width_mm: assemblyWidth,
    assembly_height_mm: assemblyHeight,
    source,
    warnings,
    envelope_ignored_for_multi_panel: envelopeIgnored,
  };
}
