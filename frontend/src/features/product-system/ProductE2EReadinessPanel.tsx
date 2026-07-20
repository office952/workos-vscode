/**
 * Product E2E Readiness Check — admin/owner surface on Product Template page.
 * Label: Verifica traseul produsului. No auto-fix / activation / writes.
 */

import { useCallback, useState } from "react";
import { getAPIBaseURL } from "@/lib/config";

type CheckStatus =
  | "PASS"
  | "PASS_WITH_WARNINGS"
  | "PARTIAL"
  | "FAIL"
  | "BLOCKED"
  | "NOT_CONFIGURED"
  | "NOT_TESTED"
  | "LEGACY_DEPENDENCY"
  | "STALE_EVIDENCE"
  | string;

interface ReadinessFinding {
  check_id: string;
  system: string;
  status: CheckStatus;
  severity?: string;
  blocking?: boolean;
  message: string;
  evidence?: Record<string, unknown> | string | null;
  recommended_navigation?: string | null;
}

interface ReadinessResponse {
  template_code: string;
  mode: "static" | "runtime_dry_run" | string;
  verdict: string;
  e2e_ready?: boolean;
  findings: ReadinessFinding[];
  no_write: boolean;
  write_performed?: boolean;
  /** BUILD spine closure — may PASS while template publication is BLOCKED. */
  build_closure_status?: string;
  /** Template publication readiness — independent of BUILD closure. */
  template_publication_status?: string;
}

const PIPELINE = [
  "Catalog",
  "Components",
  "Intake",
  "Product Truth",
  "ProductDefinition",
  "Aggregate",
  "Quantity",
  "CPP",
  "EIC",
  "Quote Snapshot",
  "Order Snapshot",
  "Execution Preview",
] as const;

function statusColor(status: CheckStatus): string {
  switch (status) {
    case "PASS":
      return "text-emerald-300 border-emerald-700/50 bg-emerald-950/30";
    case "PASS_WITH_WARNINGS":
    case "PARTIAL":
    case "STALE_EVIDENCE":
    case "LEGACY_DEPENDENCY":
      return "text-amber-200 border-amber-700/40 bg-amber-950/20";
    case "FAIL":
    case "BLOCKED":
      return "text-rose-200 border-rose-700/50 bg-rose-950/30";
    case "NOT_TESTED":
    case "NOT_CONFIGURED":
    default:
      return "text-slate-400 border-slate-700/50 bg-slate-900/40";
  }
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export function ProductE2EReadinessPanel({ templateCode }: { templateCode: string }) {
  const [staticResult, setStaticResult] = useState<ReadinessResponse | null>(null);
  const [runtimeResult, setRuntimeResult] = useState<ReadinessResponse | null>(null);
  const [workspaceId, setWorkspaceId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(true);

  const base = `${getAPIBaseURL()}/api/v1/product-system`;

  const runStatic = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJson<ReadinessResponse>(
        `${base}/e2e-readiness/${encodeURIComponent(templateCode)}/static`,
      );
      setStaticResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Static check failed");
    } finally {
      setLoading(false);
    }
  }, [base, templateCode]);

  const runRuntime = useCallback(async () => {
    if (!workspaceId.trim()) {
      setError("Introdu un workspace_id pentru runtime dry-run.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJson<ReadinessResponse>(
        `${base}/e2e-readiness/${encodeURIComponent(templateCode)}/runtime-dry-run`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ workspace_id: workspaceId.trim(), dry_run: true }),
        },
      );
      setRuntimeResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Runtime dry-run failed");
    } finally {
      setLoading(false);
    }
  }, [base, templateCode, workspaceId]);

  const active = runtimeResult ?? staticResult;
  const findings = active?.findings ?? [];

  return (
    <section
      className="rounded-xl border border-[#1E293B] bg-[#0B1220] p-3"
      data-testid="product-e2e-readiness-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-[13px] font-semibold text-slate-100">Verifica traseul produsului</h3>
          <p className="mt-0.5 text-[10px] text-slate-500">
            Product E2E Readiness — read-only. Nu activează, nu confirmă, nu creează quote/order.
          </p>
        </div>
        <button
          type="button"
          className="text-[10px] text-slate-400 underline"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded ? "Restrânge" : "Extinde"}
        </button>
      </div>

      {expanded ? (
        <div className="mt-3 space-y-3">
          <div className="flex flex-wrap gap-1.5" data-testid="product-e2e-readiness-pipeline">
            {PIPELINE.map((node) => (
              <span
                key={node}
                className="rounded border border-slate-700/60 bg-slate-900/50 px-1.5 py-0.5 text-[9px] text-slate-400"
              >
                {node}
              </span>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={() => void runStatic()}
              className="rounded-md border border-cyan-700/50 bg-cyan-950/40 px-2.5 py-1.5 text-[11px] font-medium text-cyan-100"
              data-testid="product-e2e-readiness-static-btn"
            >
              Verificare statică
            </button>
            <input
              className="min-w-[180px] flex-1 rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-[11px] text-slate-200"
              placeholder="workspace_id (runtime dry-run)"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              data-testid="product-e2e-readiness-workspace-input"
            />
            <button
              type="button"
              disabled={loading}
              onClick={() => void runRuntime()}
              className="rounded-md border border-slate-600 bg-slate-900 px-2.5 py-1.5 text-[11px] text-slate-200"
              data-testid="product-e2e-readiness-runtime-btn"
            >
              Runtime dry-run
            </button>
          </div>

          {error ? (
            <p className="text-[11px] text-rose-300" data-testid="product-e2e-readiness-error">
              {error}
            </p>
          ) : null}

          {active ? (
            <div data-testid="product-e2e-readiness-result">
              <div
                className="mb-2 grid gap-1.5 rounded border border-slate-700/60 bg-slate-950/40 p-2"
                data-testid="product-e2e-readiness-dual-axes"
              >
                <div className="flex flex-wrap items-center gap-2 text-[11px]">
                  <span className="text-slate-500">BUILD closure</span>
                  <span
                    className={`rounded border px-2 py-0.5 font-semibold ${statusColor(active.build_closure_status || "NOT_TESTED")}`}
                    data-testid="product-e2e-readiness-build-closure"
                  >
                    BUILD {active.build_closure_status || "NOT_TESTED"}
                  </span>
                </div>
                <div className="flex flex-wrap items-center gap-2 text-[11px]">
                  <span className="text-slate-500">TEMPLATE publication</span>
                  <span
                    className={`rounded border px-2 py-0.5 font-semibold ${statusColor(active.template_publication_status || "NOT_READY")}`}
                    data-testid="product-e2e-readiness-template-publication"
                  >
                    TEMPLATE PUBLICATION {active.template_publication_status || "NOT_READY"}
                  </span>
                </div>
                {active.build_closure_status?.startsWith("PASS") &&
                active.template_publication_status === "BLOCKED" ? (
                  <p
                    className="text-[10px] text-amber-200/90"
                    data-testid="product-e2e-readiness-build-pass-pub-blocked"
                  >
                    BUILD poate fi PASS în timp ce TEMPLATE PUBLICATION rămâne BLOCKED (ex. child
                    inactiv TPL-VOLUM-ALUMINIU_v1 — conflict onest, fără activare).
                  </p>
                ) : null}
              </div>
              <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px]">
                <span className={`rounded border px-2 py-0.5 font-semibold ${statusColor(active.verdict)}`}>
                  gate={active.verdict}
                </span>
                <span className="text-slate-500">
                  mode={active.mode} · no_write={String(active.no_write)} · findings={findings.length}
                </span>
              </div>
              <ul className="max-h-64 space-y-1.5 overflow-y-auto" data-testid="product-e2e-readiness-findings">
                {findings.map((f) => (
                  <li
                    key={`${f.check_id}-${f.system}`}
                    className={`rounded border px-2 py-1.5 text-[10px] ${statusColor(f.status)}`}
                  >
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="font-semibold">{f.system}</span>
                      <span>{f.status}</span>
                      {f.blocking ? (
                        <span className="rounded bg-rose-900/50 px-1 text-[9px]">blocking</span>
                      ) : null}
                    </div>
                    <p className="mt-0.5 text-slate-300">{f.message}</p>
                    {f.evidence ? (
                      <p className="mt-0.5 font-mono text-[9px] text-slate-500">
                        {typeof f.evidence === "string" ? f.evidence : JSON.stringify(f.evidence)}
                      </p>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p className="text-[10px] text-slate-500">
              Rulează verificarea statică înainte de activare / offerability.
            </p>
          )}
        </div>
      ) : null}
    </section>
  );
}
