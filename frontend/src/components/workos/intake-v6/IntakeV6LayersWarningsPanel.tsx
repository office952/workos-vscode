import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { AlertTriangle, FileWarning, Layers, Sparkles } from "lucide-react";
import { useMemo } from "react";
import IntakeV6LayerStatusIcon from "./IntakeV6LayerStatusIcon";
import { v6 } from "./atoms/intakeV6Presentation";

const PSEUDO_LAYER_HINT =
  /pseudo-layer generated from solid vector fills/i;
const STROKE_VECTOR_HINT = /stroke-only vector isolated/i;

function resolveLayerKey(
  confirmation: LayerRoleConfirmation | null,
  layer: SvgAnalysisCoreReport["layers"][number],
): string {
  const entry =
    confirmation?.layers.find(
      (item) => item.layerKey === layer.id || item.layerKey === layer.name,
    ) ?? confirmation?.layers.find((item) => item.layerName === layer.name);
  return entry?.layerKey ?? layer.id ?? layer.name;
}

function resolveLayerState(
  confirmation: LayerRoleConfirmation | null,
  layerKey: string,
): LayerRoleConfirmation["layers"][number]["confirmationState"] | undefined {
  return confirmation?.layers.find((item) => item.layerKey === layerKey)?.confirmationState;
}

export default function IntakeV6LayersWarningsPanel({
  report,
  confirmation,
  parseWarning,
  scopeWarnings,
  onJumpToLayer,
}: {
  report: SvgAnalysisCoreReport | null;
  confirmation: LayerRoleConfirmation | null;
  parseWarning?: string | null;
  scopeWarnings: string[];
  onJumpToLayer?: (layerKey: string) => void;
}) {
  const pseudoLayerGroups = useMemo(() => {
    if (!report) return [];
    const layers: Array<{
      layerKey: string;
      layerName: string;
      state: LayerRoleConfirmation["layers"][number]["confirmationState"] | undefined;
    }> = [];

    for (const layer of report.layers) {
      const messages = (layer.warnings ?? []).map((warning) =>
        typeof warning === "string" ? warning : warning.message,
      );
      if (messages.some((message) => PSEUDO_LAYER_HINT.test(message))) {
        const layerKey = resolveLayerKey(confirmation, layer);
        layers.push({
          layerKey,
          layerName: layer.name,
          state: resolveLayerState(confirmation, layerKey),
        });
      }
    }
    return layers;
  }, [report, confirmation]);

  const atypicalVectorGroups = useMemo(() => {
    if (!report) return [];
    const layers: Array<{
      layerKey: string;
      layerName: string;
      state: LayerRoleConfirmation["layers"][number]["confirmationState"] | undefined;
    }> = [];

    for (const layer of report.layers) {
      const messages = (layer.warnings ?? []).map((warning) =>
        typeof warning === "string" ? warning : warning.message,
      );
      const isAtypical = layer.autoRole === "printed_artwork" || layer.autoRole === "logo" || messages.some((message) => STROKE_VECTOR_HINT.test(message));
      if (!isAtypical) continue;
      const layerKey = resolveLayerKey(confirmation, layer);
      layers.push({
        layerKey,
        layerName: layer.name,
        state: resolveLayerState(confirmation, layerKey),
      });
    }

    return layers;
  }, [report, confirmation]);

  const otherLayerWarnings = useMemo(() => {
    if (!report) return [];
    const seen = new Set<string>();
    const items: string[] = [];
    for (const layer of report.layers) {
      for (const warning of layer.warnings ?? []) {
        const message = typeof warning === "string" ? warning : warning.message;
        if (PSEUDO_LAYER_HINT.test(message)) continue;
        if (seen.has(message)) continue;
        seen.add(message);
        items.push(message);
      }
    }
    return items.slice(0, 4);
  }, [report]);

  const totalCount =
    (parseWarning ? 1 : 0) + scopeWarnings.length + pseudoLayerGroups.length + otherLayerWarnings.length;

  if (totalCount === 0) return null;

  return (
    <div
      className="overflow-hidden rounded-lg border border-amber-500/30 bg-gradient-to-br from-amber-500/[0.08] via-[#0A0F1A]/80 to-[#0A0F1A]/90"
      data-testid="intake-v6-layers-warnings"
    >
      <div className="flex items-center justify-between gap-2 border-b border-amber-500/20 px-3 py-2">
        <h3 className={`flex items-center gap-1.5 ${v6.sectionTitle} text-amber-200`}>
          <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden />
          Atenție analiză
        </h3>
        <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[11px] font-bold tabular-nums text-amber-200">
          {totalCount}
        </span>
      </div>

      <div className="space-y-2 p-3 text-[12px]">
        {parseWarning ? (
          <div className="flex gap-2 rounded-md border border-amber-500/20 bg-amber-500/5 px-2.5 py-2 text-amber-100/90">
            <FileWarning className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-300" aria-hidden />
            <p>
              <span className="font-semibold text-amber-200">Parse SVG:</span> {parseWarning}
            </p>
          </div>
        ) : null}

        {scopeWarnings.map((warning, index) => (
          <div
            key={`scope-${index}-${warning}`}
            className="flex gap-2 rounded-md border border-amber-500/15 bg-[#0A0F1A]/40 px-2.5 py-2 text-amber-100/85"
          >
            <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-300/90" aria-hidden />
            <p>{warning}</p>
          </div>
        ))}

        {pseudoLayerGroups.length > 0 ? (
          <div
            className="rounded-md border border-amber-500/20 bg-[#0A0F1A]/50 px-2.5 py-2"
            data-testid="intake-v6-pseudo-layer-warning-group"
          >
            <div className="mb-2 flex items-start gap-2">
              <Layers className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-300" aria-hidden />
              <div>
                <p className="font-semibold text-amber-100">Layere propuse ca Vector Litere</p>
                <p className={`mt-0.5 ${v6.sectionDesc} text-amber-200/75`}>
                  Analyzer-ul a grupat automat aceste layere ca litere volumetrice. Confirmă rolul fiecărui layer înainte de Review.
                </p>
              </div>
            </div>
            <ul className="flex flex-wrap gap-1.5">
              {pseudoLayerGroups.map((layer) => (
                <li key={layer.layerKey}>
                  <button
                    type="button"
                    className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-amber-500/25 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-100 transition hover:border-amber-400/40 hover:bg-amber-500/15"
                    onClick={() => onJumpToLayer?.(layer.layerKey)}
                    data-testid={`intake-v6-warning-layer-chip-${layer.layerKey}`}
                    title={`${layer.layerName} — deschide stratul`}
                  >
                    <IntakeV6LayerStatusIcon state={layer.state} size="sm" />
                    <span className="truncate">{layer.layerName}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {atypicalVectorGroups.length > 0 ? (
          <div
            className="rounded-md border border-amber-500/20 bg-[#0A0F1A]/50 px-2.5 py-2"
            data-testid="intake-v6-atypical-layer-warning-group"
          >
            <div className="mb-2 flex items-start gap-2">
              <Sparkles className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-300" aria-hidden />
              <div>
                <p className="font-semibold text-amber-100">Layere propuse ca Vector Logo</p>
                <p className={`mt-0.5 ${v6.sectionDesc} text-amber-200/75`}>
                  Analyzer-ul a identificat aceste contururi ca logo volumetric. Confirmă rolurile înainte de Review.
                </p>
              </div>
            </div>
            <ul className="flex flex-wrap gap-1.5">
              {atypicalVectorGroups.map((layer) => (
                <li key={layer.layerKey}>
                  <button
                    type="button"
                    className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-amber-500/25 bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-100 transition hover:border-amber-400/40 hover:bg-amber-500/15"
                    onClick={() => onJumpToLayer?.(layer.layerKey)}
                    data-testid={`intake-v6-warning-atypical-chip-${layer.layerKey}`}
                    title={`${layer.layerName} — deschide stratul`}
                  >
                    <IntakeV6LayerStatusIcon state={layer.state} size="sm" />
                    <span className="truncate">{layer.layerName}</span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {otherLayerWarnings.filter((warning) => !STROKE_VECTOR_HINT.test(warning)).map((warning, index) => (
          <p
            key={`layer-other-${index}-${warning}`}
            className="rounded-md border border-amber-500/10 bg-[#0A0F1A]/35 px-2.5 py-1.5 text-[11px] text-amber-100/80"
          >
            {warning}
          </p>
        ))}
      </div>
    </div>
  );
}
