/**
 * Final Product System laboratory closure surface.
 */

import { useEffect, useState } from "react";
import {
  fetchProductSystemReferenceComplete,
  type ReferenceCompleteResponse,
} from "@/api/productSystemReferenceComplete";
import { PS_SURFACE_PANEL } from "./productSystemSurfaces";

export function ProductSystemReferenceCompletePanel() {
  const [data, setData] = useState<ReferenceCompleteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const res = await fetchProductSystemReferenceComplete();
        if (!cancelled) setData(res);
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Reference complete indisponibil");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return (
      <section
        data-testid="reference-complete-panel"
        className={`${PS_SURFACE_PANEL} px-4 py-3 text-[12px] text-rose-200`}
      >
        Reference complete: {error}
      </section>
    );
  }

  if (!data) {
    return (
      <section
        data-testid="reference-complete-panel"
        className={`${PS_SURFACE_PANEL} px-4 py-3 text-[12px] text-slate-400`}
      >
        Se încarcă declarația PRODUCT_SYSTEM_REFERENCE_COMPLETE…
      </section>
    );
  }

  const live = data.live_proof || {};
  const tone =
    data.overall_verdict === "PASS"
      ? "border-emerald-800/40 bg-emerald-950/20 text-emerald-100"
      : "border-rose-800/40 bg-rose-950/20 text-rose-100";

  return (
    <section
      data-testid="reference-complete-panel"
      className={`${PS_SURFACE_PANEL} space-y-2 px-4 py-4`}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
        Laboratory closure
      </p>
      <h3 className="text-sm font-semibold text-wo-text-primary">{data.name}</h3>
      <p
        data-testid="reference-complete-verdict"
        className={`inline-flex rounded border px-2 py-0.5 text-[11px] font-medium ${tone}`}
      >
        {data.overall_verdict} · {data.freeze_readiness}
      </p>
      <p className="text-[12px] leading-relaxed text-slate-400">{data.executive_truth_ro}</p>
      <div
        data-testid="reference-complete-live-proof"
        className="grid gap-1 font-mono text-[10px] text-slate-500 sm:grid-cols-2"
      >
        <span>EIC: {String(live.vl_internal_total ?? "—")}</span>
        <span>CPP: {String(live.vl_commercial_total ?? "—")}</span>
        <span>Fields: {String(live.field_count ?? "—")}</span>
        <span>Critical: {JSON.stringify(live.active_template_critical_codes ?? [])}</span>
        <span>PSU role: {String(live.psu_material_role ?? "—")}</span>
        <span>PSU 100W: {String(live.concrete_psu_100w ?? "—")}</span>
      </div>
      {data.accepted_limitations?.length ? (
        <details className="text-[11px] text-slate-500">
          <summary
            className="cursor-pointer select-none text-slate-400"
            data-testid="reference-complete-limitations"
          >
            Limitări acceptate ({data.accepted_limitations.length})
          </summary>
          <ul className="mt-1 space-y-0.5 pl-3">
            {data.accepted_limitations.map((l) => (
              <li key={l.id}>• {l.text_ro}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}
