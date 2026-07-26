import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { buildOperatorLogoLabelMap, getOperatorLayerLabel, isPositionalLogoLayer } from "@/lib/intakeV6/intakeV4OperatorUiDisplay";

const KNOWN_FILL_LABELS: Record<string, string> = {
  "#009846": "Verde · ANA",
  "#00a0e3": "Albastru · MARIA",
  "#00a0e3ff": "Albastru · MARIA",
  "#e31e24": "Roșu · SOARE",
  "#ef7f1a": "Portocaliu · GRADINITA",
  "#2b2a29": "Stroke decorativ",
};

export function normalizeHexColor(value: string): string {
  return value.trim().toLowerCase();
}

function pseudoLabelFromLayerName(name: string): string | null {
  const trimmed = name.trim();
  if (!trimmed) return null;
  const pseudoMatch = /^pseudo\s+(.+?)(?:\s*\([^)]+\))?$/i.exec(trimmed);
  if (pseudoMatch?.[1]) {
    return pseudoMatch[1].replace(/\s*\([^)]+\)$/i, "").trim();
  }
  if (/^layer_x0020/i.test(trimmed)) return null;
  return trimmed;
}

export function resolveLayerColorHumanLabel(
  color: string,
  report?: SvgAnalysisCoreReport | null,
): string {
  const norm = normalizeHexColor(color);
  if (!norm) return "Culoare necunoscută";

  if (report) {
    const logoLabelMap = buildOperatorLogoLabelMap(report.layers);
    for (const layer of report.layers) {
      const matches = (layer.colors ?? []).some((value) => normalizeHexColor(value) === norm);
      if (!matches) continue;
      if (isPositionalLogoLayer(layer.id, layer.name)) {
        return getOperatorLayerLabel(layer.id, layer.name, { logoLabelMap });
      }
      const fromName = pseudoLabelFromLayerName(layer.name);
      if (fromName) return fromName;
    }
  }

  return KNOWN_FILL_LABELS[norm] ?? KNOWN_FILL_LABELS[color] ?? color;
}
