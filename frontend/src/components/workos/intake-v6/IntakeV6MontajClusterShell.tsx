import type { ReactNode } from "react";

type ClusterTone = "primary" | "secondary" | "muted";

const toneClass: Record<ClusterTone, string> = {
  primary: "border-cyan-700/50 bg-cyan-950/15",
  secondary: "border-wo-border-strong bg-wo-surface-inset/50",
  muted: "border-wo-border-strong/70 bg-wo-surface-inset/30",
};

export default function IntakeV6MontajClusterShell({
  title,
  description,
  statusLabel,
  statusTone = "muted",
  tone = "secondary",
  testId,
  children,
}: {
  title: string;
  description?: string;
  statusLabel?: string | null;
  statusTone?: "ok" | "pending" | "blocked" | "muted";
  tone?: ClusterTone;
  testId: string;
  children: ReactNode;
}) {
  const statusClass =
    statusTone === "ok"
      ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-100"
      : statusTone === "blocked"
        ? "border-rose-500/40 bg-rose-500/10 text-rose-100"
        : statusTone === "pending"
          ? "border-amber-500/40 bg-amber-500/10 text-amber-100"
          : "border-wo-border-strong bg-wo-surface-raised text-slate-300";

  return (
    <section
      className={`rounded-md border px-3 py-3 space-y-3 ${toneClass[tone]}`}
      data-testid={testId}
    >
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-[13px] font-semibold text-wo-text-primary">{title}</h3>
          {description ? (
            <p className="mt-0.5 text-[11px] leading-snug text-slate-400">{description}</p>
          ) : null}
        </div>
        {statusLabel ? (
          <span
            className={`shrink-0 rounded border px-2 py-0.5 text-[10px] font-semibold ${statusClass}`}
            data-testid={`${testId}-status`}
          >
            {statusLabel}
          </span>
        ) : null}
      </header>
      <div className="space-y-3" data-testid={`${testId}-body`}>
        {children}
      </div>
    </section>
  );
}
