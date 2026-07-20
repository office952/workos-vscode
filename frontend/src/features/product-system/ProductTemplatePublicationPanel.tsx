/**
 * Publication lifecycle panel — active ≠ published; publish hard-gated by E2E readiness.
 * Blockers: human name primary, template code secondary.
 */

import { useCallback, useEffect, useState } from "react";
import {
  getProductTemplatePublication,
  transitionProductTemplatePublication,
  type PublicationAction,
  type ProductTemplatePublicationState,
} from "@/api/productTemplatePublication";
import { formatPublicationBlocker, humanTemplateName } from "./productSystemAdminDisplay";

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
          ? (nested as { blockers: string[] }).blockers.map((b) => formatPublicationBlocker(b).primary).join("; ")
          : null;
      setError(blockers || (e instanceof Error ? e.message : "Tranziție eșuată"));
      await reload();
    } finally {
      setLoading(false);
    }
  };

  const humanName = humanTemplateName(templateCode);
  const isBlocked = Boolean(state && state.publish_blockers.length > 0);

  return (
    <section
      className="rounded-xl border border-slate-700/60 bg-[#0B1220] p-3"
      data-testid="product-template-publication-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Publicare șablon</h3>
          <p className="mt-0.5 text-[11px] text-slate-400">
            <span className="font-medium text-slate-200">{humanName}</span>
            <span className="ml-1.5 font-mono text-[10px] text-slate-500">{templateCode}</span>
          </p>
          <p className="mt-1 text-[11px] text-slate-500">
            Activ în catalog ≠ publicat. Publicarea e blocată de E2E Readiness — fără auto-publicare.
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
              Catalog: {state.db_active ? "activ" : "inactiv"}
            </span>
            <span className="rounded border border-amber-800/40 px-2 py-0.5 text-amber-100">
              activ ≠ publicat
            </span>
          </div>

          {isBlocked ? (
            <div
              className="rounded-lg border border-rose-800/40 bg-rose-950/20 px-3 py-2"
              data-testid="product-template-publication-blocked-banner"
            >
              <p className="text-[12px] font-semibold text-rose-100">
                Publicare blocată — {humanName}
              </p>
              <p className="mt-0.5 text-[10px] text-rose-200/80">
                Build-ul poate rămâne PASS separat. Nu ofertaați acest șablon ca „gata de publicare”.
              </p>
              <ul
                className="mt-2 list-disc space-y-1 pl-4 text-[11px] text-rose-100"
                data-testid="product-template-publication-blockers"
              >
                {state.publish_blockers.map((b) => {
                  const display = formatPublicationBlocker(b);
                  return (
                    <li key={b}>
                      <span>{display.primary}</span>
                      {display.secondary ? (
                        <span className="ml-1 font-mono text-[10px] text-rose-200/60">
                          ({display.secondary})
                        </span>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}

          <details className="text-[11px] text-slate-500">
            <summary className="cursor-pointer select-none hover:text-slate-400">
              Detalii tehnice (poartă / verdict)
            </summary>
            <p className="mt-1">
              Poartă ofertabilitate: <code>{state.offerability_gate}</code>
            </p>
            {state.last_e2e_verdict ? (
              <p className="mt-1">
                Ultimul verdict E2E:{" "}
                <code data-testid="product-template-publication-e2e">{state.last_e2e_verdict}</code>
              </p>
            ) : null}
          </details>

          <div className="flex flex-wrap gap-1.5 pt-1">
            {state.allowed_actions.map((action) => (
              <button
                key={action}
                type="button"
                disabled={
                  loading || (action === "publish" && !state.publish_allowed && state.publish_blockers.length > 0)
                }
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
