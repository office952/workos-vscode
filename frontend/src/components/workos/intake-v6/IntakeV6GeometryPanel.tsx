import type { IntakeV6GeometryMetricDisplay } from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import {
  INTAKE_V6_ARTWORK_LOGO_PERIMETER_DIAGNOSTIC_NOTE,
} from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import type { IntakeV6QuoteGeometry } from "@/lib/intakeV6/intakeV6QuoteGeometry";
import { AtomsBadge, v6 } from "./atoms/intakeV6Presentation";

function fmtM(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value) || value <= 0) return "—";
  return `${value.toFixed(3)} m`;
}

function fmtM2(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value) || value <= 0) return "—";
  return `${value.toFixed(3)} m²`;
}

function fmtCount(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) return "—";
  return String(value);
}

function cantSourceLabel(source: IntakeV6GeometryMetricDisplay["cantPerimeterSource"]): string {
  if (source === "outer_plus_inner") return "outer + interioare eligibile";
  if (source === "outer_only") return "pre-finish: LED exterior / outer only";
  return "pending";
}

export default function IntakeV6GeometryPanel({
  geometry,
  metrics,
  scopeWarnings,
  variant = "advanced",
}: {
  geometry: IntakeV6QuoteGeometry;
  metrics: IntakeV6GeometryMetricDisplay;
  scopeWarnings: string[];
  variant?: "advanced";
}) {
  const hasMetrics =
    (geometry.letter_perimeter_m ?? 0) > 0 ||
    (geometry.face_area_m2 ?? 0) > 0 ||
    (geometry.artwork_area_m2 ?? 0) > 0 ||
    (metrics.productionPartCount ?? 0) > 0;

  const cantDisplayM = metrics.cantReturnPerimeterM;

  return (
    <div
      className={variant === "advanced" ? "mb-4" : `${v6.card} mb-4`}
      data-testid="intake-v6-geometry-panel"
    >
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-[12px] font-bold uppercase tracking-wide">Geometrie avansată</h3>
        <AtomsBadge tone={geometry.confirmed ? "ok" : hasMetrics ? "pending" : "muted"}>
          {geometry.confirmed ? "confirmată" : hasMetrics ? "sugerată" : "lipsă"}
        </AtomsBadge>
      </div>
      <p className="mb-3 text-[11px] text-slate-500">
        Metrici etichetate după sursă — Corel curve length (layer-sum) ≠ LED exterior ≠ CNC tăiere ≠ cant /
        return material.
      </p>

      <div
        className="mb-3 grid grid-cols-2 gap-3 text-[11px] sm:grid-cols-4"
        data-testid="intake-v6-geometry-count-breakdown"
      >
        <div>
          <span className="block text-slate-500">Grupuri volumetrice</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-volumetric-groups">
            {fmtCount(metrics.volumetricGroupCount)}
          </strong>
        </div>
        <div>
          <span className="block text-slate-500">Piese producție</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-production-parts">
            {fmtCount(metrics.productionPartCount)}
          </strong>
        </div>
        <div>
          <span className="block text-slate-500">Caractere text</span>
          <strong className="text-slate-400" data-testid="intake-v6-geometry-character-count">
            n/a
          </strong>
        </div>
        <div>
          <span className="block text-slate-500">Artwork / logo</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-artwork-count">
            {fmtCount(metrics.artworkLayerCount)}
          </strong>
        </div>
      </div>

      <p
        className="mb-3 text-[10px] text-slate-500"
        data-testid="intake-v6-geometry-character-count-note"
      >
        {metrics.estimatedCharacterCountReason}
      </p>

      {metrics.hasSoareEmblemNote ? (
        <p className="mb-3 text-[10px] text-sky-200/90" data-testid="intake-v6-geometry-soare-note">
          Soare = piesă volumetrică / emblemă face — nu literă tipografică.
        </p>
      ) : null}

      <div
        className="mb-3 grid grid-cols-1 gap-3 text-[11px] sm:grid-cols-2"
        data-testid="intake-v6-geometry-perimeter-table"
      >
        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2 sm:col-span-2">
          <span className="block text-slate-500">Perimetru total vectorial</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-full-vector-perimeter">
            {fmtM(metrics.fullVectorPerimeterM)}
          </strong>
        </div>
        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2">
          <span className="block text-slate-500">Perimetru vectorial producție</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-corel-curve-length">
            {fmtM(metrics.corelComparableCurveLengthM)}
          </strong>
        </div>
        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2">
          <span className="block text-slate-500">Perimetru artwork/logo vectorial</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-artwork-logo-vector-perimeter">
            {fmtM(metrics.artworkLogoVectorPerimeterM)}
          </strong>
        </div>
        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2">
          <span className="block text-slate-500">Perimetru CNC față</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-cutting-perimeter">
            {fmtM(metrics.cncFacePerimeterM)}
          </strong>
        </div>
        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2">
          <span className="block text-slate-500">Perimetru LED litere — exterior only</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-led-perimeter">
            {fmtM(metrics.ledExteriorPerimeterM)}
          </strong>
        </div>
        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2">
          <span className="block text-slate-500">Cant / volum litere — exterior + goluri eligibile</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-return-perimeter">
            {metrics.cantPricingPending && metrics.analysisBundlePending
              ? "pending"
              : fmtM(cantDisplayM)}
          </strong>
        </div>
        <div className="rounded border border-wo-border-strong bg-wo-surface-inset/40 px-3 py-2 sm:col-span-2">
          <span className="block text-slate-500">Artwork logo perimeter (detaliu rol)</span>
          <strong className="text-slate-200" data-testid="intake-v6-geometry-artwork-perimeter">
            {metrics.artworkPerimeterIsDiagnostic && metrics.artworkVectorPerimeterDiagnosticM != null
              ? fmtM(metrics.artworkVectorPerimeterDiagnosticM)
              : metrics.artworkPerimeterIsRasterNa
                ? "n/a — artwork raster, no vector perimeter"
                : fmtM(metrics.artworkVectorPerimeterM)}
          </strong>
          {metrics.artworkPerimeterIsDiagnostic ? (
            <span
              className="mt-1 block text-[10px] text-slate-500"
              data-testid="intake-v6-geometry-artwork-perimeter-diagnostic-note"
            >
              {INTAKE_V6_ARTWORK_LOGO_PERIMETER_DIAGNOSTIC_NOTE}
            </span>
          ) : null}
        </div>
      </div>

      <details
        className="mb-3 rounded border border-wo-border-strong bg-wo-surface-inset/30 px-3 py-2 text-[11px]"
        data-testid="intake-v6-geometry-area-technical"
      >
        <summary className="cursor-pointer font-semibold uppercase tracking-wide text-slate-400">
          Suprafețe geometrie (detaliu tehnic)
        </summary>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          <div>
            <span className="block text-slate-500">Suprafață față</span>
            <strong className="text-slate-200" data-testid="intake-v6-geometry-face-area">
              {fmtM2(geometry.face_area_m2)}
            </strong>
          </div>
          <div>
            <span className="block text-slate-500">Suprafață emblemă</span>
            <strong className="text-slate-200" data-testid="intake-v6-geometry-artwork-area">
              {fmtM2(geometry.artwork_area_m2)}
            </strong>
          </div>
          <div>
            <span className="block text-slate-500">Layer principal</span>
            <strong className={`${v6.mono} text-slate-200`}>
              {geometry.primary_letters_layer_key ?? "—"}
            </strong>
          </div>
        </div>
      </details>

      {metrics.showCantSection ? (
        <div
          className="mb-3 rounded border border-wo-border-strong bg-wo-surface-inset/50 px-3 py-3 text-[11px]"
          data-testid="intake-v6-geometry-cant-section"
        >
          <h4 className="mb-2 text-[11px] font-bold uppercase tracking-wide text-slate-400">
            Cant / volum litere — exterior + interioare eligibile
          </h4>
          <p className="mb-2 text-[10px] text-slate-500">
            Artwork/logo este exclus din cant volumetric, dacă este print/raster.
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <div>
              <span className="block text-slate-500">Adâncime cant</span>
              <strong className="text-slate-200" data-testid="intake-v6-geometry-cant-depth">
                {metrics.cantReturnDepthMm != null ? `${metrics.cantReturnDepthMm} mm` : "—"}
              </strong>
            </div>
            <div>
              <span className="block text-slate-500">Finisaj cant</span>
              <strong className="text-slate-200" data-testid="intake-v6-geometry-cant-finish">
                {metrics.cantReturnFinishLabel ?? "—"}
              </strong>
            </div>
            <div>
              <span className="block text-slate-500">Sursă perimetru</span>
              <strong className="text-slate-200" data-testid="intake-v6-geometry-cant-source">
                {cantSourceLabel(metrics.cantPerimeterSource)}
              </strong>
            </div>
            <div>
              <span className="block text-slate-500">Perimetru calculat</span>
              <strong className="text-slate-200" data-testid="intake-v6-geometry-cant-calculated">
                {metrics.cantPricingPending && metrics.analysisBundlePending
                  ? "pending"
                  : fmtM(cantDisplayM)}
              </strong>
            </div>
          </div>
          {metrics.cantPendingReason ? (
            <p className="mt-2 text-[10px] text-amber-200" data-testid="intake-v6-geometry-cant-pending">
              {metrics.cantPendingReason}
            </p>
          ) : null}
        </div>
      ) : null}

      {geometry.part_classification_confidence === "low" ? (
        <p className="mt-3 text-[10px] text-amber-200" data-testid="intake-v6-geometry-classification-warning">
          Clasificare contururi cu încredere scăzută — verificați rolurile vectorilor înainte de quote.
        </p>
      ) : null}

      {metrics.analysisBundlePending ? (
        <p
          className="mt-3 rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[10px] text-amber-100"
          data-testid="intake-v6-geometry-analysis-bundle-pending"
        >
          Salvează Review/Setări pentru calcul complet cant/materiale (analysis-bundle).
        </p>
      ) : null}

      {metrics.artworkLogoWarnings.length > 0 ? (
        <ul
          className="mt-3 space-y-1 rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-[10px] text-amber-100"
          data-testid="intake-v6-artwork-logo-warnings"
        >
          {metrics.artworkLogoWarnings.map((warning) => (
            <li key={warning}>• {warning}</li>
          ))}
        </ul>
      ) : null}

      {scopeWarnings.length > 0 ? (
        <ul className="mt-3 space-y-1 text-[10px] text-amber-200" data-testid="intake-v6-scope-warnings">
          {scopeWarnings.map((warning) => (
            <li key={warning}>• {warning}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}



