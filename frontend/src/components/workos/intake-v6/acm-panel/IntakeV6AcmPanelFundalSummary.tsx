/**
 * Read-only legacy Fundal surface — navigates to AcmPanel inspector.
 * No editable inputs for AcmPanel fields.
 */

import type { AcmPanelUiReadModel } from "@/lib/intakeV6/acmPanel/uiReadModel";
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";

export default function IntakeV6AcmPanelFundalSummary({
  model,
  onOpenInspector,
}: {
  model: AcmPanelUiReadModel;
  onOpenInspector: (sectionId?: string) => void;
}) {
  if (!model.exists) return null;
  const showStatus = intakeV6ShowOperatorConfigStatusBadges();

  return (
    <div
      className="rounded border border-cyan-900/50 bg-cyan-950/20 px-3 py-3"
      data-testid="intake-v6-acm-fundal-readonly-summary"
    >
      <p className="text-[11px] font-semibold text-cyan-200">Alucobond casetat</p>
      <p className="mt-1 text-[11px] text-slate-300">
        {showStatus ? (
          <>
            Stare: <span className="text-amber-100">{model.primaryStatus.label}</span>
          </>
        ) : null}
        {model.dimensionsSummary ? (
          <>
            {showStatus ? " · " : null}
            Dimensiuni: <span className="text-cyan-100">{model.dimensionsSummary}</span>
          </>
        ) : null}
        {model.segmentCount > 1 ? (
          <>
            {" "}
            · Segmente: <span className="text-cyan-100">{model.segmentCount}</span>
            {showStatus ? <> ({model.segmentedLabel})</> : null}
          </>
        ) : null}
      </p>
      {showStatus && model.unresolvedConfirmations.length ? (
        <p className="mt-1 text-[10px] text-amber-200">
          Nerezolvat: {model.unresolvedConfirmations.join(" · ")}
        </p>
      ) : null}
      <p className="mt-2 text-[10px] text-slate-500">
        Configurarea editabilă este în inspectorul componentei — nu aici.
      </p>
      <button
        type="button"
        className="mt-2 rounded border border-blue-500/45 bg-blue-50 px-2.5 py-1.5 text-[11px] font-medium text-sky-800 hover:bg-blue-100 dark:bg-blue-950/50 dark:text-sky-300 dark:hover:bg-blue-900/50"
        data-testid="intake-v6-acm-open-inspector-from-fundal"
        onClick={() => onOpenInspector("summary")}
      >
        Deschide configurarea Panoului Alucobond
      </button>
    </div>
  );
}
