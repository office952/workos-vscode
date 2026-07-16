/**
 * Task-scoped collaboration chrome for Operator / Execution.
 * Renders only when VITE_FEATURE_FLEX_COLLAB_UI is on; actions follow backend can_*.
 */
import { useMemo, useState } from "react";
import {
  CollaborationApiError,
  cancelOperatorHelpRequest,
  createOperatorHelpRequest,
  type TaskCollaborationReadDTO,
} from "@/api/collaboration";
import { operationalRegistryApi } from "@/api/operationalRegistry";
import { cn } from "@/lib/utils";

function chip(label: string, tone: "neutral" | "open" | "ok" | "warn" | "muted") {
  const tones = {
    neutral: "border-slate-600 text-slate-300 bg-slate-800/60",
    open: "border-amber-700/80 text-amber-200 bg-amber-950/40",
    ok: "border-emerald-700/70 text-emerald-200 bg-emerald-950/30",
    warn: "border-rose-700/70 text-rose-200 bg-rose-950/30",
    muted: "border-slate-700 text-slate-500 bg-slate-900/40",
  } as const;
  return (
    <span
      className={cn(
        "inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide",
        tones[tone],
      )}
    >
      {label}
    </span>
  );
}

export default function OperatorTaskCollaborationPanel({
  orderId,
  task,
  onChanged,
  compact = false,
  testIdPrefix = "operator-collab",
}: {
  orderId: number;
  task: TaskCollaborationReadDTO;
  onChanged: () => Promise<void> | void;
  compact?: boolean;
  testIdPrefix?: string;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"broadcast" | "targeted">("broadcast");
  const [targetId, setTargetId] = useState("");
  const [employees, setEmployees] = useState<Array<{ id: number; name: string }>>([]);
  const [pickerLoaded, setPickerLoaded] = useState(false);

  const openHelp = task.open_help_requests?.[0] ?? null;
  const activeHelpers = useMemo(
    () => (task.helper_memberships || []).filter((m) => m.status === "active"),
    [task.helper_memberships],
  );
  const inactiveHelpers = useMemo(
    () => (task.helper_memberships || []).filter((m) => m.status !== "active"),
    [task.helper_memberships],
  );
  const activeWorkers = task.active_workers || [];
  const canRequest = task.can_request_help === true && !task.has_open_help;
  const canCancel = task.can_cancel_help === true && Boolean(openHelp);
  const canComplete = task.can_complete_operation === true;

  const loadEmployees = async () => {
    if (pickerLoaded) return;
    try {
      const res = await operationalRegistryApi.listEmployees();
      setEmployees(
        (res.items || []).map((e) => ({
          id: e.id,
          name: e.name || `Angajat #${e.id}`,
        })),
      );
      setPickerLoaded(true);
    } catch {
      setEmployees([]);
      setPickerLoaded(true);
    }
  };

  const run = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    setError(null);
    try {
      await fn();
      await onChanged();
    } catch (err) {
      if (err instanceof CollaborationApiError) {
        setError(`${err.code}: ${err.message}`);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Acțiunea de colaborare a eșuat.");
      }
    } finally {
      setBusy(false);
    }
  };

  const principalName =
    task.optional_principal?.optional_principal_employee_name ||
    (task.optional_principal?.optional_principal_employee_id
      ? `#${task.optional_principal.optional_principal_employee_id}`
      : "—");

  return (
    <div
      data-testid={`${testIdPrefix}-${task.task_id}`}
      className={cn(
        "rounded border border-[#1F2A44] bg-[#0B1220]/80 text-left",
        compact ? "mt-1 p-2" : "mt-2 p-3",
      )}
    >
      <div className="flex flex-wrap items-center gap-1.5 mb-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
          Colaborare
        </span>
        {task.has_open_help
          ? chip(openHelp?.is_broadcast === false ? "Ajutor țintit OPEN" : "Ajutor broadcast OPEN", "open")
          : chip("Fără ajutor OPEN", "muted")}
        {task.operation_completed
          ? chip("Operație finalizată", "ok")
          : chip("Operație incompletă", "neutral")}
        {canComplete ? chip("Poți finaliza", "ok") : null}
      </div>

      <div className={cn("grid gap-2 text-[11px] text-slate-300", compact ? "" : "sm:grid-cols-3")}>
        <div>
          <div className="text-[10px] uppercase text-slate-500 mb-0.5">Principal</div>
          <div>{principalName}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-slate-500 mb-0.5">
            Helpers autorizați ({activeHelpers.length})
          </div>
          {activeHelpers.length === 0 ? (
            <div className="text-slate-500">Niciun helper activ</div>
          ) : (
            <ul className="space-y-0.5">
              {activeHelpers.map((h) => (
                <li key={h.membership_id ?? h.employee_id}>
                  {h.employee_name || `#${h.employee_id}`}{" "}
                  <span className="text-slate-500">(autorizat, nu neapărat în lucru)</span>
                </li>
              ))}
            </ul>
          )}
          {inactiveHelpers.length > 0 ? (
            <div className="mt-1 text-slate-500">
              Istoric: {inactiveHelpers.map((h) => h.employee_name || `#${h.employee_id}`).join(", ")}
            </div>
          ) : null}
        </div>
        <div>
          <div className="text-[10px] uppercase text-slate-500 mb-0.5">
            Lucrători activi ({activeWorkers.length})
          </div>
          {activeWorkers.length === 0 ? (
            <div className="text-slate-500">Nicio sesiune activă</div>
          ) : (
            <ul className="space-y-0.5">
              {activeWorkers.map((w) => (
                <li key={w.employee_id}>
                  {w.employee_name || `#${w.employee_id}`}
                  {w.is_optional_principal ? " · principal" : ""}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-2">
        {canRequest ? (
          <>
            <select
              aria-label="Tip ajutor"
              className="rounded border border-slate-700 bg-[#0A1020] px-2 py-1 text-[11px] text-slate-200"
              value={mode}
              disabled={busy}
              onChange={(e) => {
                const next = e.target.value === "targeted" ? "targeted" : "broadcast";
                setMode(next);
                if (next === "targeted") void loadEmployees();
              }}
            >
              <option value="broadcast">Broadcast</option>
              <option value="targeted">Țintit</option>
            </select>
            {mode === "targeted" ? (
              <select
                aria-label="Angajat țintă"
                className="rounded border border-slate-700 bg-[#0A1020] px-2 py-1 text-[11px] text-slate-200 max-w-[180px]"
                value={targetId}
                disabled={busy}
                onChange={(e) => setTargetId(e.target.value)}
              >
                <option value="">Selectează angajat…</option>
                {employees.map((e) => (
                  <option key={e.id} value={String(e.id)}>
                    {e.name}
                  </option>
                ))}
              </select>
            ) : null}
            <button
              type="button"
              data-testid={`${testIdPrefix}-request-help`}
              disabled={busy || (mode === "targeted" && !targetId)}
              className="rounded bg-amber-700 hover:bg-amber-600 disabled:bg-slate-700 disabled:text-slate-500 px-2 py-1 text-[11px] font-semibold text-white"
              onClick={() =>
                void run(() =>
                  createOperatorHelpRequest(orderId, task.task_id, {
                    targeted_employee_id:
                      mode === "targeted" && targetId ? Number(targetId) : null,
                    reason: "Operator help request",
                  }),
                )
              }
            >
              Cere ajutor
            </button>
          </>
        ) : null}

        {canCancel && openHelp ? (
          <button
            type="button"
            data-testid={`${testIdPrefix}-cancel-help`}
            disabled={busy}
            className="rounded border border-slate-600 hover:border-rose-600/70 px-2 py-1 text-[11px] font-semibold text-slate-200"
            onClick={() =>
              void run(() =>
                cancelOperatorHelpRequest(orderId, openHelp.help_request_id),
              )
            }
          >
            Anulează ajutorul
          </button>
        ) : null}

        {!canRequest && !canCancel ? (
          <span className="text-[10px] text-slate-500">
            Acțiunile de ajutor urmează capability-urile backend.
          </span>
        ) : null}
      </div>

      {error ? (
        <p
          data-testid={`${testIdPrefix}-error`}
          className="mt-2 text-[11px] text-rose-300"
          role="alert"
        >
          {error} — reîncarcă starea după rezolvare.
        </p>
      ) : null}
    </div>
  );
}
