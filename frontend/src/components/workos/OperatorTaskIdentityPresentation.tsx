import type { OperatorTaskTruthTask } from "@/api/operatorTaskTruth";
import {
  componentLabelFromBackend,
  componentRoleBadgeLabel,
  diagnosticTaskKey,
  firstReadinessMessage,
  identitySourceLabel,
  isLegacyTaskIdentity,
  isPartialLogoIdentity,
  taskPrimaryLabel,
  taskTruthReadinessFromRuntime,
  type TaskTruthReadiness,
} from "@/lib/operatorTaskPresentation";

export type OperatorTaskIdentityPresentationProps = {
  truth?: OperatorTaskTruthTask | null;
  /** Used only when truth is absent — never for component role inference. */
  fallbackOperationName?: string | null;
  fallbackTaskId?: string | null;
  readiness?: TaskTruthReadiness | null;
  showDiagnostics?: boolean;
  compact?: boolean;
  testId?: string;
};

function RoleBadge({ label, tone }: { label: string; tone: "role" | "legacy" | "partial" }) {
  const cls =
    tone === "legacy"
      ? "bg-slate-800/80 text-slate-300 border-slate-600"
      : tone === "partial"
        ? "bg-violet-900/30 text-violet-200 border-violet-700/60"
        : "bg-blue-900/30 text-blue-200 border-blue-700/60";
  return (
    <span
      className={`inline-flex px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide rounded border ${cls}`}
    >
      {label}
    </span>
  );
}

export function OperatorTaskIdentityPresentation({
  truth,
  fallbackOperationName,
  fallbackTaskId,
  readiness: readinessOverride,
  showDiagnostics = false,
  compact = false,
  testId,
}: OperatorTaskIdentityPresentationProps) {
  if (!truth) {
    return (
      <div data-testid={testId} className="space-y-0.5">
        <p className="text-[13px] font-medium text-slate-100">
          {fallbackOperationName || fallbackTaskId || "Task necunoscut"}
        </p>
        {fallbackTaskId ? (
          <p className="text-[10px] text-slate-500 font-mono" data-testid="operator-task-diagnostic-key">
            {fallbackTaskId}
          </p>
        ) : null}
      </div>
    );
  }

  const { identity, runtime } = truth;
  const readiness = readinessOverride ?? taskTruthReadinessFromRuntime(runtime);
  const primary = taskPrimaryLabel(identity);
  const componentLabel = componentLabelFromBackend(identity);
  const roleBadge = componentRoleBadgeLabel(identity);
  const legacy = isLegacyTaskIdentity(identity);
  const partialLogo = isPartialLogoIdentity(identity);
  const readinessMessage = firstReadinessMessage(readiness);
  const productionBlocked = runtime.production_release_blocked === true;
  const operationalNotReady =
    !productionBlocked && (readiness.is_blocked || readiness.is_startable === false);

  return (
    <div data-testid={testId} className="space-y-1 min-w-0">
      <div className="flex flex-wrap items-center gap-1.5">
        <p
          className={`font-medium text-slate-100 truncate ${compact ? "text-[12px]" : "text-[13px]"}`}
          data-testid="operator-task-primary-label"
        >
          {primary}
        </p>
        {legacy ? <RoleBadge label="Legacy" tone="legacy" /> : null}
        {partialLogo && !legacy ? <RoleBadge label="Logo parțial" tone="partial" /> : null}
        {productionBlocked ? (
          <span
            className="inline-flex px-1.5 py-0.5 text-[9px] font-semibold rounded border bg-red-900/35 text-red-200 border-red-700/60"
            data-testid="operator-task-production-blocked-badge"
          >
            Blocat pentru productie
          </span>
        ) : null}
        {operationalNotReady ? (
          <span className="inline-flex px-1.5 py-0.5 text-[9px] font-semibold rounded border bg-amber-900/30 text-amber-200 border-amber-700/60">
            {readiness.is_blocked ? "Blocat operational" : "Nepregatit"}
          </span>
        ) : !productionBlocked && readiness.is_startable ? (
          <span className="inline-flex px-1.5 py-0.5 text-[9px] font-semibold rounded border bg-emerald-900/30 text-emerald-200 border-emerald-700/60">
            Pornibil
          </span>
        ) : null}
      </div>

      {(componentLabel || roleBadge) && (
        <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-slate-400">
          {componentLabel ? (
            <span data-testid="operator-task-component-label" className="text-slate-300">
              {componentLabel}
            </span>
          ) : null}
          {roleBadge && !legacy ? <RoleBadge label={roleBadge} tone="role" /> : null}
        </div>
      )}

      {!compact && (
        <div className="text-[10px] text-slate-500 space-y-0.5">
          {identity.source_operation_code ? (
            <p>
              Operație:{" "}
              <span className="text-slate-400">{identity.source_operation_code}</span>
            </p>
          ) : null}
          {identity.component_template_code ? (
            <p>
              Șablon:{" "}
              <span className="text-slate-400">{identity.component_template_code}</span>
            </p>
          ) : null}
          {identity.parent_graph_node_id ? (
            <p>
              Părinte:{" "}
              <span className="text-slate-400 font-mono">{identity.parent_graph_node_id}</span>
            </p>
          ) : null}
          {identity.logo_segment_key ? (
            <p data-testid="operator-task-logo-segment">
              Segment logo:{" "}
              <span className="text-slate-400">{identity.logo_segment_key}</span>
            </p>
          ) : null}
          {productionBlocked && (runtime.blocking_owner_decision_codes?.length ?? 0) > 0 ? (
            <p className="text-red-300/90" data-testid="operator-task-production-blocker-summary">
              {runtime.blocking_owner_decision_codes.length} decizie(i) owner nerezolvata(e) la nivel
              de comanda
            </p>
          ) : null}
          {readinessMessage && !productionBlocked ? (
            <p className="text-amber-300/90" data-testid="operator-task-readiness-reason">
              {readinessMessage}
            </p>
          ) : null}
        </div>
      )}

      {showDiagnostics ? (
        <details className="text-[10px] text-slate-500">
          <summary className="cursor-pointer select-none">Diagnostic</summary>
          <div className="mt-1 space-y-0.5 font-mono">
            <p data-testid="operator-task-diagnostic-key">Key: {diagnosticTaskKey(identity)}</p>
            {identity.source_graph_node_id ? <p>Node: {identity.source_graph_node_id}</p> : null}
            {identity.source_task_rule_code ? <p>Rule: {identity.source_task_rule_code}</p> : null}
            <p>Source: {identitySourceLabel(identity)}</p>
            <p>Task ID: {identity.task_id}</p>
          </div>
        </details>
      ) : null}
    </div>
  );
}
