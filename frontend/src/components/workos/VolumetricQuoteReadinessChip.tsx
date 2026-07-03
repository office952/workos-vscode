import {
  isVolumetricCommercialQuoteReadiness,
  readinessStatusLabel,
  summarizeVolumetricQuoteGate,
  type QuoteReadinessSnapshot,
} from "@/lib/volumetricQuoteReady";

const CHIP_STYLES = {
  ready: "bg-emerald-900/40 text-emerald-300 border-emerald-700/50",
  ready_with_warnings: "bg-blue-900/40 text-blue-300 border-blue-700/50",
  requires_acknowledgement: "bg-amber-900/40 text-amber-300 border-amber-700/50",
  blocked: "bg-red-900/40 text-red-300 border-red-700/50",
} as const;

function formatCounts(summary: ReturnType<typeof summarizeVolumetricQuoteGate>): string | null {
  const parts: string[] = [];
  if (summary.blockerCount > 0) parts.push(`${summary.blockerCount} blocker${summary.blockerCount === 1 ? "" : "s"}`);
  if (summary.acknowledgementPendingCount > 0) {
    parts.push(
      `${summary.acknowledgementPendingCount} ack pending`
    );
  } else if (summary.warningCount > 0) {
    parts.push(`${summary.warningCount} warn${summary.warningCount === 1 ? "" : "s"}`);
  }
  return parts.length > 0 ? parts.join(" · ") : null;
}

export function VolumetricQuoteReadinessChip({
  snapshot,
  testId,
}: {
  snapshot: QuoteReadinessSnapshot | null | undefined;
  testId?: string;
}) {
  if (!isVolumetricCommercialQuoteReadiness(snapshot)) return null;

  const summary = summarizeVolumetricQuoteGate(snapshot?.quoteGate);
  const label = readinessStatusLabel(summary.status);
  const counts = formatCounts(summary);

  return (
    <span
      data-testid={testId ?? "quote-volumetric-readiness-chip"}
      data-readiness-status={summary.status}
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-semibold rounded border ${CHIP_STYLES[summary.status]}`}
      title={counts ?? label}
    >
      {label}
      {counts ? <span className="font-normal opacity-80">({counts})</span> : null}
    </span>
  );
}
