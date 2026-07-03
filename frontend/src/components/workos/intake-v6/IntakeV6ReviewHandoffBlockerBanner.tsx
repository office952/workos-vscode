import type { ReviewHandoffSurfacing } from "@/lib/intakeV6/intakeV6QuoteHandoffReadiness";

export default function IntakeV6ReviewHandoffBlockerBanner({
  surfacing,
  loading = false,
}: {
  surfacing: ReviewHandoffSurfacing;
  loading?: boolean;
}) {
  if (loading) {
    return (
      <p
        className="mb-4 rounded border border-[#2A3548] bg-[#0A0F1A]/60 px-4 py-3 text-[12px] text-slate-400"
        data-testid="intake-v6-review-handoff-blocker-banner-loading"
      >
        Verific blocajele de handoff pentru Confirmare…
      </p>
    );
  }

  if (!surfacing.showBanner) {
    return null;
  }

  return (
    <div
      className="mb-4 rounded border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-[12px] text-amber-50"
      data-testid="intake-v6-review-handoff-blocker-banner"
    >
      <p className="font-semibold text-amber-100">Confirmarea ofertei este încă blocată</p>
      {surfacing.reasons.length > 0 ? (
        <ul className="mt-2 space-y-1 text-amber-100/90" data-testid="intake-v6-review-handoff-reasons">
          {surfacing.reasons.map((reason) => (
            <li key={reason}>- {reason}</li>
          ))}
        </ul>
      ) : null}
      {surfacing.actions.length > 0 ? (
        <ul className="mt-2 space-y-1 text-amber-200/80" data-testid="intake-v6-review-handoff-actions">
          {surfacing.actions.map((action) => (
            <li key={action}>→ {action}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
