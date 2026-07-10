import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";
import { buildIntakeV6LayersAnalysisWarningSummaries } from "@/lib/intakeV6/intakeV6LayersAnalysisWarningSummaries";
import { useIntakeV6WorkspaceHeaderStatusOptional } from "./IntakeV6WorkspaceHeaderStatusContext";

export default function IntakeV6LayersWarningsPanel({
  report,
  confirmation,
  parseWarning,
  scopeWarnings,
}: {
  report: SvgAnalysisCoreReport | null;
  confirmation: LayerRoleConfirmation | null;
  parseWarning?: string | null;
  scopeWarnings: string[];
  onJumpToLayer?: (layerKey: string) => void;
}) {
  const statusCtx = useIntakeV6WorkspaceHeaderStatusOptional();
  const summaries = buildIntakeV6LayersAnalysisWarningSummaries({
    report,
    confirmation,
    parseWarning,
    scopeWarnings,
  });

  if (summaries.length === 0) return null;

  return (
    <div
      className="rounded-md border border-[#243044]/70 bg-[#101827]/40 px-3 py-2"
      data-testid="intake-v6-layers-warnings"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-[11px] text-slate-400" data-testid="intake-v6-layers-warnings-count">
          {summaries.length} {summaries.length === 1 ? "observație analiză" : "observații analiză"}
        </p>
        <button
          type="button"
          className="text-[11px] font-semibold text-cyan-300/90 hover:text-cyan-200"
          data-testid="intake-v6-layers-warnings-open-footer"
          onClick={() => statusCtx?.openFooterIssues()}
        >
          Vezi în subsol
        </button>
      </div>
    </div>
  );
}
