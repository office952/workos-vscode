/**
 * PostJobTruthPanel — coherent post-job truth on /execution/:orderId.
 * Renders backend reconciliation only; no client-side canonical math.
 */
import { useCallback, useEffect, useState } from "react";
import { ClipboardList, Info } from "lucide-react";
import {
  fetchPostJobTruth,
  formatPresenceValue,
  PostJobTruthNotFoundError,
  type PostJobTruthResponse,
} from "@/api/postJobTruth";

interface PostJobTruthPanelProps {
  orderId: number;
}

function PresenceBadge({ presence }: { presence: string }) {
  return (
    <span
      className="inline-block px-1.5 py-0.5 text-[9px] font-semibold uppercase rounded border border-slate-600 text-slate-400 bg-slate-800/60"
      data-testid="post-job-presence"
    >
      {presence}
    </span>
  );
}

export function PostJobTruthPanel({ orderId }: PostJobTruthPanelProps) {
  const [data, setData] = useState<PostJobTruthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchPostJobTruth(orderId));
    } catch (e) {
      if (e instanceof PostJobTruthNotFoundError) {
        setError("Post-job truth unavailable for this order");
      } else {
        setError(e instanceof Error ? e.message : "unknown error");
      }
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const currency = data?.baseline.currency ?? null;

  return (
    <section
      className="bg-[#1A2236] border border-[#2A3548] rounded-lg"
      data-testid="post-job-truth-panel"
    >
      <header className="flex items-center justify-between px-4 py-3 border-b border-[#2A3548]">
        <div className="flex items-center gap-2">
          <ClipboardList className="w-4 h-4 text-emerald-400" />
          <h2 className="text-[13px] font-bold text-slate-200 uppercase tracking-wide">
            Post-job truth
          </h2>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded-full">
            READ-ONLY
          </span>
        </div>
        {data && (
          <span
            className="inline-block px-2.5 py-0.5 text-[11px] font-bold rounded border bg-emerald-900/30 text-emerald-200 border-emerald-700"
            data-testid="post-job-coverage-status"
          >
            {data.profitability.cost_coverage_status}
          </span>
        )}
      </header>

      <div className="p-4 space-y-4">
        {loading && (
          <p className="text-[12px] text-slate-500" data-testid="post-job-loading">
            Loading post-job truth...
          </p>
        )}

        {!loading && error && (
          <div
            className="flex items-start gap-2 bg-slate-800/40 border border-slate-700 rounded-md px-3 py-2"
            data-testid="post-job-error"
          >
            <Info className="w-4 h-4 text-slate-400 shrink-0 mt-0.5" />
            <p className="text-[12px] text-slate-300">{error}</p>
          </div>
        )}

        {!loading && data && (
          <>
            <div data-testid="post-job-summary">
              <p className="text-[11px] text-slate-500 mb-2">
                Plan and actual stay separate. Missing is never shown as 0.
              </p>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 text-[11px]">
                <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                  <p className="text-slate-500 uppercase text-[10px]">Revenue</p>
                  <p className="mt-1 text-slate-200 font-semibold tabular-nums">
                    {formatPresenceValue(data.baseline.revenue_net, {
                      money: true,
                      currency,
                    })}
                  </p>
                </div>
                <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                  <p className="text-slate-500 uppercase text-[10px]">
                    Closed labor min
                  </p>
                  <p
                    className="mt-1 text-slate-200 font-semibold tabular-nums"
                    data-testid="post-job-labor-minutes"
                  >
                    {formatPresenceValue(data.labor.closed_minutes_total)}
                  </p>
                  <PresenceBadge presence={data.labor.completeness} />
                </div>
                <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                  <p className="text-slate-500 uppercase text-[10px]">
                    Known material cost
                  </p>
                  <p
                    className="mt-1 text-slate-200 font-semibold tabular-nums"
                    data-testid="post-job-material-cost"
                  >
                    {formatPresenceValue(data.materials.known_actual_cost_total, {
                      money: true,
                      currency,
                    })}
                  </p>
                </div>
                <div className="bg-[#111827] rounded px-2.5 py-2 border border-[#1F2A44]">
                  <p className="text-slate-500 uppercase text-[10px]">
                    Known margin (partial)
                  </p>
                  <p
                    className="mt-1 text-slate-200 font-semibold tabular-nums"
                    data-testid="post-job-known-margin"
                  >
                    {formatPresenceValue(data.profitability.known_actual_margin, {
                      money: true,
                      currency,
                    })}
                  </p>
                </div>
              </div>
            </div>

            <div data-testid="post-job-completeness">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1.5">
                Data completeness / missing
              </p>
              <ul className="space-y-1">
                {data.missing_data.map((item) => (
                  <li
                    key={item.code}
                    className="text-[11px] text-amber-200/90 bg-amber-900/15 border border-amber-800/40 rounded px-2 py-1"
                  >
                    [{item.dimension}] {item.message}
                  </li>
                ))}
                {data.missing_data.length === 0 && (
                  <li className="text-[11px] text-slate-500">No missing-data flags</li>
                )}
              </ul>
            </div>

            <div data-testid="post-job-reconciliation">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1.5">
                Plan vs actual
              </p>
              <div className="overflow-x-auto">
                <table className="w-full text-[11px]">
                  <thead>
                    <tr className="text-slate-500 text-left">
                      <th className="py-1 pr-2">Dimension</th>
                      <th className="py-1 pr-2">Planned</th>
                      <th className="py-1 pr-2">Actual</th>
                      <th className="py-1 pr-2">Δ</th>
                      <th className="py-1">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.reconciliation.variances.map((v) => (
                      <tr key={v.dimension} className="border-t border-[#1F2A44]">
                        <td className="py-1.5 pr-2 text-slate-300">{v.dimension}</td>
                        <td className="py-1.5 pr-2 tabular-nums text-slate-300">
                          {v.planned_value === null || v.planned_value === undefined
                            ? "—"
                            : String(v.planned_value)}
                        </td>
                        <td className="py-1.5 pr-2 tabular-nums text-slate-300">
                          {v.actual_value === null || v.actual_value === undefined
                            ? "—"
                            : String(v.actual_value)}
                        </td>
                        <td className="py-1.5 pr-2 tabular-nums text-slate-300">
                          {v.absolute_variance === null
                            ? "—"
                            : String(v.absolute_variance)}
                          {v.percentage_variance != null
                            ? ` (${v.percentage_variance}%)`
                            : ""}
                        </td>
                        <td className="py-1.5">
                          <PresenceBadge presence={v.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div data-testid="post-job-materials">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1.5">
                Material actuals ({data.materials.deducted_movement_count} deducted)
              </p>
              {data.materials.lines.length === 0 ? (
                <p className="text-[11px] text-slate-500">No material lines</p>
              ) : (
                <ul className="space-y-1">
                  {data.materials.lines.map((line, idx) => (
                    <li
                      key={`${line.material_id ?? "x"}-${idx}`}
                      className="text-[11px] text-slate-300 flex flex-wrap gap-2 items-center"
                    >
                      <span>{line.material_name ?? `material ${line.material_id ?? "?"}`}</span>
                      <span className="tabular-nums">
                        qty{" "}
                        {formatPresenceValue(line.actual_deducted_quantity)}
                      </span>
                      <span className="tabular-nums">
                        cost{" "}
                        {formatPresenceValue(line.actual_known_internal_cost, {
                          money: true,
                          currency,
                        })}
                      </span>
                      <PresenceBadge presence={line.completeness} />
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div data-testid="post-job-labor">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1.5">
                Labor minutes ({data.labor.session_count} sessions
                {data.labor.open_session_count > 0
                  ? `, ${data.labor.open_session_count} open`
                  : ""}
                )
              </p>
              <p className="text-[11px] text-slate-400 mb-1">
                Labor money:{" "}
                {formatPresenceValue(data.labor.monetary_cost)} — minutes only
              </p>
              <ul className="space-y-1 max-h-40 overflow-y-auto">
                {data.labor.sessions.map((s) => (
                  <li
                    key={s.session_id}
                    className="text-[11px] text-slate-300 flex flex-wrap gap-2"
                  >
                    <span>{s.employee_name ?? s.employee_id ?? "?"}</span>
                    <span className="text-slate-500">{s.role}</span>
                    <span className="tabular-nums">
                      {s.actual_minutes == null
                        ? s.status === "still_active"
                          ? "still active"
                          : "—"
                        : `${s.actual_minutes} min`}
                    </span>
                    <PresenceBadge presence={s.completeness} />
                  </li>
                ))}
              </ul>
            </div>

            <div data-testid="post-job-machines">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1.5">
                Machine / utilaj
              </p>
              <p className="text-[11px] text-slate-400">
                {data.machines.note ?? data.machines.completeness}
              </p>
              {data.machines.items.map((item, idx) => (
                <p key={idx} className="text-[11px] text-slate-300">
                  {item.task_id}: planned {item.planned_machine_type ?? "—"} —{" "}
                  <PresenceBadge presence={item.status} />
                </p>
              ))}
            </div>

            <div data-testid="post-job-profitability">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1.5">
                Profitability coverage
              </p>
              <p
                className="text-[12px] font-semibold text-emerald-200 mb-1"
                data-testid="post-job-profit-status"
              >
                {data.profitability.profitability_status}
              </p>
              <ul className="space-y-1">
                {data.profitability.wording.map((w) => (
                  <li key={w} className="text-[11px] text-slate-300">
                    {w}
                  </li>
                ))}
              </ul>
              <p className="text-[10px] text-slate-500 mt-2">
                Included: {data.profitability.included_cost_components.join(", ") || "—"}
                {" · "}
                Excluded: {data.profitability.excluded_cost_components.join(", ")}
              </p>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default PostJobTruthPanel;
