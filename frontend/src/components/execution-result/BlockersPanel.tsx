import { AlertTriangle } from "lucide-react";
import type { AlertsResponse, ObservabilityReport } from "@/api/execution";
import { blockersFor, humanReason } from "./executionResultWorkspace";

export function BlockersPanel({ observability, alerts }: { observability: ObservabilityReport; alerts: AlertsResponse | null }) {
  const blockers = blockersFor(observability, alerts);
  if (blockers.length === 0) return null;
  return (
    <section className="rounded-lg border border-wo-warning/40 bg-wo-warning/10 p-4" data-testid="execution-blockers">
      <div className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-wo-warning" /><h2 className="text-sm font-semibold text-wo-text-primary">Necesită atenție</h2></div>
      <ul className="mt-2 space-y-1 text-[12px] text-wo-text-secondary">
        {blockers.map((reason) => <li key={reason}>{humanReason(reason)}</li>)}
      </ul>
    </section>
  );
}
