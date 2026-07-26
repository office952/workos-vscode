import type { IntakeV6ConfirmConsolidatedStatusDisplay } from "@/lib/intakeV6/intakeV6ConfirmConsolidatedStatus";

function tierStyles(tier: IntakeV6ConfirmConsolidatedStatusDisplay["tier"]): {
  border: string;
  bg: string;
  indicator: string;
  headline: string;
} {
  switch (tier) {
    case "blocked":
      return {
        border: "border-rose-500/25",
        bg: "bg-rose-500/5",
        indicator: "text-rose-200/90",
        headline: "text-rose-100",
      };
    case "attention":
      return {
        border: "border-amber-500/25",
        bg: "bg-amber-500/5",
        indicator: "text-amber-200/90",
        headline: "text-amber-50",
      };
    case "ready":
      return {
        border: "border-emerald-500/20",
        bg: "bg-emerald-500/5",
        indicator: "text-emerald-200/90",
        headline: "text-emerald-50",
      };
    default:
      return {
        border: "border-wo-border-strong/70",
        bg: "bg-wo-surface-raised/40",
        indicator: "text-slate-400",
        headline: "text-slate-200",
      };
  }
}

export default function IntakeV6ConfirmConsolidatedStatusPanel({
  status,
}: {
  status: IntakeV6ConfirmConsolidatedStatusDisplay;
}) {
  const styles = tierStyles(status.tier);

  return (
    <div
      className={`rounded-md border px-3 py-2.5 ${styles.border} ${styles.bg}`}
      data-testid="intake-v6-confirm-consolidated-status"
      data-status-tier={status.tier}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">{status.title}</p>
          <p
            className={`mt-0.5 text-[13px] font-medium leading-snug ${styles.headline}`}
            data-testid="intake-v6-confirm-consolidated-headline"
          >
            {status.headline}
          </p>
        </div>
        <span
          className={`shrink-0 text-[10px] font-medium uppercase tracking-wide ${styles.indicator}`}
          data-testid="intake-v6-confirm-consolidated-indicator"
        >
          {status.indicatorLabel}
        </span>
      </div>
      {status.observations.length > 0 ? (
        <ul className="mt-2 space-y-1" data-testid="intake-v6-confirm-consolidated-observations">
          {status.observations.map((observation) => (
            <li key={observation} className="text-[11px] leading-relaxed text-slate-400">
              {observation}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
