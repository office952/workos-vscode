/**
 * Wave 5 — Pregătire pentru atribuire (evaluare read-only).
 *
 * Surfaces GET assignment-readiness. Never Assign / Auto-assign / Reserve / Schedule / Start.
 * VALID_CANDIDATE_FOR_FUTURE_ASSIGNMENT ≠ PERSISTED_ASSIGNMENT ≠ AUTHORIZED_TO_START.
 */
import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import {
  executionApi,
  type AssignmentReadinessAuditResponse,
} from "@/api/execution";

export function AssignmentReadinessPanel({ orderId }: { orderId: number }) {
  const [data, setData] = useState<AssignmentReadinessAuditResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    executionApi
      .getAssignmentReadinessAudit(orderId)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Eroare necunoscută");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  if (loading) {
    return (
      <section
        className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
        data-testid="assignment-readiness-panel-loading"
      >
        <p className="text-[12px] text-wo-text-muted">Se încarcă pregătirea pentru atribuire…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section
        className="rounded-lg border border-amber-800/40 bg-amber-950/20 p-4"
        data-testid="assignment-readiness-panel-error"
      >
        <h2 className="text-sm font-semibold text-amber-100">Pregătire pentru atribuire</h2>
        <p className="mt-1 text-[11px] text-amber-100/80">
          Evaluare read-only indisponibilă: {error}
        </p>
      </section>
    );
  }

  if (!data) return null;

  if (data.status === "blocked_not_materialized" || data.status === "plan_not_found") {
    return (
      <section
        className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
        data-testid="assignment-readiness-panel"
      >
        <h2 className="text-sm font-semibold text-wo-text-primary">Pregătire pentru atribuire</h2>
        <p className="mt-1 text-[11px] text-wo-text-muted">
          {data.status === "plan_not_found"
            ? "Plan indisponibil — auditul de atribuire nu poate rula."
            : "Taskuri operaționale nematerializate — atribuirea rămâne neautorizată."}
        </p>
        <p className="mt-2 text-[11px] font-medium text-wo-error">
          Atribuire neautorizată — {data.wave5_boundary?.authorization_blocker}
        </p>
      </section>
    );
  }

  const eligibleReady = (data.tasks || []).filter(
    (t) => t.future_assign_preconditions?.eligibility_ready && t.future_assign_preconditions?.has_eligible_candidate,
  ).length;
  const unassigned = (data.tasks || []).filter(
    (t) => t.current_assignment?.status === "unassigned",
  ).length;

  return (
    <section
      className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
      data-testid="assignment-readiness-panel"
    >
      <div className="flex items-start gap-2">
        <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-wo-warning" aria-hidden />
        <div className="min-w-0 flex-1">
          <h2 className="text-sm font-semibold text-wo-text-primary">Pregătire pentru atribuire</h2>
          <p className="mt-0.5 text-[11px] text-wo-text-muted">
            Evaluare read-only — contractul comenzii și validările cunoscute. Această evaluare nu
            atribuie angajați și nu rezervă resurse.
          </p>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
        <span className="rounded bg-wo-error/10 px-2 py-0.5 font-medium text-wo-error">
          Atribuire neautorizată
        </span>
        <span className="rounded bg-wo-surface-raised px-2 py-0.5 text-wo-text-muted">
          {data.operational_task_count ?? 0} taskuri operaționale
        </span>
        <span className="rounded bg-wo-surface-raised px-2 py-0.5 text-wo-text-muted">
          {unassigned} neatribuite
        </span>
        <span className="rounded bg-wo-surface-raised px-2 py-0.5 text-wo-text-muted">
          {eligibleReady} cu candidat eligibil (tehnic)
        </span>
        <span className="rounded bg-wo-surface-raised px-2 py-0.5 text-wo-text-muted">
          Atribuiri: {data.employee_assignment_count ?? 0} · Utilaje:{" "}
          {data.machine_assignment_count ?? 0}
        </span>
        <span className="rounded bg-wo-warning/10 px-2 py-0.5 text-wo-warning">
          Programare: {data.scheduling ?? "HOLD"}
        </span>
      </div>

      <div className="mt-3 overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-left text-[11px]">
          <thead>
            <tr className="border-b border-wo-border-subtle text-wo-text-muted">
              <th className="py-1.5 pr-2 font-medium">Task</th>
              <th className="py-1.5 pr-2 font-medium">Workcenter înghețat</th>
              <th className="py-1.5 pr-2 font-medium">Eligibilitate</th>
              <th className="py-1.5 pr-2 font-medium">Candidați</th>
              <th className="py-1.5 pr-2 font-medium">Atribuire</th>
              <th className="py-1.5 font-medium">Minute</th>
            </tr>
          </thead>
          <tbody>
            {(data.tasks || []).map((task) => (
              <tr key={task.task_key} className="border-b border-wo-border-subtle/60">
                <td className="py-1.5 pr-2 text-wo-text-primary">{task.task_key}</td>
                <td className="py-1.5 pr-2 text-wo-text-secondary">
                  {task.frozen_workcenter || "—"}
                </td>
                <td className="py-1.5 pr-2 text-wo-text-secondary">
                  {task.eligibility_status || "—"}
                </td>
                <td className="py-1.5 pr-2 text-wo-text-secondary">
                  {task.eligible_employee_count}
                </td>
                <td className="py-1.5 pr-2">
                  <span
                    className={
                      task.current_assignment?.status === "unassigned"
                        ? "text-wo-text-muted"
                        : "text-wo-warning"
                    }
                  >
                    {task.current_assignment?.status === "unassigned"
                      ? "Neatribuit"
                      : `Atribuit #${task.current_assignment?.assigned_employee_id}`}
                  </span>
                </td>
                <td className="py-1.5 text-wo-text-muted">
                  {task.estimated_minutes == null ? "null" : String(task.estimated_minutes)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <details className="mt-3 text-[11px] text-wo-text-muted">
        <summary className="cursor-pointer select-none font-medium text-wo-text-secondary">
          Detalii contract atribuire
        </summary>
        <div className="mt-1 space-y-1">
          <p>
            Contract canonic:{" "}
            <code className="text-wo-text-secondary">
              {data.command_contract?.canonical_route ||
                "PATCH /api/v1/execution/plan/{order_id}/tasks/{task_id}/assign"}
            </code>
          </p>
          <p>
            Idempotency: {data.command_contract?.idempotency?.status || "—"} ·
            Transactionality: {data.command_contract?.transactionality?.status || "—"}
            {data.command_contract?.legacy_bypass?.classification
              ? ` · Legacy bypass: ${data.command_contract.legacy_bypass.classification}`
              : null}
          </p>
          <p className="text-wo-warning">
            Protecții lipsă / parțiale:{" "}
            {(data.protections?.missing_or_partial || []).slice(0, 3).join("; ") || "—"}
          </p>
        </div>
      </details>
    </section>
  );
}
