/**
 * Wave 4 — Execution closure readiness + authorized close/reopen.
 * Displays backend F3/F4 facts only. Does not invent costs or margins.
 */
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import {
  closeExecutionJob,
  getClosureReadiness,
  reopenExecutionJob,
  type ClosureReadiness,
} from "@/api/executionJobClosure";
import {
  getProfitabilityActualReadModel,
  type ProfitabilityActualReadModel,
} from "@/api/profitabilityActualReadModel";
import { closureReasonRo, closureStateLabel } from "@/lib/executionClosureUi";

export function ExecutionClosurePanel({
  orderId,
  onChanged,
}: {
  orderId: number;
  onChanged?: () => void;
}) {
  const { user } = useAuth();
  const role = String(user?.role || "").toLowerCase();
  const canClose = role === "admin" || role === "manager";
  const isOperator = role === "operator";

  const [readiness, setReadiness] = useState<ClosureReadiness | null>(null);
  const [profit, setProfit] = useState<ProfitabilityActualReadModel | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [reopenReason, setReopenReason] = useState("");
  const [showTech, setShowTech] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [ready, model] = await Promise.all([
        getClosureReadiness(orderId).catch((e: unknown) => {
          throw e;
        }),
        canClose
          ? getProfitabilityActualReadModel(orderId).catch(() => null)
          : Promise.resolve(null),
      ]);
      setReadiness(ready);
      setProfit(model);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "load_failed";
      setError(msg);
      setReadiness(null);
    } finally {
      setLoading(false);
    }
  }, [orderId, canClose]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const costs = profit?.actual_cost_truth as Record<string, any> | undefined;
  const result = profit?.profitability_result as Record<string, any> | undefined;
  const closed =
    String(costs?.execution_closure_status || costs?.job_closure_status || "") === "closed";
  const state = closureStateLabel({
    ready: readiness?.ready ?? null,
    closed,
    loading,
  });

  async function onClose() {
    if (!canClose || busy) return;
    setBusy(true);
    setError(null);
    try {
      await closeExecutionJob(orderId, { authorized: true });
      await refresh();
      onChanged?.();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "close_failed");
    } finally {
      setBusy(false);
    }
  }

  async function onReopen() {
    if (!canClose || busy) return;
    if (!reopenReason.trim()) {
      setError("reopen_reason_required");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await reopenExecutionJob(orderId, reopenReason.trim());
      setReopenReason("");
      await refresh();
      onChanged?.();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "reopen_failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      className="rounded-lg border border-wo-border-subtle bg-wo-surface p-3 space-y-3"
      data-testid="execution-closure-panel"
    >
      <header className="space-y-1">
        <h2 className="text-sm font-semibold text-wo-text-primary">
          Închidere job operațional
        </h2>
        <p className="text-[10px] text-wo-text-muted">
          Nu închide oferta comercială. Costurile lipsă nu apar ca zero. Close doar cu
          autorizare.
        </p>
      </header>

      <div
        className={
          state.tone === "ready"
            ? "rounded-md border border-wo-success/40 bg-wo-success/10 px-3 py-2"
            : state.tone === "closed"
              ? "rounded-md border border-wo-info/40 bg-wo-info/10 px-3 py-2"
              : state.tone === "blocked"
                ? "rounded-md border border-wo-warning/40 bg-wo-warning/10 px-3 py-2"
                : "rounded-md border border-wo-border-subtle px-3 py-2"
        }
        data-testid="execution-closure-state"
      >
        <p className="text-[12px] font-semibold text-wo-text-primary">{state.title}</p>
        {!closed && readiness && !readiness.ready ? (
          <p className="mt-1 text-[11px] text-wo-text-secondary" data-testid="execution-closure-blocker">
            {closureReasonRo(readiness.reason)}
          </p>
        ) : null}
      </div>

      {canClose && costs ? (
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3 text-[11px]">
          <div>
            <p className="text-wo-text-muted">Manoperă</p>
            <p className="font-medium text-wo-text-primary">
              {costs.labor_cost_status === "complete" ? "Completă (înghețată)" : "Incompletă"}
            </p>
          </div>
          <div>
            <p className="text-wo-text-muted">Material</p>
            <p className="font-medium text-wo-text-primary">
              {costs.material_cost_status === "complete" ? "Complet (înghețat)" : "Incomplet"}
            </p>
          </div>
          <div>
            <p className="text-wo-text-muted">Marjă actuală</p>
            <p className="font-medium text-wo-text-primary">
              {result?.actual_margin?.amount?.available
                ? `${result.actual_margin.amount.value} (job închis)`
                : "Indisponibilă"}
            </p>
          </div>
        </div>
      ) : null}

      {isOperator ? (
        <p className="text-[11px] text-wo-text-muted" data-testid="execution-closure-operator-note">
          Operator: vezi doar pregătirea operațională. Ratele brute și marja nu sunt expuse.
        </p>
      ) : null}

      {error ? (
        <p className="text-[11px] text-wo-danger" data-testid="execution-closure-error">
          {closureReasonRo(error)}
        </p>
      ) : null}

      {canClose ? (
        <div className="flex flex-wrap items-end gap-2">
          {!closed ? (
            <button
              type="button"
              disabled={busy || loading || !readiness?.ready}
              onClick={() => void onClose()}
              data-testid="execution-closure-close"
              className="rounded-md border border-wo-border-strong bg-wo-surface-raised px-3 py-1.5 text-[11px] font-semibold text-wo-text-primary hover:bg-wo-hover disabled:opacity-50"
            >
              Închide job (autorizat)
            </button>
          ) : (
            <>
              <label className="flex min-w-[14rem] flex-1 flex-col gap-0.5 text-[11px]">
                <span className="text-wo-text-muted">Motiv redeschidere</span>
                <input
                  value={reopenReason}
                  onChange={(e) => setReopenReason(e.target.value)}
                  data-testid="execution-closure-reopen-reason"
                  className="rounded border border-wo-border-strong bg-wo-surface-input px-2 py-1 text-wo-text-primary"
                  placeholder="Obligatoriu"
                />
              </label>
              <button
                type="button"
                disabled={busy || loading}
                onClick={() => void onReopen()}
                data-testid="execution-closure-reopen"
                className="rounded-md border border-wo-border-strong px-3 py-1.5 text-[11px] font-semibold text-wo-text-secondary hover:bg-wo-hover disabled:opacity-50"
              >
                Redeschide
              </button>
            </>
          )}
        </div>
      ) : null}

      <details
        open={showTech}
        onToggle={(e) => setShowTech((e.target as HTMLDetailsElement).open)}
        className="text-[10px] text-wo-text-muted"
      >
        <summary className="cursor-pointer select-none" data-testid="execution-closure-tech">
          Detalii tehnice
        </summary>
        <pre className="mt-1 overflow-x-auto whitespace-pre-wrap rounded border border-wo-border-subtle bg-wo-surface-raised p-2">
          {JSON.stringify(
            {
              readiness,
              actual_cost_status: costs?.actual_cost_status,
              material_valuation_status: costs?.material_valuation_status,
              actual_margin_status: result?.actual_margin?.actual_margin_status,
            },
            null,
            2,
          )}
        </pre>
      </details>
    </section>
  );
}
