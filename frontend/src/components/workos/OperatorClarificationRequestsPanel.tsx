import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, HelpCircle, Loader2 } from "lucide-react";
import {
  listOperatorClarificationRequests,
  resolveOperatorClarificationRequest,
  type TaskClarificationRequestDTO,
} from "@/api/employeeMobileTaskClarifications";

export default function OperatorClarificationRequestsPanel() {
  const [rows, setRows] = useState<TaskClarificationRequestDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listOperatorClarificationRequests("open");
      setRows(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nu am putut încărca solicitările.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const resolve = async (requestId: number) => {
    setResolvingId(requestId);
    try {
      await resolveOperatorClarificationRequest(requestId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nu am putut marca solicitarea.");
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <section
      className="rounded-xl border border-slate-700/60 bg-slate-900/40 p-4 space-y-3"
      data-testid="operator-clarification-requests"
    >
      <div className="flex items-center gap-2">
        <HelpCircle className="w-4 h-4 text-amber-300" aria-hidden />
        <h3 className="text-sm font-semibold text-slate-100">Solicitări informații</h3>
      </div>

      {loading && <p className="text-xs text-slate-400">Se încarcă…</p>}
      {error && <p className="text-xs text-red-300">{error}</p>}

      {!loading && !error && rows.length === 0 && (
        <p className="text-xs text-slate-500">Nicio solicitare deschisă.</p>
      )}

      {!loading && rows.length > 0 && (
        <ul className="space-y-2">
          {rows.map((row) => (
            <li
              key={row.id}
              className="rounded-lg border border-slate-700/50 bg-slate-950/40 p-3 space-y-2"
              data-testid={`operator-clarification-request-${row.id}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-slate-100">
                    {row.employee_name || `Angajat #${row.employee_id}`} · {row.task_id}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    Comandă #{row.order_id}
                    {row.created_at ? ` · ${new Date(row.created_at).toLocaleString("ro-RO")}` : ""}
                  </p>
                  <p className="text-[11px] text-slate-500" data-testid={`operator-clarification-target-${row.id}`}>
                    Către:{" "}
                    {row.target_user_name?.trim()
                      ? row.target_user_name
                      : "Coada operator/admin"}
                  </p>
                </div>
                <span className="text-[10px] uppercase tracking-wide text-amber-300">{row.status}</span>
              </div>
              <p className="text-xs text-slate-300 whitespace-pre-wrap">{row.message}</p>
              <button
                type="button"
                disabled={resolvingId === row.id}
                onClick={() => void resolve(row.id)}
                className="inline-flex items-center gap-1.5 rounded-md border border-emerald-700/50 bg-emerald-900/30 px-2.5 py-1 text-[11px] font-medium text-emerald-200 hover:bg-emerald-900/50 disabled:opacity-50"
                data-testid={`operator-clarification-resolve-${row.id}`}
              >
                {resolvingId === row.id ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden />
                ) : (
                  <CheckCircle2 className="w-3.5 h-3.5" aria-hidden />
                )}
                Marchează rezolvat
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
