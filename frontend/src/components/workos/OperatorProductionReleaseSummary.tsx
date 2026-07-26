import type { OperatorTaskTruthResponse } from "@/api/operatorTaskTruth";
import {
  productionPolicyExplanation,
  productionReleaseStatusLabel,
  productionScopeLabel,
  summarizeTaskTruthProduction,
  unresolvedBlockingCount,
} from "@/lib/operatorProductionBlockerPresentation";
import { AlertTriangle, CheckCircle2 } from "lucide-react";

type Props = {
  truth: OperatorTaskTruthResponse | null;
  onOpenDetails?: () => void;
  testId?: string;
};

export function OperatorProductionReleaseSummary({ truth, onOpenDetails, testId }: Props) {
  if (!truth) return null;

  const summary = summarizeTaskTruthProduction(truth);
  if (!summary) return null;

  const blocked = summary.blocked;
  const unresolved = unresolvedBlockingCount(truth.owner_decisions_summary);

  return (
    <section
      className={`rounded-lg border px-3 py-2.5 space-y-1.5 ${
        blocked
          ? "border-red-800/60 bg-red-950/20"
          : "border-emerald-800/50 bg-emerald-950/15"
      }`}
      data-testid={testId || "operator-production-release-summary"}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {blocked ? (
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          )}
          <div className="min-w-0">
            <p
              className={`text-[12px] font-semibold ${blocked ? "text-red-200" : "text-emerald-200"}`}
              data-testid="operator-production-release-status"
            >
              {productionReleaseStatusLabel(summary.status, blocked)}
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5">
              Domeniu: {productionScopeLabel("ORDER_SCOPE")} · Politica:{" "}
              {summary.policy.replace(/_/g, " ")}
            </p>
          </div>
        </div>
        {onOpenDetails ? (
          <button
            type="button"
            onClick={onOpenDetails}
            className="text-[10px] font-semibold text-blue-300 hover:text-blue-200 shrink-0"
            data-testid="operator-production-release-details-toggle"
          >
            Detalii decizii
          </button>
        ) : null}
      </div>

      <p className="text-[11px] text-slate-300 leading-relaxed">
        {blocked
          ? productionPolicyExplanation(summary.policy)
          : "Productia poate porni conform politicii curente. Readiness-ul operational ramane evaluat separat pe fiecare task."}
      </p>

      {blocked ? (
        <p className="text-[11px] text-amber-200/90" data-testid="operator-production-blocker-count">
          {unresolved} decizie(i) de productie nerezolvata(e). Planul poate exista, dar pornirea
          task-urilor ramane blocata.
        </p>
      ) : (
        <p className="text-[11px] text-slate-400">
          Nicio blocare de productie activa. Readiness-ul operational ramane evaluat separat pe
          fiecare task.
        </p>
      )}
    </section>
  );
}
