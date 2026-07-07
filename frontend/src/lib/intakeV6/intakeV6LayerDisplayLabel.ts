import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { buildOperatorLogoLabelMap, getOperatorLayerLabel, isPositionalLogoLayer } from "./intakeV4OperatorUiDisplay";

const VISUAL_COLOR_LABELS: Record<string, string> = {
  "#00a0e3": "albastru",
  "#00a0e3ff": "albastru",
  "#e31e24": "roșu",
  "#009846": "verde",
  "#ef7f1a": "portocaliu",
  "#2b2a29": "negru",
};

function normalizeDetectedName(name: string): string {
  return name.replace(/^pseudo[:\s-]+/i, "").replace(/\s*\(([^)]+)\)\s*$/, "").trim();
}

function resolveColorToken(layer: SvgAnalysisCoreReport["layers"][number]): string | undefined {
  return layer.colors?.[0] ?? layer.paintEvidence.fills[0] ?? layer.paintEvidence.strokes[0];
}

function resolveVisualColorLabel(colorToken: string | undefined): string | null {
  const normalized = colorToken?.trim().toLowerCase() ?? "";
  return normalized ? VISUAL_COLOR_LABELS[normalized] ?? normalized : null;
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
  if (shouldUseContourLabel(layer)) {
    return `Layer ${index + 1} — ${colorLabel ? `contur ${colorLabel}${artworkSuffix}` : `contur${artworkSuffix}`}`;
  }
  if (colorLabel) return `Layer ${index + 1} — ${colorLabel}`;
  if (layer.paintEvidence.paintKind === "solid") return `Layer ${index + 1} — culoare solidă`;
  return `Layer ${index + 1} — ${layer.paintEvidence.paintKind ?? "—"}`;
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
    return {
      primaryLabel: buildPrimaryLabel(layer, index),
      secondaryLabel: `Nume layer fișier: ${neutralLogoLabel ?? layer.name}`,
      sourceLabel: null,
      technicalKey: layer.id ?? layer.name,
    };
  }

  return {
    primaryLabel: buildPrimaryLabel(layer, index),
    secondaryLabel: neutralLogoLabel
      ? `Grup detectat: ${neutralLogoLabel}`
      : normalizedName
        ? `Grup detectat: ${normalizedName}`
        : "Grup generat automat",
    sourceLabel: resolvedSourceLayerName ? `Layer sursa: ${resolvedSourceLayerName}` : null,
    technicalKey: layer.id ?? layer.name,
  };
}

export function stripIntakeV6PseudoDisplayLabel(name: string): string {
  return normalizeDetectedName(name);
}