/**
 * BUILD 9 — Quote Output Composition Preview Component.
 *
 * Read-only section displayed in Quote detail view.
 * Shows rendered output blocks composition for the quote.
 *
 * Rules:
 *   - Read-only — no save, no send, no create order
 *   - No mutation of any entity
 *   - Fetches on demand (button click)
 *   - Shows disclaimer prominently
 *   - Displays sections, warnings, blockers, trace
 */

import { useState } from "react";
import {
  AlertTriangle,
  Download,
  Eye,
  FileText,
  Info,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import {
  fetchQuoteOutputCompositionPreview,
  getQuoteOutputCompositionExportUrl,
  type QuoteOutputCompositionPreview as CompositionPreviewType,
} from "@/api/quoteOutputComposition";

interface Props {
  quoteId: number;
  quoteCode: string;
}

export default function QuoteOutputCompositionPreview({ quoteId, quoteCode }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompositionPreviewType | null>(null);
  const [expanded, setExpanded] = useState(false);

  const handleFetchPreview = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchQuoteOutputCompositionPreview(quoteId);
      setResult(data);
      setExpanded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la încărcarea preview-ului");
    } finally {
      setLoading(false);
    }
  };

  const handleExport = () => {
    const url = getQuoteOutputCompositionExportUrl(quoteId);
    window.open(url, "_blank");
  };

  return (
    <div className="rounded-lg border border-[#1E293B] bg-[#111827] overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-[#1a2234] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-purple-400" />
          <span className="text-[13px] font-semibold text-slate-200">
            Output Composition Preview
          </span>
          <span className="px-1.5 py-0.5 rounded text-[9px] bg-purple-900/30 border border-purple-800/50 text-purple-300">
            READ-ONLY
          </span>
        </div>
        <div className="flex items-center gap-2">
          {result && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleExport();
              }}
              className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition-colors"
              title="Export HTML Preview"
            >
              <Download className="w-3 h-3" />
              Export HTML
            </button>
          )}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleFetchPreview();
            }}
            disabled={loading}
            className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-purple-600 hover:bg-purple-500 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-colors"
          >
            {loading ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <Eye className="w-3 h-3" />
            )}
            {result ? "Refresh" : "Load Preview"}
          </button>
        </div>
      </div>

      {/* Content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-[#1E293B]">
          {/* Disclaimer */}
          <div className="flex items-start gap-2 px-3 py-2 mt-3 rounded border border-amber-800/50 bg-amber-900/20">
            <Info className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-[10px] text-amber-300">
              Preview only. Not saved, not sent, not part of any accepted order snapshot.
              No entity mutation.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 px-3 py-2 rounded border border-red-800/50 bg-red-900/20">
              <ShieldAlert className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" />
              <p className="text-[10px] text-red-300">{error}</p>
            </div>
          )}

          {/* Empty state */}
          {!result && !error && !loading && (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <FileText className="w-6 h-6 text-slate-600 mb-2" />
              <p className="text-[11px] text-slate-500">
                Apasă &quot;Load Preview&quot; pentru a vizualiza compoziția output blocks.
              </p>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
            </div>
          )}

          {/* Results */}
          {result && !loading && (
            <div className="space-y-3">
              {/* Template link status */}
              <div className="flex flex-wrap gap-2 text-[10px]">
                <span className="px-2 py-0.5 rounded bg-green-900/30 border border-green-800/50 text-green-300">
                  persisted: false
                </span>
                <span
                  className={`px-2 py-0.5 rounded border ${
                    result.template_link.status === "linked"
                      ? "bg-blue-900/30 border-blue-800/50 text-blue-300"
                      : result.template_link.status === "missing"
                      ? "bg-slate-800 border-slate-700 text-slate-400"
                      : "bg-amber-900/30 border-amber-800/50 text-amber-300"
                  }`}
                >
                  template: {result.template_link.status}
                  {result.template_link.template_code && ` (${result.template_link.template_code})`}
                </span>
                {result.template_link.dossier_id && (
                  <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                    dossier: #{result.template_link.dossier_id}
                  </span>
                )}
              </div>

              {/* Commercial summary */}
              <div className="rounded border border-[#2A3548] bg-[#0D1321] p-3">
                <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">
                  Commercial Summary (read-only)
                </p>
                <div className="flex gap-4 text-[11px]">
                  <span className="text-slate-400">
                    Subtotal:{" "}
                    <span className="text-slate-200">
                      {result.commercial_summary.subtotal.toLocaleString("ro-RO", {
                        minimumFractionDigits: 2,
                      })}{" "}
                      {result.commercial_summary.currency}
                    </span>
                  </span>
                  <span className="text-slate-400">
                    TVA:{" "}
                    <span className="text-slate-200">
                      {result.commercial_summary.vat.toLocaleString("ro-RO", {
                        minimumFractionDigits: 2,
                      })}{" "}
                      {result.commercial_summary.currency}
                    </span>
                  </span>
                  <span className="text-slate-400">
                    Total:{" "}
                    <span className="text-slate-100 font-semibold">
                      {result.commercial_summary.total.toLocaleString("ro-RO", {
                        minimumFractionDigits: 2,
                      })}{" "}
                      {result.commercial_summary.currency}
                    </span>
                  </span>
                </div>
              </div>

              {/* Blockers */}
              {result.blockers.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-red-400 uppercase">Blockers</p>
                  {result.blockers.map((b, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-1.5 px-2 py-1 rounded bg-red-900/20 border border-red-800/40"
                    >
                      <ShieldAlert className="w-3 h-3 text-red-400 mt-0.5 shrink-0" />
                      <span className="text-[10px] text-red-300">{b}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-amber-400 uppercase">Warnings</p>
                  {result.warnings.map((w, i) => (
                    <div
                      key={i}
                      className="flex items-start gap-1.5 px-2 py-1 rounded bg-amber-900/20 border border-amber-800/40"
                    >
                      <AlertTriangle className="w-3 h-3 text-amber-400 mt-0.5 shrink-0" />
                      <span className="text-[10px] text-amber-300">{w}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Rendered Sections */}
              {result.sections.length > 0 && (
                <div className="space-y-2">
                  <p className="text-[10px] font-bold text-slate-300 uppercase">
                    Rendered Sections ({result.sections.length})
                  </p>
                  {result.sections.map((section, i) => (
                    <div
                      key={i}
                      className="rounded border border-[#2A3548] bg-[#0D1321] p-3 space-y-1.5"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] font-medium text-slate-200">
                          {section.title}
                        </span>
                        <span className="px-1.5 py-0.5 rounded text-[9px] bg-slate-800 text-slate-400 border border-slate-700">
                          {section.source}
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-300 whitespace-pre-wrap leading-relaxed">
                        {section.rendered_text || (
                          <span className="italic text-slate-600">— empty —</span>
                        )}
                      </p>
                      {section.warnings.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {section.warnings.map((w, wi) => (
                            <span
                              key={wi}
                              className="px-1.5 py-0.5 rounded text-[9px] bg-amber-900/20 border border-amber-800/40 text-amber-300"
                            >
                              {w}
                            </span>
                          ))}
                        </div>
                      )}
                      {section.blockers.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {section.blockers.map((b, bi) => (
                            <span
                              key={bi}
                              className="px-1.5 py-0.5 rounded text-[9px] bg-red-900/20 border border-red-800/40 text-red-300"
                            >
                              {b}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Empty sections */}
              {result.sections.length === 0 && result.blockers.length === 0 && (
                <p className="text-[11px] text-slate-500 italic">
                  Niciun section randat — template-ul nu are output blocks configurate sau
                  nu este legat de un dossier.
                </p>
              )}

              {/* Trace */}
              <div className="pt-2 border-t border-[#1E293B]">
                <p className="text-[10px] font-bold text-slate-500 uppercase mb-1">Trace</p>
                <pre className="text-[9px] text-slate-600 bg-[#0A0F1C] rounded p-2 overflow-x-auto">
                  {JSON.stringify(result.trace, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}