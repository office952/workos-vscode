import {
  collectArtworkUndecidedWarnings,
  collectFatalHandoffBlockers,
  formatQuoteHandoffBlocker,
} from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";
import type { IntakeV6QuoteHandoffPreviewResponse } from "@/lib/intakeV6/intakeV6Api";
import { v6 } from "./atoms/intakeV6Presentation";

const DRAFT_ONLY_LINES = [
  "Draft intern only — nu trimite oferta clientului din acest pas.",
  "Nu creează comandă.",
  "Nu pornește producție.",
  "Nu mută stoc.",
] as const;

export default function IntakeV6ConfirmHandoffSummaryCard({
  handoffPreview,
  bindingBlockers = [],
  loading = false,
}: {
  handoffPreview: IntakeV6QuoteHandoffPreviewResponse | null;
  bindingBlockers?: string[];
  loading?: boolean;
}) {
  const fatalBlockers = [
    ...new Set([...collectFatalHandoffBlockers(handoffPreview), ...bindingBlockers]),
  ];
  const reviewWarnings = handoffPreview?.review_warnings ?? [];
  const artworkWarnings = collectArtworkUndecidedWarnings(reviewWarnings);
  const nonArtworkWarnings = reviewWarnings
    .filter(
      (code) =>
        !code.startsWith("artwork_execution_undecided:") &&
        code !== "unclassified_vector_artwork_requires_decision",
    )
    .map(formatQuoteHandoffBlocker);

  if (loading) {
    return (
      <div className={`${v6.card} mb-4`} data-testid="intake-v6-confirm-handoff-summary-loading">
        <p className="text-[12px] text-slate-400">Încarc sumarul blocajelor…</p>
      </div>
    );
  }

  return (
    <div className={`${v6.card} mb-4`} data-testid="intake-v6-confirm-handoff-summary-above-fold">
      <h3 className="mb-2 text-[12px] font-bold uppercase tracking-wide text-slate-200">
        Limite draft intern
      </h3>
      <ul className="mb-3 space-y-1 text-[11px] text-slate-300" data-testid="intake-v6-confirm-draft-only-lines">
        {DRAFT_ONLY_LINES.map((line) => (
          <li key={line}>- {line}</li>
        ))}
      </ul>

      {fatalBlockers.length > 0 ? (
        <div className="mb-3" data-testid="intake-v6-confirm-fatal-blockers-above-fold">
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-amber-200">
            Blocaje principale
          </p>
          <ul className="space-y-1 text-[11px] text-amber-100">
            {fatalBlockers.map((blocker) => (
              <li key={blocker}>- {formatQuoteHandoffBlocker(blocker)}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {artworkWarnings.length > 0 || nonArtworkWarnings.length > 0 ? (
        <div
          className="rounded border border-amber-500/30 bg-amber-500/10 px-3 py-2"
          data-testid="intake-v6-confirm-review-warnings-above-fold"
        >
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-amber-200">
            Atenționări review
          </p>
          <ul className="space-y-1 text-[11px] text-amber-100/90">
            {[...artworkWarnings, ...nonArtworkWarnings].map((warning) => (
              <li key={warning}>- {warning}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
