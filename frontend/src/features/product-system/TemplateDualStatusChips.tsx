/**
 * Dual status: BUILD/DB active vs TEMPLATE publication — never conflated.
 * Compact admin chips: lifecycle readable first; codes stay secondary.
 */

import { useEffect, useState } from "react";
import {
  getProductTemplatePublication,
  type ProductTemplatePublicationState,
} from "@/api/productTemplatePublication";

function chipClass(kind: "ok" | "warn" | "blocked" | "neutral"): string {
  switch (kind) {
    case "ok":
      return "border-emerald-800/50 bg-emerald-950/30 text-emerald-100";
    case "warn":
      return "border-amber-800/50 bg-amber-950/25 text-amber-100";
    case "blocked":
      return "border-rose-800/50 bg-rose-950/30 text-rose-100";
    case "neutral":
      return "border-slate-700/70 bg-slate-950/40 text-slate-300";
    default: {
      const _exhaustive: never = kind;
      return _exhaustive;
    }
  }
}

function publicationDisplay(pub: ProductTemplatePublicationState | null): {
  label: string;
  kind: "ok" | "warn" | "blocked" | "neutral";
} {
  if (!pub) return { label: "—", kind: "neutral" };
  const status = pub.effective_status ?? pub.publication_status ?? "—";
  if (!pub.publish_allowed) {
    return { label: `${status} · blocată`, kind: "blocked" };
  }
  if (pub.publication_status === "PUBLISHED") {
    return { label: status, kind: "ok" };
  }
  return { label: status, kind: "warn" };
}

export function TemplateDualStatusChips({
  templateCode,
  dbActive,
}: {
  templateCode: string;
  dbActive: boolean;
}) {
  const [pub, setPub] = useState<ProductTemplatePublicationState | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    void getProductTemplatePublication(templateCode)
      .then((state) => {
        if (!cancelled) setPub(state);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Publication state unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  const publication = publicationDisplay(pub);

  return (
    <div
      className="flex flex-wrap items-center gap-1.5"
      data-testid="template-dual-status-chips"
      title="active ≠ published ≠ offerable ≠ E2E-ready"
      aria-label="Status build și publicare șablon"
    >
      <span
        data-testid="template-dual-status-build"
        className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${chipClass(
          dbActive ? "ok" : "neutral",
        )}`}
      >
        Build {dbActive ? "activ" : "inactiv"}
      </span>
      <span
        data-testid="template-dual-status-publication"
        className={`rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${chipClass(
          publication.kind,
        )}`}
      >
        Publicare {publication.label}
      </span>
      {pub?.active_is_not_published ? (
        <span
          data-testid="template-dual-status-active-ne-published"
          className="rounded-md border border-slate-700/60 px-2 py-0.5 text-[10px] text-slate-400"
        >
          activ ≠ publicat
        </span>
      ) : null}
      {error ? (
        <span className="text-[10px] text-slate-500" data-testid="template-dual-status-error">
          {error}
        </span>
      ) : null}
    </div>
  );
}
