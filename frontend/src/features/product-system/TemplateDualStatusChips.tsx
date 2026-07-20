/**
 * Layered status: lifecycle (catalog) vs publication gate — never equal-weight soup.
 * Shell „În dezvoltare” must not appear here.
 */

import { useEffect, useState } from "react";
import {
  getProductTemplatePublication,
  type ProductTemplatePublicationState,
} from "@/api/productTemplatePublication";
import { getAPIBaseURL } from "@/lib/config";
import {
  resolvePublishUiGate,
  type ReadinessGateInput,
} from "./productSystemPublicationGate";

function chipClass(kind: "ok" | "warn" | "blocked" | "neutral"): string {
  switch (kind) {
    case "ok":
      return "border-emerald-800/40 bg-emerald-950/20 text-emerald-100";
    case "warn":
      return "border-amber-800/40 bg-amber-950/20 text-amber-100";
    case "blocked":
      return "border-rose-800/40 bg-rose-950/25 text-rose-100";
    case "neutral":
      return "border-slate-700/50 bg-slate-900/30 text-slate-300";
    default: {
      const _exhaustive: never = kind;
      return _exhaustive;
    }
  }
}

async function fetchReadinessGate(templateCode: string): Promise<ReadinessGateInput | null> {
  const base = `${getAPIBaseURL()}/api/v1/product-system`;
  try {
    const res = await fetch(
      `${base}/e2e-readiness/${encodeURIComponent(templateCode)}/static`,
      { credentials: "include" },
    );
    if (!res.ok) return null;
    const data = (await res.json()) as {
      verdict?: string;
      e2e_ready?: boolean;
      known_conflicts?: string[];
      findings?: Array<{ blocking?: boolean; message?: string; code?: string }>;
    };
    return {
      verdict: data.verdict ?? null,
      e2eReady: data.e2e_ready ?? null,
      knownConflicts: data.known_conflicts ?? [],
      findings: data.findings ?? [],
    };
  } catch {
    return null;
  }
}

export function TemplateDualStatusChips({
  templateCode,
  dbActive,
}: {
  templateCode: string;
  dbActive: boolean;
}) {
  const [pub, setPub] = useState<ProductTemplatePublicationState | null>(null);
  const [readiness, setReadiness] = useState<ReadinessGateInput | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    void Promise.all([
      getProductTemplatePublication(templateCode),
      fetchReadinessGate(templateCode),
    ])
      .then(([state, readinessGate]) => {
        if (cancelled) return;
        setPub(state);
        setReadiness(readinessGate);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Publication state unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  const gate = resolvePublishUiGate(pub, readiness);
  const status = pub?.effective_status ?? pub?.publication_status ?? "—";
  const publicationKind = !pub
    ? ("neutral" as const)
    : !gate.publishEnabled
      ? ("blocked" as const)
      : pub.publication_status === "PUBLISHED"
        ? ("ok" as const)
        : ("warn" as const);
  const publicationLabel = !pub
    ? "—"
    : !gate.publishEnabled
      ? `${status} · blocată`
      : status;

  return (
    <div
      className="flex flex-col items-end gap-1.5"
      data-testid="template-dual-status-chips"
      title="lifecycle ≠ publicare ≠ pregătire E2E"
      aria-label="Status lifecycle și poartă de publicare"
    >
      <div className="flex flex-wrap items-center justify-end gap-1.5">
        <span
          data-testid="template-dual-status-build"
          className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${chipClass(
            dbActive ? "ok" : "neutral",
          )}`}
        >
          {dbActive ? "Activ în catalog" : "Inactiv în catalog"}
        </span>
        <span
          data-testid="template-dual-status-publication"
          className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold tracking-wide ${chipClass(
            publicationKind,
          )}`}
        >
          Publicare: {publicationLabel}
        </span>
      </div>
      {gate.primaryBlockerRo ? (
        <p
          className="max-w-xs text-right text-[11px] font-medium text-rose-100/95"
          data-testid="template-dual-status-primary-blocker"
        >
          {gate.primaryBlockerRo}
          {gate.secondaryCode ? (
            <span className="ml-1 font-mono text-[10px] font-normal text-rose-200/55">
              ({gate.secondaryCode})
            </span>
          ) : null}
        </p>
      ) : null}
      {error ? (
        <span className="text-[10px] text-slate-500" data-testid="template-dual-status-error">
          {error}
        </span>
      ) : null}
    </div>
  );
}
