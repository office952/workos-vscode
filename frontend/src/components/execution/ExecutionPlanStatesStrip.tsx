/**
 * Display-only Execution Plan three-state strip.
 * Maps to existing preview / persisted draft / materialize (GO-gated) — no behavior change.
 */
import {
  EXECUTION_PLAN_DRAFT_STATE_LABEL,
  EXECUTION_PLAN_LABEL,
  EXECUTION_PLAN_OPERATIONAL_STATE_LABEL,
  EXECUTION_PLAN_PREVIEW_STATE_LABEL,
  EXECUTION_PLAN_STATES_HELP,
} from "@/features/product-system/productTemplateModulesVocabulary";

export type ExecutionPlanDisplayState = "preview" | "draft" | "operational";

const STATES: readonly {
  id: ExecutionPlanDisplayState;
  label: string;
}[] = [
  { id: "preview", label: EXECUTION_PLAN_PREVIEW_STATE_LABEL },
  { id: "draft", label: EXECUTION_PLAN_DRAFT_STATE_LABEL },
  { id: "operational", label: EXECUTION_PLAN_OPERATIONAL_STATE_LABEL },
] as const;

function resolveActiveState(args: {
  hasPreview: boolean;
  hasDraftPlan: boolean;
  hasOperationalTasks: boolean;
}): ExecutionPlanDisplayState {
  if (args.hasOperationalTasks) return "operational";
  if (args.hasDraftPlan) return "draft";
  return "preview";
}

export function ExecutionPlanStatesStrip({
  hasPreview = true,
  hasDraftPlan = false,
  hasOperationalTasks = false,
  operationalBlocked = true,
}: {
  hasPreview?: boolean;
  hasDraftPlan?: boolean;
  hasOperationalTasks?: boolean;
  /** When true, Operational Plan chip shows blocked (materialize GO). */
  operationalBlocked?: boolean;
}) {
  const active = resolveActiveState({ hasPreview, hasDraftPlan, hasOperationalTasks });

  return (
    <div
      className="rounded-lg border border-slate-700/50 bg-[#111827] px-3 py-2.5"
      data-testid="execution-plan-states-strip"
      data-active-state={active}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-[10px] font-bold uppercase tracking-wide text-slate-400">{EXECUTION_PLAN_LABEL}</p>
        <p className="text-[10px] text-slate-500">{EXECUTION_PLAN_STATES_HELP}</p>
      </div>
      <ol className="mt-2 flex flex-wrap items-center gap-1.5">
        {STATES.map((state, index) => {
          const isActive = state.id === active;
          const isOperationalBlocked = state.id === "operational" && operationalBlocked && !hasOperationalTasks;
          return (
            <li key={state.id} className="flex items-center gap-1.5">
              {index > 0 ? <span className="text-[10px] text-slate-600">→</span> : null}
              <span
                className={
                  isActive
                    ? "rounded border border-cyan-700/50 bg-cyan-950/40 px-2 py-0.5 text-[10px] font-bold text-cyan-200"
                    : isOperationalBlocked
                      ? "rounded border border-amber-800/40 bg-amber-950/20 px-2 py-0.5 text-[10px] font-semibold text-amber-200/80"
                      : "rounded border border-slate-700/50 bg-slate-900/40 px-2 py-0.5 text-[10px] font-semibold text-slate-400"
                }
                data-testid={`execution-plan-state-${state.id}`}
                data-active={isActive ? "true" : "false"}
                data-blocked={isOperationalBlocked ? "true" : "false"}
              >
                {state.label}
                {isOperationalBlocked ? " · blocked" : ""}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
