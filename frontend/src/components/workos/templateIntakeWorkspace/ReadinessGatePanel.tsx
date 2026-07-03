import { Calculator, CheckCircle2, XCircle } from "lucide-react";
import { INTAKE_SECTION_IDS } from "@/lib/intakeActionSummary";
import type { IntakeRequest } from "@/lib/mockData";
import type { IntakeActionSummaryModel } from "@/lib/intakeActionSummary";
import type { IntakeReadinessStageId } from "@/lib/intakeReadinessStages";
import InfoHint from "./InfoHint";

export interface ReadinessGatePanelProps {
  request: IntakeRequest;
  readiness: { canMarkReady: boolean; missing: string[] };
  actionSummary: IntakeActionSummaryModel;
  markReadyLoading: boolean;
  markReadyMessage: string | null;
  source: string;
  onMarkReady: () => void;
  onOpenQuote: () => void;
  layout?: "inline" | "stack";
}

function stageStatusIcon(ready: boolean, isActive: boolean) {
  if (ready) {
    return <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />;
  }
  if (isActive) {
    return <XCircle className="w-3 h-3 text-amber-400 shrink-0" />;
  }
  return <span className="w-3 h-3 rounded-full bg-slate-600 shrink-0" />;
}

function StagedReadinessList({
  workingStage,
  groups,
}: {
  workingStage: IntakeReadinessStageId;
  groups: IntakeActionSummaryModel["stagedMissingGroups"];
}) {
  const visible = groups.filter(
    (g) => g.stage !== "stage0_unresolved" && (!g.ready || g.missing.length > 0)
  );
  if (visible.length === 0) return null;

  return (
    <div className="mt-3 space-y-3" data-testid="staged-readiness-groups">
      {visible.map((group) => {
        const isActive = group.stage === workingStage;
        return (
          <div
            key={group.stage}
            data-testid={`readiness-stage-${group.stage}`}
            className={`rounded-lg border px-3 py-2 ${
              isActive
                ? "border-amber-900/50 bg-amber-950/20"
                : "border-[#1E293B] bg-[#0f172a]/40"
            }`}
          >
            <div className="flex items-center gap-1.5 mb-1">
              {stageStatusIcon(group.ready, isActive)}
              <p
                className={`text-[11px] font-semibold ${
                  isActive ? "text-amber-200" : "text-slate-400"
                }`}
              >
                {group.label}
              </p>
            </div>
            {group.missing.length > 0 ? (
              <ul className="space-y-0.5 pl-5">
                {group.missing.map((item) => (
                  <li
                    key={item}
                    className="text-[10px] text-red-300/90 list-disc"
                  >
                    {item}
                  </li>
                ))}
              </ul>
            ) : group.ready ? (
              <p className="text-[10px] text-emerald-400/80">Complet</p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}

export default function ReadinessGatePanel({
  request,
  readiness,
  actionSummary,
  markReadyLoading,
  markReadyMessage,
  source,
  onMarkReady,
  onOpenQuote,
  layout = "inline",
}: ReadinessGatePanelProps) {
  const canMark =
    readiness.canMarkReady &&
    request.status !== "ready_for_quote" &&
    source !== "mock";

  const showSimulate =
    actionSummary.showPreliminaryQuote &&
    (actionSummary.canSimulate || actionSummary.intakeReady);

  return (
    <div
      id={INTAKE_SECTION_IDS["ready-actions"]}
      className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 scroll-mt-4"
      data-testid="readiness-gate-panel"
    >
      <div className="mb-2">
        <p className="text-[10px] text-slate-500 uppercase tracking-wide">
          Etapă readiness
        </p>
        <p
          className="text-[12px] font-semibold text-slate-200"
          data-testid="readiness-stage-label"
        >
          {actionSummary.readinessStageLabel}
        </p>
        {actionSummary.canSimulate &&
          !actionSummary.intakeReady &&
          actionSummary.stagedMissingGroups.some(
            (g) => g.stage === "stage3_commercial_quote" && g.missing.length > 0
          ) && (
            <p
              className="text-[10px] text-blue-300/90 mt-1"
              data-testid="simulation-available-hint"
            >
              Simulare disponibilă. Oferta comercială finală mai are condiții.
            </p>
          )}
      </div>

      <div
        className={
          layout === "stack"
            ? "flex flex-col gap-2"
            : "flex flex-wrap items-center justify-end gap-2"
        }
      >
        {showSimulate && (
          <button
            type="button"
            onClick={onOpenQuote}
            data-testid="action-open-preliminary-quote"
            className={`inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-[12px] font-semibold bg-blue-600 hover:bg-blue-500 text-white ${
              layout === "stack" ? "w-full" : ""
            }`}
          >
            <Calculator className="w-3.5 h-3.5" />
            Simulare ofertă
          </button>
        )}
        <button
          type="button"
          disabled={!canMark || markReadyLoading}
          onClick={() => void onMarkReady()}
          data-testid="action-mark-ready"
          className={`inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-[12px] font-bold transition-colors ${
            layout === "stack" ? "w-full" : ""
          } ${
            canMark
              ? "bg-emerald-600 hover:bg-emerald-500 text-white"
              : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
          }`}
        >
          <CheckCircle2 className="w-4 h-4" />
          {markReadyLoading ? "Se salvează…" : "Gata pt. Ofertă"}
        </button>
        {layout === "stack" ? (
          <div className="flex justify-end">
            <InfoHint label="Despre marcare ready">
              „Gata pt. Ofertă” = readiness comercial (legacy ready_for_quote).
              Simularea preliminară nu creează ofertă comercială și poate rula
              mai devreme.
            </InfoHint>
          </div>
        ) : (
          <InfoHint label="Despre marcare ready">
            „Gata pt. Ofertă” = readiness comercial (legacy ready_for_quote).
            Simularea preliminară nu creează ofertă comercială și poate rula
            mai devreme.
          </InfoHint>
        )}
      </div>

      {markReadyMessage && (
        <p className="text-[11px] text-emerald-400 mt-2">{markReadyMessage}</p>
      )}

      <StagedReadinessList
        workingStage={actionSummary.readinessStage}
        groups={actionSummary.stagedMissingGroups}
      />

      {!readiness.canMarkReady &&
        request.status !== "ready_for_quote" &&
        actionSummary.stagedMissingGroups.every(
          (g) => g.stage === "stage0_unresolved" || g.missing.length === 0
        ) &&
        readiness.missing.length > 0 && (
          <ul className="mt-3 space-y-1" data-testid="readiness-blockers">
            {readiness.missing.map((f) => (
              <li
                key={f}
                className="flex items-center gap-1.5 text-[11px] text-red-300/90"
              >
                <XCircle className="w-3 h-3 text-red-400 shrink-0" />
                {f}
              </li>
            ))}
          </ul>
        )}
    </div>
  );
}
