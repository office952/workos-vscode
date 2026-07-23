/**
 * Product E2E Readiness Check — admin/owner surface on Product Template page.
 * Compact dual BUILD/TEMPLATE summary; findings progressive disclosure.
 */

import { useCallback, useState } from "react";
import { getAPIBaseURL } from "@/lib/config";
import { formatReadinessFindingMessage, humanTemplateName } from "./productSystemAdminDisplay";
import { PS_SURFACE_INSET, PS_SURFACE_INPUT, PS_SURFACE_PANEL } from "./productSystemSurfaces";

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

interface SystemNode {
  system: string;
  status: CheckStatus;
  blocking?: boolean;
  finding_count?: number;
  summary?: string;
}

interface ReadinessResponse {
  template_code: string;
  mode: "static" | "runtime_dry_run" | string;
  verdict: string;
  e2e_ready?: boolean;
  findings: ReadinessFinding[];
  systems?: SystemNode[];
  no_write: boolean;
  write_performed?: boolean;
  build_closure_status?: string;
  template_publication_status?: string;
}

/** Catalog → … → Execution Preview — System Link Check order. */
const PIPELINE = [
  { key: "catalog", label: "Catalog" },
  { key: "components", label: "Module produs" },
  { key: "intake", label: "Intake" },
  { key: "product_truth", label: "Product Truth" },
  { key: "product_definition", label: "ProductDefinition" },
  { key: "aggregate", label: "Aggregate" },
  { key: "quantity", label: "Quantity" },
  { key: "cpp", label: "CPP" },
  { key: "eic", label: "EIC" },
  { key: "quote_snapshot", label: "Quote Snapshot" },
  { key: "order_snapshot", label: "Order Snapshot" },
  { key: "execution_preview", label: "Execution Preview" },
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
  const [expanded, setExpanded] = useState(false);
  const [findingsOpen, setFindingsOpen] = useState(false);

  const base = `${getAPIBaseURL()}/api/v1/product-system`;
  const humanName = humanTemplateName(templateCode);

  const runStatic = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJson<ReadinessResponse>(
        `${base}/e2e-readiness/${encodeURIComponent(templateCode)}/static`,
      );
      setStaticResult(data);
      setExpanded(true);
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
      setExpanded(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Runtime dry-run failed");
    } finally {
      setLoading(false);
    }
  }, [base, templateCode, workspaceId]);

  const active = runtimeResult ?? staticResult;
  const findings = active?.findings ?? [];
  const blockingCount = findings.filter((f) => f.blocking).length;

  return (
    <section
      className={`${PS_SURFACE_PANEL} p-3`}
      data-testid="product-e2e-readiness-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-[13px] font-semibold text-slate-100">Verifică traseul produsului</h3>
          <p className="mt-0.5 text-[11px] text-slate-400">
            <span className="font-medium text-slate-200">{humanName}</span>
            <span className="ml-1.5 font-mono text-[10px] text-slate-500">{templateCode}</span>
          </p>
          <p className="mt-0.5 text-[10px] text-slate-500">
            Read-only · nu activează · nu confirmă · nu creează quote/order.
          </p>
        </div>
        <button
          type="button"
          className="text-[10px] text-slate-400 underline"
          onClick={() => setExpanded((v) => !v)}
          data-testid="product-e2e-readiness-toggle"
          aria-expanded={expanded}
        >
          {expanded ? "Restrânge" : "Extinde"}
        </button>
      </div>

      {/* Compact dual-axis strip — always visible once result exists */}
      {active ? (
        <div
          className={`mt-3 grid gap-1.5 ${PS_SURFACE_INSET} p-2.5`}
          data-testid="product-e2e-readiness-dual-axes"
        >
          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            <span className="w-28 shrink-0 text-slate-500">Build</span>
            <span
              className={`rounded border px-2 py-0.5 font-semibold ${statusColor(active.build_closure_status || "NOT_TESTED")}`}
              data-testid="product-e2e-readiness-build-closure"
            >
              BUILD {active.build_closure_status || "NOT_TESTED"}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            <span className="w-28 shrink-0 text-slate-500">Publicare</span>
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
              Build poate fi PASS în timp ce publicarea rămâne blocată (ex.{" "}
              {humanTemplateName("TPL-VOLUM-ALUMINIU_v1")} inactiv — conflict onest, fără activare).
            </p>
          ) : null}
          <p className="text-[10px] text-slate-500">
            Verdict poartă: <span className="text-slate-300">{active.verdict}</span>
            {blockingCount > 0 ? ` · ${blockingCount} blocking` : ""} · {findings.length} findings
          </p>
        </div>
      ) : null}

      {expanded ? (
        <div className="mt-3 space-y-3">
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
              className={`min-w-[180px] flex-1 ${PS_SURFACE_INPUT} px-2 py-1 text-[11px]`}
              placeholder="workspace_id (runtime dry-run)"
              value={workspaceId}
              onChange={(e) => setWorkspaceId(e.target.value)}
              data-testid="product-e2e-readiness-workspace-input"
              aria-label="workspace_id pentru runtime dry-run"
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

          {!active ? (
            <p className="text-[10px] text-slate-500">
              Rulează verificarea statică pentru a vedea Build vs Publicare.
            </p>
          ) : (
            <div data-testid="product-e2e-readiness-result">
              <button
                type="button"
                className="mb-2 text-[11px] text-slate-400 underline"
                onClick={() => setFindingsOpen((v) => !v)}
                data-testid="product-e2e-readiness-findings-toggle"
                aria-expanded={findingsOpen}
              >
                {findingsOpen ? "Ascunde findings" : `Arată findings (${findings.length})`}
              </button>
              {findingsOpen ? (
                <ul
                  className="max-h-64 space-y-1.5 overflow-y-auto"
                  data-testid="product-e2e-readiness-findings"
                >
                  {findings.map((f) => {
                    const msg = formatReadinessFindingMessage(f.message);
                    return (
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
                        <p className="mt-0.5 text-slate-200">{msg.primary}</p>
                        {msg.secondary ? (
                          <p className="mt-0.5 font-mono text-[9px] text-slate-500">{msg.secondary}</p>
                        ) : null}
                        {f.evidence ? (
                          <details className="mt-0.5">
                            <summary className="cursor-pointer text-[9px] text-slate-500">
                              evidence
                            </summary>
                            <p className="font-mono text-[9px] text-slate-500">
                              {typeof f.evidence === "string" ? f.evidence : JSON.stringify(f.evidence)}
                            </p>
                          </details>
                        ) : null}
                      </li>
                    );
                  })}
                </ul>
              ) : null}

              <details className="mt-2" open data-testid="product-e2e-readiness-system-link-check">
                <summary className="cursor-pointer text-[10px] text-slate-400 hover:text-slate-300">
                  System Link Check — Catalog → Execution Preview
                </summary>
                <p className="mt-1 text-[10px] text-slate-500">
                  Read-only. Nu repară, nu activează, nu publică.
                </p>
                <table
                  className="mt-1.5 w-full border-collapse text-[10px]"
                  data-testid="product-e2e-readiness-system-link-table"
                >
                  <thead>
                    <tr className="text-left text-slate-500">
                      <th className="border-b border-slate-800 py-1 pr-2 font-medium">Hop</th>
                      <th className="border-b border-slate-800 py-1 pr-2 font-medium">Status</th>
                      <th className="border-b border-slate-800 py-1 font-medium">Summary</th>
                    </tr>
                  </thead>
                  <tbody>
                    {PIPELINE.map((node) => {
                      const live = (active.systems ?? []).find((s) => s.system === node.key);
                      const status = live?.status ?? "NOT_TESTED";
                      return (
                        <tr key={node.key} data-testid={`system-link-row-${node.key}`}>
                          <td className="border-b border-slate-900/80 py-1 pr-2 text-slate-300">
                            {node.label}
                          </td>
                          <td className="border-b border-slate-900/80 py-1 pr-2">
                            <span
                              className={`rounded border px-1 py-0.5 ${statusColor(status)}`}
                            >
                              {status}
                            </span>
                          </td>
                          <td className="border-b border-slate-900/80 py-1 text-slate-500">
                            {live?.summary
                              || (live?.finding_count
                                ? `${live.finding_count} findings`
                                : "—")}
                            {live?.blocking ? " · blocking" : ""}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
                <p className="mt-1 text-[10px] text-slate-600">
                  mode={active.mode} · no_write={String(active.no_write)}
                </p>
              </details>
            </div>
          )}
        </div>
      ) : (
        <div className="mt-3 flex flex-wrap gap-2">
          <button
            type="button"
            disabled={loading}
            onClick={() => void runStatic()}
            className="rounded-md border border-cyan-700/50 bg-cyan-950/40 px-2.5 py-1.5 text-[11px] font-medium text-cyan-100"
            data-testid="product-e2e-readiness-static-btn"
          >
            Verificare statică
          </button>
          {!active ? (
            <p className="self-center text-[10px] text-slate-500">
              Compact: rulează check-ul pentru axe Build / Publicare.
            </p>
          ) : null}
        </div>
      )}
    </section>
  );
}
