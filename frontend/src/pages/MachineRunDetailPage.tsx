/**
 * MachineRun detail — /execution/machine-runs/:id
 * Command → wait → refetch canonical detail. No optimistic lifecycle flips.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, Cog, RefreshCw } from "lucide-react";
import {
  cancelMachineRun,
  completeMachineRun,
  confirmMachineRun,
  getMachineRun,
  MachineRunRequestError,
  releaseMachineRun,
  removeMachineRunParticipant,
  rescheduleMachineRun,
  startMachineRun,
  type MachineRunDetail,
  type MachineRunParticipantRead,
} from "@/api/machineRuns";
import { Button } from "@/components/ui/button";
import FlowBreadcrumb from "@/components/workos/FlowBreadcrumb";
import { useCurrentPermissions } from "@/hooks/useCurrentPermissions";
import {
  ADD_UI,
  MACHINE_RUN_STATUS_LABEL,
  formatReservationWindow,
  formatRuntimeSeconds,
  mapMachineRunError,
  planOrderSummary,
  statusBadgeClass,
  visibleActionsForRole,
  type MachineRunAction,
} from "@/lib/machineRunUi";

function toLocalInputValue(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInputValue(local: string): string {
  const d = new Date(local);
  return d.toISOString();
}

export default function MachineRunDetailPage() {
  const { machineRunId: rawId } = useParams<{ machineRunId: string }>();
  const machineRunId = Number(rawId);
  const { role, can } = useCurrentPermissions();
  const canRead = can("execution.machine_run.read");

  const [detail, setDetail] = useState<MachineRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [errorBanner, setErrorBanner] = useState<{
    message: string;
    nextAction: string;
  } | null>(null);
  const [showReschedule, setShowReschedule] = useState(false);
  const [rescheduleStart, setRescheduleStart] = useState("");
  const [rescheduleEnd, setRescheduleEnd] = useState("");
  const [showRemoved, setShowRemoved] = useState(false);

  const load = useCallback(async () => {
    if (!canRead || !Number.isFinite(machineRunId) || machineRunId <= 0) {
      setLoading(false);
      setErrorBanner({
        message: "Nu am putut deschide rularea.",
        nextAction: "Verifică linkul sau drepturile de citire.",
      });
      return;
    }
    setLoading(true);
    try {
      const row = await getMachineRun(machineRunId);
      setDetail(row);
      setRescheduleStart(toLocalInputValue(row.reservation.reservation_start));
      setRescheduleEnd(toLocalInputValue(row.reservation.reservation_end));
    } catch (err) {
      const code = err instanceof MachineRunRequestError ? err.code : "request_failed";
      const mapped = mapMachineRunError(
        code,
        err instanceof Error ? err.message : undefined,
      );
      setErrorBanner({ message: mapped.message, nextAction: mapped.nextAction });
      setDetail(null);
    } finally {
      setLoading(false);
    }
  }, [canRead, machineRunId]);

  useEffect(() => {
    void load();
  }, [load]);

  const actions = useMemo(
    () => (detail ? visibleActionsForRole(detail.status, role) : []),
    [detail, role],
  );

  const activeParticipants = useMemo(
    () => detail?.participants.filter((p) => p.status === "ACTIVE") ?? [],
    [detail],
  );
  const removedParticipants = useMemo(
    () => detail?.participants.filter((p) => p.status === "REMOVED") ?? [],
    [detail],
  );

  const runCommand = useCallback(
    async (action: MachineRunAction, participant?: MachineRunParticipantRead) => {
      if (!detail) return;
      setBusy(true);
      setErrorBanner(null);
      const version = detail.version;
      try {
        switch (action) {
          case "confirm":
            await confirmMachineRun(detail.machine_run_id, version);
            break;
          case "start":
            await startMachineRun(detail.machine_run_id, version);
            break;
          case "complete":
            await completeMachineRun(detail.machine_run_id, version);
            break;
          case "release": {
            const ok =
              detail.status === "RESERVED"
                ? window.confirm(
                    "Eliberezi rezervarea fără a rula utilajul? Intervalul se închide.",
                  )
                : window.confirm(
                    "Eliberezi utilajul după finalizarea lucrului pe această rulare?",
                  );
            if (!ok) {
              setBusy(false);
              return;
            }
            await releaseMachineRun(detail.machine_run_id, version);
            break;
          }
          case "cancel": {
            if (!window.confirm("Anulezi această rulare de utilaj?")) {
              setBusy(false);
              return;
            }
            await cancelMachineRun(detail.machine_run_id, version);
            break;
          }
          case "reschedule": {
            if (!rescheduleStart || !rescheduleEnd) {
              setErrorBanner({
                message: "Completează intervalul de rezervare.",
                nextAction: "Setează început și sfârșit.",
              });
              setBusy(false);
              return;
            }
            await rescheduleMachineRun(detail.machine_run_id, {
              expected_version: version,
              reservation_start: fromLocalInputValue(rescheduleStart),
              reservation_end: fromLocalInputValue(rescheduleEnd),
              timezone: detail.timezone || detail.reservation.timezone,
            });
            setShowReschedule(false);
            break;
          }
          case "remove_participant": {
            if (!participant) {
              setBusy(false);
              return;
            }
            if (activeParticipants.length <= 2) {
              setErrorBanner({
                message: "Trebuie cel puțin doi participanți activi pentru această operație.",
                nextAction: "Nu elimina ultimul participant necesar.",
              });
              setBusy(false);
              return;
            }
            if (
              !window.confirm(
                `Elimini participantul ${participant.task_key} (comandă ${participant.order_id})?`,
              )
            ) {
              setBusy(false);
              return;
            }
            await removeMachineRunParticipant(detail.machine_run_id, {
              expected_version: version,
              execution_plan_id: participant.execution_plan_id,
              task_key: participant.task_key,
            });
            break;
          }
          default: {
            const _exhaustive: never = action;
            void _exhaustive;
          }
        }
        const refreshed = await getMachineRun(detail.machine_run_id);
        setDetail(refreshed);
        setRescheduleStart(toLocalInputValue(refreshed.reservation.reservation_start));
        setRescheduleEnd(toLocalInputValue(refreshed.reservation.reservation_end));
      } catch (err) {
        const code = err instanceof MachineRunRequestError ? err.code : "request_failed";
        const mapped = mapMachineRunError(
          code,
          err instanceof Error ? err.message : undefined,
        );
        setErrorBanner({ message: mapped.message, nextAction: mapped.nextAction });
        try {
          const refreshed = await getMachineRun(detail.machine_run_id);
          setDetail(refreshed);
        } catch {
          /* keep prior detail if refetch fails */
        }
      } finally {
        setBusy(false);
      }
    },
    [activeParticipants.length, detail, rescheduleEnd, rescheduleStart],
  );

  const machineLabel = detail
    ? detail.machine.name || detail.machine.machine_code || `Utilaj ${detail.machine.machine_id}`
    : "";

  const runtimeLabel = formatRuntimeSeconds(detail?.actual_runtime_seconds);

  return (
    <div className="space-y-4 p-4 md:p-6" data-testid="machine-run-detail-page">
      <FlowBreadcrumb
        items={[
          { label: "Planificare", to: "/execution" },
          { label: "Rulări utilaj", to: "/execution/machine-runs" },
          {
            label: Number.isFinite(machineRunId) ? `Rulare ${machineRunId}` : "Detaliu",
            active: true,
          },
        ]}
      />

      <div className="flex flex-wrap items-center justify-between gap-2">
        <Link
          to="/execution/machine-runs"
          className="inline-flex items-center gap-1 text-sm text-wo-text-muted hover:text-wo-text-primary"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Înapoi la listă
        </Link>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => void load()}
          disabled={loading || busy}
          className="border-wo-border bg-wo-surface-raised text-wo-text-primary"
        >
          <RefreshCw className={`mr-1.5 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Reîncarcă
        </Button>
      </div>

      {errorBanner ? (
        <div
          className="rounded-md border border-wo-error/35 bg-wo-error-muted px-3 py-2 text-sm text-wo-error"
          role="alert"
          data-testid="machine-run-error"
        >
          <p className="font-medium">{errorBanner.message}</p>
          <p className="mt-0.5 text-xs opacity-90">{errorBanner.nextAction}</p>
        </div>
      ) : null}

      {loading && !detail ? (
        <p className="text-sm text-wo-text-muted">Se încarcă detaliul…</p>
      ) : null}

      {detail ? (
        <>
          {/* Above fold */}
          <section className="space-y-3 rounded-md border border-wo-border bg-wo-surface-raised p-4">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <Cog className="h-5 w-5 text-wo-text-muted" aria-hidden />
                  <h1 className="text-xl font-semibold text-wo-text-primary">
                    Rulare utilaj #{detail.machine_run_id}
                  </h1>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={`inline-flex rounded border px-2 py-0.5 text-xs font-medium ${statusBadgeClass(detail.status)}`}
                    data-testid="machine-run-status"
                  >
                    {MACHINE_RUN_STATUS_LABEL[detail.status]}
                  </span>
                  <span className="text-sm font-medium text-wo-text-primary">{machineLabel}</span>
                  {detail.order_ids.length > 1 ? (
                    <span className="rounded border border-wo-border px-1.5 py-0.5 text-[10px] text-wo-text-muted">
                      Mai multe comenzi
                    </span>
                  ) : null}
                </div>
                <p className="text-sm text-wo-text-muted">
                  Fereastră:{" "}
                  {formatReservationWindow(
                    detail.reservation.reservation_start,
                    detail.reservation.reservation_end,
                    detail.reservation.timezone,
                  )}
                </p>
                {(detail.started_at || detail.completed_at || runtimeLabel) && (
                  <p className="text-xs text-wo-text-muted">
                    {detail.started_at
                      ? `Pornit: ${new Date(detail.started_at).toLocaleString("ro-RO")}`
                      : null}
                    {detail.completed_at
                      ? ` · Finalizat: ${new Date(detail.completed_at).toLocaleString("ro-RO")}`
                      : null}
                    {runtimeLabel ? ` · Durată utilaj: ${runtimeLabel}` : null}
                  </p>
                )}
                {detail.status === "COMPLETED" ? (
                  <p
                    className="text-xs text-wo-warning"
                    data-testid="machine-run-complete-release-hint"
                  >
                    Lucrul pe utilaj este finalizat. Utilajul rămâne rezervat până la eliberare.
                  </p>
                ) : null}
              </div>

              <div className="flex flex-col items-stretch gap-2 sm:items-end">
                {actions
                  .filter((a) => a.kind === "primary")
                  .map((a) => (
                    <Button
                      key={a.action}
                      type="button"
                      disabled={busy}
                      onClick={() => {
                        if (a.action === "reschedule") {
                          setShowReschedule(true);
                          return;
                        }
                        void runCommand(a.action);
                      }}
                      data-testid={`machine-run-action-${a.action}`}
                    >
                      {a.label}
                    </Button>
                  ))}
                <div className="flex flex-wrap justify-end gap-2">
                  {actions
                    .filter((a) => a.kind === "secondary" && a.action !== "remove_participant")
                    .map((a) => (
                      <Button
                        key={a.action}
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={busy}
                        onClick={() => {
                          if (a.action === "reschedule") {
                            setShowReschedule((v) => !v);
                            return;
                          }
                          void runCommand(a.action);
                        }}
                        data-testid={`machine-run-action-${a.action}`}
                        className="border-wo-border text-wo-text-primary"
                      >
                        {a.label}
                      </Button>
                    ))}
                  {actions
                    .filter((a) => a.kind === "danger")
                    .map((a) => (
                      <Button
                        key={a.action}
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={busy}
                        onClick={() => void runCommand(a.action)}
                        data-testid={`machine-run-action-${a.action}`}
                        className="border-wo-error/40 text-wo-error"
                      >
                        {a.label}
                      </Button>
                    ))}
                </div>
              </div>
            </div>

            {showReschedule ? (
              <div
                className="mt-2 space-y-2 rounded border border-wo-border bg-wo-surface-inset p-3"
                data-testid="machine-run-reschedule"
              >
                <p className="text-xs font-medium text-wo-text-primary">Reprogramează fereastra</p>
                <p className="text-[11px] text-wo-text-muted">
                  Doar început/sfârșit. Utilajul și participanții rămân neschimbați. Fus:{" "}
                  {detail.timezone || detail.reservation.timezone}
                </p>
                <div className="flex flex-wrap gap-3">
                  <label className="text-xs text-wo-text-muted">
                    Început
                    <input
                      type="datetime-local"
                      value={rescheduleStart}
                      onChange={(e) => setRescheduleStart(e.target.value)}
                      className="mt-1 block rounded border border-wo-border bg-wo-surface-raised px-2 py-1 text-sm text-wo-text-primary"
                    />
                  </label>
                  <label className="text-xs text-wo-text-muted">
                    Sfârșit
                    <input
                      type="datetime-local"
                      value={rescheduleEnd}
                      onChange={(e) => setRescheduleEnd(e.target.value)}
                      className="mt-1 block rounded border border-wo-border bg-wo-surface-raised px-2 py-1 text-sm text-wo-text-primary"
                    />
                  </label>
                </div>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    size="sm"
                    disabled={busy}
                    onClick={() => void runCommand("reschedule")}
                  >
                    Salvează intervalul
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    disabled={busy}
                    onClick={() => setShowReschedule(false)}
                  >
                    Renunță
                  </Button>
                </div>
              </div>
            ) : null}
          </section>

          {/* ACTIVE participants */}
          <section className="space-y-2 rounded-md border border-wo-border bg-wo-surface-raised p-4">
            <h2 className="text-sm font-semibold text-wo-text-primary">
              Participanți activi ({activeParticipants.length})
            </h2>
            <p className="text-xs text-wo-text-muted">
              Această rulare poate cuprinde mai multe planuri/comenzi. Nu aparține unui singur
              plan.
            </p>
            {ADD_UI === "DEFERRED" && detail.status === "HELD" ? (
              <p className="text-xs text-wo-text-muted" data-testid="machine-run-add-deferred">
                Adăugarea de participanți din UI este amânată (fără API de candidați eligibili).
              </p>
            ) : null}
            {activeParticipants.length === 0 ? (
              <p className="text-sm text-wo-text-muted">Niciun participant activ.</p>
            ) : (
              <ul className="divide-y divide-wo-border rounded border border-wo-border">
                {activeParticipants.map((p) => (
                  <li
                    key={p.participant_id}
                    className="flex flex-wrap items-center justify-between gap-2 px-3 py-2"
                    data-testid={`machine-run-participant-${p.participant_id}`}
                  >
                    <div className="min-w-0 text-sm">
                      <p className="font-medium text-wo-text-primary">{p.task_key}</p>
                      <p className="text-xs text-wo-text-muted">
                        Comandă {p.order_id} · Plan {p.execution_plan_id}
                        {p.operation_code ? ` · ${p.operation_code}` : ""}
                        {p.workcenter ? ` · ${p.workcenter}` : ""}
                      </p>
                    </div>
                    {actions.some((a) => a.action === "remove_participant") ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={busy || activeParticipants.length <= 2}
                        onClick={() => void runCommand("remove_participant", p)}
                        className="border-wo-border text-wo-text-primary"
                        data-testid={`machine-run-remove-${p.participant_id}`}
                      >
                        Elimină
                      </Button>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* Secondary provenance / diagnostics */}
          <section className="space-y-2 rounded-md border border-wo-border bg-wo-surface-raised p-4">
            <h2 className="text-sm font-semibold text-wo-text-primary">Proveniență</h2>
            <dl className="grid gap-2 text-xs text-wo-text-muted sm:grid-cols-2">
              <div>
                <dt className="text-wo-text-dim">Planuri / comenzi</dt>
                <dd className="text-wo-text-primary">
                  {planOrderSummary(detail.order_ids, detail.execution_plan_ids)}
                </dd>
              </div>
              <div>
                <dt className="text-wo-text-dim">Rezervare</dt>
                <dd className="text-wo-text-primary">
                  #{detail.reservation.reservation_id} · {detail.reservation.status} · v
                  {detail.reservation.version}
                </dd>
              </div>
              <div>
                <dt className="text-wo-text-dim">Versiune rulare</dt>
                <dd className="text-wo-text-primary">v{detail.version}</dd>
              </div>
              <div>
                <dt className="text-wo-text-dim">Cod utilaj</dt>
                <dd className="text-wo-text-primary">{detail.machine.machine_code}</dd>
              </div>
            </dl>

            {removedParticipants.length > 0 ? (
              <div className="pt-2">
                <button
                  type="button"
                  className="text-xs text-wo-info hover:underline"
                  onClick={() => setShowRemoved((v) => !v)}
                  data-testid="machine-run-toggle-removed"
                >
                  {showRemoved ? "Ascunde" : "Arată"} istoric participanți eliminați (
                  {removedParticipants.length})
                </button>
                {showRemoved ? (
                  <ul className="mt-2 space-y-1 text-xs text-wo-text-muted">
                    {removedParticipants.map((p) => (
                      <li key={p.participant_id}>
                        {p.task_key} · comandă {p.order_id} · plan {p.execution_plan_id} (eliminat)
                      </li>
                    ))}
                  </ul>
                ) : null}
              </div>
            ) : null}
          </section>
        </>
      ) : null}
    </div>
  );
}
