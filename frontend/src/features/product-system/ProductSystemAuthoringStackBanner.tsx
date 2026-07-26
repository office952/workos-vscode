/**
 * Fail-loud when FE proxy hits a BE missing publication / e2e-readiness.
 * Presentation only — does not change backends.
 */

import { useEffect, useState } from "react";
import { getAPIBaseURL } from "@/lib/config";

const PROBE_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2";

export type AuthoringStackProbe = {
  kind: "ok" | "missing_routes" | "error";
  publicationStatus: number | null;
  readinessStatus: number | null;
  detail: string;
};

export async function probeProductSystemAuthoringStack(
  fetchFn: typeof fetch = fetch,
): Promise<AuthoringStackProbe> {
  const base = `${getAPIBaseURL()}/api/v1/product-system`;
  try {
    const [pub, ready] = await Promise.all([
      fetchFn(`${base}/templates/${encodeURIComponent(PROBE_TEMPLATE)}/publication`, {
        credentials: "include",
      }),
      fetchFn(`${base}/e2e-readiness/${encodeURIComponent(PROBE_TEMPLATE)}/static`, {
        credentials: "include",
      }),
    ]);
    if (pub.ok && ready.ok) {
      return {
        kind: "ok",
        publicationStatus: pub.status,
        readinessStatus: ready.status,
        detail: "Publication and Pregătire E2E APIs reachable.",
      };
    }
    return {
      kind: "missing_routes",
      publicationStatus: pub.status,
      readinessStatus: ready.status,
      detail:
        "Backend-ul proxiat nu servește publication și/sau e2e-readiness. Reporniți stack-ul cu BACKEND_PORT=8000 (AGENTS) pe BE-ul curent, sau opriți procesul stale de pe alt port.",
    };
  } catch {
    return {
      kind: "error",
      publicationStatus: null,
      readinessStatus: null,
      detail: "Nu pot sonda API-urile Product System (rețea / proxy).",
    };
  }
}

export function ProductSystemAuthoringStackBanner() {
  const [probe, setProbe] = useState<AuthoringStackProbe | null>(null);

  useEffect(() => {
    let cancelled = false;
    void probeProductSystemAuthoringStack().then((result) => {
      if (!cancelled) setProbe(result);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!probe || probe.kind === "ok") return null;

  return (
    <div
      role="alert"
      data-testid="product-system-authoring-stack-banner"
      className="rounded-lg border border-amber-800/50 bg-amber-950/30 px-3 py-2 text-[12px] text-amber-100"
    >
      <p className="font-semibold">Mediu authoring — API lipsă</p>
      <p className="mt-0.5 text-amber-100/85">{probe.detail}</p>
      <p className="mt-1 font-mono text-[10px] text-amber-200/70">
        publication HTTP {probe.publicationStatus ?? "—"} · readiness HTTP{" "}
        {probe.readinessStatus ?? "—"}
      </p>
    </div>
  );
}
