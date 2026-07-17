import { useEffect, useState } from "react";
import {
  productTemplateLifecycleApi,
  type TemplateLifecycleReadiness,
} from "@/lib/api";

function statusClass(status: string): string {
  if (status === "PASS" || status === "VALIDATED" || status === "WIRED") {
    return "text-emerald-300 border-emerald-700/40 bg-emerald-950/30";
  }
  if (status === "BLOCKED") {
    return "text-rose-300 border-rose-700/40 bg-rose-950/30";
  }
  if (status === "OWNER_GATE_REQUIRED" || status === "PREVIEW_ONLY") {
    return "text-amber-200 border-amber-700/40 bg-amber-950/25";
  }
  return "text-slate-300 border-slate-700/50 bg-slate-950/40";
}

export function TemplateLifecycleReadinessPanel({
  templateCode,
}: {
  templateCode: string;
}) {
  const [data, setData] = useState<TemplateLifecycleReadiness | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    productTemplateLifecycleApi
      .readiness(templateCode)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Lifecycle readiness unavailable.");
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  if (loading) {
    return (
      <p className="text-sm text-slate-500" data-testid="product-system-lifecycle-loading">
        Se încarcă lifecycle readiness…
      </p>
    );
  }

  if (error || !data) {
    return (
      <p className="text-sm text-amber-200/90" data-testid="product-system-lifecycle-error">
        {error ?? "Nu există readiness derivat pentru acest template."}
      </p>
    );
  }

  const blockers = data.stages.flatMap((s) =>
    s.blockers.map((b) => `${s.stage}: ${b.code}`),
  );
  const warnings = data.stages.flatMap((s) =>
    s.warnings.map((w) => `${s.stage}: ${w.code}`),
  );

  return (
    <section
      data-testid="product-system-lifecycle-readiness"
      className="space-y-4 rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4 text-sm text-slate-200"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
            Lifecycle readiness
          </p>
          <p className="mt-1 font-mono text-xs text-slate-400">{data.template_code}</p>
          <p className="mt-1 text-[12px] text-slate-500">
            Derivare Product System — fără registry paralel. Read-only.
          </p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span
            className={`rounded border px-2 py-0.5 text-[10px] font-semibold ${statusClass(data.lifecycle_status)}`}
            data-testid="product-system-lifecycle-status"
          >
            {data.lifecycle_status}
          </span>
          <span className="text-[12px] text-slate-400" data-testid="product-system-lifecycle-score">
            Score: {data.readiness_score}/100
          </span>
          <span className="text-[11px] text-slate-500">
            Activare: {data.activation_eligible ? "eligibilă (gated)" : "blocată"}
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[520px] border-collapse text-left text-[11px]">
          <thead>
            <tr className="border-b border-slate-800 text-slate-500">
              <th className="py-1.5 pr-2 font-medium">Etapa</th>
              <th className="py-1.5 pr-2 font-medium">Status</th>
              <th className="py-1.5 pr-2 font-medium">Dovadă</th>
              <th className="py-1.5 font-medium">Blocker</th>
            </tr>
          </thead>
          <tbody>
            {data.stages.map((stage) => (
              <tr
                key={stage.stage}
                className="border-b border-slate-900/80"
                data-testid={`product-system-lifecycle-stage-${stage.stage}`}
              >
                <td className="py-1.5 pr-2 font-mono text-slate-300">{stage.stage}</td>
                <td className="py-1.5 pr-2">
                  <span className={`rounded border px-1.5 py-0.5 ${statusClass(stage.status)}`}>
                    {stage.status}
                  </span>
                </td>
                <td className="max-w-[220px] truncate py-1.5 pr-2 text-slate-500" title={stage.evidence.join(" | ")}>
                  {stage.evidence[0] ?? "—"}
                </td>
                <td className="py-1.5 text-rose-300/90">
                  {stage.blockers[0]?.code ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <details className="rounded-lg border border-slate-800/60 px-3 py-2">
        <summary className="cursor-pointer text-[12px] text-slate-400 hover:text-slate-200">
          Owner gates ({data.owner_gates.length})
        </summary>
        <ul className="mt-2 space-y-1 text-[11px] text-slate-400" data-testid="product-system-lifecycle-owner-gates">
          {data.owner_gates.length === 0 ? (
            <li>—</li>
          ) : (
            data.owner_gates.map((gate) => (
              <li key={gate.code}>
                <span className="font-mono text-amber-200/90">{gate.code}</span> — {gate.reason}
              </li>
            ))
          )}
        </ul>
      </details>

      <details className="rounded-lg border border-slate-800/60 px-3 py-2">
        <summary className="cursor-pointer text-[12px] text-slate-400 hover:text-slate-200">
          Impact / legacy ({(data.legacy_conflicts?.length ?? 0)} conflicts)
        </summary>
        <div className="mt-2 space-y-2 text-[11px] text-slate-400" data-testid="product-system-lifecycle-impact">
          {data.impact_summary ? (
            <div>
              <p className="text-slate-300">Changed: {data.impact_summary.changed}</p>
              <p>Intake: {(data.impact_summary.affected_intake ?? []).join(", ") || "—"}</p>
              <p>
                ProductDefinition:{" "}
                {(data.impact_summary.affected_product_definition ?? []).join(", ") || "—"}
              </p>
              <p>CPP: {(data.impact_summary.cpp ?? []).join(", ") || "—"}</p>
            </div>
          ) : null}
          <ul>
            {(data.legacy_conflicts ?? []).map((conflict) => (
              <li key={conflict.code}>
                <span className="font-mono">{conflict.code}</span> [{conflict.classification}] —{" "}
                {conflict.message}
              </li>
            ))}
          </ul>
          {blockers.length ? (
            <p className="text-rose-300/90">Blockers: {blockers.slice(0, 8).join("; ")}</p>
          ) : null}
          {warnings.length ? (
            <p className="text-amber-200/80">Warnings: {warnings.slice(0, 8).join("; ")}</p>
          ) : null}
        </div>
      </details>
    </section>
  );
}
