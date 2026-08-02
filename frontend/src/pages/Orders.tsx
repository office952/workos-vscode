import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { orderDetailPath } from "@/lib/commercialSpineNavigation";
import { type Order, type OrderStatus, executionJobs } from "@/lib/mockData";
import { useBackendData } from "@/hooks/useBackendData";
import { executionApi, PlanGenerationError } from "@/api/execution";
import { SectionHeader, JobStatusBadge, ProgressBar } from "@/components/workos/SharedComponents";
import { SourceBadge, StatusBadge } from "@/components/workos/design-system";
import FlowBreadcrumb, { ordersBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import CommercialFlowStrip from "@/components/workos/CommercialFlowStrip";
import ExecutionFlowStrip from "@/components/workos/ExecutionFlowStrip";
import NextStepPanel from "@/components/workos/NextStepPanel";
import TechnicalDetailsDisclosure from "@/components/workos/TechnicalDetailsDisclosure";
import { chromeBanner } from "@/components/workos/design-system/chromeRecipes";
import OrderDocumentGovernancePanel from "@/components/workos/OrderDocumentGovernancePanel";
import FieldInstallationTeamPanel from "@/components/workos/FieldInstallationTeamPanel";
import {
  ClipboardList,
  Lock,
  CheckCircle2,
  XCircle,
  Clock,
  ArrowRight,
  Package,
  Activity,
  RefreshCw,
  AlertTriangle,
  Inbox,
} from "lucide-react";

import {
  formatOrderMoney,
  formatExchangeRate,
} from "@/lib/orderCurrency";

const statusConfig: Record<OrderStatus, { label: string; icon: React.ReactNode }> = {
  created: { label: "Creat", icon: <ClipboardList className="w-3 h-3" /> },
  confirmed: { label: "Confirmat", icon: <CheckCircle2 className="w-3 h-3" /> },
  locked: { label: "Înghețat", icon: <Lock className="w-3 h-3" /> },
  in_execution: { label: "În Execuție", icon: <Activity className="w-3 h-3" /> },
  completed: { label: "Finalizat", icon: <CheckCircle2 className="w-3 h-3" /> },
  cancelled: { label: "Anulat", icon: <XCircle className="w-3 h-3" /> },
};

const paymentConfig: Record<string, { label: string; cls: string }> = {
  pending: { label: "Neplătit", cls: "text-red-400 bg-red-900/20 border-red-800/30" },
  partial: { label: "Avans", cls: "text-amber-400 bg-amber-900/20 border-amber-800/30" },
  paid: { label: "Plătit", cls: "text-emerald-400 bg-emerald-900/20 border-emerald-800/30" },
};

function resolvePaymentConfig(status: string) {
  return paymentConfig[status] ?? paymentConfig.pending;
}

function resolveReadinessSnapshotView(snapshot: NonNullable<Order["readinessSnapshot"]>) {
  const readinessResult = snapshot.readiness_result ?? null;
  return {
    statusLabel: readinessResult?.overall_status ?? snapshot.quote_status ?? "captured",
    readyForQuote: readinessResult?.ready_for_quote ?? null,
    contractVersion: readinessResult?.contract_version ?? null,
    quoteStatus: snapshot.quote_status ?? null,
    requiresProductionHandoffBuild: snapshot.requires_production_handoff_build ?? null,
    executionPlanCreated: snapshot.execution_plan_created ?? null,
    inventoryMutated: snapshot.inventory_mutated ?? null,
    warningsAcknowledged: snapshot.warnings_acknowledged ?? false,
    warningsAcknowledgedAt: snapshot.warnings_acknowledged_at ?? null,
  };
}

function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const cfg = statusConfig[status] ?? {
    label: status,
    icon: <ClipboardList className="w-3 h-3" />,
  };
  return (
    <StatusBadge
      domain="order"
      status={status}
      label={cfg.label}
      icon={cfg.icon}
      className="text-[11px]"
    />
  );
}

function formatCurrency(val: number) {
  return val.toLocaleString("ro-RO", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function OrderValueDisplay({ order }: { order: Order }) {
  const handoff = order.commercialCurrencyHandoff;
  const baseCurrency = order.baseCurrency ?? handoff?.base_currency ?? "RON";
  if (handoff?.commercial_total_eur != null && handoff.exchange_rate_eur_ron != null) {
    return (
      <div data-testid="order-value-display">
        <p className="text-[14px] font-bold text-wo-text-primary">
          {formatOrderMoney(order.totalAmount, baseCurrency)}
        </p>
        <p className="text-[10px] text-slate-500 mt-0.5">
          Ofertă: {formatOrderMoney(handoff.commercial_total_eur, "EUR")} · Curs:{" "}
          {formatExchangeRate(handoff.exchange_rate_eur_ron)} RON/EUR
        </p>
      </div>
    );
  }
  return (
    <p className="text-[14px] font-bold text-wo-text-primary">
      {formatOrderMoney(order.totalAmount, baseCurrency)}
    </p>
  );
}

export default function Orders() {
  const navigate = useNavigate();
  const { orderId: orderIdParam } = useParams<{ orderId?: string }>();
  const { orders, loading, refresh, source, sourcesDetail, error } = useBackendData();
  const ordersSource = sourcesDetail?.orders ?? source;
  const canUseLiveOrders = ordersSource === "db";
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [orderNotFound, setOrderNotFound] = useState(false);
  const [filterStatus, setFilterStatus] = useState<OrderStatus | "all">("all");
  const [refreshing, setRefreshing] = useState(false);
  const [executionHasPlan, setExecutionHasPlan] = useState<boolean | null>(null);
  const [planGenerating, setPlanGenerating] = useState(false);
  const [planError, setPlanError] = useState<string | null>(null);
  const [generatedPlanTaskCount, setGeneratedPlanTaskCount] = useState<number | null>(null);
  const useMockExecution = ordersSource === "mock";
  const orderDbId = selectedOrder?.dbId;
  const readinessSnapshot = selectedOrder?.readinessSnapshot ?? null;
  const readinessSnapshotView = readinessSnapshot ? resolveReadinessSnapshotView(readinessSnapshot) : null;

  const handleRefresh = async () => {
    setRefreshing(true);
    await refresh();
    setRefreshing(false);
  };

  useEffect(() => {
    setPlanError(null);
    setGeneratedPlanTaskCount(null);
    if (!orderDbId || !canUseLiveOrders) {
      setExecutionHasPlan(null);
      return;
    }
    let cancelled = false;
    executionApi
      .getObservability(orderDbId)
      .then((obs) => {
        if (!cancelled) setExecutionHasPlan(obs.has_plan);
      })
      .catch(() => {
        if (!cancelled) setExecutionHasPlan(null);
      });
    return () => {
      cancelled = true;
    };
  }, [orderDbId, canUseLiveOrders, selectedOrder?.id]);

  const handleGenerateExecutionPlan = async () => {
    if (!orderDbId) return;
    setPlanGenerating(true);
    setPlanError(null);
    try {
      const plan = await executionApi.generatePlan(orderDbId);
      setExecutionHasPlan(true);
      setGeneratedPlanTaskCount(plan.tasks.length);
    } catch (err) {
      if (err instanceof PlanGenerationError) {
        if (err.code === "plan_already_exists") {
          setExecutionHasPlan(true);
          setPlanError("Există deja un plan execuție pentru această comandă.");
        } else {
          setPlanError(err.message);
        }
      } else {
        setPlanError(err instanceof Error ? err.message : "Generarea planului a eșuat.");
      }
    } finally {
      setPlanGenerating(false);
    }
  };

  const executionDetailPath =
    orderDbId && Number.isInteger(orderDbId) ? `/execution/${orderDbId}` : null;

  const selectOrder = useCallback(
    (order: Order | null) => {
      setSelectedOrder(order);
      setOrderNotFound(false);
      if (order) {
        navigate(orderDetailPath(order.id), { replace: true });
      } else if (orderIdParam) {
        navigate("/orders", { replace: true });
      }
    },
    [navigate, orderIdParam]
  );

  useEffect(() => {
    if (!orderIdParam || loading) return;
    const match = orders.find(
      (o) => o.id.toLowerCase() === orderIdParam.toLowerCase()
    );
    if (match) {
      setOrderNotFound(false);
      setSelectedOrder((prev) => (prev?.id === match.id ? prev : match));
      return;
    }
    if (orders.length > 0) {
      setOrderNotFound(true);
      setSelectedOrder(null);
    }
  }, [orderIdParam, orders, loading]);

  if (loading && orders.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p className="text-[12px] text-slate-500">Încărcare comenzi...</p>
        </div>
      </div>
    );
  }

  const filtered = filterStatus === "all" ? orders : orders.filter((o) => o.status === filterStatus);

  const totalRevenue = orders.reduce((sum, o) => sum + o.totalAmount, 0);
  const inExecCount = orders.filter((o) => o.status === "in_execution").length;
  const completedCount = orders.filter((o) => o.status === "completed").length;

  const linkedJob = selectedOrder?.jobId
    ? (useMockExecution ? executionJobs.find((j) => j.id === selectedOrder.jobId) : null)
    : null;

  const isOrdersEmpty = orders.length === 0;

  return (
    <div className="space-y-4" data-testid="orders-page">
      <FlowBreadcrumb items={ordersBreadcrumb()} />
      <CommercialFlowStrip active="comenzi" />
      <ExecutionFlowStrip
        active="comenzi"
        orderExecutionPath={executionDetailPath}
      />

      {/* Header */}
      <div className="flex flex-wrap items-center gap-2">
        <ClipboardList className="w-5 h-5 text-blue-500" />
        <div className="min-w-0">
          <h1 className="text-[18px] font-bold text-wo-text-primary">Comenzi</h1>
          <p className="text-[12px] text-wo-text-muted">
            Snapshot acceptat și stare execuție — fără re-pricing din acest ecran.
          </p>
        </div>
        <span className="text-[10px] text-wo-text-muted bg-wo-surface-raised border border-wo-border-strong px-2 py-0.5 rounded-full">
          {orders.length} comenzi
        </span>
        <SourceBadge source={ordersSource} />
        <div className="ml-auto">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-medium rounded border border-wo-border-strong bg-wo-surface-raised text-wo-text-primary hover:bg-wo-hover disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-3 h-3 ${refreshing ? "animate-spin" : ""}`} />
            Actualizează
          </button>
        </div>
      </div>

      {error && source !== "mock" && (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] ${chromeBanner.error}`}>
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <p>Datele comenzilor nu au putut fi încărcate din backend: {error}</p>
        </div>
      )}

      {orderIdParam && orderNotFound && !loading && (
        <div
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] ${chromeBanner.warning}`}
          data-testid="order-not-found"
        >
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <p>
            Comanda <span className="font-mono">{orderIdParam}</span> nu a fost
            găsită.{" "}
            <button
              type="button"
              onClick={() => navigate("/orders", { replace: true })}
              className="underline font-medium"
            >
              Înapoi la listă
            </button>
          </p>
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-blue-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-wo-text-muted uppercase tracking-wide">Total Comenzi</p>
          <p className="text-[20px] font-bold text-wo-text-primary mt-1">{orders.length}</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-emerald-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-wo-text-muted uppercase tracking-wide">În Execuție</p>
          <p className="text-[20px] font-bold text-emerald-600 dark:text-emerald-400 mt-1">{inExecCount}</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-purple-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-wo-text-muted uppercase tracking-wide">Finalizate</p>
          <p className="text-[20px] font-bold text-purple-600 dark:text-purple-400 mt-1">{completedCount}</p>
        </div>
        <div className="bg-wo-surface-raised border border-wo-border-strong border-t-2 border-t-amber-500 rounded-lg px-4 py-3">
          <p className="text-[11px] text-wo-text-muted uppercase tracking-wide">Valoare Totală</p>
          <p className="text-[16px] font-bold text-amber-700 dark:text-amber-400 mt-1">{formatCurrency(totalRevenue)}</p>
          <p className="text-[10px] text-wo-text-muted">RON</p>
        </div>
      </div>

      {/* Filter */}
      <div className="flex items-center gap-1.5 flex-wrap">
        {(["all", "created", "confirmed", "locked", "in_execution", "completed", "cancelled"] as const).map((s) => {
          const count = s === "all" ? orders.length : orders.filter((o) => o.status === s).length;
          if (s !== "all" && count === 0) return null;
          const label = s === "all" ? "Toate" : statusConfig[s as OrderStatus].label;
          return (
            <button
              key={s}
              onClick={() => setFilterStatus(s === "all" ? "all" : s as OrderStatus)}
              className={`px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all ${
                filterStatus === s
                  ? "bg-blue-50 text-blue-700 border-blue-300 dark:bg-blue-600/20 dark:text-blue-400 dark:border-blue-600/50"
                  : "bg-transparent text-wo-text-muted border-wo-border-strong hover:border-wo-border-strong hover:text-wo-text-primary"
              }`}
            >
              {label} ({count})
            </button>
          );
        })}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Order List */}
        <div className="lg:col-span-2 space-y-2">
          {isOrdersEmpty ? (
            <div
              className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-8 text-center"
              data-testid="orders-empty-state"
            >
              <ClipboardList className="w-10 h-10 text-wo-text-dim mx-auto mb-3" />
              <h2 className="text-[15px] font-semibold text-wo-text-primary">Nu există comenzi încă</h2>
              <p className="text-[12px] text-wo-text-muted mt-2 max-w-md mx-auto leading-relaxed">
                Comenzile apar aici după acceptarea sau conversia unei oferte.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-2 mt-5">
                <button
                  type="button"
                  onClick={() => navigate("/quotes")}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-[12px] font-semibold rounded-lg bg-blue-600 hover:bg-blue-500 text-white transition-colors"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                  Mergi la Oferte
                </button>
                <button
                  type="button"
                  onClick={() => navigate("/intake")}
                  className="inline-flex items-center gap-1.5 px-4 py-2 text-[12px] font-medium rounded-lg border border-wo-border-strong bg-wo-surface-raised text-wo-text-primary hover:bg-wo-hover transition-colors"
                >
                  <Inbox className="w-3.5 h-3.5" />
                  Deschide Cereri
                </button>
              </div>
            </div>
          ) : null}
          {filtered.map((order) => {
            const job = order.jobId && useMockExecution ? executionJobs.find((j) => j.id === order.jobId) : null;
            const payCfg = resolvePaymentConfig(order.paymentStatus);
            return (
              <div
                key={order.id}
                onClick={() => selectOrder(order)}
                className={`bg-wo-surface-raised border rounded-lg p-4 cursor-pointer transition-all ${
                  selectedOrder?.id === order.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-wo-border-subtle hover:border-slate-500"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[12px] font-mono text-blue-400">{order.id}</span>
                    <OrderStatusBadge status={order.status} />
                    <span className={`px-1.5 py-0.5 text-[10px] font-semibold rounded border ${payCfg.cls}`}>
                      {payCfg.label}
                    </span>
                  </div>
                  <span className="text-[14px] font-bold text-wo-text-primary">
                    {formatOrderMoney(order.totalAmount, order.baseCurrency ?? "RON")}
                  </span>
                </div>
                <p className="text-[13px] font-semibold text-wo-text-primary">{order.client}</p>
                <p className="text-[11px] text-slate-400 mt-0.5">{order.productSummary}</p>
                <div className="flex items-center gap-4 mt-2 text-[10px] text-slate-500">
                  <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> Termen: {order.promisedDelivery}</span>
                  {order.jobId && <span className="flex items-center gap-1"><Package className="w-3 h-3" /> {order.jobId}</span>}
                  {job && (
                    <span className="flex items-center gap-1 ml-auto">
                      <Activity className="w-3 h-3" /> {job.progress}%
                    </span>
                  )}
                </div>
                {job && (
                  <div className="mt-2">
                    <ProgressBar value={job.progress} />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Detail Panel */}
        <div className="space-y-4">
          {selectedOrder ? (
            <>
              <div
                className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4"
                data-testid="order-detail-selected"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[12px] font-mono text-blue-400">{selectedOrder.id}</span>
                  <OrderStatusBadge status={selectedOrder.status} />
                </div>
                <h3 className="text-[16px] font-bold text-wo-text-primary">{selectedOrder.client}</h3>
                <p className="text-[12px] text-slate-400 mt-0.5">{selectedOrder.contactPerson}</p>

                <div className="mt-4 space-y-3">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Produs</p>
                    <p className="text-[12px] text-slate-300">{selectedOrder.productSummary}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Valoare</p>
                      <OrderValueDisplay order={selectedOrder} />
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Plată</p>
                      <span className={`px-2 py-0.5 text-[11px] font-semibold rounded border ${resolvePaymentConfig(selectedOrder.paymentStatus).cls}`}>
                        {resolvePaymentConfig(selectedOrder.paymentStatus).label}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Termen Livrare</p>
                      <p className="text-[12px] text-slate-300">{selectedOrder.promisedDelivery}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Snapshot</p>
                      <p className="text-[12px] text-slate-300 flex items-center gap-1">
                        <Lock className="w-3 h-3 text-purple-400" /> v{selectedOrder.snapshotVersion}
                        {selectedOrder.lockedAt && (
                          <span className="text-[10px] text-slate-500 ml-1">
                            {new Date(selectedOrder.lockedAt).toLocaleDateString("ro-RO")}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Ofertă Sursă</p>
                    <p className="text-[12px] text-blue-400 font-mono">{selectedOrder.quoteId}</p>
                  </div>
                </div>

                {selectedOrder.notes && (
                  <div className="mt-3 bg-wo-surface-raised rounded-lg p-3">
                    <p className="text-[12px] text-slate-300">{selectedOrder.notes}</p>
                  </div>
                )}
              </div>

              {/* Execution plan dispatch */}
              {(selectedOrder.status === "locked" || selectedOrder.status === "in_execution") &&
                canUseLiveOrders &&
                orderDbId && (
                  <div
                    className="bg-wo-surface-raised border border-emerald-900/40 rounded-lg p-4 space-y-3"
                    data-testid="order-execution-dispatch-panel"
                  >
                    <SectionHeader title="Taskuri producție" icon={<Activity className="w-4 h-4" />} />
                    {executionHasPlan ? (
                      <p className="text-[11px] text-slate-400">
                        Planul de execuție a fost generat din snapshot-ul înghețat. Monitorizați progresul
                        în Operator, Shop Floor și Tablet.
                      </p>
                    ) : (
                      <>
                        <p className="text-[11px] text-slate-400">
                          Planul se generează o singură dată pe baza comenzii înghețate. Taskurile apar apoi
                          în Operator, Shop Floor și Tablet.
                        </p>
                      </>
                    )}
                    {executionHasPlan ? (
                      <p className="text-[11px] text-emerald-300" data-testid="order-execution-plan-exists">
                        Plan execuție existent
                        {generatedPlanTaskCount != null ? ` · ${generatedPlanTaskCount} taskuri` : ""}
                      </p>
                    ) : executionHasPlan === false ? (
                      <p className="text-[11px] text-amber-300" data-testid="order-execution-plan-missing">
                        Planul de execuție nu a fost generat
                      </p>
                    ) : null}
                    {!executionHasPlan && (
                      <button
                        type="button"
                        data-testid="order-generate-execution-plan-action"
                        onClick={() => void handleGenerateExecutionPlan()}
                        disabled={planGenerating}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white rounded-lg text-[12px] font-semibold transition-colors"
                      >
                        <Package className="w-3.5 h-3.5" />
                        {planGenerating ? "Se generează..." : "Generează taskuri producție"}
                      </button>
                    )}
                    {executionHasPlan && executionDetailPath && (
                      <button
                        type="button"
                        data-testid="order-view-execution-cta"
                        onClick={() => navigate(executionDetailPath)}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded-lg text-[12px] font-semibold transition-colors"
                      >
                        <ArrowRight className="w-3.5 h-3.5" /> Vezi execuția
                      </button>
                    )}
                    {planError ? (
                      <p className="text-[11px] text-red-300" data-testid="order-execution-plan-error">
                        {planError}
                      </p>
                    ) : null}
                  </div>
                )}

              {!canUseLiveOrders && (selectedOrder.status === "in_execution" || selectedOrder.status === "locked") && (
                <p className="text-[10px] text-amber-400 px-1" data-testid="order-execution-live-source-warning">
                  Navigarea către Execuție este disponibilă doar pe sursă backend live.
                </p>
              )}

              {/* Linked Job */}
              {linkedJob && (
                <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4">
                  <SectionHeader title="Job Execuție" icon={<Package className="w-4 h-4" />} />
                  <div className="bg-wo-surface-raised border border-wo-border-strong rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[12px] font-mono text-blue-400">{linkedJob.id}</span>
                      <JobStatusBadge status={linkedJob.status} />
                    </div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[11px] text-slate-400">
                        Op: {linkedJob.currentOperation} · WC: {linkedJob.currentWorkcenter}
                      </span>
                      <span className="text-[14px] font-bold text-wo-text-primary">{linkedJob.progress}%</span>
                    </div>
                    <ProgressBar value={linkedJob.progress} size="md" />
                    <div className="flex items-center gap-3 mt-2 text-[10px] text-slate-500">
                      <span>{linkedJob.operationsCompleted}/{linkedJob.operationsTotal} operații</span>
                      {linkedJob.riskReason && (
                        <span className="text-red-400">⚠ {linkedJob.riskReason}</span>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Readiness Snapshot at Acceptance — secondary diagnostic */}
              <TechnicalDetailsDisclosure
                title="Detalii tehnice — readiness la acceptare"
                testId="order-readiness-snapshot-details"
              >
                {readinessSnapshot && readinessSnapshotView ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 mb-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                      <p className="text-[12px] font-semibold text-wo-text-primary">
                        Snapshot readiness (acceptare)
                      </p>
                    </div>
                    <div className="flex items-center justify-between rounded bg-wo-surface-raised px-2 py-1.5">
                      <span>Status</span>
                      <span className="font-semibold text-emerald-700 dark:text-emerald-300">
                        {readinessSnapshotView.statusLabel}
                      </span>
                    </div>
                    {readinessSnapshotView.readyForQuote !== null && (
                      <div className="flex items-center justify-between rounded bg-wo-surface-raised px-2 py-1.5">
                        <span>Gata pentru ofertă</span>
                        <span
                          className={
                            readinessSnapshotView.readyForQuote
                              ? "font-semibold text-emerald-700 dark:text-emerald-300"
                              : "font-semibold text-red-700 dark:text-red-300"
                          }
                        >
                          {readinessSnapshotView.readyForQuote ? "Da" : "Nu"}
                        </span>
                      </div>
                    )}
                    {readinessSnapshotView.quoteStatus && (
                      <div className="flex items-center justify-between rounded bg-wo-surface-raised px-2 py-1.5">
                        <span>Status ofertă</span>
                        <span className="font-mono">{readinessSnapshotView.quoteStatus}</span>
                      </div>
                    )}
                    <div className="flex items-center justify-between rounded bg-wo-surface-raised px-2 py-1.5">
                      <span>Capturat</span>
                      <span>{new Date(readinessSnapshot.snapshot_at).toLocaleString("ro-RO")}</span>
                    </div>
                    {readinessSnapshotView.contractVersion && (
                      <div className="flex items-center justify-between rounded bg-wo-surface-raised px-2 py-1.5">
                        <span>Contract</span>
                        <span className="font-mono">v{readinessSnapshotView.contractVersion}</span>
                      </div>
                    )}
                    {readinessSnapshotView.warningsAcknowledged && (
                      <p className={`rounded px-2 py-1.5 text-[10px] ${chromeBanner.warning}`}>
                        Avertismente acknowledge:{" "}
                        {readinessSnapshotView.warningsAcknowledgedAt
                          ? new Date(readinessSnapshotView.warningsAcknowledgedAt).toLocaleString("ro-RO")
                          : "da"}
                      </p>
                    )}
                  </div>
                ) : (
                  <p>Niciun snapshot de pregătire capturat pentru această comandă.</p>
                )}
              </TechnicalDetailsDisclosure>

              {/* Field installation team allocation (montaj teren) */}
              {selectedOrder.dbId && canUseLiveOrders && (
                <FieldInstallationTeamPanel
                  orderId={selectedOrder.dbId}
                  orderCode={selectedOrder.id}
                  defaultSiteAddress={selectedOrder.notes || ""}
                  visible
                />
              )}

              {/* Document Governance Surface (BUILD 26.40) */}
              <OrderDocumentGovernancePanel
                orderId={selectedOrder.dbId ?? null}
                orderCode={selectedOrder.id}
                visible={!!selectedOrder.dbId}
              />

              {/* Snapshot Law */}
              <div className="rounded-lg border border-violet-200 bg-violet-50 p-3 dark:border-purple-800/40 dark:bg-purple-950/20">
                <div className="flex items-center gap-2 mb-1.5">
                  <Lock className="w-4 h-4 text-violet-700 dark:text-purple-300" />
                  <p className="text-[12px] text-violet-800 dark:text-purple-300 font-semibold">
                    Snapshot acceptat
                  </p>
                </div>
                <p className="text-[11px] text-violet-900/80 dark:text-slate-300 leading-relaxed">
                  Configurația, prețul și termenele nu se modifică după înghețare. Orice schimbare
                  necesită un nou ciclu Ofertă → Comandă.
                </p>
              </div>

              {/* Next Step Panel */}
              {selectedOrder.quoteId ? (
                <NextStepPanel
                  title="Ofertă sursă"
                  description="Deschide oferta acceptată care a generat această comandă (read-only contextual)."
                  primaryAction={{
                    label: `Vezi oferta ${selectedOrder.quoteId}`,
                    to: `/quotes/${encodeURIComponent(selectedOrder.quoteId)}`,
                  }}
                  secondaryAction={{
                    label: "Lista oferte",
                    to: "/quotes",
                    variant: "ghost",
                  }}
                />
              ) : null}

              {selectedOrder.status === "created" && (
                <NextStepPanel
                  title="Următorul pas: Confirmă comanda"
                  description="Comanda a fost creată din ofertă. Confirmarea blochează snapshot-ul și permite pregătirea producției."
                  reason="Confirmarea este necesară pentru a trece la execuție."
                  primaryAction={{
                    label: "Confirmă comanda",
                    disabled: !canUseLiveOrders,
                    disabledReason: !canUseLiveOrders ? "Disponibil doar pe sursa backend live" : undefined,
                  }}
                />
              )}
              {selectedOrder.status === "confirmed" && (
                <NextStepPanel
                  title="Următorul pas: Pregătește producția"
                  description="Comanda este confirmată. Următorul pas este pregătirea și lansarea producției."
                  primaryAction={{
                    label: "Deschide Producție",
                    to: "/execution",
                  }}
                  secondaryAction={{
                    label: "Vezi Shop Floor",
                    to: "/shop-floor",
                    variant: "ghost",
                  }}
                />
              )}
              {selectedOrder.status === "locked" && (
                <NextStepPanel
                  title={
                    executionHasPlan
                      ? "Următorul pas: Vezi execuția"
                      : "Următorul pas: Generează taskuri producție"
                  }
                  description={
                    executionHasPlan
                      ? "Planul de execuție există. Deschide dashboard-ul pentru monitorizarea taskurilor."
                      : "Comanda este înghețată. Generează planul o singură dată, apoi deschide execuția pentru monitorizare."
                  }
                  primaryAction={
                    executionHasPlan && executionDetailPath
                      ? {
                          label: "Vezi execuția",
                          to: executionDetailPath,
                          disabled: !canUseLiveOrders,
                          disabledReason:
                            !canUseLiveOrders ? "Disponibil doar pe sursa backend live" : undefined,
                        }
                      : {
                          label: "Generează taskuri producție",
                          onClick: () => void handleGenerateExecutionPlan(),
                          disabled: !canUseLiveOrders || planGenerating || executionHasPlan === true,
                          disabledReason:
                            !canUseLiveOrders
                              ? "Disponibil doar pe sursa backend live"
                              : executionHasPlan
                                ? "Plan execuție existent"
                                : undefined,
                        }
                  }
                />
              )}
              {selectedOrder.status === "in_execution" && (
                <NextStepPanel
                  title="Comandă în execuție"
                  description="Producția este în desfășurare. Monitorizați progresul din dashboard-ul de execuție."
                  primaryAction={{
                    label: "Vezi execuția",
                    to: executionDetailPath || "/execution",
                    disabled: !canUseLiveOrders || !executionDetailPath,
                    disabledReason: !canUseLiveOrders ? "Disponibil doar pe sursa backend live" : undefined,
                  }}
                  secondaryAction={{
                    label: "Vezi Shop Floor",
                    to: "/shop-floor",
                    variant: "ghost",
                  }}
                />
              )}
              {selectedOrder.status === "completed" && (
                <NextStepPanel
                  title="Comandă finalizată"
                  description="Producția este completă. Verificați realitatea execuției și rapoartele."
                  primaryAction={{
                    label: "Vezi Rapoarte",
                    to: "/reports",
                  }}
                  secondaryAction={{
                    label: "Istoric Execuție",
                    to: "/execution",
                    variant: "ghost",
                  }}
                />
              )}
            </>
          ) : isOrdersEmpty ? (
            <div
              className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-6 space-y-3"
              data-testid="orders-empty-detail-panel"
            >
              <p className="text-[12px] text-wo-text-muted leading-relaxed text-center">
                Comenzile nu se creează manual din această pagină. Începe din Cereri sau
                convertește o ofertă acceptată.
              </p>
              <NextStepPanel
                title="Următorul pas: Deschide o ofertă"
                description="Acceptarea/conversia ofertei creează comanda — fără auto-order din UI."
                primaryAction={{ label: "Deschide oferte", to: "/quotes" }}
                secondaryAction={{ label: "Înapoi la cereri", to: "/intake", variant: "ghost" }}
              />
            </div>
          ) : (
            <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-6 space-y-3">
              <div className="text-center">
                <ClipboardList className="w-8 h-8 text-wo-text-dim mx-auto mb-2" />
                <p className="text-[13px] text-wo-text-muted">Selectează o comandă pentru detalii</p>
                <p className="text-[11px] text-wo-text-dim mt-1">
                  Alege o comandă din listă pentru snapshot acceptat și starea execuției.
                </p>
              </div>
              <NextStepPanel
                title="Flux comercial"
                description="Comanda închide lanțul Cerere → Produs → Ofertă. Selectează o comandă pentru pasul următor."
                primaryAction={{ label: "Vezi oferte", to: "/quotes", variant: "secondary" }}
                secondaryAction={{
                  label: "Vezi produse",
                  to: "/product-system/products",
                  variant: "ghost",
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}