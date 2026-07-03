import type { CSSProperties } from "react";
import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { resolveLayerColorHumanLabel } from "./layerColorDisplay";
import { v6 } from "./atoms/intakeV6Presentation";

function normalizeColorToken(value: string): string {
  const trimmed = value.trim();
  if (/^#[0-9a-f]{3,8}$/i.test(trimmed)) return trimmed;
  if (/^(rgb|hsl)\(/i.test(trimmed)) return trimmed;
  return trimmed;
}

function colorSwatchStyle(value: string): CSSProperties | undefined {
  const token = normalizeColorToken(value);
  if (/^#[0-9a-f]{3,8}$/i.test(token)) return { backgroundColor: token };
  if (/^rgb/i.test(token)) return { backgroundColor: token };
  return undefined;
}

function humanizeColorLabel(value: string, index: number, report: SvgAnalysisCoreReport): string {
  const token = value.trim();
  if (!token) return `Culoare ${index + 1}`;
  if (token.toLowerCase().includes("stroke")) return "Stroke decorativ";
  return resolveLayerColorHumanLabel(token, report);
}

export function isSingleLayerColorMode(report: SvgAnalysisCoreReport): boolean {
  const structuralLayers = report.layers.filter((layer) => layer.layerKind !== "raster_artwork");
  return structuralLayers.length <= 1;
}

export default function IntakeV6LayersColorBreakdown({
  report,
}: {
  report: SvgAnalysisCoreReport;
}) {
  const fillColors = report.colors?.fills?.length
    ? report.colors.fills
    : report.layers.flatMap((layer) => layer.colors ?? []);
  const strokeColors = report.colors?.strokes ?? [];
  const uniqueFills = [...new Set(fillColors.map(normalizeColorToken).filter(Boolean))];
  const uniqueStrokes = [...new Set(strokeColors.map(normalizeColorToken).filter(Boolean))];

  if (uniqueFills.length === 0 && uniqueStrokes.length === 0) return null;

  return (
    <div
      className="rounded-md border border-[#2A3548]/70 bg-[#0A0F1A]/35 px-3 py-3"
      data-testid="intake-v6-layers-color-breakdown"
    >
      <h3 className={`mb-2 ${v6.sectionTitle}`}>Culori detectate</h3>
      <p className={`mb-3 ${v6.helper}`}>
        Strat unic — culorile sunt grupate vizual pentru decizii de rol și finisaj.
      </p>
      {uniqueFills.length > 0 ? (
        <ul className="space-y-2" data-testid="intake-v6-layers-color-fill-list">
          {uniqueFills.map((color, index) => (
            <li key={`fill-${color}-${index}`} className="flex items-center gap-2 text-[11px]">
              <span
                className="inline-block h-3.5 w-3.5 shrink-0 rounded border border-[#2A3548]"
                style={colorSwatchStyle(color)}
                aria-hidden
              />
              <span className="font-medium text-slate-200">{humanizeColorLabel(color, index, report)}</span>
              <span className={`${v6.mono} text-slate-500`}>{color}</span>
            </li>
          ))}
        </ul>
      ) : null}
      {uniqueStrokes.length > 0 ? (
        <ul
          className={`space-y-2 ${uniqueFills.length > 0 ? "mt-3 border-t border-[#2A3548]/60 pt-3" : ""}`}
          data-testid="intake-v6-layers-color-stroke-list"
        >
          {uniqueStrokes.map((color, index) => (
            <li key={`stroke-${color}-${index}`} className="flex items-center gap-2 text-[11px]">
              <span
                className="inline-block h-3.5 w-3.5 shrink-0 rounded border border-[#2A3548]"
                style={colorSwatchStyle(color)}
                aria-hidden
              />
              <span className="font-medium text-slate-200">Stroke decorativ</span>
              <span className={`${v6.mono} text-slate-500`}>{color}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
