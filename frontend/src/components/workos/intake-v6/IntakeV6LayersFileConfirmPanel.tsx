import type { SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { CheckCircle2, FileCheck, Maximize2, Upload } from "lucide-react";
import IntakeV6Nest2SvgUploader from "./IntakeV6Nest2SvgUploader";
import IntakeV6LayersMetricsStrip from "./IntakeV6LayersMetricsStrip";
import IntakeV6SvgPreviewCanvas from "./IntakeV6SvgPreviewCanvas";
import { v6 } from "./atoms/intakeV6Presentation";
import type { IntakeV6GeometryMetricDisplay } from "@/lib/intakeV6/intakeV6GeometryMetricDisplay";
import type { IntakeV6QuoteGeometry } from "@/lib/intakeV6/intakeV6QuoteGeometry";
import type { SvgPreviewLayerHighlightTarget } from "@/lib/intakeV6/intakeV6SvgPreviewLayerHighlight";
import type { SvgPreviewContourOverlayTarget } from "@/lib/intakeV6/intakeV6SvgPreviewContourOverlay";

export default function IntakeV6LayersFileConfirmPanel({
  fileName,
  previewSource,
  missingExternalRaster,
  report,
  quoteGeometry,
  geometryMetrics,
  analyzing,
  canImportSvg,
  onImportFile,
  onOpenInspect,
  highlightedLayer = null,
  contourOverlay = null,
}: {
  fileName?: string | null;
  previewSource?: string | null;
  missingExternalRaster?: boolean;
  report: SvgAnalysisCoreReport | null;
  quoteGeometry: IntakeV6QuoteGeometry;
  geometryMetrics: IntakeV6GeometryMetricDisplay;
  analyzing: boolean;
  canImportSvg: boolean;
  onImportFile: (file: File) => void | Promise<void>;
  onOpenInspect: () => void;
  highlightedLayer?: SvgPreviewLayerHighlightTarget | null;
  contourOverlay?: SvgPreviewContourOverlayTarget | null;
}) {
  const hasPreview = Boolean(previewSource);

  return (
    <div className={`${v6.cardCompact} min-w-0`} data-testid="intake-v6-layers-preview-panel">
      <div className="mb-2 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className={`${v6.sectionTitle} flex items-center gap-1.5`}>
            {hasPreview ? (
              <FileCheck className="h-3.5 w-3.5 shrink-0 text-emerald-400/90" aria-hidden />
            ) : (
              <Upload className="h-3.5 w-3.5 shrink-0 text-slate-500" aria-hidden />
            )}
            {hasPreview ? "Fișier recunoscut" : "Confirmă fișierul SVG"}
          </h2>
          <p className={v6.sectionDesc}>
            {hasPreview
              ? "Verifică thumbnail-ul — deschide preview mare pentru detalii și straturi."
              : "Încarcă SVG-ul corect înainte de confirmarea rolurilor."}
          </p>
        </div>
        {hasPreview && fileName ? (
          <span
            className="inline-flex max-w-[14rem] items-center gap-1 truncate rounded border border-emerald-500/25 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-200"
            data-testid="intake-v6-file-confirm-chip"
            title={fileName}
          >
            <CheckCircle2 className="h-3 w-3 shrink-0" aria-hidden />
            <span className="truncate">{fileName}</span>
          </span>
        ) : null}
      </div>

      {hasPreview && previewSource ? (
        <>
          <IntakeV6SvgPreviewCanvas
            source={previewSource}
            missingExternalRaster={missingExternalRaster}
            missingExternalRasterMessage="Preview incomplet: SVG-ul face referire la imagini externe care nu sunt incluse în fișier."
            variant="thumb"
            highlightedLayer={highlightedLayer}
            contourOverlay={contourOverlay}
          />
          {report ? (
            <div className="mt-2">
              <IntakeV6LayersMetricsStrip
                report={report}
                geometry={quoteGeometry}
                metrics={geometryMetrics}
                widthMm={report.document.widthMm}
                heightMm={report.document.heightMm}
                variant="hero"
              />
            </div>
          ) : null}
          <div className="mt-2 flex flex-wrap gap-2">
            <button
              type="button"
              className={`${v6.btnPrimary} inline-flex items-center gap-1.5`}
              onClick={onOpenInspect}
              data-testid="intake-v6-open-preview-inspect"
            >
              <Maximize2 className="h-3.5 w-3.5" aria-hidden />
              Deschide preview
            </button>
            <IntakeV6Nest2SvgUploader
              busy={analyzing}
              disabled={!canImportSvg}
              label="Schimbă fișier"
              busyLabel="Analizez..."
              buttonClassName={v6.btnGhost}
              buttonTestId="intake-v6-change-svg-file"
              inputTestId="intake-v6-svg-input-change"
              onFileSelected={(file) => void onImportFile(file)}
            />
          </div>
        </>
      ) : (
        <div
          className="flex min-h-[140px] flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-wo-border-strong bg-wo-surface-inset/40 px-4 py-6 text-center"
          data-testid="intake-v6-svg-preview-empty"
        >
          <Upload className="h-8 w-8 text-slate-600" aria-hidden />
          <p className={v6.helper}>Trage SVG aici sau folosește panoul operator.</p>
          <IntakeV6Nest2SvgUploader
            busy={analyzing}
            disabled={!canImportSvg}
            label="Încarcă SVG"
            busyLabel="Analizez..."
            buttonClassName={v6.btnPrimary}
            inputTestId="intake-v6-svg-input-preview"
            onFileSelected={(file) => void onImportFile(file)}
          />
        </div>
      )}
    </div>
  );
}
