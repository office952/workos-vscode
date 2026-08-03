/**
 * Execution Result Workspace.
 * Orchestrates backend facts and explicit operator actions; it does not calculate cost.
 * Wave 1 / Step 9B: surfaces ExecutionPlan V2 draft readiness read-only before work panels.
 */
import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  executionApi,
  PlanGenerationError,
  RealityActionError,
  type AlertsResponse,
  type ExecutionPlanResponse,
  type ExecutionRealityResponse,
  type ObservabilityReport,
} from "@/api/execution";
import { ExecutionClosurePanel } from "@/components/execution/ExecutionClosurePanel";
import { ExecutionPlanV2TruthPanel } from "@/components/execution/ExecutionPlanV2TruthPanel";
import { allowExecutionSessionActions } from "@/components/execution/executionPlanV2Readiness";
import { PostJobTruthPanel } from "@/components/execution/PostJobTruthPanel";
import ExecutionFlowNextStep from "@/components/workos/ExecutionFlowNextStep";
import ExecutionFlowStrip from "@/components/workos/ExecutionFlowStrip";
import { useAuth } from "@/contexts/AuthContext";
import { useExecutionPlanV2Truth } from "@/hooks/useExecutionPlanV2Truth";
import { executionDetailNextStepHint } from "@/lib/executionFlowUi";
import { BlockersPanel } from "@/components/execution-result/BlockersPanel";
import { CostsCompletenessPanel } from "@/components/execution-result/CostsCompletenessPanel";
import { FinalResultPanel } from "@/components/execution-result/FinalResultPanel";
import { ExecutionResultHeader } from "@/components/execution-result/Header";
import { OperationalSummary } from "@/components/execution-result/OperationalSummary";
import { PlanActualPanel } from "@/components/execution-result/PlanActualPanel";
import { ResourceReadinessPanel } from "@/components/execution-result/ResourceReadinessPanel";
import { TechnicalDetails } from "@/components/execution-result/TechnicalDetails";
import { WorkPanel } from "@/components/execution-result/WorkPanel";
import { executionResultRole, isManagementRole } from "@/components/execution-result/executionResultWorkspace";

function errorMessage(error: unknown): string {
  if (error instanceof PlanGenerationError) {
    if (error.code === "snapshot_incomplete") return "Planul nu poate fi generat deoarece snapshot-ul comenzii este incomplet.";
    if (error.code === "plan_already_exists") return "Planul a fost deja generat. Datele au fost reîncărcate.";
    return "Planul nu a putut fi generat. Verifică detaliile tehnice sau contactează administratorul.";
  }
  if (error instanceof RealityActionError) return "Acțiunea nu a fost acceptată de execuție. Reîncarcă datele și verifică pregătirea taskului.";
  return error instanceof Error ? error.message : "A apărut o eroare necunoscută.";
}

export default function ExecutionDetail() {
  const { order_id } = useParams<{ order_id: string }>();
  const orderId = order_id ? Number.parseInt(order_id, 10) : Number.NaN;
  const validOrderId = Number.isInteger(orderId) && orderId > 0;
  const { user } = useAuth();
  const role = executionResultRole(user?.role);
  const [observability, setObservability] = useState<ObservabilityReport | null>(null);
  const [alerts, setAlerts] = useState<AlertsResponse | null>(null);
  const [plan, setPlan] = useState<ExecutionPlanResponse | null>(null);
  const [reality, setReality] = useState<ExecutionRealityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionTaskId, setActionTaskId] = useState<string | null>(null);
  const [generatingPlan, setGeneratingPlan] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [refreshedAt, setRefreshedAt] = useState<string | null>(null);

  const v2Truth = useExecutionPlanV2Truth(validOrderId ? orderId : null, validOrderId);
  const allowSessionActions = allowExecutionSessionActions(v2Truth.audit);

  const load = useCallback(async () => {
    if (!validOrderId) {
      setMessage("ID-ul comenzii este invalid.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      const [nextObservability, nextAlerts] = await Promise.all([
        executionApi.getObservability(orderId),
        executionApi.getAlerts(orderId),
      ]);
      setObservability(nextObservability);
      setAlerts(nextAlerts);
      if (nextObservability.has_plan) {
        const [nextPlan, nextReality] = await Promise.all([
          executionApi.getExecutionPlan(orderId),
          executionApi.getReality(orderId),
        ]);
        setPlan(nextPlan);
        setReality(nextReality);
      } else {
        setPlan(null);
        setReality(null);
      }
      setRefreshedAt(new Date().toLocaleTimeString("ro-RO"));
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setLoading(false);
    }
  }, [orderId, validOrderId]);

  useEffect(() => {
    void load();
  }, [load]);

  const generatePlan = async () => {
    if (!validOrderId || generatingPlan) return;
    setGeneratingPlan(true);
    setMessage(null);
    try {
      await executionApi.generatePlan(orderId);
      await load();
      await v2Truth.refresh();
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setGeneratingPlan(false);
    }
  };

  const capture = async (taskId: string, action: "start" | "complete") => {
    if (!validOrderId || !allowSessionActions) return;
    setActionTaskId(taskId);
    setMessage(null);
    try {
      if (action === "start") await executionApi.startTask(orderId, taskId, new Date().toISOString());
      else await executionApi.endTask(orderId, taskId, new Date().toISOString());
      await load();
    } catch (error) {
      setMessage(errorMessage(error));
    } finally {
      setActionTaskId(null);
    }
  };

  return (
    <div className="space-y-4">
      <ExecutionFlowStrip active="executie" orderExecutionPath={validOrderId ? `/execution/${orderId}` : null} />
      <ExecutionFlowNextStep hint={executionDetailNextStepHint(validOrderId ? orderId : null)} />
      <ExecutionResultHeader
        observability={observability}
        refreshedAt={refreshedAt}
        loading={loading}
        onRefresh={() => {
          void load();
          void v2Truth.refresh();
        }}
      />
      {message ? (
        <p role="alert" className="rounded-md border border-wo-danger/40 bg-wo-danger/10 px-3 py-2 text-[12px] text-wo-danger">
          {message}
        </p>
      ) : null}
      {loading && !observability ? (
        <p className="py-12 text-center text-[12px] text-wo-text-muted">Se încarcă rezultatul execuției…</p>
      ) : null}

      {validOrderId ? (
        <div data-testid="execution-plan-v2-truth-slot">
          {v2Truth.loading && !v2Truth.preview ? (
            <p className="rounded-md border border-wo-border-subtle bg-wo-surface px-3 py-2 text-[12px] text-wo-text-muted">
              Se încarcă planul de execuție (draft / audit)…
            </p>
          ) : null}
          {v2Truth.previewError && !v2Truth.preview ? (
            <div
              className="rounded-md border border-amber-800/50 bg-amber-950/20 px-3 py-2 text-[12px] text-amber-100"
              data-testid="execution-plan-v2-preview-error"
            >
              <p className="font-semibold">Previzualizare ExecutionPlan V2 indisponibilă</p>
              <p className="mt-1 text-[11px] text-amber-100/80">{v2Truth.previewError}</p>
            </div>
          ) : null}
          {v2Truth.preview ? (
            <ExecutionPlanV2TruthPanel
              preview={v2Truth.preview}
              audit={v2Truth.audit}
              auditError={v2Truth.auditError}
              loading={v2Truth.loading}
            />
          ) : null}
        </div>
      ) : null}

      {observability ? (
        <>
          <OperationalSummary observability={observability} />
          <BlockersPanel observability={observability} alerts={alerts} />
          {observability.has_plan ? <ResourceReadinessPanel orderId={orderId} /> : null}
          {!observability.has_plan ? (
            <section
              className="rounded-lg border border-wo-border-subtle bg-wo-surface p-4"
              data-testid="execution-primary-action"
            >
              <h2 className="text-sm font-semibold text-wo-text-primary">Următorul pas</h2>
              <p className="mt-1 text-[12px] text-wo-text-muted">
                Dacă comanda are Order Snapshot V2, folosește traseul V2 (previzualizare de mai sus). Generarea de mai jos
                este calea legacy și poate fi respinsă pentru comenzi V2.
              </p>
              <button
                type="button"
                data-testid="execution-plan-generate-action"
                onClick={() => void generatePlan()}
                disabled={generatingPlan}
                className="mt-3 rounded-md bg-blue-600 px-3 py-1.5 text-[12px] font-semibold text-white disabled:opacity-50"
              >
                {generatingPlan ? "Se generează planul…" : "Generează plan de execuție (legacy)"}
              </button>
            </section>
          ) : null}
          <WorkPanel
            plan={plan}
            reality={reality}
            busyTaskId={actionTaskId}
            allowSessionActions={allowSessionActions}
            onStart={(taskId) => void capture(taskId, "start")}
            onComplete={(taskId) => void capture(taskId, "complete")}
          />
          <PlanActualPanel observability={observability} />
          <CostsCompletenessPanel orderId={orderId} role={role} />
          <FinalResultPanel orderId={orderId} role={role} />
          <ExecutionClosurePanel orderId={orderId} onChanged={() => void load()} />
          {isManagementRole(role) ? <PostJobTruthPanel orderId={orderId} /> : null}
          <TechnicalDetails orderId={orderId} />
          <p className="text-[10px] italic text-wo-text-muted">
            Toate valorile sunt fapte backend. Interfața nu calculează și nu completează valori lipsă.
          </p>
        </>
      ) : null}
    </div>
  );
}
