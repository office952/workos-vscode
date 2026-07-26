import { ImageOff, Layers, Loader2, ScanSearch } from "lucide-react";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { VECTOR_FILE_TYPE_OPTIONS } from "@/lib/intakeVolumetricSpec";
import { MANUAL_SVG_LAYER_MAPPING_TARGETS } from "@/lib/intakeVectorLayerMapping";
import { layerStatusLabel, type SvgLayerAnalysisResult } from "@/lib/svgLayerAnalysis";
import {
  MAPPING_ROLE_HELP,
  buildSafeSvgPreview,
  buildVectorStudioInfo,
  humanizeLayerMappingStatus,
  humanizeVectorAnalysisStatus,
  humanizeVectorParseStatus,
  resolvePreviewUnavailableMessage,
  svgPreviewDataUrl,
} from "@/lib/vectorStudioPreview";

function fieldClass() {
  return "w-full bg-wo-surface-inset border border-wo-border-strong rounded-lg px-3 py-2 text-[12px] text-slate-200 outline-none focus:border-blue-500/50";
}

function labelClass() {
  return "text-[11px] text-slate-400 font-semibold mb-1 block";
}

export interface VectorStudioPanelProps {
  spec: IntakeProductSpec;
  readOnly?: boolean;
  svgPasteText: string;
  onSvgPasteTextChange: (value: string) => void;
  layerAnalysis: SvgLayerAnalysisResult | null;
  layerAnalyzing: boolean;
  layerAnalysisError: string | null;
  onAnalyze: () => void;
  onLayerMappingChange: (layerName: string, target: string) => void;
  onSpecUpdate: <K extends keyof IntakeProductSpec>(key: K, value: IntakeProductSpec[K]) => void;
  onFilenameChange: (filename: string) => void;
  onFileTypeChange: (fileType: IntakeProductSpec["vector_file_type"]) => void;
}

export function VectorStudioPanel({
  spec,
  readOnly = false,
  svgPasteText,
  onSvgPasteTextChange,
  layerAnalysis,
  layerAnalyzing,
  layerAnalysisError,
  onAnalyze,
  onLayerMappingChange,
  onSpecUpdate,
  onFilenameChange,
  onFileTypeChange,
}: VectorStudioPanelProps) {
  const info = buildVectorStudioInfo(spec, layerAnalysis);
  const previewSource =
    layerAnalysis?.preview_svg ?? buildSafeSvgPreview(svgPasteText) ?? null;
  const pasteBlocked =
    Boolean(svgPasteText.trim()) && !layerAnalysis?.preview_svg && !previewSource;
  const previewUrl = previewSource ? svgPreviewDataUrl(previewSource) : null;
  const previewMessage = resolvePreviewUnavailableMessage(
    info,
    spec.vector_file_type === "svg",
    Boolean(previewUrl),
    pasteBlocked
  );
  const isSvg = spec.vector_file_type === "svg";
  const isDxfDwg = spec.vector_file_type === "dxf" || spec.vector_file_type === "dwg";
  const showLiveLayerRows = (layerAnalysis?.layers.length ?? 0) > 0;
  const showPersistedLayerRows =
    !showLiveLayerRows && (spec.vector_detected_layers_summary?.length ?? 0) > 0;

  return (
    <div className="md:col-span-2 space-y-4 rounded-xl border border-wo-border-subtle bg-wo-surface-inset/60 p-4">
      <div className="flex items-center gap-2">
        <Layers className="w-4 h-4 text-purple-400" />
        <h4 className="text-[13px] font-bold text-slate-200">Vector Studio</h4>
      </div>

      <p className="text-[10px] text-slate-500">
        Un singur fișier poate conține mai multe layere. Mapează fiecare layer după rol.
        Doar layerul de litere poate fi folosit pentru geometria literelor; barele/supportul
        nu intră în perimetrul literelor.
      </p>
      <p className="text-[10px] text-amber-300/80 bg-amber-900/10 border border-amber-800/30 rounded px-2 py-1.5">
        Pentru ofertă comercială finală: fișier vector + layer litere mapat + review manual
        sau analiză validă. Mapping-ul nu inventează geometrie — aria/perimetrul se introduc
        manual în QuoteWizard.
      </p>
      {spec.vector_manual_review_approved === true && (
        <p className="text-[10px] text-emerald-300/90">
          Vector verificat manual. Geometria trebuie introdusă manual sau extrasă valid.
        </p>
      )}

      {/* File metadata */}
      <div className="grid gap-3 md:grid-cols-2">
        <div>
          <label className={labelClass()}>Nume fișier vector / producție</label>
          <input
            className={fieldClass()}
            value={spec.vector_file_name ?? ""}
            onChange={(e) => onFilenameChange(e.target.value)}
            readOnly={readOnly}
            placeholder="ex. litere_fata.svg"
          />
        </div>
        <div>
          <label className={labelClass()}>Tip fișier</label>
          {readOnly ? (
            <input className={fieldClass()} value={spec.vector_file_type ?? "—"} readOnly />
          ) : (
            <select
              className={fieldClass()}
              value={spec.vector_file_type ?? ""}
              onChange={(e) =>
                onFileTypeChange(
                  (e.target.value || undefined) as IntakeProductSpec["vector_file_type"]
                )
              }
            >
              <option value="">—</option>
              {VECTOR_FILE_TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Preview */}
      <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-inset p-3">
        <p className="text-[11px] text-slate-400 font-semibold mb-2">Previzualizare vector</p>
        {isSvg && previewUrl ? (
          <div className="flex items-center justify-center min-h-[140px] max-h-[220px] overflow-hidden rounded-md bg-wo-surface-inset border border-wo-border-subtle">
            <img
              src={previewUrl}
              alt="Previzualizare SVG"
              className="max-w-full max-h-[200px] object-contain"
            />
          </div>
        ) : isSvg ? (
          <div className="flex items-center gap-2 text-[11px] text-slate-500 min-h-[80px]">
            <ImageOff className="w-4 h-4 shrink-0" />
            {previewMessage}
          </div>
        ) : isDxfDwg ? (
          <div className="flex items-center gap-2 text-[11px] text-slate-500 min-h-[80px]">
            <ImageOff className="w-4 h-4 shrink-0" />
            Preview indisponibil pentru DWG/DXF momentan. Fișier atașat ca sursă/producție.
            Necesită review manual sau conversie SVG.
          </div>
        ) : (
          <p className="text-[11px] text-slate-500">Selectează tip SVG pentru analiză layer.</p>
        )}
        <p className="text-[10px] text-amber-400/80 mt-2">
          Preview-ul este orientativ. Calculul de ofertă folosește doar metrici extrase valid
          sau valori introduse manual.
        </p>
      </div>

      {/* Analysis summary under preview */}
      <div className="space-y-2">
        <p className="text-[11px] text-slate-400 font-semibold">Analiză</p>
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 text-[10px]">
          <InfoCard label="Nume fișier" value={info.fileName} />
          <InfoCard label="Tip fișier" value={info.fileType} />
          <InfoCard
            label="Status parsare"
            value={humanizeVectorParseStatus(info.parseStatus)}
          />
          <InfoCard
            label="Sanitizare"
            value={info.sanitized ? "DOCTYPE eliminat (copie analiză)" : "—"}
          />
          <InfoCard
            label="Status analiză"
            value={humanizeVectorAnalysisStatus(info.analysisStatus)}
          />
          <InfoCard label={info.layersDetectedLabel} value={info.layersDetectedValue} />
          {info.savedMappingsCount > 0 && (
            <InfoCard
              label="Layere mapate salvate"
              value={String(info.savedMappingsCount)}
              highlight="ok"
            />
          )}
          <InfoCard
            label="Layer litere"
            value={info.lettersLayerLabel}
            highlight={info.lettersMapped ? "ok" : "warn"}
          />
          <InfoCard
            label="Metrici geometrice"
            value={
              info.hasMetrics
                ? info.metricLabels.join("; ")
                : "Nu s-au extras metrici geometrice automat."
            }
          />
        </div>
      </div>

      {/* Saved mappings when no live analysis rows */}
      {info.savedMappingsCount > 0 && !showLiveLayerRows && (
        <div className="rounded-lg border border-wo-border-subtle bg-wo-surface-inset p-3 space-y-1">
          <p className="text-[11px] text-slate-400 font-semibold">Mapări salvate în specificație</p>
          <ul className="text-[10px] text-emerald-400/90 space-y-0.5">
            {info.savedMappingsList.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </div>
      )}

      {info.warnings.length > 0 && (
        <ul className="text-[10px] text-slate-500 space-y-1 list-disc pl-4">
          {info.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      {isSvg && !readOnly && (
        <div>
          <label className={labelClass()}>Conținut SVG pentru analiză (local)</label>
          <textarea
            className={`${fieldClass()} min-h-[80px] resize-y font-mono text-[10px]`}
            value={svgPasteText}
            onChange={(e) => onSvgPasteTextChange(e.target.value)}
            placeholder="Lipește XML SVG exportat (ex. CorelDRAW) — nu se salvează în spec."
          />
          <div className="mt-2 flex items-center gap-2">
            <button
              type="button"
              onClick={onAnalyze}
              disabled={layerAnalyzing}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded-lg text-[11px] font-semibold"
            >
              {layerAnalyzing ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ScanSearch className="w-3.5 h-3.5" />
              )}
              Analizează layere SVG
            </button>
            {layerAnalysisError && (
              <span className="text-[10px] text-red-400">{layerAnalysisError}</span>
            )}
          </div>
        </div>
      )}

      {/* Live layer mapping rows */}
      {showLiveLayerRows && (
        <div className="space-y-2">
          <p className="text-[11px] text-slate-400 font-semibold">Mapare layere (analiză curentă)</p>
          {layerAnalysis!.layers.map((layer) => {
            const selected = spec.svg_layer_mappings?.[layer.svg_layer_name] ?? "";
            return (
              <div
                key={layer.svg_layer_id}
                className="rounded-lg border border-wo-border-subtle bg-wo-surface-inset p-3 space-y-2"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <span className="text-[11px] text-slate-200 font-mono">
                    {layer.svg_layer_name}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {layerStatusLabel(layer)}
                    {layer.mapped_by ? ` · ${layer.mapped_by}` : ""}
                  </span>
                </div>
                {layer.detected_kind && layer.detected_kind !== "unknown" && (
                  <p className="text-[10px] text-slate-500">Detectat: {layer.detected_kind}</p>
                )}
                {!readOnly && (
                  <select
                    className={fieldClass()}
                    value={selected}
                    onChange={(e) => onLayerMappingChange(layer.svg_layer_name, e.target.value)}
                  >
                    {MANUAL_SVG_LAYER_MAPPING_TARGETS.map((o) => (
                      <option key={o.value || "unset"} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                )}
                {selected && MAPPING_ROLE_HELP[selected] && (
                  <p className="text-[10px] text-slate-500">{MAPPING_ROLE_HELP[selected]}</p>
                )}
                {!Object.values(layer.quote_input_suggestions).some((v) => v != null) && (
                  <p className="text-[10px] text-slate-500">
                    Fără metrici geometrice extrase automat.
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Persisted layer summary (read-only) when no live session */}
      {showPersistedLayerRows && (
        <div className="space-y-2">
          <p className="text-[11px] text-slate-400 font-semibold">Layere (rezumat salvat)</p>
          {spec.vector_detected_layers_summary!.map((row) => (
            <div
              key={row.layer_name}
              className="rounded-lg border border-wo-border-subtle bg-wo-surface-inset p-3 space-y-1"
            >
              <span className="text-[11px] text-slate-200 font-mono">{row.layer_name}</span>
              <p className="text-[10px] text-slate-500">
                {humanizeLayerMappingStatus(row.mapping_status, row.mapped_by)}
                {row.mapped_target ? ` → ${row.mapped_target}` : ""}
              </p>
              {row.detected_kind && (
                <p className="text-[10px] text-slate-500">Detectat: {row.detected_kind}</p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Manual review */}
      <div className="rounded-lg border border-wo-border-subtle p-3 space-y-2">
        <p className="text-[11px] text-slate-400 font-semibold">Review manual vector</p>
        <label className="flex items-center gap-2 text-[12px] text-slate-300 cursor-pointer">
          <input
            type="checkbox"
            checked={spec.vector_manual_review_approved === true}
            onChange={(e) => {
              const approved = e.target.checked;
              onSpecUpdate("vector_manual_review_approved", approved);
              if (approved) {
                onSpecUpdate("vector_analysis_status", "manual_review_approved");
              } else if (spec.vector_file_name) {
                onSpecUpdate("vector_analysis_status", "attached_unanalyzed");
              } else {
                onSpecUpdate("vector_analysis_status", "not_provided");
              }
            }}
            disabled={readOnly}
            className="rounded border-slate-600"
          />
          Confirmare manuală vector (DWG/DXF sau analiză fără metrici)
        </label>
        <p className="text-[10px] text-slate-500">
          Bifează doar după verificarea manuală a fișierului vector. Această confirmare nu
          inventează arie, perimetru sau număr de litere.
        </p>
        <label className={labelClass()}>Note verificare vector</label>
        <textarea
          className={`${fieldClass()} min-h-[56px] resize-y`}
          value={spec.vector_manual_review_notes ?? ""}
          onChange={(e) => onSpecUpdate("vector_manual_review_notes", e.target.value)}
          readOnly={readOnly}
          placeholder="Conversie DXF→SVG, verificare contur, reviewer..."
        />
      </div>
    </div>
  );
}

function InfoCard({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "ok" | "warn";
}) {
  return (
    <div className="rounded-md border border-wo-border-subtle bg-wo-surface-inset px-2 py-1.5">
      <p className="text-slate-500">{label}</p>
      <p
        className={
          highlight === "ok"
            ? "text-emerald-400/90"
            : highlight === "warn"
              ? "text-amber-400/90"
              : "text-slate-300"
        }
      >
        {value}
      </p>
    </div>
  );
}
