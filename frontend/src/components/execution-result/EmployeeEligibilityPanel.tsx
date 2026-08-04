/**
 * Wave 4 — Candidați eligibili (read-only DEC-015).
 *
 * Presents GET employee-eligibility verbatim. Never Assign / Schedule / Start.
 * ELIGIBLE_CANDIDATE ≠ ASSIGNED_EMPLOYEE ≠ AUTHORIZED_TO_START.
 */
import { useEffect, useState } from "react";
import { Users } from "lucide-react";
import {
  executionApi,
  type EmployeeEligibilityReadModelResponse,
} from "@/api/execution";
import {
  eligibilityStatusLabel,
  eligibilityStatusTone,
  type EligibilityTone,
} from "./employeeEligibilityDisplay";

const TONE_CLASSES: Record<EligibilityTone, string> = {
  success: "bg-wo-success/10 text-wo-success",
  warning: "bg-wo-warning/10 text-wo-warning",
  danger: "bg-wo-error/10 text-wo-error",
  neutral: "bg-wo-surface-raised text-wo-text-muted",
};

export function EmployeeEligibilityPanel({ orderId }: { orderId: number }) {
  const [data, setData] = useState<EmployeeEligibilityReadModelResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    executionApi
      .getEmployeeEligibilityReadModel(orderId)
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
        data-testid="employee-eligibility-panel-loading"
      >
        <p className="text-[12px] text-wo-text-muted">Se încarcă eligibilitatea angajaților…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section
        className="rounded-lg border border-amber-800/40 bg-amber-950/20 p-4"
        data-testid="employee-eligibility-panel-error"
      >
        <h2 className="text-sm font-semibold text-amber-100">Candidați eligibili</h2>
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
        data-testid="employee-eligibility-panel-empty"
      >
        <div className="flex items-center gap-2">
          <Users className="h-4 w-4 text-wo-text-muted" />
          <h2 className="text-sm font-semibold text-wo-text-primary">Candidați eligibili</h2>
        </div>
        <p className="mt-1 text-[11px] text-wo-text-muted">
          {data.status === "plan_not_found"
            ? "Plan de execuție lipsă — eligibilitatea nu poate fi evaluată."
            : "Taskurile operaționale nu sunt materializate — eligibilitatea rămâne neevaluată."}
        </p>
      </section>
    );
  }

  if (data.status !== "ok" || data.tasks.length === 0) return null;

  return (
    <section
      className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
      data-testid="employee-eligibility-panel"
    >
      <div className="flex items-center gap-2">
        <Users className="h-4 w-4 text-wo-text-muted" />
        <h2 className="text-sm font-semibold text-wo-text-primary">Candidați eligibili</h2>
      </div>
      <p className="mt-1 text-[11px] text-wo-text-muted">
        Evaluare read-only · potrivire rol/skill pe workcenter înghețat. Candidat eligibil ≠ atribuit ≠
        autorizat să pornească. Assignment și scheduling rămân blocate.
      </p>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-left text-[12px]">
          <thead>
            <tr className="text-wo-text-muted">
              <th className="pb-1 pr-3 font-medium">Task</th>
              <th className="pb-1 pr-3 font-medium">Workcenter înghețat</th>
              <th className="pb-1 pr-3 font-medium">Candidați</th>
              <th className="pb-1 pr-3 font-medium">Stare</th>
            </tr>
          </thead>
          <tbody>
            {data.tasks.map((task, index) => {
              const tone = eligibilityStatusTone(task.eligibility_status);
              const names = (task.eligible_employees ?? [])
                .slice(0, 5)
                .map((e) => e.display_name)
                .filter(Boolean);
              const extra =
                (task.eligible_employee_count ?? 0) > names.length
                  ? ` +${(task.eligible_employee_count ?? 0) - names.length}`
                  : "";
              return (
                <tr
                  key={task.task_key || `${task.source_operation_code ?? "task"}-${index}`}
                  className="border-t border-wo-border-subtle align-top"
                  data-testid="employee-eligibility-row"
                >
                  <td className="py-1.5 pr-3 text-wo-text-primary">
                    <span className="font-mono text-[11px]">
                      {task.source_operation_code ?? task.task_key ?? "—"}
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 text-wo-text-secondary">
                    {task.workcenter_code ?? "—"}
                  </td>
                  <td className="py-1.5 pr-3 text-wo-text-secondary">
                    {names.length > 0 ? `${names.join(", ")}${extra}` : "—"}
                    {task.blockers?.length ? (
                      <p className="mt-0.5 text-[10px] text-wo-text-muted">
                        {task.blockers.join(" · ")}
                      </p>
                    ) : null}
                  </td>
                  <td className="py-1.5 pr-3">
                    <span
                      className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${TONE_CLASSES[tone]}`}
                    >
                      {eligibilityStatusLabel(task.eligibility_status)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[10px] text-wo-text-muted" data-testid="employee-eligibility-summary">
        {(data.ready_or_warning_count ?? 0)} cu candidați · {(data.blocked_count ?? 0)} blocate ·
        neatribuit · neprogramat · sesiuni blocate
      </p>
    </section>
  );
}
