export default function IntakeV6ReviewSaveFooter({
  saving,
  pendingSave,
  error,
}: {
  saving: boolean;
  pendingSave: boolean;
  error?: string | null;
}) {
  // D1: successful idle sync is quiet — do not keep a persistent success slab.
  if (!saving && !pendingSave && !error) {
    return (
      <p className="sr-only" data-testid="intake-v6-review-autosave-status" aria-live="polite">
        Preturi si materiale actualizate
      </p>
    );
  }

  const label = saving
    ? "Sincronizez preturile..."
    : error
      ? "Sincronizare esuata"
      : "Sincronizare automata in asteptare";
  const tone = error ? "text-red-300" : "text-slate-400";

  return (
    <div
      className="relative z-0 mb-20 rounded border border-wo-border-strong/70 bg-wo-surface-inset/70 px-3 py-2"
      data-testid="intake-v6-review-save-footer"
    >
      <div className={`flex items-center justify-between gap-3 text-[12px] ${tone}`}>
        <span data-testid="intake-v6-review-autosave-status">{label}</span>
      </div>
    </div>
  );
}
