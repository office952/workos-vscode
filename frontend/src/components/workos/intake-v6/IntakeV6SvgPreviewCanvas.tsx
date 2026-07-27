import { useEffect, useRef } from "react";
import {
  applySvgPreviewLayerHighlight,
  clearSvgPreviewLayerHighlight,
  type SvgPreviewLayerHighlightTarget,
} from "@/lib/intakeV6/intakeV6SvgPreviewLayerHighlight";
import {
  applySvgPreviewContourOverlay,
  clearSvgPreviewContourOverlay,
  type SvgPreviewContourOverlayTarget,
} from "@/lib/intakeV6/intakeV6SvgPreviewContourOverlay";

interface IntakeV6SvgPreviewCanvasProps {
  source: string;
  testId?: string;
  missingExternalRaster?: boolean;
  missingExternalRasterMessage?: string;
  /** Larger preview for Step 1 full-width layout. */
  variant?: "default" | "large" | "compact" | "thumb";
  highlightedLayer?: SvgPreviewLayerHighlightTarget | null;
  /** Closed-contour overlay (preview DOM only; never mutates SVG source). */
  contourOverlay?: SvgPreviewContourOverlayTarget | null;
}

const PREVIEW_HIGHLIGHT_STYLE_ID = "intake-v6-svg-preview-highlight-styles";

function ensurePreviewHighlightStyles(): void {
  if (typeof document === "undefined") return;
  if (document.getElementById(PREVIEW_HIGHLIGHT_STYLE_ID)) return;
  const style = document.createElement("style");
  style.id = PREVIEW_HIGHLIGHT_STYLE_ID;
  style.textContent = `
    svg[data-intake-v6-layer-highlight] .intake-v6-svg-layer-dim {
      opacity: 0.16;
      transition: opacity 120ms ease;
    }
    svg[data-intake-v6-layer-highlight] .intake-v6-svg-layer-active {
      opacity: 1 !important;
      filter: drop-shadow(0 0 1px rgba(6, 182, 212, 0.95))
        drop-shadow(0 0 6px rgba(6, 182, 212, 0.5));
      transition: opacity 120ms ease, filter 120ms ease;
    }
    svg[data-intake-v6-layer-highlight] .intake-v6-svg-layer-bbox-highlight {
      pointer-events: none;
    }
  `;
  document.head.appendChild(style);
}

/** Fits inline SVG to panel — overrides natural mm/px size from source file (nest2/V3 pattern). */
export default function IntakeV6SvgPreviewCanvas({
  source,
  testId = "intake-v6-svg-preview",
  missingExternalRaster = false,
  missingExternalRasterMessage,
  variant = "default",
  highlightedLayer = null,
  contourOverlay = null,
}: IntakeV6SvgPreviewCanvasProps) {
  const canvasRef = useRef<HTMLDivElement | null>(null);
  const placeholderMessage =
    missingExternalRasterMessage ??
    "Preview incomplet: SVG-ul face referire la imagini externe care nu sunt incluse în fișier.";

  const isLarge = variant === "large";
  const isCompact = variant === "compact";
  const isThumb = variant === "thumb";
  const canvasClass = isLarge
    ? "mx-auto flex min-h-[360px] w-full max-h-[min(78vh,860px)] items-center justify-center overflow-auto sm:min-h-[420px] lg:min-h-[480px] [&_svg]:mx-auto [&_svg]:block [&_svg]:h-auto [&_svg]:max-h-[min(74vh,820px)] [&_svg]:max-w-full [&_svg]:w-full"
    : isThumb
      ? "mx-auto flex max-h-[180px] min-h-[120px] w-full items-center justify-center overflow-hidden [&_svg]:mx-auto [&_svg]:block [&_svg]:h-auto [&_svg]:max-h-[168px] [&_svg]:max-w-full [&_svg]:w-full"
      : isCompact
        ? "mx-auto flex max-h-[140px] min-h-[100px] w-full items-center justify-center overflow-hidden [&_svg]:mx-auto [&_svg]:block [&_svg]:h-auto [&_svg]:max-h-[128px] [&_svg]:max-w-full [&_svg]:w-full"
        : "mx-auto flex max-h-[320px] min-h-[160px] w-full items-center justify-center overflow-auto [&_svg]:mx-auto [&_svg]:block [&_svg]:h-auto [&_svg]:max-h-[300px] [&_svg]:max-w-full [&_svg]:w-full";

  const framePadding = isThumb ? "p-2" : "p-4";

  useEffect(() => {
    ensurePreviewHighlightStyles();
    const svg = canvasRef.current?.querySelector("svg");
    if (!(svg instanceof SVGSVGElement)) return;
    applySvgPreviewLayerHighlight(svg, highlightedLayer);
    applySvgPreviewContourOverlay(svg, contourOverlay);
    return () => {
      clearSvgPreviewContourOverlay(svg);
      clearSvgPreviewLayerHighlight(svg);
    };
  }, [source, highlightedLayer, contourOverlay]);

  return (
    <div className={isLarge ? "min-w-0" : "mb-3"} data-testid={testId}>
      {missingExternalRaster ? (
        <div
          className="mb-2 rounded border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-[11px] text-amber-100"
          data-testid={`${testId}-missing-raster-banner`}
        >
          {placeholderMessage}
        </div>
      ) : null}
      <div
        className={`relative overflow-hidden rounded-lg border border-wo-border-strong bg-slate-50 ${framePadding}`}
        data-testid={`${testId}-frame`}
      >
        {missingExternalRaster ? (
          <div
            className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-slate-900/5 p-6 text-center text-[11px] font-medium text-slate-600"
            data-testid={`${testId}-raster-placeholder`}
          >
            Imagine externă lipsă — preview geometric disponibil
          </div>
        ) : null}
        <div
          ref={canvasRef}
          className={canvasClass}
          data-testid={`${testId}-canvas`}
          dangerouslySetInnerHTML={{ __html: source }}
        />
      </div>
    </div>
  );
}
