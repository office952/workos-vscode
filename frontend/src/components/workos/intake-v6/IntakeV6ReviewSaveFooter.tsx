export default function IntakeV6ReviewSaveFooter({
  saving,
  pendingSave,
  error,
}: {
  saving: boolean;
  pendingSave: boolean;
  error?: string | null;
}) {
  const label = saving
    ? "Sincronizez preturile..."
    : error
      ? "Sincronizare esuata"
      : pendingSave
        ? "Sincronizare automata in asteptare"
        : "Preturi si materiale actualizate";
  const tone = error ? "text-red-300" : pendingSave || saving ? "text-amber-200" : "text-emerald-300";

  return (
    <div
      className="sticky bottom-0 z-10 mb-4 rounded border border-[#2A3548] bg-[#0A0F1A]/95 px-4 py-3 backdrop-blur-sm"
      data-testid="intake-v6-review-save-footer"
    >
      <div className={`flex items-center justify-between gap-3 text-[12px] ${tone}`}>
        <span data-testid="intake-v6-review-autosave-status">{label}</span>
        <span className="h-2 w-2 rounded-full bg-current opacity-80" aria-hidden />
      </div>
    </div>
  );
}



