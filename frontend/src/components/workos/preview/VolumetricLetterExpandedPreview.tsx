import { useState } from "react";
import type { VolumetricLetterPreviewConfig, VolumetricLetterPreviewMode } from "@/lib/volumetricLetterPreview/volumetricLetterPreviewTypes";
import {
  buildMaterialBadges,
  buildPreviewLayerStack,
  geometrySourceLabel,
  geometrySourceShortLabel,
  resolveGeometrySource,
  usesEstimatedLedPlacement,
} from "@/lib/volumetricLetterPreview/volumetricLetterPreviewGeometry";
import { VolumetricLetterPreviewSvg } from "./VolumetricLetterPreviewSvg";

export type VolumetricLetterExpandedPreviewProps = {
  config: VolumetricLetterPreviewConfig;
  mode?: VolumetricLetterPreviewMode;
  defaultMode?: VolumetricLetterPreviewMode;
  showLabels?: boolean;
  defaultShowLabels?: boolean;
  onModeChange?: (mode: VolumetricLetterPreviewMode) => void;
  onShowLabelsChange?: (show: boolean) => void;
  onBlockerClick?: (blocker: string) => void;
  onWarningClick?: (warning: string) => void;
  /** Hide per-instance mode/label toggles (e.g. demo page with global controls). */
  hideControls?: boolean;
  testId?: string;
};

function ReadinessBadge({
  ready,
  blockerCount,
  warningCount,
}: {
  ready: boolean;
  blockerCount: number;
  warningCount: number;
}) {
  if (blockerCount > 0) {
    return (
      <span className="inline-flex items-center rounded border border-red-700/50 bg-red-900/30 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-red-300">
        Blocat ({blockerCount})
      </span>
    );
  }
  if (warningCount > 0) {
    return (
      <span className="inline-flex items-center rounded border border-amber-700/50 bg-amber-900/30 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-300">
        Avertismente ({warningCount})
      </span>
    );
  }
  if (ready) {
    return (
      <span className="inline-flex items-center rounded border border-emerald-700/50 bg-emerald-900/30 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-emerald-300">
        Pregătit producție
      </span>
    );
  }
  return (
    <span className="inline-flex items-center rounded border border-slate-600 bg-slate-800/40 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-slate-400">
      Incomplet
    </span>
  );
}

/**
 * Data-driven SVG construction preview for TPL-VOLUMETRIC-LETTERS.
 * Consumes readiness from config; does not run validation.
 */
export default function VolumetricLetterExpandedPreview({
  config,
  mode: controlledMode,
  defaultMode = "compact",
  showLabels: controlledShowLabels,
  defaultShowLabels = true,
  onModeChange,
  onShowLabelsChange,
  onBlockerClick,
  onWarningClick,
  hideControls = false,
  testId = "volumetric-letter-preview",
}: VolumetricLetterExpandedPreviewProps) {
  const [internalMode, setInternalMode] = useState<VolumetricLetterPreviewMode>(defaultMode);
  const [internalShowLabels, setInternalShowLabels] = useState(defaultShowLabels);

  const mode = controlledMode ?? internalMode;
  const showLabels = controlledShowLabels ?? internalShowLabels;

  const layers = buildPreviewLayerStack(config);
  const badges = buildMaterialBadges(config);
  const geometrySource = resolveGeometrySource(config);
  const estimatedLed = usesEstimatedLedPlacement(config);
  const { blockers, warnings, isProductionReady } = config.readiness;
  const showLabelsInSvg = showLabels;

  function setMode(next: VolumetricLetterPreviewMode) {
    if (controlledMode === undefined) setInternalMode(next);
    onModeChange?.(next);
  }

  function setShowLabels(next: boolean) {
    if (controlledShowLabels === undefined) setInternalShowLabels(next);
    onShowLabelsChange?.(next);
  }

  return (
    <section
      className="rounded-md border border-[#2A3548] bg-[#0A0F1A]/40 p-3 space-y-3"
      data-testid={testId}
      data-template={config.templateCode}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="space-y-1 min-w-0">
          <h3 className="text-[12px] font-bold text-slate-200">Preview construcție literă</h3>
          <p className="text-[10px] text-slate-500" data-testid={`${testId}-geometry-source`}>
            {geometrySourceLabel(geometrySource)}
          </p>
        </div>
        <ReadinessBadge
          ready={isProductionReady}
          blockerCount={blockers.length}
          warningCount={warnings.length}
        />
      </div>

      {!hideControls && (
        <div className="flex flex-wrap gap-2" data-testid={`${testId}-controls`}>
          <div className="inline-flex rounded border border-[#1E293B] overflow-hidden">
            <button
              type="button"
              className={`px-2.5 py-1 text-[10px] uppercase tracking-wide ${
                mode === "compact"
                  ? "bg-slate-700 text-slate-100"
                  : "bg-transparent text-slate-400 hover:text-slate-200"
              }`}
              onClick={() => setMode("compact")}
              data-testid={`${testId}-mode-compact`}
            >
              Compact
            </button>
            <button
              type="button"
              className={`px-2.5 py-1 text-[10px] uppercase tracking-wide ${
                mode === "expanded"
                  ? "bg-slate-700 text-slate-100"
                  : "bg-transparent text-slate-400 hover:text-slate-200"
              }`}
              onClick={() => setMode("expanded")}
              data-testid={`${testId}-mode-expanded`}
            >
              Explodat
            </button>
          </div>
          <button
            type="button"
            className={`px-2.5 py-1 text-[10px] uppercase tracking-wide rounded border border-[#1E293B] ${
              showLabels ? "bg-slate-700 text-slate-100" : "text-slate-400 hover:text-slate-200"
            }`}
            onClick={() => setShowLabels(!showLabels)}
            data-testid={`${testId}-toggle-labels`}
          >
            Etichete {showLabels ? "ON" : "OFF"}
          </button>
        </div>
      )}

      <div
        className="relative rounded border border-[#1E293B]/80 bg-[#0F172A]/50 p-3"
        data-testid={`${testId}-canvas`}
      >
        <div className="absolute top-2 right-2 z-10 flex flex-wrap gap-1 justify-end max-w-[70%]">
          <span
            className="rounded border border-slate-600/70 bg-slate-900/80 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-slate-300"
            data-testid={`${testId}-geometry-badge`}
          >
            {geometrySourceShortLabel(geometrySource)}
          </span>
          {estimatedLed && config.lighting.enabled && (
            <span
              className="rounded border border-amber-700/50 bg-amber-950/70 px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-amber-300/90"
              data-testid={`${testId}-led-estimate-badge`}
            >
              LED estimat
            </span>
          )}
        </div>
        <VolumetricLetterPreviewSvg
          config={config}
          mode={mode}
          showLabels={showLabelsInSvg}
          layers={layers}
          testId={testId}
        />
      </div>

      {badges.length > 0 && (
        <ul className="flex flex-wrap gap-1.5" data-testid={`${testId}-badges`}>
          {badges.map((badge) => (
            <li
              key={badge}
              className="rounded border border-slate-600/60 bg-slate-800/50 px-2 py-0.5 text-[10px] text-slate-300"
            >
              {badge}
            </li>
          ))}
        </ul>
      )}

      {showLabels && (
        <ul className="space-y-1" data-testid={`${testId}-layer-legend`}>
          {layers.map((layer) => (
            <li
              key={layer.id}
              className="flex items-baseline gap-2 text-[10px]"
              data-testid={`${testId}-legend-${layer.id}`}
            >
              <span
                className={`font-medium ${layer.configured ? "text-slate-300" : "text-amber-300/90"}`}
              >
                {layer.label}
              </span>
              {layer.detail && (
                <span className="text-slate-500 truncate">{layer.detail}</span>
              )}
              {!layer.configured && (
                <span className="text-[9px] uppercase tracking-wide text-amber-400/80">
                  incomplet
                </span>
              )}
            </li>
          ))}
        </ul>
      )}

      {blockers.length > 0 && (
        <ul className="space-y-1 pt-1 border-t border-red-900/30" data-testid={`${testId}-blockers`}>
          <li className="text-[10px] uppercase tracking-wide text-red-400/90">Blockere</li>
          {blockers.map((code) => (
            <li key={code}>
              {onBlockerClick ? (
                <button
                  type="button"
                  className="text-[11px] text-red-300 hover:underline font-mono"
                  onClick={() => onBlockerClick(code)}
                  data-testid={`${testId}-blocker-${code}`}
                >
                  {code}
                </button>
              ) : (
                <span className="text-[11px] text-red-300 font-mono">{code}</span>
              )}
            </li>
          ))}
        </ul>
      )}

      {warnings.length > 0 && (
        <ul className="space-y-1 pt-1 border-t border-amber-900/30" data-testid={`${testId}-warnings`}>
          <li className="text-[10px] uppercase tracking-wide text-amber-400/90">Avertismente</li>
          {warnings.map((code) => (
            <li key={code}>
              {onWarningClick ? (
                <button
                  type="button"
                  className="text-[11px] text-amber-300 hover:underline font-mono"
                  onClick={() => onWarningClick(code)}
                  data-testid={`${testId}-warning-${code}`}
                >
                  {code}
                </button>
              ) : (
                <span className="text-[11px] text-amber-300 font-mono">{code}</span>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export { VolumetricLetterExpandedPreview };
