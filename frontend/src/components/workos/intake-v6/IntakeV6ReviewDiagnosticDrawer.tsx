import { useEffect, type ReactNode } from "react";
import { X } from "lucide-react";

/**
 * Technical diagnostic lives outside the operator document scroll.
 * Content is mounted only while open (caller should lazy-fetch too).
 */
export default function IntakeV6ReviewDiagnosticDrawer({
  open,
  onOpenChange,
  title = "Diagnostic tehnic",
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  children: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onOpenChange(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onOpenChange]);

  if (!open) {
    return (
      <div className="mt-2" data-testid="intake-v6-review-diagnostic-entry">
        <button
          type="button"
          className="text-[11px] font-medium text-slate-500 underline-offset-2 hover:text-slate-300 hover:underline"
          onClick={() => onOpenChange(true)}
          data-testid="intake-v6-review-technical-details-toggle"
        >
          Deschide diagnostic tehnic
        </button>
      </div>
    );
  }

  return (
    <div
      className="fixed inset-0 z-40 flex justify-end bg-black/45"
      data-testid="intake-v6-review-diagnostic-drawer"
      data-expanded="true"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      <button
        type="button"
        className="absolute inset-0 cursor-default"
        aria-label="Închide diagnostic"
        onClick={() => onOpenChange(false)}
        data-testid="intake-v6-review-diagnostic-backdrop"
      />
      <aside
        className="relative z-10 flex h-full w-full max-w-xl flex-col border-l border-wo-border-strong bg-wo-surface-inset shadow-2xl"
        data-testid="intake-v6-review-technical-details"
        data-expanded="true"
      >
        <header className="flex items-center justify-between gap-2 border-b border-wo-border-strong px-3 py-2.5">
          <h2 className="text-[13px] font-semibold text-slate-100">{title}</h2>
          <button
            type="button"
            className="rounded border border-wo-border-strong p-1 text-slate-400 hover:text-slate-100"
            onClick={() => onOpenChange(false)}
            aria-label="Închide"
            data-testid="intake-v6-review-diagnostic-close"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </header>
        <div
          className="min-h-0 flex-1 overflow-y-auto px-3 py-3"
          data-testid="intake-v6-review-diagnostic-tehnic"
          id="intake-v6-review-diagnostic-tehnic"
        >
          {children}
        </div>
      </aside>
    </div>
  );
}
