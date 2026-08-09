/**
 * MachineRun list — /execution/machine-runs
 * Consumes GET …/resource-state/machine-runs. No fake/demo runs.
 */
import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Cog, RefreshCw } from "lucide-react";
import {
  listMachineRuns,
  MachineRunRequestError,
  type MachineRunListItem,
} from "@/api/machineRuns";
import { Button } from "@/components/ui/button";
import FlowBreadcrumb from "@/components/workos/FlowBreadcrumb";
import { useCurrentPermissions } from "@/hooks/useCurrentPermissions";
import {
  CREATE_UI,
  MACHINE_RUN_STATUS_LABEL,
  formatReservationWindow,
  planOrderSummary,
  primaryActionLabel,
  statusBadgeClass,
} from "@/lib/machineRunUi";

type Scope = "active" | "all";

export default function MachineRunsListPage() {
  const navigate = useNavigate();
  const { role, can } = useCurrentPermissions();
  const canRead = can("execution.machine_run.read");

  const [scope, setScope] = useState<Scope>("active");
  const [items, setItems] = useState<MachineRunListItem[]>([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!canRead) {
      setLoading(false);
      setError("Nu ai dreptul să vezi rulările de utilaj.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await listMachineRuns({
        open_only: scope === "active",
      });
      setItems(result.items);
      setCount(result.count);
    } catch (err) {
      const msg =
        err instanceof MachineRunRequestError
          ? err.message
          : "Nu am putut încărca rulările de utilaj.";
      setError(msg);
      setItems([]);
      setCount(0);
    } finally {
      setLoading(false);
    }
  }, [canRead, scope]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-4 p-4 md:p-6" data-testid="machine-runs-list-page">
      <FlowBreadcrumb
        items={[
          { label: "Planificare", to: "/execution" },
          { label: "Rulări utilaj", active: true },
        ]}
      />

      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Cog className="h-5 w-5 text-wo-text-muted" aria-hidden />
            <h1 className="text-xl font-semibold text-wo-text-primary">Rulări utilaj</h1>
          </div>
          <p className="max-w-2xl text-sm text-wo-text-muted">
            Grupări și rezervări pe utilaj (multi-plan / multi-comandă). Start/Finalizează aici
            se referă la lucrul pe utilaj — nu la task sau sesiune angajat.
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => void load()}
          disabled={loading}
          className="border-wo-border bg-wo-surface-raised text-wo-text-primary"
        >
          <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Reîncarcă
        </Button>
      </header>

      <div
        className="inline-flex rounded-md border border-wo-border bg-wo-surface-raised p-0.5"
        role="tablist"
        aria-label="Filtru rulări"
      >
        {(
          [
            { id: "active" as const, label: "Active" },
            { id: "all" as const, label: "Toate" },
          ] as const
        ).map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={scope === tab.id}
            onClick={() => setScope(tab.id)}
            className={
              scope === tab.id
                ? "rounded px-3 py-1.5 text-sm font-medium bg-wo-surface-inset text-wo-text-primary"
                : "rounded px-3 py-1.5 text-sm text-wo-text-muted hover:text-wo-text-primary"
            }
          >
            {tab.label}
          </button>
        ))}
      </div>

      {CREATE_UI === "DEFERRED" ? (
        <p className="text-xs text-wo-text-muted" data-testid="machine-runs-create-deferred">
          Crearea unei rulări noi din UI este amânată — lipsește API-ul de descoperire a
          taskurilor eligibile.
        </p>
      ) : null}

      {error ? (
        <div
          className="rounded-md border border-wo-error/35 bg-wo-error-muted px-3 py-2 text-sm text-wo-error"
          role="alert"
        >
          {error}
        </div>
      ) : null}

      {loading ? (
        <p className="text-sm text-wo-text-muted">Se încarcă rulările…</p>
      ) : null}

      {!loading && !error && items.length === 0 ? (
        <div
          className="rounded-md border border-wo-border bg-wo-surface-raised px-4 py-8 text-center"
          data-testid="machine-runs-empty"
        >
          <p className="text-sm font-medium text-wo-text-primary">
            {scope === "active"
              ? "Nu există rulări de utilaj active."
              : "Nu există rulări de utilaj."}
          </p>
          <p className="mt-1 text-xs text-wo-text-muted">
            Lista reflectă doar datele din backend. Nu se afișează rulări demonstrative.
          </p>
        </div>
      ) : null}

      {!loading && items.length > 0 ? (
        <div className="overflow-hidden rounded-md border border-wo-border bg-wo-surface-raised">
          <div className="border-b border-wo-border px-3 py-2 text-xs text-wo-text-muted">
            {count} {count === 1 ? "rulare" : "rulări"}
            {scope === "active" ? " active (rezervare HELD sau RESERVED)" : ""}
          </div>
          <ul className="divide-y divide-wo-border" data-testid="machine-runs-list">
            {items.map((row) => {
              const machineLabel =
                row.machine_name || row.machine_code || `Utilaj ${row.machine_id}`;
              const actionHint = primaryActionLabel(row.status, role);
              return (
                <li key={row.machine_run_id}>
                  <button
                    type="button"
                    onClick={() => navigate(`/execution/machine-runs/${row.machine_run_id}`)}
                    className="flex w-full flex-col gap-2 px-3 py-3 text-left transition-colors hover:bg-wo-surface-inset/60 md:flex-row md:items-center md:justify-between"
                    data-testid={`machine-run-row-${row.machine_run_id}`}
                  >
                    <div className="min-w-0 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span
                          className={`inline-flex rounded border px-2 py-0.5 text-xs font-medium ${statusBadgeClass(row.status)}`}
                        >
                          {MACHINE_RUN_STATUS_LABEL[row.status]}
                        </span>
                        <span className="text-sm font-medium text-wo-text-primary">
                          {machineLabel}
                        </span>
                        {row.order_ids.length > 1 ? (
                          <span className="rounded border border-wo-border px-1.5 py-0.5 text-[10px] text-wo-text-muted">
                            Mai multe comenzi
                          </span>
                        ) : null}
                      </div>
                      <p className="text-xs text-wo-text-muted">
                        {formatReservationWindow(
                          row.reservation_start,
                          row.reservation_end,
                          row.timezone,
                        )}
                      </p>
                      <p className="text-xs text-wo-text-muted">
                        {row.active_participant_count} participanți activi ·{" "}
                        {planOrderSummary(row.order_ids, row.execution_plan_ids)}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2 text-xs">
                      {actionHint ? (
                        <span className="rounded border border-wo-border bg-wo-surface-inset px-2 py-1 text-wo-text-primary">
                          {actionHint}
                        </span>
                      ) : (
                        <span className="text-wo-text-muted">Doar citire</span>
                      )}
                      <Link
                        to={`/execution/machine-runs/${row.machine_run_id}`}
                        className="text-wo-info hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        Detaliu
                      </Link>
                    </div>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
