import { useState } from "react";
import { AlertTriangle, Layers, Loader2, Play } from "lucide-react";
import type { ProductTemplateEntity } from "@/lib/api";
import { costSimulationApi } from "@/api/costSimulation";
import { vectorAssetsApi } from "@/api/vectorAssets";
import { parsePreliminaryCostBreakdown } from "@/lib/preliminaryCostBreakdown";
import {
  aggregateLayerSimulations,
  layerStatusLabel,
  overallAnalysisWarning,
  suggestionsToQuoteInputStrings,
  type SvgLayerAnalysisResult,
  type SvgLayerSimulationRow,
  type SvgMultiLayerPreliminaryAggregate,
} from "@/lib/svgLayerAnalysis";
import {
  ACM_CASSETTED_QUOTE_INPUT_FIELDS,
  buildAcmCasettedQuoteInputPayload,
  buildCutAcmQuoteInputPayload,
  CUT_ACM_QUOTE_INPUT_FIELDS,
  rearLipWarning,
  TPL_ACM_CASSETTED_PANEL,
  TPL_CUT_ACM_LETTERS,
} from "@/lib/acmQuoteInput";
import { buildVolumetricQuoteInputPayload } from "@/lib/volumetricQuoteInput";

function formatRON(val: number) {
  return val.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

export interface SvgLayerAnalysisPanelProps {
  templates: ProductTemplateEntity[];
  quantity: number;
  widthMm: number;
  heightMm: number;
  depthMm: number;
  marginPct: number;
  vatPct: number;
  discountPct: number;
  quoteInputValues: Record<string, string>;
  onApplyVolumetricSuggestions: (values: Record<string, string>) => void;
}

export default function SvgLayerAnalysisPanel({
  templates,
  quantity,
  widthMm,
  heightMm,
  depthMm,
  marginPct,
  vatPct,
  discountPct,
  quoteInputValues,
  onApplyVolumetricSuggestions,
}: SvgLayerAnalysisPanelProps) {
  const [svgText, setSvgText] = useState("");
  const [analysis, setAnalysis] = useState<SvgLayerAnalysisResult | null>(null);
  const [layerSims, setLayerSims] =
    useState<SvgMultiLayerPreliminaryAggregate | null>(null);
  const [loading, setLoading] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [acmLayerInputs, setAcmLayerInputs] = useState<
    Record<string, Record<string, string>>
  >({});

  const templateCodes = templates.map((t) => t.template_code);

  function getAcmLayerValues(layerId: string, templateCode: string) {
    const stored = acmLayerInputs[layerId] ?? {};
    const layer = analysis?.layers.find((l) => l.svg_layer_id === layerId);
    const suggested = layer
      ? suggestionsToQuoteInputStrings(layer.quote_input_suggestions)
      : {};
    const defaults: Record<string, string> = {
      acm_thickness_mm: "3",
      fold_sides: "all",
      v_groove_angle_deg: "135",
      rear_lip_mm: "25",
      return_depth_mm: "60",
      ...suggested,
      ...stored,
    };
    if (templateCode === TPL_ACM_CASSETTED_PANEL) {
      if (!defaults.panel_width_mm && widthMm > 0) {
        defaults.panel_width_mm = String(widthMm);
      }
      if (!defaults.panel_height_mm && heightMm > 0) {
        defaults.panel_height_mm = String(heightMm);
      }
    }
    return defaults;
  }

  function setAcmField(layerId: string, key: string, value: string) {
    setAcmLayerInputs((prev) => ({
      ...prev,
      [layerId]: { ...(prev[layerId] ?? {}), [key]: value },
    }));
  }

  async function handleAnalyze() {
    setLoading(true);
    setError(null);
    setLayerSims(null);
    try {
      const result = await vectorAssetsApi.analyzeLayers(svgText, {
        knownTemplateCodes: templateCodes,
      });
      setAnalysis(result);
      if (result.parse_status === "failed") {
        setError(result.error_detail ?? result.error_code ?? "Analiză eșuată");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analiză SVG eșuată");
    } finally {
      setLoading(false);
    }
  }

  function handleApplyLayerSuggestions(templateCode: string) {
    const layer = analysis?.layers.find(
      (l) => l.mapped_template_code === templateCode
    );
    if (!layer) return;
    const suggested = suggestionsToQuoteInputStrings(
      layer.quote_input_suggestions
    );
    onApplyVolumetricSuggestions({ ...quoteInputValues, ...suggested });
  }

  async function handleSimulateMappedLayers() {
    if (!analysis?.layers.length) return;
    setSimulating(true);
    setError(null);
    const rows: SvgLayerSimulationRow[] = [];

    for (const layer of analysis.layers) {
      if (layer.mapping_status !== "mapped" || !layer.mapped_template_code) {
        rows.push({
          layer,
          template_id: null,
          simulation: null,
          error: null,
        });
        continue;
      }

      const tpl = templates.find(
        (t) => t.template_code === layer.mapped_template_code
      );
      if (!tpl) {
        rows.push({
          layer,
          template_id: null,
          simulation: null,
          error: "template_id_not_found",
        });
        continue;
      }

      if (layer.mapped_template_code === "TPL-VOLUMETRIC-LETTERS") {
        const merged = {
          ...quoteInputValues,
          ...suggestionsToQuoteInputStrings(layer.quote_input_suggestions),
        };
        const qi = buildVolumetricQuoteInputPayload(merged);
        try {
          const sim = await costSimulationApi.simulate({
            template_id: tpl.id,
            quantity,
            quote_input: {
              ...qi,
              width_mm: widthMm,
              height_mm: heightMm,
              depth_mm: depthMm,
            },
            pricing: {
              margin_pct: marginPct,
              vat_pct: vatPct,
              discount_pct: discountPct,
            },
            simulation_context: {
              source: "svg_layer_analysis",
              reason: `preliminary layer ${layer.svg_layer_name}`,
            },
          });
          rows.push({ layer, template_id: tpl.id, simulation: sim, error: null });
        } catch (e) {
          rows.push({
            layer,
            template_id: tpl.id,
            simulation: null,
            error: e instanceof Error ? e.message : "simulate failed",
          });
        }
        continue;
      }

      if (layer.mapped_template_code === TPL_ACM_CASSETTED_PANEL) {
        const merged = getAcmLayerValues(layer.svg_layer_id, TPL_ACM_CASSETTED_PANEL);
        const qi = buildAcmCasettedQuoteInputPayload(merged);
        try {
          const sim = await costSimulationApi.simulate({
            template_id: tpl.id,
            quantity,
            quote_input: qi,
            pricing: {
              margin_pct: marginPct,
              vat_pct: vatPct,
              discount_pct: discountPct,
            },
            simulation_context: {
              source: "svg_layer_analysis",
              reason: `preliminary layer ${layer.svg_layer_name}`,
            },
          });
          rows.push({ layer, template_id: tpl.id, simulation: sim, error: null });
        } catch (e) {
          rows.push({
            layer,
            template_id: tpl.id,
            simulation: null,
            error: e instanceof Error ? e.message : "simulate failed",
          });
        }
        continue;
      }

      if (layer.mapped_template_code === TPL_CUT_ACM_LETTERS) {
        const merged = getAcmLayerValues(layer.svg_layer_id, TPL_CUT_ACM_LETTERS);
        const qi = buildCutAcmQuoteInputPayload(merged);
        try {
          const sim = await costSimulationApi.simulate({
            template_id: tpl.id,
            quantity,
            quote_input: qi,
            pricing: {
              margin_pct: marginPct,
              vat_pct: vatPct,
              discount_pct: discountPct,
            },
            simulation_context: {
              source: "svg_layer_analysis",
              reason: `preliminary layer ${layer.svg_layer_name}`,
            },
          });
          rows.push({ layer, template_id: tpl.id, simulation: sim, error: null });
        } catch (e) {
          rows.push({
            layer,
            template_id: tpl.id,
            simulation: null,
            error: e instanceof Error ? e.message : "simulate failed",
          });
        }
        continue;
      }

      rows.push({
        layer,
        template_id: tpl.id,
        simulation: null,
        error: "quote_input_contract_unknown",
      });
    }

    setLayerSims(aggregateLayerSimulations(rows));
    setSimulating(false);
  }

  return (
    <div className="space-y-3 border border-[#1E293B] rounded-lg bg-[#0B111E] p-3">
      <div className="flex items-center gap-2">
        <Layers className="w-4 h-4 text-cyan-400" />
        <h3 className="text-[12px] font-semibold text-slate-200">
          Analiză SVG — layere grafice → template_code
        </h3>
      </div>
      <p className="text-[10px] text-slate-500">{overallAnalysisWarning()}</p>
      <textarea
        value={svgText}
        onChange={(e) => setSvgText(e.target.value)}
        rows={4}
        placeholder="Lipiți SVG cu layere denumite exact ca template_code (ex. TPL-VOLUMETRIC-LETTERS)…"
        className="w-full bg-[#111827] border border-[#2A3548] rounded px-3 py-2 text-[11px] font-mono text-slate-300 outline-none focus:border-cyan-500/50"
      />
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={handleAnalyze}
          disabled={loading || !svgText.trim()}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] rounded bg-cyan-700 hover:bg-cyan-600 text-white disabled:opacity-40"
        >
          {loading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Layers className="w-3.5 h-3.5" />
          )}
          Analizează layere
        </button>
        {analysis && analysis.layers.some((l) => l.mapping_status === "mapped") && (
          <button
            type="button"
            onClick={handleSimulateMappedLayers}
            disabled={simulating}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] rounded border border-cyan-700/50 text-cyan-200 hover:bg-cyan-900/20 disabled:opacity-40"
          >
            {simulating ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Play className="w-3.5 h-3.5" />
            )}
            Simulează layere mapate
          </button>
        )}
      </div>

      {error && (
        <div className="text-[11px] text-red-300 bg-red-900/20 border border-red-800/40 rounded px-3 py-2">
          {error}
        </div>
      )}

      {analysis && analysis.parse_status === "parsed" && (
        <div className="space-y-2">
          <div className="text-[10px] text-slate-400 font-mono">
            Layere: {analysis.summary.layers_found ?? 0} · mapate:{" "}
            {analysis.summary.layers_mapped ?? 0} · nemapate:{" "}
            {analysis.summary.layers_unmapped ?? 0}
          </div>
          <div className="overflow-auto max-h-56 border border-[#1E293B] rounded">
            <table className="w-full text-[11px]">
              <thead className="bg-[#111827] text-[10px] uppercase text-slate-500">
                <tr>
                  <th className="text-left px-2 py-1.5">Layer (template_code)</th>
                  <th className="text-left px-2 py-1.5">Status</th>
                  <th className="text-left px-2 py-1.5">Metrici</th>
                  <th className="text-right px-2 py-1.5">Acțiuni</th>
                </tr>
              </thead>
              <tbody>
                {analysis.layers.map((layer) => (
                  <tr key={layer.svg_layer_id} className="border-t border-[#1E293B]">
                    <td className="px-2 py-1.5">
                      <div className="font-mono text-cyan-300">
                        {layer.mapped_template_code ?? layer.svg_layer_name}
                      </div>
                      {layer.mapped_template_code && (
                        <div className="text-[10px] text-slate-500">
                          {layer.human_description}
                        </div>
                      )}
                      {layer.suggested_template_code && (
                        <div className="text-[10px] text-amber-300/80">
                          Sugerat: {layer.suggested_template_code}
                        </div>
                      )}
                    </td>
                    <td className="px-2 py-1.5 text-slate-300">
                      {layerStatusLabel(layer)}
                    </td>
                    <td className="px-2 py-1.5 text-slate-400">
                      {layer.metrics.metrics_confidence === "unavailable"
                        ? "—"
                        : `${layer.metrics.metrics_confidence} · arie ${
                            layer.metrics.path_area_m2 ?? "?"
                          } m²`}
                    </td>
                    <td className="px-2 py-1.5 text-right">
                      {layer.mapped_template_code === "TPL-VOLUMETRIC-LETTERS" &&
                        layer.metrics.metrics_confidence !== "unavailable" && (
                          <button
                            type="button"
                            onClick={() =>
                              handleApplyLayerSuggestions(
                                "TPL-VOLUMETRIC-LETTERS"
                              )
                            }
                            className="text-[10px] text-cyan-300 hover:underline"
                          >
                            Aplică sugestii
                          </button>
                        )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {analysis.layers
            .filter(
              (l) =>
                l.mapping_status === "mapped" &&
                (l.mapped_template_code === TPL_ACM_CASSETTED_PANEL ||
                  l.mapped_template_code === TPL_CUT_ACM_LETTERS)
            )
            .map((layer) => {
              const fields =
                layer.mapped_template_code === TPL_ACM_CASSETTED_PANEL
                  ? ACM_CASSETTED_QUOTE_INPUT_FIELDS
                  : CUT_ACM_QUOTE_INPUT_FIELDS;
              const values = getAcmLayerValues(
                layer.svg_layer_id,
                layer.mapped_template_code!
              );
              const rearWarn =
                layer.mapped_template_code === TPL_ACM_CASSETTED_PANEL
                  ? rearLipWarning(parseFloat(values.rear_lip_mm ?? "0"))
                  : null;
              return (
                <div
                  key={`inputs-${layer.svg_layer_id}`}
                  className="border border-[#1E293B] rounded p-2 space-y-2"
                >
                  <div className="text-[10px] font-mono text-cyan-300">
                    {layer.mapped_template_code} — parametri manuali
                  </div>
                  <p className="text-[10px] text-slate-500">
                    Date geometrice necesită completare/verificare manuală. Nu
                    confunda panoul ACM cu Forex 10 mm (spate litere volumetrice).
                  </p>
                  {rearWarn && (
                    <p className="text-[10px] text-amber-300">{rearWarn}</p>
                  )}
                  <div className="grid grid-cols-2 gap-2">
                    {fields.map((field) => (
                      <label
                        key={field.key}
                        className="text-[10px] text-slate-400 space-y-0.5"
                      >
                        {field.label}
                        {field.selectOptions ? (
                          <select
                            value={values[field.key] ?? field.placeholder}
                            onChange={(e) =>
                              setAcmField(
                                layer.svg_layer_id,
                                field.key,
                                e.target.value
                              )
                            }
                            className="w-full bg-[#111827] border border-[#2A3548] rounded px-2 py-1 text-[11px] text-slate-200"
                          >
                            {field.selectOptions.map((opt) => (
                              <option key={opt.value} value={opt.value}>
                                {opt.label}
                              </option>
                            ))}
                          </select>
                        ) : field.numberOptions ? (
                          <select
                            value={values[field.key] ?? String(field.numberOptions[0])}
                            onChange={(e) =>
                              setAcmField(
                                layer.svg_layer_id,
                                field.key,
                                e.target.value
                              )
                            }
                            className="w-full bg-[#111827] border border-[#2A3548] rounded px-2 py-1 text-[11px] text-slate-200"
                          >
                            {field.numberOptions.map((opt) => (
                              <option key={opt} value={String(opt)}>
                                {opt} mm
                              </option>
                            ))}
                          </select>
                        ) : (
                          <input
                            type="number"
                            value={values[field.key] ?? ""}
                            placeholder={field.placeholder}
                            onChange={(e) =>
                              setAcmField(
                                layer.svg_layer_id,
                                field.key,
                                e.target.value
                              )
                            }
                            className="w-full bg-[#111827] border border-[#2A3548] rounded px-2 py-1 text-[11px] text-slate-200"
                          />
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
        </div>
      )}

      {layerSims && (
        <div className="space-y-2 border-t border-[#1E293B] pt-2">
          <div className="flex items-center gap-2 text-[11px] text-amber-200">
            <AlertTriangle className="w-3.5 h-3.5" />
            {layerSims.is_partial
              ? "Total preliminar parțial — layere nemapate/blocate excluse parțial"
              : "Total preliminar layere mapate"}
          </div>
          <div className="text-[12px] font-semibold text-slate-100">
            Total preliminar layere: {formatRON(layerSims.preliminary_total)} RON
          </div>
          {layerSims.layer_results.map((row) => {
            if (!row.simulation) return null;
            const breakdown = parsePreliminaryCostBreakdown(row.simulation);
            return (
              <div
                key={row.layer.svg_layer_id}
                className="text-[10px] bg-[#111827] border border-[#1E293B] rounded px-2 py-1.5"
              >
                <span className="font-mono text-cyan-300">
                  {row.layer.mapped_template_code}
                </span>
                {" · "}
                {formatRON(breakdown.partialTotal)} RON ({row.simulation.status})
                {" · "}
                persisted=false
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
