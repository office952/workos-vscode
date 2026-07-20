/**
 * Read-only legacy Fundal surface — navigates to AcmPanel inspector.
 * No editable inputs for AcmPanel fields.
 */

import type { AcmPanelUiReadModel } from "@/lib/intakeV6/acmPanel/uiReadModel";

export default function IntakeV6AcmPanelFundalSummary({
  model,
  onOpenInspector,
}: {
  model: AcmPanelUiReadModel;
  onOpenInspector: (sectionId?: string) => void;
}) {
  if (!model.exists) return null;

  return (
    <div
      className="rounded border border-cyan-900/50 bg-cyan-950/20 px-3 py-3"
      data-testid="intake-v6-acm-fundal-readonly-summary"
    >
      <p className="text-[11px] font-semibold text-cyan-200">Panou Alucobond casetat</p>
      <p className="mt-1 text-[11px] text-slate-300">
        Stare: <span className="text-amber-100">{model.primaryStatus.label}</span>
        {model.dimensionsSummary ? (
          <>
            {" "}
            · Dimensiuni: <span className="text-cyan-100">{model.dimensionsSummary}</span>
          </>
        ) : null}
        {model.segmentCount > 1 ? (
          <>
            {" "}
            · Segmente: <span className="text-cyan-100">{model.segmentCount}</span> (
            {model.segmentedLabel})
          </>
        ) : null}
      </p>
      {model.unresolvedConfirmations.length ? (
        <p className="mt-1 text-[10px] text-amber-200">
          Nerezolvat: {model.unresolvedConfirmations.join(" · ")}
        </p>
      ) : null}
      <p className="mt-2 text-[10px] text-slate-500">
        Configurarea editabilă este în inspectorul componentei — nu aici.
      </p>
      <button
        type="button"
        className="mt-2 rounded border border-[#3b82f5]/45 bg-[#172952]/60 px-2.5 py-1.5 text-[11px] font-medium text-[#93c5fd] hover:bg-[#1e3a5f]"
        data-testid="intake-v6-acm-open-inspector-from-fundal"
        onClick={() => onOpenInspector("summary")}
      >
        Deschide configurarea Panoului Alucobond
      </button>
    </div>
  );
}
