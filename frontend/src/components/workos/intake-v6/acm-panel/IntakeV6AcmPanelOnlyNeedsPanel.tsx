/**
 * Operator teaching surface: what ACM panel-alone needs vs VL letter chrome.
 */

import {
  resolveAcmPanelOnlyUiScope,
  type AcmPanelOnlyUiScope,
} from "@/lib/intakeV6/acmPanel/acmPanelOnlyComposition";

export default function IntakeV6AcmPanelOnlyNeedsPanel({
  payload,
  scope: scopeProp,
  variant = "review",
}: {
  payload?: Record<string, unknown> | null;
  scope?: AcmPanelOnlyUiScope;
  variant?: "review" | "offer_scope" | "confirm";
}) {
  const scope = scopeProp ?? resolveAcmPanelOnlyUiScope(payload);
  if (!scope.isAcmPanelOnly) return null;

  const title =
    variant === "offer_scope"
      ? scope.offerScopeTitleRo
      : variant === "confirm"
        ? "Rezumat — panou ACM (fără litere)"
        : "Ce cere oferta pe panou";

  const shellClass =
    variant === "offer_scope"
      ? "rounded-lg border border-cyan-500/30 bg-gradient-to-b from-cyan-500/[0.08] to-transparent px-3.5 py-3"
      : "rounded-lg border border-cyan-500/25 bg-cyan-500/[0.06] px-3 py-2.5";

  return (
    <section
      className={shellClass}
      data-testid="intake-v6-acm-panel-only-needs"
      data-variant={variant}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <h3 className="text-[12px] font-semibold tracking-tight text-cyan-100">{title}</h3>
        <span
          className="rounded border border-cyan-500/25 bg-cyan-500/10 px-1.5 py-0.5 text-[10px] font-medium text-cyan-200/90"
          data-testid="intake-v6-acm-panel-only-badge"
        >
          Panou ACM
        </span>
      </div>
      <p className="mt-1.5 max-w-2xl text-[11px] leading-relaxed text-slate-300/95">
        {scope.offerScopeBodyRo}
      </p>
      <div className="mt-2.5 grid gap-2.5 sm:grid-cols-2">
        <div
          className="rounded border border-emerald-500/20 bg-emerald-500/[0.06] px-2.5 py-2"
          data-testid="intake-v6-acm-panel-only-in-scope"
        >
          <p className="text-[10px] font-semibold uppercase tracking-wide text-emerald-300/90">
            În scope
          </p>
          <ul className="mt-1.5 list-disc space-y-1 pl-4 text-[11px] leading-snug text-slate-200">
            {scope.inScopeNeedsRo.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
        <div
          className="rounded border border-amber-500/20 bg-amber-500/[0.05] px-2.5 py-2"
          data-testid="intake-v6-acm-panel-only-out-of-scope"
        >
          <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-200/90">
            Nu se cere
          </p>
          <ul className="mt-1.5 list-disc space-y-1 pl-4 text-[11px] leading-snug text-slate-400">
            {scope.outOfScopeNeedsRo.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      </div>
      {variant === "review" ? (
        <p className="mt-2.5 text-[10px] leading-relaxed text-slate-500">
          Confirmă panoul Alucobond o singură dată, la finalul formularului. Tab-urile Față / Cant
          litere nu apar pe această ofertă.
        </p>
      ) : null}
    </section>
  );
}
