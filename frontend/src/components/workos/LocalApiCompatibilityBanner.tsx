/**
 * DEV-only fail-loud banner when the configured API base is stale/unavailable.
 * Never renders in production builds.
 */
import { useSyncExternalStore } from "react";
import {
  getLocalApiCompatibilitySnapshot,
  subscribeLocalApiCompatibility,
  type LocalCompatSnapshot,
} from "@/lib/localApiCompatibility";

function titleFor(kind: LocalCompatSnapshot["kind"]): string {
  if (kind === "unavailable") return "Backend local indisponibil";
  return "Backend local incompatibil";
}

export function LocalApiCompatibilityBannerView({ snapshot }: { snapshot: LocalCompatSnapshot }) {
  if (snapshot.kind !== "unavailable" && snapshot.kind !== "incompatible") {
    return null;
  }

  const apiLabel = snapshot.apiBase || "(same-origin / Vite proxy)";

  return (
    <div
      className="border-b border-rose-700/60 bg-rose-950/95 px-4 py-3 text-[12px] text-rose-50"
      role="alert"
      data-testid="local-api-compat-banner"
      data-kind={snapshot.kind}
    >
      <p className="text-[13px] font-semibold" data-testid="local-api-compat-title">
        {titleFor(snapshot.kind)}
      </p>
      <p className="mt-1 text-rose-100/95" data-testid="local-api-compat-message">
        Aplicatia este conectata la un backend vechi sau diferit de cel configurat. Verifica
        procesele active si adresa API.
      </p>
      <dl className="mt-2 grid gap-1 text-[11px] text-rose-100/90 sm:grid-cols-2">
        <div>
          <dt className="text-rose-300/80">API base</dt>
          <dd data-testid="local-api-compat-api-base">{apiLabel}</dd>
        </div>
        <div>
          <dt className="text-rose-300/80">Status</dt>
          <dd data-testid="local-api-compat-status">
            {snapshot.kind}
            {snapshot.httpStatus != null ? ` · HTTP ${snapshot.httpStatus}` : ""}
          </dd>
        </div>
        <div>
          <dt className="text-rose-300/80">Detectat</dt>
          <dd data-testid="local-api-compat-detected">
            {snapshot.service || "—"} · {snapshot.contract || "fara contract"} ·{" "}
            {snapshot.apiVersion || "fara versiune"}
          </dd>
        </div>
        <div>
          <dt className="text-rose-300/80">Lipseste</dt>
          <dd data-testid="local-api-compat-missing">
            {snapshot.missingCapabilities.length
              ? snapshot.missingCapabilities.join(", ")
              : snapshot.detail}
          </dd>
        </div>
      </dl>
      <p className="mt-2 text-[11px] text-rose-200/90" data-testid="local-api-compat-next">
        Pas recomandat: {snapshot.recommendedStep || snapshot.detail}
      </p>
      <p className="mt-1 text-[10px] text-rose-300/70">
        Scrierile catre API sunt blocate pana la remediere. Diagnostic:{" "}
        <code className="rounded bg-black/30 px-1">npm run diag:local-listeners</code>
      </p>
    </div>
  );
}

export default function LocalApiCompatibilityBanner() {
  if (!import.meta.env.DEV) return null;

  const snapshot = useSyncExternalStore(
    subscribeLocalApiCompatibility,
    getLocalApiCompatibilitySnapshot,
    getLocalApiCompatibilitySnapshot,
  );

  return <LocalApiCompatibilityBannerView snapshot={snapshot} />;
}
