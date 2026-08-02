import type { ObservabilityReport } from "@/api/execution";
import { formatMinutes } from "./executionResultWorkspace";

export function PlanActualPanel({ observability }: { observability: ObservabilityReport }) {
  return (
    <section className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4" data-testid="execution-plan-actual">
      <h2 className="text-sm font-semibold text-wo-text-primary">Plan și realizat</h2>
      <p className="mt-1 text-[11px] text-wo-text-muted">Abaterile sunt furnizate de backend; valorile lipsă nu sunt estimate.</p>
      <dl className="mt-3 grid grid-cols-3 gap-2 text-[12px]">
        <Value label="Planificat" value={formatMinutes(observability.plan_total_estimated_minutes)} />
        <Value label="Realizat" value={formatMinutes(observability.reality_total_actual_minutes)} />
        <Value label="Abatere" value={observability.delta_minutes == null ? "—" : `${observability.delta_minutes.toFixed(1)} min${observability.delta_pct == null ? "" : ` · ${observability.delta_pct.toFixed(2)}%`}`} />
      </dl>
    </section>
  );
}
function Value({ label, value }: { label: string; value: string }) {
  return <div className="rounded-md bg-wo-surface-raised px-3 py-2"><dt className="text-[10px] uppercase text-wo-text-muted">{label}</dt><dd className="mt-1 font-semibold text-wo-text-primary">{value}</dd></div>;
}
