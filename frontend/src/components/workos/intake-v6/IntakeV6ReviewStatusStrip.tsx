import { useState } from "react";
import { AlertTriangle, CheckCircle2, ChevronDown, ChevronUp } from "lucide-react";
import type { ReviewHandoffSurfacing } from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";

export default function IntakeV6ReviewStatusStrip({
  surfacing,
  loading = false,
  pendingSave = false,
  pendingConfirmationCount = 0,
  onJumpToPending,
  embedded = false,
}: {
  surfacing: ReviewHandoffSurfacing;
  loading?: boolean;
  pendingSave?: boolean;
  pendingConfirmationCount?: number;
  onJumpToPending?: () => void;
  /** Tighter layout when nested in compact Review header. */
  embedded?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  const hasBlockers = surfacing.showBanner;
  const pendingItems =
    pendingConfirmationCount +
    (pendingSave ? 1 : 0) +
    (hasBlockers ? Math.max(surfacing.reasons.length, 1) : 0);

  if (loading) {
    return (
      <p
        className={`${embedded ? "mb-0 px-1 py-1" : "mb-3 rounded-md border border-wo-border-strong/80 bg-wo-surface-inset/40 px-3 py-2"} text-[11px] text-wo-text-dim`}
        data-testid="intake-v6-review-status-strip-loading"
      >
        Verific starea lucrării…
      </p>
    );
  }

  const allClear = !hasBlockers && pendingConfirmationCount === 0 && !pendingSave;

  const summaryText = allClear
    ? "Toate setările tehnice sunt complete"
    : pendingConfirmationCount > 0
      ? `Mai ${pendingConfirmationCount === 1 ? "este" : "sunt"} ${pendingConfirmationCount} element${pendingConfirmationCount === 1 ? "" : "e"} de confirmat`
      : hasBlockers
        ? "Există elemente de verificat înainte de Confirmare"
        : pendingSave
          ? "Modificări în curs de salvare"
          : "Stare Review";

  return (
    <div
      className={
        embedded
          ? "px-1 py-0.5"
          : `mb-3 rounded-md border px-3 py-2 ${
              allClear
                ? "border-emerald-200 bg-emerald-50/80 dark:border-emerald-500/25 dark:bg-emerald-500/5"
                : "border-wo-border-strong/90 bg-wo-surface-inset/50"
            }`
      }
      data-testid="intake-v6-review-status-strip"
    >
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
        {allClear ? (
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" aria-hidden />
        ) : (
          <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-600 dark:text-amber-400/90" aria-hidden />
        )}
        <p
          className={`min-w-0 flex-1 text-[11px] font-medium leading-snug ${
            allClear
              ? "text-emerald-800 dark:text-emerald-200/90"
              : "text-wo-text-secondary"
          }`}
          data-testid="intake-v6-review-status-strip-summary"
        >
          {summaryText}
        </p>
        {!allClear && (surfacing.reasons.length > 0 || surfacing.actions.length > 0) ? (
          <button
            type="button"
            className="inline-flex shrink-0 items-center gap-1 rounded border border-wo-border-strong bg-wo-surface-raised px-2 py-0.5 text-[10px] font-semibold text-wo-text-secondary hover:border-slate-400/50"
            onClick={() => setExpanded((open) => !open)}
            data-testid="intake-v6-review-status-strip-toggle"
            aria-expanded={expanded}
          >
            {expanded ? "Ascunde" : "Vezi detalii"}
            {expanded ? (
              <ChevronUp className="h-3 w-3" aria-hidden />
            ) : (
              <ChevronDown className="h-3 w-3" aria-hidden />
            )}
          </button>
        ) : null}
        {pendingConfirmationCount > 0 && onJumpToPending ? (
          <button
            type="button"
            className="inline-flex shrink-0 items-center rounded border border-cyan-300/60 bg-cyan-50 px-2 py-0.5 text-[10px] font-semibold text-cyan-800 hover:bg-cyan-100 dark:border-cyan-500/30 dark:bg-cyan-500/10 dark:text-cyan-200 dark:hover:bg-cyan-500/15"
            onClick={onJumpToPending}
            data-testid="intake-v6-review-status-strip-jump"
          >
            Salt la neconfirmate
          </button>
        ) : null}
      </div>

      {expanded && !allClear ? (
        <div
          className="mt-2 space-y-1 border-t border-wo-border-strong/60 pt-2 text-[10px] leading-snug text-wo-text-muted"
          data-testid="intake-v6-review-status-strip-details"
        >
          {pendingSave ? <p>• Modificări locale — așteaptă autosave.</p> : null}
          {surfacing.reasons.map((reason) => (
            <p key={reason}>• {reason}</p>
          ))}
          {surfacing.actions.map((action) => (
            <p key={action} className="text-wo-text-dim">
              → {action}
            </p>
          ))}
        </div>
      ) : null}

      {!expanded && pendingItems > 0 && !allClear ? (
        <p className="sr-only" data-testid="intake-v6-review-status-strip-pending-count">
          {pendingItems}
        </p>
      ) : null}
    </div>
  );
}
