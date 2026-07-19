import { AlertTriangle, ChevronDown } from "lucide-react";
import { useState } from "react";
import type { OperatorBlockerBannerDisplay } from "@/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay";

/**
 * Compact attention corner — assists the form; does not lead the page.
 * Full-width incomplete slabs are forbidden for normal incomplete config.
 */
export default function IntakeV6ReviewOperatorBlockerBanner({
  display,
  nextStepGuidance = null,
  onJumpToDiagnostic,
  onFocusTarget,
  suppressCompactDetail = true,
}: {
  display: OperatorBlockerBannerDisplay;
  nextStepGuidance?: string | null;
  onJumpToDiagnostic?: () => void;
  onFocusTarget?: (targetId: string) => void;
  suppressCompactDetail?: boolean;
}) {
  const [expanded, setExpanded] = useState(false);
  void nextStepGuidance;
  void suppressCompactDetail;

  if (display.loading) {
    return (
      <p
        className="rounded-full border border-[#2A3548]/70 bg-[#0A0F1A]/80 px-2.5 py-1 text-[11px] text-slate-400"
        data-testid="intake-v6-review-operator-blocker-banner-loading"
      >
        …
      </p>
    );
  }

  if (!display.show) {
    return null;
  }

  const blocked = display.severity === "blocked";
  const issueCount = display.issues.length;
  const chipLabel =
    issueCount <= 0
      ? "Atenție"
      : issueCount === 1
        ? "! 1 problemă"
        : `! ${issueCount} probleme`;

  return (
    <div
      className="relative"
      data-testid="intake-v6-review-operator-blocker-banner"
      data-banner-severity={display.severity}
      data-blocker-count={display.blockerCount}
      data-warning-count={display.warningCount}
      data-sticky="false"
      data-attention-weight="corner"
      role="status"
    >
      <button
        type="button"
        className={
          blocked
            ? "inline-flex items-center gap-1.5 rounded-full border border-rose-400/50 bg-rose-500/25 px-2.5 py-1 text-[11px] font-bold text-rose-50 shadow-[0_0_12px_rgba(244,63,94,0.35)]"
            : "inline-flex items-center gap-1.5 rounded-full border border-amber-400/45 bg-amber-500/20 px-2.5 py-1 text-[11px] font-bold text-amber-50 shadow-[0_0_12px_rgba(245,158,11,0.3)]"
        }
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
        data-testid="intake-v6-review-operator-blocker-banner-toggle"
      >
        <AlertTriangle className="h-3 w-3 shrink-0" aria-hidden />
        <span data-testid="intake-v6-review-operator-blocker-banner-title">{chipLabel}</span>
        <ChevronDown
          className={`h-3 w-3 shrink-0 transition ${expanded ? "rotate-180" : ""}`}
          aria-hidden
        />
      </button>

      {expanded ? (
        <div
          className="absolute right-0 z-20 mt-1.5 w-[min(22rem,calc(100vw-2rem))] rounded-md border border-[#2A3548] bg-[#101827] p-2.5 shadow-xl"
          data-testid="intake-v6-review-operator-blocker-banner-list"
        >
          <p className="mb-2 text-[11px] font-semibold text-slate-200">{display.summaryTitle}</p>
          <ul className="space-y-2">
            {display.issues.map((issue) => (
              <li
                key={issue.id}
                className="rounded border border-[#2A3548]/80 bg-[#0A0F1A]/50 px-2 py-1.5"
                data-testid={`intake-v6-review-operator-blocker-issue-${issue.id}`}
              >
                <p className="text-[11px] leading-snug text-slate-200">{issue.message}</p>
                {issue.action ? (
                  <p className="mt-0.5 text-[10px] text-slate-500">{issue.action}</p>
                ) : null}
                {issue.focusTarget && onFocusTarget ? (
                  <button
                    type="button"
                    className="mt-1 text-[10px] font-semibold text-cyan-300 hover:text-cyan-200"
                    onClick={() => onFocusTarget(issue.focusTarget!)}
                    data-testid={`intake-v6-review-operator-blocker-jump-${issue.id}`}
                  >
                    Mergi la câmp
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
          {onJumpToDiagnostic ? (
            <button
              type="button"
              className="mt-2 text-[10px] font-semibold text-slate-500 underline-offset-2 hover:text-slate-300 hover:underline"
              onClick={onJumpToDiagnostic}
              data-testid="intake-v6-review-operator-blocker-diagnostic-link"
            >
              Diagnostic tehnic
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
