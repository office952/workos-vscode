/**
 * F7C — Pregătire resurse (read-only ORR allow-list ∩ registru utilaje).
 *
 * Compact, read-only. Presents backend truth from
 * `GET /execution/plan-v2/from-order/{id}/resource-readiness` verbatim —
 * NO Assign / Schedule / Start controls, NO computed minutes, NO invented
 * machine assignment. Section is display-only and never mutates state.
 */
import { useEffect, useState } from "react";
import { Wrench } from "lucide-react";
import { executionApi, type OperationalResourceReadinessResponse } from "@/api/execution";
import {
  resourceReadinessStatusLabel,
  resourceReadinessStatusTone,
  resourceRequirementModeLabel,
  workcenterRegistryStatusLabel,
  type ResourceReadinessTone,
} from "./resourceReadinessDisplay";

const TONE_CLASSES: Record<ResourceReadinessTone, string> = {
  success: "bg-wo-success/10 text-wo-success",
  warning: "bg-wo-warning/10 text-wo-warning",
  danger: "bg-wo-error/10 text-wo-error",
  neutral: "bg-wo-surface-raised text-wo-text-muted",
};

function StatusBadge({ status }: { status: OperationalResourceReadinessResponse["tasks"][number]["status"] }) {
  const tone = resourceReadinessStatusTone(status);
  return (
    <span className={`inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${TONE_CLASSES[tone]}`}>
      {resourceReadinessStatusLabel(status)}
    </span>
  );
}

export function ResourceReadinessPanel({ orderId }: { orderId: number }) {
  const [data, setData] = useState<OperationalResourceReadinessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    executionApi
      .getOperationalResourceReadiness(orderId)
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

  if (loading) return null;
  if (error) return null; // Silent — this is a supplementary read-only section, not a blocking gate.
  if (!data || data.status !== "ok" || data.tasks.length === 0) return null;

  return (
    <section
      className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
      data-testid="resource-readiness-panel"
    >
      <div className="flex items-center gap-2">
        <Wrench className="h-4 w-4 text-wo-text-muted" />
        <h2 className="text-sm font-semibold text-wo-text-primary">Pregătire resurse</h2>
      </div>
      <p className="mt-1 text-[11px] text-wo-text-muted">
        Sursă: registru ORR ∩ registru utilaje. Nicio alocare automată — doar constatare.
      </p>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-left text-[12px]">
          <thead>
            <tr className="text-wo-text-muted">
              <th className="pb-1 pr-3 font-medium">Operație</th>
              <th className="pb-1 pr-3 font-medium">Punct de lucru</th>
              <th className="pb-1 pr-3 font-medium">Cerință resursă</th>
              <th className="pb-1 pr-3 font-medium">Utilaje compatibile</th>
              <th className="pb-1 pr-3 font-medium">Stare</th>
            </tr>
          </thead>
          <tbody>
            {data.tasks.map((task, index) => {
              const machineNames = task.compatible_machine_candidates.map((c) => c.resource_code);
              const workAreaNames = task.work_area_candidates.map((c) => c.resource_code);
              return (
                <tr
                  key={task.task_key ?? `${task.source_operation_code ?? "task"}-${index}`}
                  className="border-t border-wo-border-subtle align-top"
                >
                  <td className="py-1.5 pr-3 text-wo-text-primary">
                    {task.display_name ?? task.source_operation_code ?? "—"}
                  </td>
                  <td className="py-1.5 pr-3 text-wo-text-secondary">
                    {task.workcenter_code ?? "—"}
                    <span className="ml-1 text-[10px] text-wo-text-muted">
                      ({workcenterRegistryStatusLabel(task.workcenter_registry_status)})
                    </span>
                  </td>
                  <td className="py-1.5 pr-3 text-wo-text-secondary">
                    {resourceRequirementModeLabel(task.resource_requirement_mode)}
                  </td>
                  <td className="py-1.5 pr-3 text-wo-text-secondary">
                    {machineNames.length > 0
                      ? machineNames.join(", ")
                      : workAreaNames.length > 0
                        ? workAreaNames.join(", ")
                        : "—"}
                  </td>
                  <td className="py-1.5 pr-3">
                    <StatusBadge status={task.status} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {data.warning_count > 0 || data.blocked_count > 0 ? (
        <p className="mt-2 text-[10px] text-wo-text-muted">
          {data.ready_count} pregătit(e) · {data.warning_count} cu atenționări · {data.blocked_count} blocate.
        </p>
      ) : null}
    </section>
  );
}
