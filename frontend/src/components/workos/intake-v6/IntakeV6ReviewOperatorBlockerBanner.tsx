import { AlertTriangle, ChevronDown } from "lucide-react";
import { useState } from "react";
import type { OperatorBlockerBannerDisplay } from "@/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay";

export default function IntakeV6ReviewOperatorBlockerBanner({
  display,
  nextStepGuidance = null,
  onJumpToDiagnostic,
  onFocusTarget,
  /** When true, do not repeat the single-issue next-action line (footer owns it). */
  suppressCompactDetail = true,
}: {
  display: OperatorBlockerBannerDisplay;
  /** Neutral guidance when the only pending gate is a future step (e.g. Step 3 confirmation). */
  nextStepGuidance?: string | null;
  onJumpToDiagnostic?: () => void;
  onFocusTarget?: (targetId: string) => void;
  suppressCompactDetail?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);

  if (display.loading) {
    return (
      <p
        className="mb-3 rounded-md border border-[#2A3548] bg-[#0A0F1A]/60 px-4 py-2.5 text-[12px] text-slate-400"
        data-testid="intake-v6-review-operator-blocker-banner-loading"
      >
        Verific blocajele operator…
      </p>
    );
  }

  if (!display.show) {
    if (!nextStepGuidance) return null;
    return (
      <p
        className="mb-3 rounded-md border border-[#2A3548]/80 bg-[#0A0F1A]/50 px-3 py-2 text-[12px] text-slate-300"
        data-testid="intake-v6-review-next-step-guidance"
        role="status"
      >
        {nextStepGuidance}
      </p>
    );
  }

  const blocked = display.severity === "blocked";
  const issueCount = display.issues.length;

  return (
    <div
      className={
        blocked
          ? "sticky top-0 z-20 mb-3 rounded-md border border-rose-500/45 bg-rose-950/95 px-3 py-2 shadow-lg shadow-black/40 backdrop-blur-sm"
          : "sticky top-0 z-20 mb-3 rounded-md border border-amber-500/40 bg-amber-950/90 px-3 py-2 shadow-lg shadow-black/30 backdrop-blur-sm"
      }
      data-testid="intake-v6-review-operator-blocker-banner"
      data-banner-severity={display.severity}
      data-blocker-count={display.blockerCount}
      data-warning-count={display.warningCount}
      data-sticky="true"
      role="status"
    >
      <div className="flex flex-wrap items-start gap-2">
        <AlertTriangle
          className={`mt-0.5 h-4 w-4 shrink-0 ${blocked ? "text-rose-300" : "text-amber-300"}`}
          aria-hidden
        />
        <div className="min-w-0 flex-1">
          <button
            type="button"
            className="flex w-full min-w-0 items-start gap-2 text-left"
            onClick={() => setExpanded((value) => !value)}
            aria-expanded={expanded}
            data-testid="intake-v6-review-operator-blocker-banner-toggle"
          >
            <p
              className={`min-w-0 flex-1 text-[12px] font-semibold leading-snug ${
                blocked ? "text-rose-100" : "text-amber-100"
              }`}
              data-testid="intake-v6-review-operator-blocker-banner-title"
            >
              {display.summaryTitle}
            </p>
            <ChevronDown
              className={`mt-0.5 h-3.5 w-3.5 shrink-0 transition ${expanded ? "rotate-180" : ""} ${
                blocked ? "text-rose-300" : "text-amber-300"
              }`}
              aria-hidden
            />
          </button>

          {!expanded && issueCount === 1 && !suppressCompactDetail ? (
            <p
              className={`mt-1 text-[11px] leading-snug ${blocked ? "text-rose-50/90" : "text-amber-50/90"}`}
              data-testid="intake-v6-review-operator-blocker-compact-one"
            >
              {display.issues[0]?.message}
              {display.issues[0]?.action ? ` — ${display.issues[0].action}` : ""}
            </p>
          ) : null}
          {!expanded && suppressCompactDetail && issueCount > 0 ? (
            <p
              className={`mt-1 text-[11px] leading-snug ${blocked ? "text-rose-50/80" : "text-amber-50/80"}`}
              data-testid="intake-v6-review-operator-blocker-footer-hint"
            >
              Următorul pas este în footer. Deschide lista pentru detalii.
            </p>
          ) : null}

          {expanded ? (
            <ul
              className={`mt-2 space-y-2 text-[11px] leading-snug ${
                blocked ? "text-rose-50/95" : "text-amber-50/95"
              }`}
              data-testid="intake-v6-review-operator-blocker-messages"
            >
              {display.issues.map((issue) => (
                <li
                  key={issue.id}
                  className="rounded border border-white/10 bg-black/20 px-2 py-1.5"
                  data-testid={`intake-v6-review-operator-blocker-issue-${issue.id}`}
                  data-issue-severity={issue.severity}
                >
                  <p className="font-semibold">
                    {issue.severity === "blocker" ? "Blocaj" : "Avertisment"}
                    {issue.tabId === "montaj"
                      ? " · Montaj"
                      : issue.tabId === "iluminare"
                        ? " · Iluminare și surse"
                        : issue.tabId === "finisaje"
                          ? " · Finisaje"
                          : issue.tabId === "layers"
                            ? " · Straturi"
                            : ""}
                  </p>
                  <p className="mt-0.5">{issue.message}</p>
                  {issue.action ? <p className="mt-0.5 opacity-90">Acțiune: {issue.action}</p> : null}
                  {(issue.focusTarget || issue.tabId) && onFocusTarget ? (
                    <button
                      type="button"
                      className="mt-1 text-[10px] font-semibold underline-offset-2 hover:underline"
                      data-testid={`intake-v6-review-operator-blocker-goto-${issue.id}`}
                      onClick={() => onFocusTarget(issue.focusTarget || `tab:${issue.tabId}`)}
                    >
                      Mergi la secțiune
                    </button>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}

          {onJumpToDiagnostic ? (
            <button
              type="button"
              className={`mt-2 text-[11px] font-semibold underline-offset-2 hover:underline ${
                blocked ? "text-rose-200" : "text-amber-200"
              }`}
              onClick={onJumpToDiagnostic}
              data-testid="intake-v6-review-operator-blocker-diagnostic-link"
            >
              Vezi detalii tehnice și diagnostic
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}
