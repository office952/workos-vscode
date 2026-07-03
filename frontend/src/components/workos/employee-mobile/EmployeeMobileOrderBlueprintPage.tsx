import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import {
  fetchEmployeeMobileOrderBlueprint,
  type EmployeeMobileOrderBlueprintDTO,
} from "@/api/employeeMobileOrderBlueprint";
import { listEmployeeMobileTasks, type EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import EmployeeMobileOrderPipelineView from "@/components/workos/employee-mobile/EmployeeMobileOrderPipelineView";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { buildEmployeeMobileTasksPath } from "@/lib/employeeMobileTaskViews";

export default function EmployeeMobileOrderBlueprintPage({ orderId }: { orderId: number }) {
  const [blueprint, setBlueprint] = useState<EmployeeMobileOrderBlueprintDTO | null>(null);
  const [personalTasks, setPersonalTasks] = useState<EmployeeMobileTaskDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [blueprintData, tasks] = await Promise.all([
        fetchEmployeeMobileOrderBlueprint(orderId),
        listEmployeeMobileTasks(),
      ]);
      setBlueprint(blueprintData);
      setPersonalTasks(tasks.filter((task) => task.order_id === orderId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nu am putut încărca blueprint-ul.");
      setBlueprint(null);
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-4" data-testid="employee-mobile-order-blueprint">
      <Link
        to={buildEmployeeMobileTasksPath("pipeline")}
        className="inline-flex items-center gap-1.5 text-[12px] text-slate-400 hover:text-slate-200"
        data-testid="employee-mobile-blueprint-back"
      >
        <ArrowLeft className="w-3.5 h-3.5" aria-hidden />
        Înapoi la taskuri
      </Link>

      <div className="space-y-1">
        <h2
          className="text-xl font-semibold text-slate-100"
          data-testid="employee-mobile-blueprint-title"
        >
          Tot fluxul comenzii
        </h2>
        <p className="text-sm text-slate-400">
          Unde sunt taskurile tale în fluxul comenzii
        </p>
      </div>

      {loading && (
        <EmployeeMobileLoadingState
          message="Se încarcă fluxul comenzii…"
          testId="employee-mobile-blueprint-loading"
        />
      )}
      {!loading && error && (
        <EmployeeMobileErrorState message={error} testId="employee-mobile-blueprint-error" />
      )}

      {!loading && !error && blueprint && (
        <EmployeeMobileOrderPipelineView
          blueprint={blueprint}
          personalTasks={personalTasks}
          showSummaryChips
          showRefresh
          onRefresh={() => void load()}
          listHeading="Tot fluxul comenzii"
          listTestId="employee-mobile-blueprint-task-list"
          compactCards={false}
        />
      )}

      {!loading && !error && !blueprint && (
        <EmployeeMobileEmptyState
          message="Flux indisponibil pentru această comandă."
          testId="employee-mobile-blueprint-empty"
        />
      )}
    </div>
  );
}
