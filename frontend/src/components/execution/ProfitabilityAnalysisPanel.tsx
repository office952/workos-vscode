/**
 * ProfitabilityAnalysisPanel — read-only display (Slice 10.4).
 * Binds GET /api/v1/profitability-analysis/order/{order_id}.
 * Does not compute profit, reprice, or mutate order/quote.
 */
import { useCallback, useEffect, useState } from "react";
import { BarChart3, Info } from "lucide-react";
import {
  fetchProfitabilityAnalysis,
  ProfitabilityAnalysisNotFoundError,
  PROFITABILITY_STATUS_LABELS,
  PROFITABILITY_WARNING_LABELS,
  type ProfitabilityAnalysisResponse,
} from "@/api/profitabilityAnalysis";

interface ProfitabilityAnalysisPanelProps {
  orderId: number;
}

function fmtMoney(
  value: number | null | undefined,
  currency: string | null | undefined,
): string {
  if (value === null || value === undefined) return "—";
  const unit = currency?.trim() || "RON";
  return `${value.toFixed(2)} ${unit}`;
}

function fmtPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(2)}%`;
}

function fmtMinutes(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${value.toFixed(1)} min`;
}

export function ProfitabilityAnalysisPanel({
  orderId,
}: ProfitabilityAnalysisPanelProps) {
  const [data, setData] = useState<ProfitabilityAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchProfitabilityAnalysis(orderId);
      setData(result);
    } catch (e) {
      if (e instanceof ProfitabilityAnalysisNotFoundError) {
        setError("Profitability analysis unavailable for this order");
        setData(null);
      } else {
        const msg = e instanceof Error ? e.message : "unknown error";
        setError(msg);
        setData(null);
      }
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const statusLabel = data
    ? PROFITABILITY_STATUS_LABELS[data.profitability_status] ??
      data.profitability_status
    : null;

  return (
    <section
      className="bg-[#1A2236] border border-[#2A3548] rounded-lg"
      data-testid="profitability-analysis-panel"
    >
      <header className="flex items-center justify-between px-4 py-3 border-b border-[#2A3548]">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-violet-400" />
          <h2 className="text-[13px] font-bold text-slate-200 uppercase tracking-wide">
            Profitability analysis
          </h2>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded-full">
            READ-ONLY
          </span>
        </div>
        {statusLabel && (
          <span
            className="inline-block px-2.5 py-0.5 text-[11px] font-bold rounded border bg-violet-900/30 text-violet-200 border-violet-700"
            data-testid="profitability-analysis-status"
          >
            {statusLabel}
          </span>
        )}
      </header>

      <div className="p-4 space-y-4">
        {loading && (
          <p className="text-[12px] text-slate-500">
            Loading profitability analysis...
          </p>
        )}

        {!loading && error && (
          <div className="flex items-start gap-2 bg-slate-800/40 border border-slate-700 rounded-md px-3 py-2">
            <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <p className="text-[12px] text-slate-300">{error}</p>
          </div>
        )}

        {!loading && data && (
          <>
            <p className="text-[11px] text-slate-500">
              Read-only analysis. Does not change accepted quote.
            </p>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
              <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                <p className="text-slate-500 uppercase text-[10px] tracking-wide">
                  Accepted revenue
                </p>
                <p
                  className="mt-1 text-slate-200 font-semibold tabular-nums"
                  data-testid="profitability-accepted-revenue"
                >
                  {fmtMoney(
                    data.accepted_commercial_total,
                    data.accepted_currency,
                  )}
                </p>
              </div>
              <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                <p className="text-slate-500 uppercase text-[10px] tracking-wide">
                  Estimated internal cost
                </p>
                <p
                  className="mt-1 text-slate-200 font-semibold tabular-nums"
                  data-testid="profitability-estimated-internal"
                >
                  {fmtMoney(
                    data.estimated_internal_total,
                    data.accepted_currency,
                  )}
                </p>
              </div>
              <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                <p className="text-slate-500 uppercase text-[10px] tracking-wide">
                  Estimated margin
                </p>
                <p
                  className="mt-1 text-slate-200 font-semibold tabular-nums"
                  data-testid="profitability-estimated-margin"
                >
                  {fmtMoney(
                    data.estimated_margin_amount,
                    data.accepted_currency,
                  )}
                  <span className="text-slate-500 font-normal">
                    {" "}
                    / {fmtPct(data.estimated_margin_percent)}
                  </span>
                </p>
              </div>
              <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                <p className="text-slate-500 uppercase text-[10px] tracking-wide">
                  Actual cost
                </p>
                <p className="mt-1 text-slate-200 font-semibold tabular-nums">
                  {data.actual_total_cost === null
                    ? "not available"
                    : fmtMoney(
                        data.actual_total_cost,
                        data.accepted_currency,
                      )}
                </p>
              </div>
            </div>

            {!data.has_execution_reality && (
              <div
                role="status"
                className="flex items-start gap-2 bg-slate-800/40 border border-slate-700 rounded-md px-3 py-2"
                data-testid="profitability-actuals-missing"
              >
                <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
                <p className="text-[12px] text-slate-300">
                  Actuals not recorded yet. Estimated figures only — not final
                  profit.
                </p>
              </div>
            )}

            {data.has_execution_reality && (
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                  <p className="text-slate-500 uppercase text-[10px] tracking-wide">
                    Actual labor minutes
                  </p>
                  <p className="mt-1 text-slate-200 font-semibold tabular-nums">
                    {fmtMinutes(data.actual_labor_minutes)}
                  </p>
                </div>
                <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                  <p className="text-slate-500 uppercase text-[10px] tracking-wide">
                    Known material cost
                  </p>
                  <p
                    className="mt-1 text-slate-200 font-semibold tabular-nums"
                    data-testid="profitability-known-material-cost"
                  >
                    {data.actual_materials_total === null ||
                    data.actual_materials_total === undefined
                      ? "not captured"
                      : fmtMoney(
                          data.actual_materials_total,
                          data.accepted_currency,
                        )}
                  </p>
                </div>
                <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                  <p className="text-slate-500 uppercase text-[10px] tracking-wide">
                    Known margin (partial)
                  </p>
                  <p
                    className="mt-1 text-slate-200 font-semibold tabular-nums"
                    data-testid="profitability-known-margin"
                  >
                    {data.known_actual_margin === null ||
                    data.known_actual_margin === undefined
                      ? "unavailable — cost coverage incomplete"
                      : fmtMoney(
                          data.known_actual_margin,
                          data.accepted_currency,
                        )}
                  </p>
                </div>
                <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                  <p className="text-slate-500 uppercase text-[10px] tracking-wide">
                    Cost coverage
                  </p>
                  <p
                    className="mt-1 text-slate-200 font-semibold"
                    data-testid="profitability-coverage-status"
                  >
                    {data.cost_coverage_status ?? "NOT_AVAILABLE"}
                  </p>
                </div>
              </div>
            )}

            {data.profitability_wording && data.profitability_wording.length > 0 && (
              <ul
                className="space-y-1 text-[11px] text-slate-400"
                data-testid="profitability-wording"
              >
                {data.profitability_wording.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            )}

            {data.has_execution_reality && (
              <p className="text-[11px] text-slate-500">
                Final actual margin unavailable until labor monetary cost is
                authorized —{" "}
                {data.actual_margin_amount === null
                  ? "actual_margin remains unset (not final profit)"
                  : fmtMoney(data.actual_margin_amount, data.accepted_currency)}
              </p>
            )}

            {data.warnings.length > 0 && (
              <div>
                <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1.5">
                  Warnings
                </p>
                <ul className="flex flex-wrap gap-1.5">
                  {data.warnings.map((code) => (
                    <li
                      key={code}
                      className="inline-flex items-center px-2 py-0.5 text-[10px] font-medium rounded border bg-amber-900/20 text-amber-200 border-amber-800/60"
                    >
                      {PROFITABILITY_WARNING_LABELS[code] ?? code}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            <p className="text-[10px] text-slate-600">
              retroactive_change_allowed=
              {String(data.retroactive_change_allowed)} · write_back_performed=
              {String(data.write_back_performed)} · No write-back
            </p>
          </>
        )}
      </div>
    </section>
  );
}
