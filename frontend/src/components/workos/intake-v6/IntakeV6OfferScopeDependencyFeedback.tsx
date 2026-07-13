import {
  CODE_ELECTRICAL_LOAD_NOT_SOLD,
  CODE_LED_INSTALLATION_BY_US,
  CODE_LED_MOUNT_SURFACE_NOT_SOLD,
  firstDependencyBlockerMessage,
  readDependencyConfirmations,
  type SoldScopeDependencyValidation,
} from "@/lib/intakeV6/intakeV6OfferScopeDependency";

export default function IntakeV6OfferScopeDependencyFeedback({
  validation,
  onConfirmCode,
  confirmingCode,
  dependencyConfirmations,
}: {
  validation: SoldScopeDependencyValidation | null;
  onConfirmCode: (code: string) => void;
  confirmingCode: string | null;
  dependencyConfirmations?: Set<string>;
}) {
  if (!validation) {
    return null;
  }

  const hasIssues =
    validation.blockers.length > 0 ||
    validation.confirmations_required.length > 0 ||
    validation.warnings.length > 0;

  const showInstallByUsPrompt =
    dependencyConfirmations?.has(CODE_LED_MOUNT_SURFACE_NOT_SOLD) &&
    !dependencyConfirmations.has(CODE_LED_INSTALLATION_BY_US);

  if (!hasIssues && !showInstallByUsPrompt) {
    return null;
  }

  const primary = hasIssues ? firstDependencyBlockerMessage(validation) : null;

  return (
    <div
      className="mt-3 space-y-2 rounded-md border border-amber-500/30 bg-amber-500/5 p-3"
      data-testid="intake-v6-offer-scope-dependency-feedback"
    >
      {primary ? (
        <p className="text-[11px] text-amber-100" data-testid="intake-v6-offer-scope-dependency-primary">
          {primary}
        </p>
      ) : null}

      {validation.confirmations_required.map((issue) => (
        <div key={issue.code} className="flex flex-wrap items-center gap-2">
          <p className="text-[10px] text-slate-300">{issue.message}</p>
          <button
            type="button"
            className="rounded border border-emerald-500/40 px-2 py-1 text-[10px] text-emerald-200 hover:bg-emerald-500/10"
            data-testid={`intake-v6-offer-scope-dependency-confirm-${issue.code}`}
            disabled={confirmingCode === issue.code}
            onClick={() => onConfirmCode(issue.code)}
          >
            {confirmingCode === issue.code ? "Confirm…" : "Confirm"}
          </button>
        </div>
      ))}

      {validation.missing_capabilities.includes("LED_MOUNT_SURFACE") ? (
        <p className="text-[10px] text-slate-400" data-testid="intake-v6-offer-scope-dependency-mount-hint">
          Iluminarea necesita un suport de montaj. Selecteaza Spate sau Față+Cant, sau confirmă suport existent.
        </p>
      ) : null}

      {(validation.warnings.some((w) => w.code === CODE_ELECTRICAL_LOAD_NOT_SOLD) ||
        validation.confirmations_required.some((c) => c.code === CODE_ELECTRICAL_LOAD_NOT_SOLD)) && (
        <p className="text-[10px] text-slate-400" data-testid="intake-v6-offer-scope-dependency-electrical-hint">
          Electrica fără Iluminare presupune sarcină LED existentă sau furnizată separat.
        </p>
      )}

      {validation.satisfied_capabilities.includes("LED_MOUNT_SURFACE") ? (
        <p className="text-[10px] text-emerald-300" data-testid="intake-v6-offer-scope-dependency-mount-satisfied">
          Suport montaj LED: satisfăcut
        </p>
      ) : null}

      {dependencyConfirmations?.has(CODE_LED_MOUNT_SURFACE_NOT_SOLD) &&
      !dependencyConfirmations.has(CODE_LED_INSTALLATION_BY_US) ? (
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-[10px] text-slate-300">
            Suportul LED este extern. Confirmă dacă atelierul montează modulele LED.
          </p>
          <button
            type="button"
            className="rounded border border-emerald-500/40 px-2 py-1 text-[10px] text-emerald-200 hover:bg-emerald-500/10"
            data-testid={`intake-v6-offer-scope-dependency-confirm-${CODE_LED_INSTALLATION_BY_US}`}
            disabled={confirmingCode === CODE_LED_INSTALLATION_BY_US}
            onClick={() => onConfirmCode(CODE_LED_INSTALLATION_BY_US)}
          >
            {confirmingCode === CODE_LED_INSTALLATION_BY_US ? "Confirm…" : "Montaj de noi"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
