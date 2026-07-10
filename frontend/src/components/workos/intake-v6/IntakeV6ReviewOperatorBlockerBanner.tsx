import { AlertTriangle } from "lucide-react";
import type { OperatorBlockerBannerDisplay } from "@/lib/intakeV6/intakeV6OperatorBlockerBannerDisplay";

export default function IntakeV6ReviewOperatorBlockerBanner({
  display,
  onJumpToDiagnostic,
}: {
  display: OperatorBlockerBannerDisplay;
  onJumpToDiagnostic?: () => void;
}) {
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
    return null;
  }

  const blocked = display.severity === "blocked";

  return (
    <div
      className={
        blocked
          ? "mb-3 rounded-md border border-rose-500/45 bg-rose-500/10 px-4 py-3"
          : "mb-3 rounded-md border border-amber-500/40 bg-amber-500/10 px-4 py-3"
      }
      data-testid="intake-v6-review-operator-blocker-banner"
      role="status"
    >
      <div className="flex flex-wrap items-start gap-2">
        <AlertTriangle
          className={`mt-0.5 h-4 w-4 shrink-0 ${blocked ? "text-rose-300" : "text-amber-300"}`}
          aria-hidden
        />
        <div className="min-w-0 flex-1">
          <p
            className={`text-[12px] font-semibold ${blocked ? "text-rose-100" : "text-amber-100"}`}
            data-testid="intake-v6-review-operator-blocker-banner-title"
          >
            {blocked
              ? "Acțiune necesară înainte de Confirmare"
              : "Verifică starea secțiunii Review"}
          </p>
          <ul
            className={`mt-2 space-y-1 text-[12px] leading-snug ${blocked ? "text-rose-50/95" : "text-amber-50/95"}`}
            data-testid="intake-v6-review-operator-blocker-messages"
          >
            {display.messages.map((message) => (
              <li key={message}>• {message}</li>
            ))}
          </ul>
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
