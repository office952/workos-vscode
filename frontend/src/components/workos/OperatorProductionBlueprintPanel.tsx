import { useCallback, useEffect, useState } from "react";
import {
  fetchOrderProductionBlueprint,
  patchMaterialProcurementStatus,
  type ProductionBlueprintDTO,
} from "@/api/operatorProductionBlueprint";
import { SectionHeader } from "@/components/workos/SharedComponents";
import { StatusBadge } from "@/components/workos/design-system";
import { Loader2, RefreshCw, Users } from "lucide-react";
import {
  operationalReadinessBadgeClasses,
  operationalReadinessLabel,
} from "@/lib/executionOperationalReadinessDisplay";

const REFRESH_MS = 15_000;

function SummaryChip({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-lg border border-[#243044] bg-[#0A1020]/60 px-2.5 py-1.5 text-center min-w-[72px]">
      <div className="text-[14px] font-semibold text-slate-100">{value}</div>
      <div className="text-[10px] text-slate-500">{label}</div>
    </div>
  );
}

const PREPARATION_DOMAIN_LABELS: Record<string, string> = {
  cnc: "CNC",
  instrumentation: "Instrumentare",
  print: "Print",
  workshop_info: "Info atelier",
  other: "Altele",
};

function PreparationGroupSection({
  title,
  tasks,
  testId,
}: {
  title: string;
  tasks: Array<{
    task_id: string;
    name: string;
    status_display: string;
    assigned_employee_name?: string | null;
    documents_count?: number;
    has_instructions?: boolean;
  }>;
  testId: string;
}) {
  if (tasks.length === 0) return null;
  return (
    <div className="space-y-2" data-testid={testId}>
      <h3 className="text-[12px] font-semibold text-slate-300">{title}</h3>
      <ul className="space-y-1.5">
        {tasks.map((task) => (
          <li
            key={task.task_id}
            className="rounded-lg border border-[#243044] bg-[#0A1020]/50 px-3 py-2 text-[11px] text-slate-300"
          >
            <span className="font-medium text-slate-100">{task.name}</span>
            {" · "}
            {task.status_display}
            {task.assigned_employee_name ? ` · ${task.assigned_employee_name}` : " · neatribuit"}
            {task.documents_count ? ` · ${task.documents_count} doc` : ""}
            {task.has_instructions ? " · instrucțiuni" : ""}
          </li>
        ))}
      </ul>
    </div>
  );
}

interface OperatorProductionBlueprintPanelProps {
  orderIds: number[];
  defaultOrderId?: number | null;
}

export default function OperatorProductionBlueprintPanel({
  orderIds,
  defaultOrderId = null,
}: OperatorProductionBlueprintPanelProps) {
  const sortedOrderIds = [...new Set(orderIds.filter((id) => id > 0))].sort((a, b) => a - b);
  const initialOrderId = defaultOrderId && sortedOrderIds.includes(defaultOrderId)
    ? defaultOrderId
    : sortedOrderIds[0] ?? null;

  const [selectedOrderId, setSelectedOrderId] = useState<number | null>(initialOrderId);
  const [blueprint, setBlueprint] = useState<ProductionBlueprintDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);
  const [procurementSaving, setProcurementSaving] = useState<string | null>(null);
  const [procurementDrafts, setProcurementDrafts] = useState<
    Record<string, { status: string; note: string }>
  >({});

  const load = useCallback(async () => {
    if (selectedOrderId == null) {
      setBlueprint(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOrderProductionBlueprint(selectedOrderId);
      setBlueprint(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la încărcarea blueprint-ului");
      setBlueprint(null);
    } finally {
      setLoading(false);
    }
  }, [selectedOrderId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (collapsed || selectedOrderId == null) return;
    const timer = window.setInterval(() => {
      void load();
    }, REFRESH_MS);
    return () => window.clearInterval(timer);
  }, [collapsed, load, selectedOrderId]);

  useEffect(() => {
    if (selectedOrderId == null && sortedOrderIds.length > 0) {
      setSelectedOrderId(sortedOrderIds[0]);
    }
  }, [selectedOrderId, sortedOrderIds]);

  const criticalMaterials = (blueprint?.tasks ?? [])
    .flatMap((task) => task.material_planning_items ?? [])
    .filter((item, index, items) => items.findIndex((x) => x.code === item.code) === index)
    .filter((item) => item.category === "project_critical");

  const saveProcurementStatus = async (materialCode: string) => {
    if (selectedOrderId == null) return;
    const draft = procurementDrafts[materialCode];
    if (!draft?.status) return;
    setProcurementSaving(materialCode);
    setError(null);
    try {
      await patchMaterialProcurementStatus(selectedOrderId, materialCode, {
        status: draft.status,
        note: draft.note || undefined,
      });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare la salvarea statusului material");
    } finally {
      setProcurementSaving(null);
    }
  };

  if (sortedOrderIds.length === 0) {
    return null;
  }

  return (
    <section
      className="rounded-xl border border-[#243044] bg-[#0A1020]/40 p-4 space-y-3"
      data-testid="operator-production-blueprint-panel"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <SectionHeader title="Blueprint execuție comandă" />
          <p className="text-[11px] text-slate-500 -mt-2">
            Stare taskuri, oameni activi și ce mai urmează
          </p>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => void load()}
            disabled={loading || selectedOrderId == null}
            className="inline-flex items-center gap-1 rounded border border-[#243044] px-2 py-1 text-[11px] text-slate-300 hover:bg-[#121826] disabled:opacity-50"
            data-testid="operator-blueprint-refresh"
          >
            {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
            Reîmprospătează
          </button>
          <button
            type="button"
            onClick={() => setCollapsed((v) => !v)}
            className="text-[11px] text-slate-400 hover:text-slate-200"
          >
            {collapsed ? "Deschide" : "Restrânge"}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <label className="text-[11px] text-slate-500" htmlFor="operator-blueprint-order">
          Comandă
        </label>
        <select
          id="operator-blueprint-order"
          value={selectedOrderId ?? ""}
          onChange={(e) => setSelectedOrderId(Number(e.target.value))}
          className="rounded border border-[#243044] bg-[#0A1020] px-2 py-1 text-[12px] text-slate-200"
          data-testid="operator-blueprint-order-select"
        >
          {sortedOrderIds.map((id) => (
            <option key={id} value={id}>
              #{id}
            </option>
          ))}
        </select>
      </div>

      {!collapsed && error && (
        <p className="text-[12px] text-amber-300" data-testid="operator-blueprint-error">
          {error}
        </p>
      )}

      {!collapsed && blueprint && (
        <>
          <div className="flex flex-wrap gap-2" data-testid="operator-blueprint-summary">
            <SummaryChip label="Total" value={blueprint.summary.total_tasks} />
            <SummaryChip label="În lucru" value={blueprint.summary.in_progress} />
            <SummaryChip label="Blocate" value={blueprint.summary.blocked} />
            <SummaryChip label="Finalizate" value={blueprint.summary.done} />
            <SummaryChip label="Neatribuite" value={blueprint.summary.unassigned} />
            <SummaryChip label="Progres %" value={`${blueprint.summary.progress_percent}%`} />
            {blueprint.operational_readiness_status ? (
              <span
                className={`inline-flex items-center self-center rounded-lg border px-2.5 py-1.5 text-[10px] font-medium ${operationalReadinessBadgeClasses(blueprint.operational_readiness_status)}`}
                data-testid="operator-blueprint-operational-readiness"
                title={blueprint.operational_readiness_status}
              >
                {operationalReadinessLabel(blueprint.operational_readiness_status)}
              </span>
            ) : null}
          </div>

          {blueprint.material_planning_summary ? (
            <div
              className="flex flex-wrap gap-2"
              data-testid="operator-blueprint-material-summary"
            >
              <SummaryChip
                label="Materiale critice"
                value={blueprint.material_planning_summary.project_critical_count}
              />
              <SummaryChip
                label="Verificare preventivă"
                value={blueprint.material_planning_summary.suggest_replenishment_count}
              />
              <SummaryChip
                label="Consumabile checklist"
                value={blueprint.material_planning_summary.checklist_count}
              />
            </div>
          ) : null}

          {blueprint.production_planning_summary ? (
            <div
              className="rounded-lg border border-[#243044] bg-[#0A1020]/50 p-3 space-y-2"
              data-testid="operator-blueprint-production-control"
            >
              <h3 className="text-[12px] font-semibold text-slate-300">Control producție</h3>
              <p className="text-[11px] text-slate-400">
                {blueprint.production_planning_summary.suggested_next_action}
              </p>
              <div className="flex flex-wrap gap-2">
                <SummaryChip
                  label="Eligibile"
                  value={blueprint.production_planning_summary.eligible_tasks}
                />
                <SummaryChip
                  label="Așteaptă anterior"
                  value={blueprint.production_planning_summary.waiting_predecessor_tasks}
                />
                <SummaryChip
                  label="Așteaptă material"
                  value={blueprint.production_planning_summary.waiting_material_tasks}
                />
                {(blueprint.production_planning_summary.waiting_file_tasks ?? 0) > 0 ? (
                  <SummaryChip
                    label="Așteaptă fișiere"
                    value={blueprint.production_planning_summary.waiting_file_tasks ?? 0}
                  />
                ) : null}
                {(blueprint.production_planning_summary.waiting_template_tasks ?? 0) > 0 ? (
                  <SummaryChip
                    label="Așteaptă șablon"
                    value={blueprint.production_planning_summary.waiting_template_tasks ?? 0}
                  />
                ) : null}
                <SummaryChip
                  label="Critice neverificate"
                  value={blueprint.production_planning_summary.critical_materials_not_checked}
                />
                <SummaryChip
                  label="Awaiting advance"
                  value={blueprint.production_planning_summary.awaiting_advance_items}
                />
                <SummaryChip
                  label="Reaprovizionare"
                  value={blueprint.production_planning_summary.suggest_replenishment_items}
                />
              </div>
            </div>
          ) : null}

          {criticalMaterials.length > 0 ? (
            <div className="space-y-2" data-testid="operator-blueprint-procurement-controls">
              <h3 className="text-[12px] font-semibold text-slate-300">Status materiale critice</h3>
              <ul className="space-y-2">
                {criticalMaterials.slice(0, 6).map((item) => {
                  const draft = procurementDrafts[item.code] ?? {
                    status: item.procurement_status || "not_checked",
                    note: item.operator_note || "",
                  };
                  return (
                    <li
                      key={item.code}
                      className="rounded-lg border border-[#243044] bg-[#0A1020]/60 px-3 py-2 text-[11px] text-slate-300"
                      data-testid={`operator-procurement-item-${item.code}`}
                    >
                      <p className="font-medium text-slate-100">
                        {item.name}{" "}
                        <span className="text-slate-500">({item.procurement_label || "Neverificat"})</span>
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        <select
                          value={draft.status}
                          onChange={(e) =>
                            setProcurementDrafts((prev) => ({
                              ...prev,
                              [item.code]: { ...draft, status: e.target.value },
                            }))
                          }
                          className="rounded border border-[#243044] bg-[#0A1020] px-2 py-1 text-[11px]"
                          data-testid={`operator-procurement-status-${item.code}`}
                        >
                          <option value="not_checked">Neverificat</option>
                          <option value="check_required">Verificare necesară</option>
                          <option value="awaiting_advance">Așteaptă avans</option>
                          <option value="to_order">De comandat</option>
                          <option value="ordered">Comandat</option>
                          <option value="received">Primit</option>
                          <option value="available">Disponibil</option>
                          <option value="not_required">Nu este necesar</option>
                        </select>
                        <input
                          type="text"
                          value={draft.note}
                          placeholder="Notă operator"
                          onChange={(e) =>
                            setProcurementDrafts((prev) => ({
                              ...prev,
                              [item.code]: { ...draft, note: e.target.value },
                            }))
                          }
                          className="min-w-[160px] flex-1 rounded border border-[#243044] bg-[#0A1020] px-2 py-1 text-[11px]"
                          data-testid={`operator-procurement-note-${item.code}`}
                        />
                        <button
                          type="button"
                          disabled={procurementSaving === item.code}
                          onClick={() => void saveProcurementStatus(item.code)}
                          className="rounded border border-emerald-800/60 px-2 py-1 text-[11px] text-emerald-200 hover:bg-emerald-950/30 disabled:opacity-50"
                          data-testid={`operator-procurement-save-${item.code}`}
                        >
                          {procurementSaving === item.code ? "..." : "Salvează"}
                        </button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          ) : null}

          {blueprint.preparation_ownership ? (
            <div
              className="rounded-lg border border-[#243044] bg-[#0A1020]/50 p-3 space-y-3"
              data-testid="operator-blueprint-preparation-ownership"
            >
              <h3 className="text-[12px] font-semibold text-slate-200">
                Pregătire operațională
              </h3>
              <div className="grid gap-2 sm:grid-cols-2 text-[11px] text-slate-400">
                <div>
                  <p className="text-slate-500 uppercase text-[9px] tracking-wide">
                    Instrumentare comandă
                  </p>
                  <p className="mt-1 text-slate-200">
                    {blueprint.preparation_ownership.instrumentation.prepared_by_user_name
                      || blueprint.preparation_ownership.instrumentation.prepared_by_user_id
                      || "—"}
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    Sursă: execution_plan.prepared_by_user_id
                  </p>
                </div>
                <div>
                  <p className="text-slate-500 uppercase text-[9px] tracking-wide">
                    Pregătire CNC
                  </p>
                  <p className="mt-1 text-slate-200">
                    {blueprint.preparation_ownership.cnc.task_count} task(uri) CNC
                  </p>
                  <p className="text-[10px] text-slate-500 mt-0.5">
                    Registry: {blueprint.preparation_ownership.cnc.registry_operation_hint || "cnc_cutting"}
                  </p>
                </div>
              </div>
              {blueprint.preparation_ownership.mounting_template.material_type !== "none" ? (
                <div className="text-[11px] text-slate-400 border-t border-[#243044] pt-2">
                  <p className="text-slate-500 uppercase text-[9px] tracking-wide mb-1">
                    Șablon montaj
                  </p>
                  <p className="text-slate-200">
                    Tip: {blueprint.preparation_ownership.mounting_template.material_type}
                    {" · "}
                    Material: {blueprint.preparation_ownership.mounting_template.material_code || "—"}
                    {blueprint.preparation_ownership.mounting_template.registry_rate_display
                      ? ` · ${blueprint.preparation_ownership.mounting_template.registry_rate_display}`
                      : ""}
                  </p>
                </div>
              ) : null}
            </div>
          ) : null}

          {blueprint.preparation_groups ? (
            <div className="space-y-3" data-testid="operator-blueprint-preparation-groups">
              <PreparationGroupSection
                title="Pregătire CNC"
                tasks={blueprint.preparation_groups.cnc ?? []}
                testId="operator-blueprint-cnc-group"
              />
              <PreparationGroupSection
                title="Instrumentare / documente"
                tasks={[
                  ...(blueprint.preparation_groups.instrumentation ?? []),
                  ...(blueprint.preparation_groups.workshop_info ?? []),
                ]}
                testId="operator-blueprint-instrumentation-group"
              />
              <PreparationGroupSection
                title="Print / vinyl"
                tasks={blueprint.preparation_groups.print ?? []}
                testId="operator-blueprint-print-group"
              />
            </div>
          ) : null}

          {blueprint.active_workers.length > 0 && (
            <div className="space-y-2" data-testid="operator-blueprint-active-workers">
              <h3 className="text-[12px] font-semibold text-slate-300 inline-flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5" aria-hidden />
                Lucrează acum
              </h3>
              <ul className="space-y-1.5">
                {blueprint.active_workers.map((worker) => (
                  <li
                    key={`${worker.task_id}-${worker.employee_id}`}
                    className="rounded-lg border border-emerald-900/40 bg-emerald-950/20 px-3 py-2 text-[12px] text-emerald-100"
                  >
                    <span className="font-medium">{worker.employee_name || `#${worker.employee_id}`}</span>
                    {" · "}
                    {worker.task_name} ({worker.task_id})
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="space-y-2">
            <h3 className="text-[12px] font-semibold text-slate-300">Taskuri</h3>
            <ul className="space-y-2" data-testid="operator-blueprint-task-list">
              {blueprint.tasks.map((task) => (
                <li
                  key={task.task_id}
                  className="rounded-lg border border-[#243044] bg-[#0A1020]/60 px-3 py-2.5"
                  data-testid={`operator-blueprint-task-${task.task_id}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-[13px] font-medium text-slate-100 truncate">
                        {task.name}
                      </p>
                      <p className="text-[10px] text-slate-500">{task.task_id}</p>
                      {task.preparation_domain ? (
                        <p className="text-[10px] text-slate-500">
                          Domeniu: {PREPARATION_DOMAIN_LABELS[task.preparation_domain] || task.preparation_domain}
                        </p>
                      ) : null}
                    </div>
                    <StatusBadge
                      domain="executionTask"
                      status={
                        task.status === "todo" || task.status === "unassigned"
                          ? "assigned"
                          : task.status
                      }
                      className="text-[10px] shrink-0"
                    />
                  </div>
                  <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] text-slate-400">
                    <span>Atribuit: {task.assigned_employee_name || "—"}</span>
                    <span>
                      Lucrează: {task.active_worker_name || "—"}
                    </span>
                    <span>Doc: {task.documents_count > 0 ? task.documents_count : "nu"}</span>
                    <span>Instrucțiuni: {task.has_instructions ? "da" : "nu"}</span>
                    <span>Info open: {task.has_open_clarification ? "da" : "nu"}</span>
                    {task.block_reason ? (
                      <span className="col-span-2 text-amber-300/90">Blocat: {task.block_reason}</span>
                    ) : null}
                    {task.readiness_label && task.is_startable === false ? (
                      <span className="col-span-2 text-amber-300/90">
                        Readiness: {task.readiness_label}
                        {(task.readiness_reasons?.[0]?.message ||
                          task.blocking_reasons?.[0]?.message) &&
                          ` — ${task.readiness_reasons?.[0]?.message || task.blocking_reasons?.[0]?.message}`}
                      </span>
                    ) : null}
                    {(task.blocking_tasks?.length ?? 0) > 0 ? (
                      <span className="col-span-2 text-slate-400">
                        Blochează:{" "}
                        {(task.blocking_tasks ?? []).map((blocker) => blocker.name).join(", ")}
                      </span>
                    ) : null}
                    {task.dependency_warning ? (
                      <span className="col-span-2 text-amber-300/90">{task.dependency_warning}</span>
                    ) : null}
                    {task.material_warning ? (
                      <span className="col-span-2 text-amber-300/80">{task.material_warning}</span>
                    ) : null}
                    {(task.blocking_materials?.length ?? 0) > 0 ? (
                      <span className="col-span-2 text-amber-300/90">
                        Materiale blocante:{" "}
                        {(task.blocking_materials ?? [])
                          .map((item) => `${item.name} (${item.label || item.status})`)
                          .join(" · ")}
                      </span>
                    ) : null}
                    {(task.material_planning_items?.length ?? 0) > 0 ? (
                      <span className="col-span-2 text-slate-400">
                        Plan materiale:{" "}
                        {(task.material_planning_items ?? [])
                          .slice(0, 3)
                          .map((item) => item.name)
                          .join(" · ")}
                      </span>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </section>
  );
}
