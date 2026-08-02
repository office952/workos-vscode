import { ArrowLeft, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
import type { ObservabilityReport } from "@/api/execution";
import { statusLabel } from "./executionResultWorkspace";

export function ExecutionResultHeader({
  observability,
  refreshedAt,
  loading,
  onRefresh,
}: {
  observability: ObservabilityReport | null;
  refreshedAt: string | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-wo-border-subtle pb-4">
      <div className="space-y-1">
        <Link to="/execution" className="inline-flex items-center gap-1 text-[12px] text-wo-text-muted hover:text-wo-text-primary">
          <ArrowLeft className="h-3.5 w-3.5" /> Execuție
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-bold text-wo-text-primary">Rezultat execuție</h1>
          {observability ? <span className="rounded-full bg-wo-surface-raised px-2 py-0.5 text-[11px] text-wo-text-secondary">{observability.order_code} · #{observability.order_id}</span> : null}
          {observability ? <span className="rounded-full border border-wo-border-subtle px-2 py-0.5 text-[11px] text-wo-text-secondary">{statusLabel(observability.status)}</span> : null}
        </div>
        <p className="text-[12px] text-wo-text-muted">Lucru, costuri realizate și închidere operațională din faptele backend.</p>
      </div>
      <div className="flex items-center gap-3">
        {refreshedAt ? <span className="text-[11px] text-wo-text-muted">Actualizat: {refreshedAt}</span> : null}
        <button type="button" onClick={onRefresh} disabled={loading} className="inline-flex items-center gap-1.5 rounded-md bg-blue-600 px-3 py-1.5 text-[12px] font-semibold text-white hover:bg-blue-500 disabled:opacity-50">
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} /> Reîncarcă
        </button>
      </div>
    </header>
  );
}
