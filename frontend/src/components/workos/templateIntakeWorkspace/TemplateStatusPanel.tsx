import type { IntakeActionSummaryModel } from "@/lib/intakeActionSummary";
import InfoHint from "./InfoHint";

function statusDot(ok: boolean | null) {
  if (ok === null) return "bg-slate-600";
  return ok ? "bg-emerald-400" : "bg-amber-400";
}

export interface TemplateStatusPanelProps {
  actionSummary: IntakeActionSummaryModel;
  readinessMissing?: string[];
  variant?: "inline" | "stacked";
}

/** Compact readiness strip — no badge spam. */
export default function TemplateStatusPanel({
  actionSummary,
  readinessMissing = [],
  variant = "inline",
}: TemplateStatusPanelProps) {
  const items = [
    { label: "Template", ok: actionSummary.templateOk, value: actionSummary.templateLabel },
    { label: "Spec", ok: actionSummary.productSpecOk, value: actionSummary.productSpecLabel },
    { label: "Teren", ok: actionSummary.terrainOk, value: actionSummary.terrainLabel },
    { label: "Intake", ok: actionSummary.intakeReady, value: actionSummary.intakeStatusLabel },
  ];

  const itemRow = (item: (typeof items)[number]) => (
    <span key={item.label} className="inline-flex items-center gap-1.5 min-w-0">
      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${statusDot(item.ok)}`} />
      <span className="text-slate-500 shrink-0">{item.label}</span>
      <span className="text-slate-300 font-medium truncate">{item.value}</span>
    </span>
  );

  return (
    <div
      className={`bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-3 text-[11px] text-slate-400 ${
        variant === "stacked" ? "space-y-2" : ""
      }`}
      data-testid="template-status-panel"
    >
      {variant === "stacked" ? (
        <div className="flex flex-col gap-1.5">{items.map(itemRow)}</div>
      ) : (
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          {items.map(itemRow)}
        </div>
      )}
      <p className="text-slate-500 mt-1">
        Etapă:{" "}
        <span
          className="text-slate-300 font-medium"
          data-testid="template-status-stage"
        >
          {actionSummary.readinessStageLabel}
        </span>
      </p>
      {readinessMissing.length > 0 && (
        <p className="inline-flex items-start gap-1 text-amber-400/90 mt-1">
          <span>Comercial: {readinessMissing.join(", ")}</span>
          <InfoHint label="Detalii readiness">
            Condiții pentru marcare Gata pt. Ofertă (comercial). Simularea poate
            fi disponibilă separat.
          </InfoHint>
        </p>
      )}
    </div>
  );
}
