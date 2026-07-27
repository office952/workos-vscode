import type { OperatorTaskTruthResponse } from "@/api/operatorTaskTruth";
import { chromeBanner } from "@/components/workos/design-system/chromeRecipes";
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
        blocked ? chromeBanner.error : chromeBanner.success
      }`}
      data-testid={testId || "operator-production-release-summary"}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {blocked ? (
            <AlertTriangle className="w-4 h-4 text-red-700 dark:text-red-400 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-700 dark:text-emerald-400 shrink-0" />
          )}
          <div className="min-w-0">
            <p
              className={`text-[12px] font-semibold ${
                blocked
                  ? "text-red-900 dark:text-red-100"
                  : "text-emerald-900 dark:text-emerald-100"
              }`}
              data-testid="operator-production-release-status"
            >
              {productionReleaseStatusLabel(summary.status, blocked)}
            </p>
            <p
              className={`text-[10px] mt-0.5 ${
                blocked
                  ? "text-red-800/80 dark:text-red-200/70"
                  : "text-emerald-800/85 dark:text-emerald-200/75"
              }`}
            >
              Domeniu: {productionScopeLabel("ORDER_SCOPE")} · Politica:{" "}
              {summary.policy.replace(/_/g, " ")}
            </p>
          </div>
        </div>
        {onOpenDetails ? (
          <button
            type="button"
            onClick={onOpenDetails}
            className="text-[10px] font-semibold text-blue-700 hover:text-blue-900 dark:text-blue-300 dark:hover:text-blue-200 shrink-0"
            data-testid="operator-production-release-details-toggle"
          >
            Detalii decizii
          </button>
        ) : null}
      </div>

      <p
        className={`text-[11px] leading-relaxed ${
          blocked
            ? "text-red-900/90 dark:text-red-100/85"
            : "text-emerald-900/90 dark:text-emerald-50/85"
        }`}
      >
        {blocked
          ? productionPolicyExplanation(summary.policy)
          : "Producția poate porni conform politicii curente. Readiness-ul operațional rămâne evaluat separat pe fiecare task."}
      </p>

      {blocked ? (
        <p
          className="text-[11px] text-amber-900 dark:text-amber-200/90"
          data-testid="operator-production-blocker-count"
        >
          {unresolved} decizie(i) de producție nerezolvată(e). Planul poate exista, dar pornirea
          task-urilor rămâne blocată.
        </p>
      ) : (
        <p className="text-[11px] text-emerald-800/80 dark:text-emerald-200/70">
          Nicio blocare de producție activă. Readiness-ul operațional rămâne evaluat separat pe
          fiecare task.
        </p>
      )}
    </section>
  );
}
