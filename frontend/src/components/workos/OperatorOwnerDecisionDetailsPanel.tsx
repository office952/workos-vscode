import { useState } from "react";
import type { OperatorTaskTruthResponse, OwnerDecisionSummaryItem } from "@/api/operatorTaskTruth";
import {
  decisionDisplayLabel,
  decisionRequiredAction,
  frozenStatusLabel,
  operationalStatusLabel,
  splitOwnerDecisions,
} from "@/lib/operatorProductionBlockerPresentation";
import { ChevronDown, ChevronRight } from "lucide-react";

type Props = {
  truth: OperatorTaskTruthResponse | null;
  defaultOpen?: boolean;
  testId?: string;
};

function DecisionRow({
  item,
  showResolverMeta,
}: {
  item: OwnerDecisionSummaryItem;
  showResolverMeta: boolean;
}) {
  return (
    <li
      className="rounded-md border border-[#243044] bg-[#0A1020]/50 px-3 py-2 space-y-1"
      data-testid={`owner-decision-row-${item.code}`}
    >
      <div className="flex flex-wrap items-center gap-1.5">
        <p className="text-[12px] font-medium text-slate-100">{decisionDisplayLabel(item)}</p>
        {item.blocking ? (
          <span className="text-[9px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded border bg-red-900/30 text-red-200 border-red-700/60">
            Blocheaza productia
          </span>
        ) : (
          <span className="text-[9px] font-semibold uppercase tracking-wide px-1.5 py-0.5 rounded border bg-slate-800/80 text-slate-300 border-slate-600">
            Informativ intern
          </span>
        )}
      </div>
      <p className="text-[10px] text-slate-400">{frozenStatusLabel(item.frozen_status)}</p>
      <p className="text-[10px] text-slate-300">{operationalStatusLabel(item.operational_status)}</p>
      {decisionRequiredAction(item) ? (
        <p className="text-[10px] text-amber-200/90">{decisionRequiredAction(item)}</p>
      ) : null}
      {item.requires_resolution ? (
        <p className="text-[10px] text-slate-400">Necesita rezolvare operationala</p>
      ) : null}
      {item.acknowledgement_sufficient ? (
        <p className="text-[10px] text-slate-500">Confirmarea poate fi suficienta (conform backend)</p>
      ) : null}
      {showResolverMeta ? (
        <div className="text-[10px] text-slate-400 space-y-0.5 pt-1 border-t border-[#243044]">
          <p>Poate rezolva: {item.can_resolve ? "da" : "nu"}</p>
          {item.resolved_at ? <p>Rezolvat la: {item.resolved_at}</p> : null}
          {item.resolved_by_user_name ? <p>Rezolvat de: {item.resolved_by_user_name}</p> : null}
          {item.has_resolution_note ? <p>Nota rezolvare: prezenta</p> : null}
        </div>
      ) : (
        <p className="text-[10px] text-slate-500">
          Rezolvare: {item.can_resolve ? "manager/admin" : "nu este disponibila pentru rolul curent"}
        </p>
      )}
      <p className="text-[9px] text-slate-600 font-mono" data-testid={`owner-decision-code-${item.code}`}>
        {item.code}
      </p>
    </li>
  );
}

export function OperatorOwnerDecisionDetailsPanel({
  truth,
  defaultOpen = false,
  testId,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);
  if (!truth || truth.owner_decisions_summary.length === 0) return null;

  const { blocking, nonblocking } = splitOwnerDecisions(truth.owner_decisions_summary);
  const showResolverMeta = truth.role_capabilities.can_resolve_owner_decisions;

  return (
    <section
      className="rounded-lg border border-[#243044] bg-[#0D1321]"
      data-testid={testId || "operator-owner-decision-details"}
    >
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 text-left"
      >
        <span className="text-[12px] font-semibold text-slate-200">
          Decizii owner — productie ({blocking.length} blocante, {nonblocking.length} informative)
        </span>
        {open ? (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronRight className="w-4 h-4 text-slate-400" />
        )}
      </button>

      {open ? (
        <div className="px-3 pb-3 space-y-3">
          {blocking.length > 0 ? (
            <div data-testid="owner-decisions-blocking-section">
              <h4 className="text-[11px] font-semibold text-red-300 mb-1.5">Blocante productie</h4>
              <ul className="space-y-2">
                {blocking.map((item) => (
                  <DecisionRow key={item.code} item={item} showResolverMeta={showResolverMeta} />
                ))}
              </ul>
            </div>
          ) : null}

          {nonblocking.length > 0 ? (
            <div data-testid="owner-decisions-nonblocking-section">
              <h4 className="text-[11px] font-semibold text-slate-400 mb-1.5">
                Analiza interna (nu blocheaza productia)
              </h4>
              <ul className="space-y-2">
                {nonblocking.map((item) => (
                  <DecisionRow key={item.code} item={item} showResolverMeta={showResolverMeta} />
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
