/**
 * BUILD 9 — Output Blocks Coverage Diagnostics Component.
 *
 * Displays coverage report for output blocks across all product templates.
 * Read-only — no mutation, no persist.
 */

import { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Eye,
  Info,
  Loader2,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import {
  fetchOutputBlocksCoverage,
  type OutputBlocksCoverage,
} from "@/api/quoteOutputComposition";

export default function OutputBlocksCoverageDiagnostics() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<OutputBlocksCoverage | null>(null);
  const [expanded, setExpanded] = useState(false);

  const handleFetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchOutputBlocksCoverage();
      setData(result);
      setExpanded(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la încărcarea diagnosticelor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-lg border border-[#1E293B] bg-[#111827] overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-[#1a2234] transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <Eye className="w-4 h-4 text-cyan-400" />
          <span className="text-[13px] font-semibold text-slate-200">
            Output Blocks Coverage
          </span>
          {data && (
            <span
              className={`px-1.5 py-0.5 rounded text-[9px] border ${
                data.coverage_pct >= 80
                  ? "bg-green-900/30 border-green-800/50 text-green-300"
                  : data.coverage_pct >= 50
                  ? "bg-amber-900/30 border-amber-800/50 text-amber-300"
                  : "bg-red-900/30 border-red-800/50 text-red-300"
              }`}
            >
              {data.coverage_pct}%
            </span>
          )}
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleFetch();
          }}
          disabled={loading}
          className="flex items-center gap-1 px-2 py-1 rounded text-[10px] bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-colors"
        >
          {loading ? (
            <Loader2 className="w-3 h-3 animate-spin" />
          ) : (
            <Eye className="w-3 h-3" />
          )}
          {data ? "Refresh" : "Load"}
        </button>
      </div>

      {/* Content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-[#1E293B]">
          {/* Disclaimer */}
          <div className="flex items-start gap-2 px-3 py-2 mt-3 rounded border border-cyan-800/50 bg-cyan-900/20">
            <Info className="w-3.5 h-3.5 text-cyan-400 mt-0.5 shrink-0" />
            <p className="text-[10px] text-cyan-300">
              Diagnostics: shows which templates have output_blocks_json configured in their
              blueprint dossier. Read-only — no mutation.
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-start gap-2 px-3 py-2 rounded border border-red-800/50 bg-red-900/20">
              <ShieldAlert className="w-3.5 h-3.5 text-red-400 mt-0.5 shrink-0" />
              <p className="text-[10px] text-red-300">{error}</p>
            </div>
          )}

          {/* Loading */}
          {loading && (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
            </div>
          )}

          {/* Results */}
          {data && !loading && (
            <div className="space-y-3">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-2">
                <div className="rounded border border-[#2A3548] bg-[#0D1321] p-2 text-center">
                  <p className="text-[16px] font-bold text-slate-100">{data.total_templates}</p>
                  <p className="text-[9px] text-slate-500 uppercase">Total</p>
                </div>
                <div className="rounded border border-green-800/40 bg-green-900/10 p-2 text-center">
                  <p className="text-[16px] font-bold text-green-300">{data.covered_count}</p>
                  <p className="text-[9px] text-green-500 uppercase">Covered</p>
                </div>
                <div className="rounded border border-amber-800/40 bg-amber-900/10 p-2 text-center">
                  <p className="text-[16px] font-bold text-amber-300">{data.partial_count}</p>
                  <p className="text-[9px] text-amber-500 uppercase">Partial</p>
                </div>
                <div className="rounded border border-red-800/40 bg-red-900/10 p-2 text-center">
                  <p className="text-[16px] font-bold text-red-300">{data.missing_count}</p>
                  <p className="text-[9px] text-red-500 uppercase">Missing</p>
                </div>
              </div>

              {/* Covered */}
              {data.covered.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-green-400 uppercase flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3" /> Covered ({data.covered.length})
                  </p>
                  {data.covered.map((item, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between px-2 py-1.5 rounded bg-green-900/10 border border-green-800/30"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-green-300">
                          {item.template_code}
                        </span>
                        <span className="text-[9px] text-slate-500">{item.description}</span>
                      </div>
                      <span className="text-[9px] text-green-400">{item.block_count} blocks</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Partial */}
              {data.partial.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-amber-400 uppercase flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3" /> Partial ({data.partial.length})
                  </p>
                  {data.partial.map((item, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between px-2 py-1.5 rounded bg-amber-900/10 border border-amber-800/30"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-amber-300">
                          {item.template_code}
                        </span>
                        <span className="text-[9px] text-slate-500">{item.reason}</span>
                      </div>
                      <span className="text-[9px] text-amber-400">
                        {item.complete_blocks}/{item.block_count}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Missing */}
              {data.missing.length > 0 && (
                <div className="space-y-1">
                  <p className="text-[10px] font-bold text-red-400 uppercase flex items-center gap-1">
                    <XCircle className="w-3 h-3" /> Missing ({data.missing.length})
                  </p>
                  {data.missing.map((item, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between px-2 py-1.5 rounded bg-red-900/10 border border-red-800/30"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono text-red-300">
                          {item.template_code}
                        </span>
                        <span className="text-[9px] text-slate-500">{item.description}</span>
                      </div>
                      <span className="text-[9px] text-red-400">{item.reason}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}