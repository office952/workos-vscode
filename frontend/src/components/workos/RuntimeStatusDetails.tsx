/**
 * UI-TRUTH-01C — Drill-down panel for runtime health (no raw JSON primary UI).
 */

import type { RuntimeTruthSnapshot } from "@/types/runtimeStatus";
import {
  RUNTIME_BANNER_LABELS,
  buildRuntimeStatusSummary,
  type RuntimeStatusSummaryView,
} from "@/components/workos/RuntimeStatusSummary";
import type { RuntimeHealthErrorKind } from "@/types/runtimeStatus";

export interface RuntimeStatusDetailsProps {
  snapshot: RuntimeTruthSnapshot;
  view?: RuntimeStatusSummaryView;
  isLoading?: boolean;
  isRefreshing?: boolean;
  lastError?: RuntimeHealthErrorKind | null;
}

function DetailRow({ label, value, testId }: { label: string; value: string; testId?: string }) {
  return (
    <div className="flex flex-wrap gap-x-2 gap-y-0.5 text-[11px]" data-testid={testId}>
      <span className="text-slate-500 shrink-0">{label}</span>
      <span className="text-slate-200">{value}</span>
    </div>
  );
}

export function RuntimeStatusDetails({
  snapshot,
  view: viewProp,
  isLoading = false,
  isRefreshing = false,
  lastError = null,
}: RuntimeStatusDetailsProps) {
  const view =
    viewProp ??
    buildRuntimeStatusSummary({
      snapshot,
      isLoading: isLoading || isRefreshing,
      lastError,
      serviceVersion: snapshot.environment.serviceVersion,
    });

  const ageMs = (() => {
    const iso = snapshot.backend.checkedAt ?? snapshot.backend.lastSuccessfulAt;
    if (!iso) return null;
    const ms = Date.parse(iso);
    if (Number.isNaN(ms)) return null;
    return Math.max(0, Date.now() - ms);
  })();

  const ageText =
    ageMs == null
      ? "—"
      : ageMs < 60_000
        ? `${Math.round(ageMs / 1000)} s`
        : `${Math.round(ageMs / 60_000)} min`;

  let diagnosticsAccess = "Neverificat";
  if (snapshot.diagnostics.authorized === true) {
    diagnosticsAccess = snapshot.diagnostics.available
      ? "Disponibile (autorizat)"
      : RUNTIME_BANNER_LABELS.diagnosticsUnavailable;
  } else if (snapshot.diagnostics.authorized === false) {
    diagnosticsAccess = RUNTIME_BANNER_LABELS.diagnosticsRestricted;
  }

  return (
    <div
      className="w-full border-t border-current/10 pt-1.5 mt-0.5 space-y-1"
      data-testid="runtime-status-details"
      role="region"
      aria-label={view.detailsTitle}
    >
      <p className="text-[10px] font-semibold uppercase tracking-wide opacity-80">
        {view.detailsTitle}
      </p>
      <DetailRow label="Mediu" value={view.environmentLabel} testId="runtime-details-env" />
      <DetailRow label="Backend" value={view.backendLabel} testId="runtime-details-backend" />
      <DetailRow
        label="Bază de date"
        value={view.databaseLabel || RUNTIME_BANNER_LABELS.dbNeverVerifiedAlt}
        testId="runtime-details-db"
      />
      {view.freshnessText ? (
        <DetailRow label="Verificare" value={view.freshnessText} testId="runtime-details-freshness" />
      ) : null}
      {view.staleLabel ? (
        <DetailRow label="Prospețime" value={view.staleLabel} testId="runtime-details-stale" />
      ) : null}
      {view.lastKnownText ? (
        <DetailRow label="Istoric" value={view.lastKnownText} testId="runtime-details-last-known" />
      ) : null}
      <DetailRow label="Vârsta răspunsului" value={ageText} testId="runtime-details-age" />
      {snapshot.environment.serviceVersion ? (
        <DetailRow
          label="Versiune serviciu"
          value={snapshot.environment.serviceVersion}
          testId="runtime-details-version"
        />
      ) : null}
      <DetailRow
        label="Diagnostice"
        value={diagnosticsAccess}
        testId="runtime-details-diagnostics"
      />
      {view.diagnosticsMessage ? (
        <p
          className="text-[11px] text-amber-200/90 leading-snug"
          data-testid="runtime-details-diagnostics-message"
        >
          {view.diagnosticsMessage}
        </p>
      ) : null}
      {lastError ? (
        <DetailRow
          label="Eroare tehnică"
          value={lastError}
          testId="runtime-details-error"
        />
      ) : null}
      {snapshot.diagnostics.httpStatus != null && snapshot.diagnostics.authorized === false ? (
        <DetailRow
          label="Cod acces"
          value={String(snapshot.diagnostics.httpStatus)}
          testId="runtime-details-http"
        />
      ) : null}
      {view.technicalStrip ? (
        <p
          className="font-mono text-[10px] opacity-60"
          data-testid="runtime-details-tech"
        >
          {view.technicalStrip}
        </p>
      ) : null}
    </div>
  );
}

export default RuntimeStatusDetails;
