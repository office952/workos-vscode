/**
 * Publication lifecycle panel — active ≠ published; publish hard-gated by E2E readiness.
 */

import { useCallback, useEffect, useState } from "react";
import {
  getProductTemplatePublication,
  transitionProductTemplatePublication,
  type PublicationAction,
  type ProductTemplatePublicationState,
} from "@/api/productTemplatePublication";

const ACTION_LABELS: Record<PublicationAction, string> = {
  enter_draft: "Intră în DRAFT",
  mark_validated: "Marchează VALIDATED",
  mark_e2e_checked: "Marchează E2E_CHECKED",
  publish: "Publică",
  deprecate: "Depreciază",
  archive: "Arhivează",
  reopen_draft: "Redeschide DRAFT",
};

function statusTone(status: string): string {
  switch (status) {
    case "PUBLISHED":
      return "border-emerald-700/50 bg-emerald-950/30 text-emerald-200";
    case "E2E_CHECKED":
    case "VALIDATED":
      return "border-sky-700/40 bg-sky-950/20 text-sky-200";
    case "DRAFT":
    case "LEGACY_UNSPECIFIED":
      return "border-amber-700/40 bg-amber-950/20 text-amber-100";
    case "DEPRECATED":
    case "ARCHIVED":
      return "border-slate-600/50 bg-slate-900/50 text-slate-300";
    default:
      return "border-slate-700/50 bg-slate-900/40 text-slate-300";
  }
}

export function ProductTemplatePublicationPanel({ templateCode }: { templateCode: string }) {
  const [state, setState] = useState<ProductTemplatePublicationState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setState(await getProductTemplatePublication(templateCode));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Eroare încărcare publicație");
    } finally {
      setLoading(false);
    }
  }, [templateCode]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const runAction = async (action: PublicationAction) => {
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const result = await transitionProductTemplatePublication(templateCode, action);
      setState(result.state);
      setMessage(result.message);
    } catch (e) {
      const detail = (e as Error & { detail?: { detail?: { blockers?: string[]; error?: string } } })
        ?.detail;
      const nested = detail && typeof detail === "object" && "detail" in detail ? detail.detail : detail;
      const blockers =
        nested && typeof nested === "object" && Array.isArray((nested as { blockers?: string[] }).blockers)
          ? (nested as { blockers: string[] }).blockers.join("; ")
          : null;
      setError(blockers || (e instanceof Error ? e.message : "Tranziție eșuată"));
      await reload();
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      className="rounded-xl border border-violet-800/40 bg-violet-950/10 p-3"
      data-testid="product-template-publication-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-violet-100">Publicare șablon</h3>
          <p className="mt-0.5 text-[11px] text-violet-200/80">
            active ≠ published. Publicarea este blocată de E2E Readiness. Fără tabel component_templates.
          </p>
        </div>
        <button
          type="button"
          className="rounded border border-slate-700 px-2 py-1 text-[11px] text-slate-300 hover:bg-slate-900"
          onClick={() => void reload()}
          disabled={loading}
          data-testid="product-template-publication-reload"
        >
          Reîncarcă
        </button>
      </div>

      {state ? (
        <div className="mt-3 space-y-2" data-testid="product-template-publication-state">
          <div className="flex flex-wrap gap-2 text-[11px]">
            <span
              className={`rounded border px-2 py-0.5 ${statusTone(state.effective_status)}`}
              data-testid="product-template-publication-status"
            >
              {state.effective_status}
            </span>
            <span className="rounded border border-slate-700/60 px-2 py-0.5 text-slate-300">
              DB active: {state.db_active ? "da" : "nu"}
            </span>
            <span className="rounded border border-amber-800/40 px-2 py-0.5 text-amber-100">
              active ≠ published
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            Poartă ofertabilitate: <code>{state.offerability_gate}</code>
          </p>
          {state.last_e2e_verdict ? (
            <p className="text-[11px] text-slate-400">
              Ultimul verdict E2E: <code data-testid="product-template-publication-e2e">{state.last_e2e_verdict}</code>
            </p>
          ) : null}
          {state.publish_blockers.length > 0 ? (
            <ul
              className="list-disc space-y-0.5 pl-4 text-[11px] text-rose-200"
              data-testid="product-template-publication-blockers"
            >
              {state.publish_blockers.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          ) : null}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {state.allowed_actions.map((action) => (
              <button
                key={action}
                type="button"
                disabled={loading || (action === "publish" && !state.publish_allowed && state.publish_blockers.length > 0)}
                onClick={() => void runAction(action)}
                className={
                  action === "publish"
                    ? "rounded border border-emerald-700/50 bg-emerald-950/40 px-2.5 py-1 text-[11px] text-emerald-100 hover:bg-emerald-900/40 disabled:opacity-40"
                    : "rounded border border-slate-700 bg-slate-950/40 px-2.5 py-1 text-[11px] text-slate-200 hover:bg-slate-900 disabled:opacity-40"
                }
                data-testid={`product-template-publication-action-${action}`}
              >
                {ACTION_LABELS[action]}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {loading ? <p className="mt-2 text-[11px] text-slate-500">Se procesează…</p> : null}
      {error ? (
        <p className="mt-2 text-[11px] text-rose-300" data-testid="product-template-publication-error">
          {error}
        </p>
      ) : null}
      {message ? (
        <p className="mt-2 text-[11px] text-emerald-300" data-testid="product-template-publication-message">
          {message}
        </p>
      ) : null}
    </section>
  );
}
