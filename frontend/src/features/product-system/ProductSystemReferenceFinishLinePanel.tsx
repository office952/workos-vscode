/**
 * Reference finish-line contract summary — lab freeze surface.
 */

import { useEffect, useState } from "react";
import {
  fetchReferenceFinishLineContract,
  type FinishLineContractResponse,
} from "@/api/productSystemReferenceFinishLine";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";

export function ProductSystemReferenceFinishLinePanel() {
  const [data, setData] = useState<FinishLineContractResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const res = await fetchReferenceFinishLineContract();
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Finish line indisponibil");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <section
        data-testid="reference-finish-line-panel"
        className={`${PS_SURFACE_PANEL} px-4 py-3 text-[12px] text-rose-200`}
      >
        Finish line: {error}
      </section>
    );
  }

  if (!data) {
    return (
      <section
        data-testid="reference-finish-line-panel"
        className={`${PS_SURFACE_PANEL} px-4 py-3 text-[12px] text-slate-400`}
      >
        Se încarcă contractul finish line…
      </section>
    );
  }

  const critical = data.critical_materials_summary?.active_template_critical;
  const criticalLabel = Array.isArray(critical) ? critical.join(", ") || "—" : "—";

  return (
    <section
      data-testid="reference-finish-line-panel"
      className={`${PS_SURFACE_PANEL} space-y-2 px-4 py-4`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        Reference finish line
      </p>
      <h3 className="text-sm font-semibold text-wo-text-primary">{data.finish_line_name}</h3>
      <p className="text-[11px] text-slate-400">
        Verdict: <span className="text-slate-200">{data.overall_verdict}</span>
        {" · "}
        Modularitate: <span className="text-slate-200">{data.modularity_verdict}</span>
        {" · "}
        Form: <span className="text-slate-200">{data.form_system_verdict}</span>
        {" · "}
        Scalabilitate: <span className="text-slate-200">{data.scalability_verdict}</span>
      </p>
      <p className="text-[11px] text-slate-500" data-testid="reference-finish-line-authoring">
        Authoring: {data.authoring_decision}
      </p>
      <p className="text-[11px] text-amber-100/85" data-testid="reference-finish-line-critical">
        ACTIVE_TEMPLATE_CRITICAL (preț lipsă): {criticalLabel}
      </p>
      {data.warnings?.length ? (
        <ul className="space-y-0.5 text-[11px] text-slate-500">
          {data.warnings.slice(0, 4).map((w) => (
            <li key={w}>• {w}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
