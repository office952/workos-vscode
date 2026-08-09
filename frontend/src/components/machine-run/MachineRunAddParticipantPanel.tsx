/**
 * ADD participant — HELD + manage + candidate-participants API.
 * Respects mutation_allowed; single-task add; server-confirmed + refetch.
 */
import { useCallback, useEffect, useState } from "react";
import {
  addMachineRunParticipant,
  listMachineRunAddCandidates,
  MachineRunRequestError,
  type MachineRunCandidateTask,
} from "@/api/machineRuns";
import { Button } from "@/components/ui/button";
import {
  candidateDisplayLabel,
  candidateSelectionKey,
  mapMachineRunError,
} from "@/lib/machineRunUi";

export function MachineRunAddParticipantPanel({
  machineRunId,
  expectedVersion,
  visible,
  onAdded,
}: {
  machineRunId: number;
  expectedVersion: number;
  /** Parent gates: HELD + manage permission. */
  visible: boolean;
  onAdded: () => void | Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<"idle" | "loading" | "ready" | "empty" | "blocked" | "error">(
    "idle",
  );
  const [items, setItems] = useState<MachineRunCandidateTask[]>([]);
  const [blockMessage, setBlockMessage] = useState<string | null>(null);
  const [error, setError] = useState<{ message: string; nextAction: string } | null>(
    null,
  );
  const [picked, setPicked] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setState("loading");
    setError(null);
    setPicked(null);
    try {
      const result = await listMachineRunAddCandidates(machineRunId);
      if (!result.mutation_allowed) {
        setItems([]);
        setState("blocked");
        setBlockMessage(
          result.message?.trim() ||
            "Adăugarea nu este permisă în starea actuală a rulării.",
        );
        return;
      }
      setItems(result.items);
      setState(result.items.length === 0 ? "empty" : "ready");
      setBlockMessage(null);
    } catch (err) {
      setItems([]);
      setState("error");
      const code = err instanceof MachineRunRequestError ? err.code : "request_failed";
      const mapped = mapMachineRunError(
        code,
        err instanceof Error ? err.message : undefined,
      );
      setError({ message: mapped.message, nextAction: mapped.nextAction });
    }
  }, [machineRunId]);

  useEffect(() => {
    if (!visible) {
      setOpen(false);
      setState("idle");
      return;
    }
    if (open) void load();
  }, [visible, open, load]);

  if (!visible) return null;

  const submit = async () => {
    if (!picked) return;
    const candidate = items.find(
      (c) => candidateSelectionKey(c.execution_plan_id, c.task_key) === picked,
    );
    if (!candidate) return;
    setBusy(true);
    setError(null);
    try {
      await addMachineRunParticipant(machineRunId, {
        expected_version: expectedVersion,
        execution_plan_id: candidate.execution_plan_id,
        task_key: candidate.task_key,
      });
      setOpen(false);
      setPicked(null);
      await onAdded();
    } catch (err) {
      const code = err instanceof MachineRunRequestError ? err.code : "request_failed";
      const mapped = mapMachineRunError(
        code,
        err instanceof Error ? err.message : undefined,
      );
      setError({ message: mapped.message, nextAction: mapped.nextAction });
      void load();
      if (mapped.isCasStale) {
        await onAdded();
      }
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-2" data-testid="machine-run-add-panel">
      {!open ? (
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="border-wo-border text-wo-text-primary"
          onClick={() => setOpen(true)}
          data-testid="machine-run-add-open"
        >
          Adaugă participant
        </Button>
      ) : (
        <div
          className="space-y-2 rounded border border-wo-border bg-wo-surface p-3"
          data-testid="machine-run-add-picker"
        >
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-wo-text-primary">
              Adaugă un task eligibil
            </p>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              disabled={busy}
              onClick={() => {
                setOpen(false);
                setError(null);
              }}
            >
              Închide
            </Button>
          </div>

          {state === "loading" ? (
            <p className="text-sm text-wo-text-muted">Se încarcă candidații…</p>
          ) : null}
          {state === "blocked" ? (
            <p className="text-sm text-wo-text-muted" data-testid="machine-run-add-blocked">
              {blockMessage}
            </p>
          ) : null}
          {state === "empty" ? (
            <p
              className="text-sm text-wo-text-muted"
              data-testid="machine-run-add-empty"
            >
              Nu există taskuri eligibile pentru acest utilaj.
            </p>
          ) : null}
          {state === "error" && error ? (
            <p className="text-sm text-wo-error" role="alert">
              {error.message}
            </p>
          ) : null}
          {state === "ready" ? (
            <ul className="max-h-48 space-y-1 overflow-y-auto">
              {items.map((c) => {
                const k = candidateSelectionKey(c.execution_plan_id, c.task_key);
                return (
                  <li key={k}>
                    <label
                      className="flex cursor-pointer items-start gap-2 rounded px-1.5 py-1 hover:bg-wo-surface-inset"
                      data-testid={`machine-run-add-candidate-${k}`}
                    >
                      <input
                        type="radio"
                        name="machine-run-add-pick"
                        checked={picked === k}
                        disabled={busy}
                        onChange={() => setPicked(k)}
                      />
                      <span className="min-w-0">
                        <span className="block text-sm font-medium text-wo-text-primary">
                          {candidateDisplayLabel(c)}
                        </span>
                        <span className="block text-[11px] text-wo-text-muted">
                          Comandă {c.order_id} · Plan {c.execution_plan_id}
                          {c.workcenter ? ` · ${c.workcenter}` : ""}
                        </span>
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
          ) : null}

          {error && state !== "error" ? (
            <div
              className="rounded-md border border-wo-error/35 bg-wo-error-muted px-3 py-2 text-sm text-wo-error"
              role="alert"
              data-testid="machine-run-add-error"
            >
              <p>{error.message}</p>
              <p className="mt-0.5 text-xs opacity-90">{error.nextAction}</p>
            </div>
          ) : null}

          {state === "ready" ? (
            <Button
              type="button"
              size="sm"
              disabled={!picked || busy}
              onClick={() => void submit()}
              data-testid="machine-run-add-submit"
            >
              {busy ? "Se adaugă…" : "Adaugă"}
            </Button>
          ) : null}
        </div>
      )}
    </div>
  );
}
