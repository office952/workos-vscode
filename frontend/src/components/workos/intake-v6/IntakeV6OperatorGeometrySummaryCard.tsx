import type { IntakeV6GeometryMetricDisplay } from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import { getFullVectorPerimeterM } from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import type { IntakeV6QuoteGeometry } from "@/lib/intakeV6/intakeV6QuoteGeometry";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";

function fmtMm(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return `${Math.round(value)} mm`;
}

function fmtM(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value) || value <= 0) return "—";
  return `${value.toFixed(3)} m`;
}

export default function IntakeV6OperatorGeometrySummaryCard({
  geometry,
  metrics,
  widthMm,
  heightMm,
  compact = false,
}: {
  geometry: IntakeV6QuoteGeometry;
  metrics: IntakeV6GeometryMetricDisplay;
  widthMm?: number | null;
  heightMm?: number | null;
  compact?: boolean;
}) {
  const width = widthMm ?? geometry.width_mm;
  const height = heightMm ?? geometry.height_mm;
  const fullVectorPerimeterM = getFullVectorPerimeterM(metrics);
  const hasMetrics =
    (geometry.letter_perimeter_m ?? 0) > 0 ||
    (geometry.face_area_m2 ?? 0) > 0 ||
    (fullVectorPerimeterM ?? 0) > 0;

  return (
    <div
      className={
        compact
          ? "rounded-md border border-[#2A3548]/70 bg-[#0A0F1A]/35 px-3 py-2.5"
          : "mb-4 rounded-[10px] border border-[#2A3548] bg-[#111827] p-5 border-blue-500/20 bg-gradient-to-br from-[#0A0F1A] to-[#0f172a]/80"
      }
      data-testid="intake-v6-operator-geometry-summary"
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h2 className={compact ? v6.label : v6.sectionTitle}>Dimensiune lucrare</h2>
        <AtomsBadge tone={geometry.confirmed ? "ok" : hasMetrics ? "pending" : "muted"}>
          {geometry.confirmed ? "confirmată" : hasMetrics ? "sugerată" : "lipsă"}
        </AtomsBadge>
      </div>

      <div
        className="grid grid-cols-3 gap-2 sm:gap-3"
        data-testid="intake-v6-operator-geometry-summary-metrics"
      >
        <div>
          <span className="block text-[9px] font-medium uppercase tracking-wide text-slate-500">
            Lățime
          </span>
          <strong className={`mt-0.5 block ${v6.metricValue}`} data-testid="intake-v6-operator-geometry-width">
            {fmtMm(width)}
          </strong>
        </div>
        <div>
          <span className="block text-[9px] font-medium uppercase tracking-wide text-slate-500">
            Înălțime
          </span>
          <strong className={`mt-0.5 block ${v6.metricValue}`} data-testid="intake-v6-operator-geometry-height">
            {fmtMm(height)}
          </strong>
        </div>
        <div>
          <span className="block text-[9px] font-medium uppercase tracking-wide text-slate-500">
            Perimetru vectorial total
          </span>
          <strong
            className={`mt-0.5 block ${v6.metricValue} text-blue-200/90`}
            data-testid="intake-v6-operator-geometry-vector-perimeter"
          >
            {fmtM(fullVectorPerimeterM)}
          </strong>
        </div>
      </div>
    </div>
  );
}
