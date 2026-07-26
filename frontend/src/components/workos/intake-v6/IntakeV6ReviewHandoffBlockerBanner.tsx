import { AlertBanner } from "@/components/workos/design-system";
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
        className="mb-3 rounded-md border border-wo-border-strong bg-wo-surface-inset/60 px-3 py-2 text-[12px] text-wo-text-muted"
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
    <div className="mb-3" data-testid="intake-v6-review-handoff-blocker-banner">
      <AlertBanner variant="warning" title="Confirmarea ofertei este încă blocată" compact>
        {surfacing.reasons.length > 0 ? (
          <ul className="mt-1 space-y-0.5" data-testid="intake-v6-review-handoff-reasons">
            {surfacing.reasons.map((reason) => (
              <li key={reason}>- {reason}</li>
            ))}
          </ul>
        ) : null}
        {surfacing.actions.length > 0 ? (
          <ul className="mt-1 space-y-0.5" data-testid="intake-v6-review-handoff-actions">
            {surfacing.actions.map((action) => (
              <li key={action}>→ {action}</li>
            ))}
          </ul>
        ) : null}
      </AlertBanner>
    </div>
  );
}
