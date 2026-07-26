import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { buildOperatorLogoLabelMap, getOperatorLayerLabel, isPositionalLogoLayer } from "./intakeV4OperatorUiDisplay";

const VISUAL_COLOR_LABELS: Record<string, string> = {
  "#00a0e3": "albastru",
  "#00a0e3ff": "albastru",
  "#e31e24": "roșu",
  "#009846": "verde",
  "#ef7f1a": "portocaliu",
  "#2b2a29": "negru",
  "#c5c6c6": "gri",
  "#c5c6c6ff": "gri",
  "#64748b": "gri",
  "#64748bff": "gri",
};

function normalizeDetectedName(name: string): string {
  return name.replace(/^pseudo[:\s-]+/i, "").replace(/\s*\(([^)]+)\)\s*$/, "").trim();
}

/** True when the analyzer name/id is a fill-hex pseudo token (not a human letter/logo name). */
export function isPseudoFillToken(value: string | null | undefined): boolean {
  const raw = String(value ?? "").trim();
  if (!raw) return false;
  if (/^pseudo[:\s-]*fill[-_]?[0-9a-f]{3,8}$/i.test(raw)) return true;
  if (/^fill[-_]?[0-9a-f]{3,8}$/i.test(raw)) return true;
  if (/^pseudo:fill-/i.test(raw)) return true;
  return false;
}

function resolveColorToken(layer: SvgAnalysisCoreReport["layers"][number]): string | undefined {
  return layer.colors?.[0] ?? layer.paintEvidence.fills[0] ?? layer.paintEvidence.strokes[0];
}

function resolveVisualColorLabel(colorToken: string | undefined): string | null {
  const normalized = colorToken?.trim().toLowerCase() ?? "";
  if (!normalized) return null;
  if (VISUAL_COLOR_LABELS[normalized]) return VISUAL_COLOR_LABELS[normalized];
  // Do not leak raw hex into primary UI.
  if (/^#?[0-9a-f]{3,8}$/i.test(normalized.replace(/^#/, "#") === normalized ? normalized : `#${normalized}`)) {
    return null;
  }
  if (/^#[0-9a-f]{3,8}$/i.test(normalized) || /^[0-9a-f]{3,8}$/i.test(normalized)) {
    return null;
  }
  return null;
}

function shouldUseContourLabel(layer: SvgAnalysisCoreReport["layers"][number]): boolean {
  if (layer.paintEvidence.paintKind === "none") return true;
  if (layer.paintEvidence.fills.length === 0 && layer.paintEvidence.strokes.length > 0) return true;
  if (layer.layerOrigin === "stroke_vector_outline") return true;
  return false;
}

function buildPrimaryLabel(layer: SvgAnalysisCoreReport["layers"][number], index: number): string {
  const colorLabel = resolveVisualColorLabel(resolveColorToken(layer));
  const artworkSuffix = layer.autoRole === "printed_artwork" || layer.autoRole === "logo" ? " / artwork" : "";
  const n = index + 1;
  if (shouldUseContourLabel(layer)) {
    return `Element ${n} — ${colorLabel ? `contur ${colorLabel}${artworkSuffix}` : `contur${artworkSuffix}`}`;
  }
  if (colorLabel) return `Element ${n} — ${colorLabel}`;
  if (layer.paintEvidence.paintKind === "solid") return `Element ${n} — formă grafică`;
  if (isPseudoFillToken(layer.id) || isPseudoFillToken(layer.name)) {
    return `Element ${n} — formă grafică detectată`;
  }
  return `Element ${n} — ${layer.paintEvidence.paintKind ?? "detectat"}`;
}

function resolveSourceLayerName(
  layer: SvgAnalysisCoreReport["layers"][number],
  report: SvgAnalysisCoreReport | undefined,
  sourceLayerName: string | null | undefined,
): string | null {
  if (!report || layer.layerKind === "real") return null;
  if (sourceLayerName?.trim()) return sourceLayerName.trim();
  const nativeLayers = report.layers.filter((item) => item.layerKind === "real");
  if (nativeLayers.length !== 1) return null;
  return nativeLayers[0].name;
}

function readStringField(record: Record<string, unknown>, key: string): string | null {
  const value = record[key];
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function readFirstLayerName(rows: unknown): string | null {
  if (!Array.isArray(rows)) return null;
  for (const row of rows) {
    if (row == null || typeof row !== "object" || Array.isArray(row)) continue;
    const record = row as Record<string, unknown>;
    return (
      readStringField(record, "layer_name") ??
      readStringField(record, "layer_key") ??
      readStringField(record, "display_name") ??
      readStringField(record, "layer_id")
    );
  }
  return null;
}

export function resolveIntakeV6SourceLayerNameFromPayload(
  payload: Record<string, unknown> | null | undefined,
): string | null {
  const raw = payload?.path_geometry_summary;
  if (raw == null || typeof raw !== "object" || Array.isArray(raw)) return null;
  const summary = raw as Record<string, unknown>;
  return readFirstLayerName(summary.drawable_layers) ?? readFirstLayerName(summary.layers);
}

function operatorSecondaryForPseudo(
  layer: SvgAnalysisCoreReport["layers"][number],
  normalizedName: string,
  neutralLogoLabel: string | null,
): string {
  if (neutralLogoLabel) return `Grup detectat: ${neutralLogoLabel}`;
  if (isPseudoFillToken(layer.id) || isPseudoFillToken(layer.name) || isPseudoFillToken(normalizedName)) {
    return "Grup culoare detectat — selectează rolul corect";
  }
  if (normalizedName) return `Grup detectat: ${normalizedName}`;
  return "Grup generat automat — selectează rolul corect";
}

export function buildIntakeV6LayerDisplayLabel(
  layer: SvgAnalysisCoreReport["layers"][number],
  index: number,
  report?: SvgAnalysisCoreReport,
  sourceLayerName?: string | null,
): {
  primaryLabel: string;
  secondaryLabel: string;
  sourceLabel: string | null;
  technicalKey: string;
} {
  const normalizedName = normalizeDetectedName(layer.name ?? "");
  const resolvedSourceLayerName = resolveSourceLayerName(layer, report, sourceLayerName);
  const logoLabelMap = report ? buildOperatorLogoLabelMap(report.layers) : undefined;
  const neutralLogoLabel = isPositionalLogoLayer(layer.id, layer.name)
    ? getOperatorLayerLabel(layer.id, layer.name, { logoLabelMap })
    : null;

  if (layer.layerKind === "real") {
    const fileName = neutralLogoLabel ?? layer.name;
    const showFileName =
      fileName &&
      !isPseudoFillToken(fileName) &&
      !/^layer[_x0]/i.test(String(fileName));
    return {
      primaryLabel: buildPrimaryLabel(layer, index),
      secondaryLabel: showFileName
        ? `Nume layer fișier: ${fileName}`
        : "Strat din fișier — selectează rolul corect",
      sourceLabel: null,
      technicalKey: layer.id ?? layer.name,
    };
  }

  return {
    primaryLabel: buildPrimaryLabel(layer, index),
    secondaryLabel: operatorSecondaryForPseudo(layer, normalizedName, neutralLogoLabel),
    sourceLabel: resolvedSourceLayerName ? `Layer sursă: ${resolvedSourceLayerName}` : null,
    technicalKey: layer.id ?? layer.name,
  };
}

export function stripIntakeV6PseudoDisplayLabel(name: string): string {
  return normalizeDetectedName(name);
}

/** Operator-safe label for any layout (cards, legend, table, composition). */
export function resolveIntakeV6OperatorLayerTitle(
  layer: SvgAnalysisCoreReport["layers"][number],
  index: number,
  report: SvgAnalysisCoreReport,
): string {
  return buildIntakeV6LayerDisplayLabel(layer, index, report).primaryLabel;
}

export type IntakeV6StoredLayerDisplayRef = {
  layerKey?: string | null;
  layerName?: string | null;
  /** 0-based operator index for Element N fallbacks */
  index?: number;
  report?: SvgAnalysisCoreReport | null;
  sourceFillColor?: string | null;
};

function findLayerInReport(
  report: SvgAnalysisCoreReport,
  layerKey: string,
  layerName: string,
): SvgAnalysisCoreReport["layers"][number] | null {
  const key = layerKey.trim().toLowerCase();
  const name = layerName.trim().toLowerCase();
  if (!key && !name) return null;
  return (
    report.layers.find((layer) => {
      const id = String(layer.id ?? "").trim().toLowerCase();
      const ln = String(layer.name ?? "").trim().toLowerCase();
      return (key && (id === key || ln === key)) || (name && (id === name || ln === name));
    }) ?? null
  );
}

function extractFillTokenSuffix(value: string): string | null {
  const match = value.trim().match(/fill[-_]?([0-9a-f]{1,8})/i);
  return match?.[1] ?? null;
}

function looksLikeInternalPathToken(value: string): boolean {
  const v = value.trim();
  if (!v) return false;
  if (/^GROUP[_-]/i.test(v)) return true;
  if (/^PATH[_-]/i.test(v)) return true;
  if (/^[A-Z][A-Z0-9_]{3,}$/.test(v) && v.includes("_")) return true;
  return false;
}

/**
 * Single presentation adapter for stored letter/artwork refs (Finisaje, Confirmare, Review).
 * Does not mutate analyzer truth or persisted layer_name — render-time only.
 */
export function resolveIntakeV6StoredLayerDisplayLabel(ref: IntakeV6StoredLayerDisplayRef): string {
  const layerKey = String(ref.layerKey ?? "").trim();
  const layerName = String(ref.layerName ?? "").trim();
  const index = Math.max(0, ref.index ?? 0);
  const n = index + 1;

  if (ref.report) {
    const layer = findLayerInReport(ref.report, layerKey || layerName, layerName || layerKey);
    if (layer) {
      const reportIndex = Math.max(0, ref.report.layers.indexOf(layer));
      return buildIntakeV6LayerDisplayLabel(layer, ref.index ?? reportIndex, ref.report).primaryLabel;
    }
  }

  const raw = layerName || layerKey;
  if (!raw) return "Element grafic fără rol confirmat";

  if (isPseudoFillToken(layerName) || isPseudoFillToken(layerKey) || isPseudoFillToken(raw)) {
    const color =
      resolveVisualColorLabel(ref.sourceFillColor ?? undefined) ??
      resolveVisualColorLabel(
        (() => {
          const suffix = extractFillTokenSuffix(raw);
          if (!suffix || suffix.length < 3) return undefined;
          return `#${suffix}`;
        })(),
      );
    if (color) return `Element ${n} — ${color}`;
    const suffix = extractFillTokenSuffix(raw);
    if (suffix && /^\d{1,3}$/.test(suffix)) return `Element grafic ${suffix}`;
    return `Element ${n} — formă grafică detectată`;
  }

  if (/^layer[_x0]/i.test(layerName) || /^layer[_x0]/i.test(layerKey)) {
    return `Element ${n} — detectat`;
  }

  if (looksLikeInternalPathToken(layerName) || looksLikeInternalPathToken(layerKey)) {
    return "Element personalizat";
  }

  const op = getOperatorLayerLabel(layerKey || raw, layerName || raw);
  if (op && !isPseudoFillToken(op) && !/^artwork layer$/i.test(op) && !/pseudo|fill-/i.test(op)) {
    return op;
  }

  const stripped = normalizeDetectedName(raw);
  if (!stripped || /pseudo|fill-/i.test(stripped) || looksLikeInternalPathToken(stripped)) {
    return "Element grafic fără rol confirmat";
  }
  if (/^#?[0-9a-f]{3,8}$/i.test(stripped)) {
    return "Element grafic fără rol confirmat";
  }
  return stripped;
}

/** Letter-group convenience wrapper — same single display path. */
export function resolveIntakeV6LetterGroupDisplayLabel(
  group: {
    group_key?: string | null;
    layer_name?: string | null;
    source_fill_color?: string | null;
  },
  index: number,
  report?: SvgAnalysisCoreReport | null,
): string {
  return resolveIntakeV6StoredLayerDisplayLabel({
    layerKey: group.group_key,
    layerName: group.layer_name,
    index,
    report,
    sourceFillColor: group.source_fill_color,
  });
}
