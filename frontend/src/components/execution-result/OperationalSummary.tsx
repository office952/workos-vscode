import type { ObservabilityReport } from "@/api/execution";
import { formatMinutes, statusLabel } from "./executionResultWorkspace";

export function OperationalSummary({ observability }: { observability: ObservabilityReport }) {
  return (
    <section className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4" data-testid="execution-operational-summary">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-wo-text-primary">Situație operațională</h2>
        <span className="text-[11px] text-wo-text-secondary">{statusLabel(observability.status)}</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4 text-[12px]">
        <Metric label="Comandă" value={observability.has_order ? "Disponibilă" : "Lipsește"} />
        <Metric label="Plan" value={observability.has_plan ? "Pregătit" : "Lipsește"} />
        <Metric label="Durată planificată" value={formatMinutes(observability.plan_total_estimated_minutes)} />
        <Metric label="Durată realizată" value={formatMinutes(observability.reality_total_actual_minutes)} />
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md bg-wo-surface-raised px-3 py-2"><p className="text-[10px] uppercase text-wo-text-muted">{label}</p><p className="mt-1 font-semibold text-wo-text-primary">{value}</p></div>;
}
