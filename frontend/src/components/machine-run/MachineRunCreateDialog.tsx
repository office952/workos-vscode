/**
 * CREATE MachineRun — machine → candidate API → ≥2 tasks → window → POST → detail.
 * Eligibility is backend-only; UI never reconstructs rules.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  createMachineRun,
  listMachineRunCreateCandidates,
  listMachinesForPicker,
  MachineRunRequestError,
  type MachinePickerRow,
  type MachineRunCandidateTask,
} from "@/api/machineRuns";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DEFAULT_MACHINE_RUN_TIMEZONE,
  MIN_CREATE_PARTICIPANTS,
  candidateDisplayLabel,
  candidateSelectionKey,
  mapMachineRunError,
} from "@/lib/machineRunUi";

function toLocalInputValue(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function fromLocalInputValue(local: string): string {
  return new Date(local).toISOString();
}

function defaultWindow(): { start: string; end: string } {
  const start = new Date();
  start.setMinutes(0, 0, 0);
  start.setHours(start.getHours() + 1);
  const end = new Date(start);
  end.setHours(end.getHours() + 2);
  return { start: toLocalInputValue(start), end: toLocalInputValue(end) };
}

type CandidateGroup = {
  key: string;
  orderId: number;
  planId: number;
  items: MachineRunCandidateTask[];
};

export function MachineRunCreateDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const navigate = useNavigate();
  const [machines, setMachines] = useState<MachinePickerRow[]>([]);
  const [machinesLoading, setMachinesLoading] = useState(false);
  const [machineId, setMachineId] = useState<number | "">("");
  const [candidates, setCandidates] = useState<MachineRunCandidateTask[]>([]);
  const [candidatesState, setCandidatesState] = useState<
    "idle" | "loading" | "ready" | "empty" | "error"
  >("idle");
  const [candidatesError, setCandidatesError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [windowLocal, setWindowLocal] = useState(defaultWindow);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<{
    message: string;
    nextAction: string;
  } | null>(null);

  const resetForm = useCallback(() => {
    setMachineId("");
    setCandidates([]);
    setCandidatesState("idle");
    setCandidatesError(null);
    setSelected(new Set());
    setWindowLocal(defaultWindow());
    setFormError(null);
    setSubmitting(false);
  }, []);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    setMachinesLoading(true);
    void listMachinesForPicker()
      .then((rows) => {
        if (cancelled) return;
        setMachines(rows.filter((m) => m.is_active));
      })
      .catch(() => {
        if (cancelled) return;
        setMachines([]);
        setFormError({
          message: "Nu am putut încărca lista de utilaje.",
          nextAction: "Închide și reîncearcă.",
        });
      })
      .finally(() => {
        if (!cancelled) setMachinesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const loadCandidates = useCallback(async (mid: number) => {
    setCandidatesState("loading");
    setCandidatesError(null);
    setSelected(new Set());
    try {
      const result = await listMachineRunCreateCandidates({ machine_id: mid });
      setCandidates(result.items);
      setCandidatesState(result.items.length === 0 ? "empty" : "ready");
    } catch (err) {
      setCandidates([]);
      setCandidatesState("error");
      const code = err instanceof MachineRunRequestError ? err.code : "request_failed";
      const mapped = mapMachineRunError(
        code,
        err instanceof Error ? err.message : undefined,
      );
      setCandidatesError(mapped.message);
    }
  }, []);

  useEffect(() => {
    if (!open || machineId === "") {
      setCandidates([]);
      setCandidatesState("idle");
      return;
    }
    void loadCandidates(Number(machineId));
  }, [open, machineId, loadCandidates]);

  const groups = useMemo((): CandidateGroup[] => {
    const map = new Map<string, CandidateGroup>();
    for (const c of candidates) {
      const key = `o${c.order_id}-p${c.execution_plan_id}`;
      let g = map.get(key);
      if (!g) {
        g = {
          key,
          orderId: c.order_id,
          planId: c.execution_plan_id,
          items: [],
        };
        map.set(key, g);
      }
      g.items.push(c);
    }
    return Array.from(map.values()).sort(
      (a, b) => a.orderId - b.orderId || a.planId - b.planId,
    );
  }, [candidates]);

  const selectedCount = selected.size;
  const canSubmit =
    machineId !== "" &&
    selectedCount >= MIN_CREATE_PARTICIPANTS &&
    Boolean(windowLocal.start) &&
    Boolean(windowLocal.end) &&
    !submitting;

  const toggle = (c: MachineRunCandidateTask) => {
    const k = candidateSelectionKey(c.execution_plan_id, c.task_key);
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  };

  const handleSubmit = async () => {
    if (!canSubmit || machineId === "") return;
    setSubmitting(true);
    setFormError(null);
    const participants = candidates
      .filter((c) =>
        selected.has(candidateSelectionKey(c.execution_plan_id, c.task_key)),
      )
      .map((c) => ({
        execution_plan_id: c.execution_plan_id,
        task_key: c.task_key,
      }));
    try {
      const result = await createMachineRun({
        machine_id: Number(machineId),
        reservation_start: fromLocalInputValue(windowLocal.start),
        reservation_end: fromLocalInputValue(windowLocal.end),
        timezone: DEFAULT_MACHINE_RUN_TIMEZONE,
        participants,
      });
      onOpenChange(false);
      resetForm();
      navigate(`/execution/machine-runs/${result.machine_run_id}`);
    } catch (err) {
      const code = err instanceof MachineRunRequestError ? err.code : "request_failed";
      const mapped = mapMachineRunError(
        code,
        err instanceof Error ? err.message : undefined,
      );
      setFormError({ message: mapped.message, nextAction: mapped.nextAction });
      if (machineId !== "") {
        void loadCandidates(Number(machineId));
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) resetForm();
        onOpenChange(next);
      }}
    >
      <DialogContent
        className="max-h-[90vh] max-w-xl overflow-y-auto border-wo-border bg-wo-surface text-wo-text-primary"
        data-testid="machine-run-create-dialog"
      >
        <DialogHeader>
          <DialogTitle className="text-wo-text-primary">Rulare utilaj nouă</DialogTitle>
          <DialogDescription className="text-wo-text-muted">
            Alege utilajul, apoi taskurile eligibile returnate de sistem (minim{" "}
            {MIN_CREATE_PARTICIPANTS}, pot fi din comenzi/planuri diferite).
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <label className="block space-y-1 text-sm">
            <span className="text-wo-text-muted">Utilaj</span>
            <select
              className="w-full rounded-md border border-wo-border bg-wo-surface-raised px-2 py-1.5 text-sm text-wo-text-primary"
              value={machineId === "" ? "" : String(machineId)}
              disabled={machinesLoading || submitting}
              onChange={(e) => {
                const v = e.target.value;
                setMachineId(v === "" ? "" : Number(v));
                setFormError(null);
              }}
              data-testid="machine-run-create-machine"
            >
              <option value="">
                {machinesLoading ? "Se încarcă…" : "Selectează utilajul"}
              </option>
              {machines.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                  {m.machine_code ? ` (${m.machine_code})` : ""}
                </option>
              ))}
            </select>
          </label>

          {machineId !== "" ? (
            <div
              className="space-y-2"
              data-testid="machine-run-create-candidates"
              data-state={candidatesState}
            >
              <div className="flex items-baseline justify-between gap-2">
                <p className="text-sm font-medium text-wo-text-primary">
                  Taskuri eligibile
                </p>
                <p className="text-xs text-wo-text-muted">
                  Selectate: {selectedCount} / min. {MIN_CREATE_PARTICIPANTS}
                </p>
              </div>

              {candidatesState === "loading" ? (
                <p className="text-sm text-wo-text-muted">Se încarcă candidații…</p>
              ) : null}
              {candidatesState === "error" ? (
                <p className="text-sm text-wo-error" role="alert">
                  {candidatesError}
                </p>
              ) : null}
              {candidatesState === "empty" ? (
                <p
                  className="text-sm text-wo-text-muted"
                  data-testid="machine-run-create-candidates-empty"
                >
                  Nu există taskuri eligibile pentru acest utilaj.
                </p>
              ) : null}
              {candidatesState === "ready" ? (
                <div className="max-h-56 space-y-3 overflow-y-auto rounded border border-wo-border p-2">
                  {groups.map((g) => (
                    <div key={g.key} data-testid={`machine-run-create-group-${g.key}`}>
                      <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-wo-text-muted">
                        Comandă {g.orderId} · Plan {g.planId}
                      </p>
                      <ul className="space-y-1">
                        {g.items.map((c) => {
                          const k = candidateSelectionKey(
                            c.execution_plan_id,
                            c.task_key,
                          );
                          const checked = selected.has(k);
                          return (
                            <li key={k}>
                              <label
                                className="flex cursor-pointer items-start gap-2 rounded px-1.5 py-1 hover:bg-wo-surface-inset"
                                data-testid={`machine-run-create-candidate-${k}`}
                              >
                                <input
                                  type="checkbox"
                                  className="mt-0.5"
                                  checked={checked}
                                  disabled={submitting}
                                  onChange={() => toggle(c)}
                                />
                                <span className="min-w-0">
                                  <span className="block text-sm font-medium text-wo-text-primary">
                                    {candidateDisplayLabel(c)}
                                  </span>
                                  <span className="block text-[11px] text-wo-text-muted">
                                    {c.operation_code ? `${c.operation_code} · ` : ""}
                                    {c.workcenter ? `${c.workcenter} · ` : ""}
                                    <span className="font-mono opacity-70">
                                      {c.task_key.length > 40
                                        ? `${c.task_key.slice(0, 37)}…`
                                        : c.task_key}
                                    </span>
                                  </span>
                                </span>
                              </label>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block space-y-1 text-sm">
              <span className="text-wo-text-muted">Început rezervare</span>
              <input
                type="datetime-local"
                className="w-full rounded-md border border-wo-border bg-wo-surface-raised px-2 py-1.5 text-sm text-wo-text-primary"
                value={windowLocal.start}
                disabled={submitting}
                onChange={(e) =>
                  setWindowLocal((w) => ({ ...w, start: e.target.value }))
                }
                data-testid="machine-run-create-start"
              />
            </label>
            <label className="block space-y-1 text-sm">
              <span className="text-wo-text-muted">Sfârșit rezervare</span>
              <input
                type="datetime-local"
                className="w-full rounded-md border border-wo-border bg-wo-surface-raised px-2 py-1.5 text-sm text-wo-text-primary"
                value={windowLocal.end}
                disabled={submitting}
                onChange={(e) =>
                  setWindowLocal((w) => ({ ...w, end: e.target.value }))
                }
                data-testid="machine-run-create-end"
              />
            </label>
          </div>
          <p className="text-[11px] text-wo-text-muted">
            Fus orar organizație: {DEFAULT_MACHINE_RUN_TIMEZONE}
          </p>

          {formError ? (
            <div
              className="rounded-md border border-wo-error/35 bg-wo-error-muted px-3 py-2 text-sm text-wo-error"
              role="alert"
              data-testid="machine-run-create-error"
            >
              <p>{formError.message}</p>
              <p className="mt-0.5 text-xs opacity-90">{formError.nextAction}</p>
            </div>
          ) : null}
        </div>

        <DialogFooter className="gap-2">
          <Button
            type="button"
            variant="ghost"
            disabled={submitting}
            onClick={() => {
              resetForm();
              onOpenChange(false);
            }}
          >
            Renunță
          </Button>
          <Button
            type="button"
            disabled={!canSubmit}
            onClick={() => void handleSubmit()}
            data-testid="machine-run-create-submit"
          >
            {submitting ? "Se creează…" : "Creează rularea"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
