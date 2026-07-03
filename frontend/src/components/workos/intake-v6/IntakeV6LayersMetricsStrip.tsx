import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import type { IntakeV6GeometryMetricDisplay } from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import { getFullVectorPerimeterM } from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import type { IntakeV6QuoteGeometry } from "@/lib/intakeV6/intakeV6QuoteGeometry";
import { Layers, Palette, PenTool, Ruler } from "lucide-react";
import type { CSSProperties, ReactNode } from "react";
import { v6 } from "./atoms/intakeV6Presentation";

function fmtMm(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${Math.round(value)} mm`;
}

function fmtM(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value) || value <= 0) return "—";
  return `${value.toFixed(3)} m`;
}

function fmtCount(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return String(value);
}

function colorDotStyle(color: string): CSSProperties | undefined {
  const token = color.trim();
  if (/^#[0-9a-f]{3,8}$/i.test(token)) return { backgroundColor: token };
  if (/^rgb/i.test(token)) return { backgroundColor: token };
  return undefined;
}

function HeroMetricTile({
  icon,
  label,
  value,
  accentClass,
  testId,
  footer,
}: {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  accentClass: string;
  testId?: string;
  footer?: ReactNode;
}) {
  return (
    <div
      className={`flex min-w-0 items-center gap-2 rounded-lg border border-[#2A3548]/70 bg-[#0A0F1A]/55 px-2 py-2 ${accentClass}`}
      data-testid={testId}
    >
      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md border border-[#2A3548]/80 bg-[#111827]/80 text-slate-300">
        {icon}
      </span>
      <div className="min-w-0">
        <span className={`${v6.metricLabel} block truncate`}>{label}</span>
        <strong className="block truncate text-[13px] font-semibold tabular-nums leading-tight text-slate-50">
          {value}
        </strong>
        {footer}
      </div>
    </div>
  );
}

export default function IntakeV6LayersMetricsStrip({
  report,
  geometry,
  metrics,
  widthMm,
  heightMm,
  variant = "full",
}: {
  report: SvgAnalysisCoreReport;
  geometry: IntakeV6QuoteGeometry;
  metrics: IntakeV6GeometryMetricDisplay;
  widthMm?: number | null;
  heightMm?: number | null;
  variant?: "hero" | "full";
}) {
  const width = widthMm ?? report.document.widthMm ?? geometry.width_mm;
  const height = heightMm ?? report.document.heightMm ?? geometry.height_mm;
  const fullVectorPerimeterM = getFullVectorPerimeterM(metrics);
  const ledLetterPerimeterM =
    metrics.ledExteriorPerimeterM != null && metrics.ledExteriorPerimeterM > 0
      ? metrics.ledExteriorPerimeterM
      : geometry.letter_perimeter_m != null && geometry.letter_perimeter_m > 0
        ? geometry.letter_perimeter_m
        : null;

  const uniqueColors =
    report.colors?.unique?.length ??
    new Set(report.layers.flatMap((layer) => layer.colors ?? [])).size;
  const closedContours =
    report.geometry?.closedSubPathCount ??
    report.layers.reduce((sum, layer) => sum + (layer.closedSubPathCount ?? 0), 0);

  if (variant === "hero") {
    const colorTokens = [
      ...(report.colors?.fills ?? []),
      ...(report.colors?.unique ?? []),
      ...report.layers.flatMap((layer) => layer.colors ?? []),
    ]
      .map((color) => color.trim())
      .filter(Boolean);
    const uniqueDots = [...new Set(colorTokens)].slice(0, 5);
    const aspectRatio =
      width != null && height != null && height > 0 ? Math.min(width / height, 4) : 1;

    return (
      <div
        className="grid grid-cols-2 gap-2 sm:grid-cols-4"
        data-testid="intake-v6-layers-metrics-hero"
      >
        <HeroMetricTile
          icon={<Ruler className="h-4 w-4 text-sky-400/90" aria-hidden />}
          label="Dimensiuni"
          value={
            <>
              {fmtMm(width)} × {fmtMm(height)}
            </>
          }
          accentClass="border-l-2 border-l-sky-500/50"
          footer={
            <span
              className="mt-1 inline-block h-1 max-w-[4.5rem] rounded-full bg-slate-700/80"
              title="Proporție lățime / înălțime"
              aria-hidden
            >
              <span
                className="block h-full rounded-full bg-sky-400/70"
                style={{ width: `${Math.max(18, Math.min(100, aspectRatio * 22))}%` }}
              />
            </span>
          }
        />
        <HeroMetricTile
          icon={<Layers className="h-4 w-4 text-cyan-400/90" aria-hidden />}
          label="Straturi"
          value={fmtCount(report.layers.length)}
          accentClass="border-l-2 border-l-cyan-500/45"
          testId="intake-v6-layers-metric-layer-count"
        />
        <HeroMetricTile
          icon={<Palette className="h-4 w-4 text-violet-400/90" aria-hidden />}
          label="Culori"
          value={fmtCount(uniqueColors)}
          accentClass="border-l-2 border-l-violet-500/45"
          testId="intake-v6-layers-metric-color-count"
          footer={
            uniqueDots.length > 0 ? (
              <span className="mt-1 flex gap-0.5" aria-hidden>
                {uniqueDots.map((color, index) => (
                  <span
                    key={`${color}-${index}`}
                    className="h-2 w-2 rounded-full border border-slate-600/80"
                    style={colorDotStyle(color) ?? { backgroundColor: "#64748b" }}
                  />
                ))}
              </span>
            ) : null
          }
        />
        <HeroMetricTile
          icon={<PenTool className="h-4 w-4 text-emerald-400/90" aria-hidden />}
          label="Contururi"
          value={fmtCount(closedContours)}
          accentClass="border-l-2 border-l-emerald-500/45"
          testId="intake-v6-layers-metric-contour-count"
        />
      </div>
    );
  }

  return (
    <div
      className="grid grid-cols-2 gap-x-4 gap-y-3 rounded-md border border-[#2A3548]/70 bg-[#0A0F1A]/35 px-3 py-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7"
      data-testid="intake-v6-layers-metrics-strip"
    >
      <div>
        <span className={v6.label}>Lățime</span>
        <strong className={v6.metricValue} data-testid="intake-v6-layers-metric-width">
          {fmtMm(width)}
        </strong>
      </div>
      <div>
        <span className={v6.label}>Înălțime</span>
        <strong className={v6.metricValue} data-testid="intake-v6-layers-metric-height">
          {fmtMm(height)}
        </strong>
      </div>
      <div>
        <span className={v6.label}>Perimetru vectorial total</span>
        <strong
          className={`${v6.metricValue} text-blue-200/90`}
          data-testid="intake-v6-layers-metric-vector-perimeter"
        >
          {fmtM(fullVectorPerimeterM)}
        </strong>
      </div>
      {ledLetterPerimeterM != null && ledLetterPerimeterM > 0 ? (
        <div>
          <span className={v6.label}>Perimetru LED / litere</span>
          <strong
            className={`${v6.metricValue} text-emerald-200/90`}
            data-testid="intake-v6-layers-metric-led-perimeter"
          >
            {fmtM(ledLetterPerimeterM)}
          </strong>
        </div>
      ) : null}
      <div>
        <span className={v6.label}>Straturi</span>
        <strong className={v6.metricValue} data-testid="intake-v6-layers-metric-layer-count">
          {fmtCount(report.layers.length)}
        </strong>
      </div>
      <div>
        <span className={v6.label}>Culori</span>
        <strong className={v6.metricValue} data-testid="intake-v6-layers-metric-color-count">
          {fmtCount(uniqueColors)}
        </strong>
      </div>
      <div>
        <span className={v6.label}>Contururi închise</span>
        <strong className={v6.metricValue} data-testid="intake-v6-layers-metric-contour-count">
          {fmtCount(closedContours)}
        </strong>
      </div>
    </div>
  );
}
