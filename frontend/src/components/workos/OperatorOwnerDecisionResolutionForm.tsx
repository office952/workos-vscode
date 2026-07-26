import { useState } from "react";
import type { OwnerDecisionSummaryItem } from "@/api/operatorTaskTruth";
import {
  OwnerDecisionResolutionError,
  RESOLUTION_NOTE_MIN_LENGTH,
  resolutionErrorHeadline,
  resolveOwnerDecision,
} from "@/api/executionOwnerDecisionRelease";
import { Loader2 } from "lucide-react";

type Props = {
  orderId: number;
  item: OwnerDecisionSummaryItem;
  onResolved: () => Promise<void>;
};

export function OperatorOwnerDecisionResolutionForm({
  orderId,
  item,
  onResolved,
}: Props) {
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<{
    idempotent: boolean;
    releaseStatus: string;
  } | null>(null);

  const alreadyResolved = item.operational_status === "resolved";
  const canSubmit =
    !submitting &&
    !alreadyResolved &&
    item.can_resolve &&
    note.trim().length >= RESOLUTION_NOTE_MIN_LENGTH;

  async function handleSubmit() {
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    setLastResult(null);
    try {
      const result = await resolveOwnerDecision(orderId, item.code, {
        status: "resolved",
        note: note.trim(),
      });
      setLastResult({
        idempotent: result.idempotent,
        releaseStatus: result.release_status,
      });
      if (!result.idempotent) {
        setNote("");
      }
      await onResolved();
    } catch (err) {
      if (err instanceof OwnerDecisionResolutionError) {
        setError(resolutionErrorHeadline(err));
      } else {
        setError(err instanceof Error ? err.message : "Eroare la rezolvare");
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (!item.can_resolve) return null;

  if (alreadyResolved) {
    return (
      <div
        className="mt-2 rounded border border-emerald-800/50 bg-emerald-950/20 px-2.5 py-2 text-[10px] text-emerald-200"
        data-testid={`owner-decision-resolved-state-${item.code}`}
      >
        Decizie rezolvata operational. Snapshot-ul inghetat ramane neschimbat.
      </div>
    );
  }

  return (
    <div
      className="mt-2 space-y-2 rounded border border-blue-900/40 bg-blue-950/15 px-2.5 py-2"
      data-testid={`owner-decision-resolve-form-${item.code}`}
    >
      <p className="text-[10px] font-semibold text-blue-200">Rezolvare operationala</p>
      <label className="block text-[10px] text-slate-400">
        Nota rezolvare (obligatorie, min. {RESOLUTION_NOTE_MIN_LENGTH} caractere)
        <textarea
          value={note}
          onChange={(e) => setNote(e.target.value)}
          rows={2}
          className="mt-1 w-full rounded border border-[#243044] bg-[#0A1020] px-2 py-1.5 text-[11px] text-slate-200 placeholder:text-slate-500"
          placeholder="Descrieti rezolvarea operationala..."
          data-testid={`owner-decision-resolve-note-${item.code}`}
        />
      </label>
      {error ? (
        <p className="text-[10px] text-red-300" data-testid={`owner-decision-resolve-error-${item.code}`}>
          {error}
        </p>
      ) : null}
      {lastResult ? (
        <p className="text-[10px] text-emerald-300" data-testid={`owner-decision-resolve-success-${item.code}`}>
          {lastResult.idempotent
            ? "Rezolvare deja inregistrata (idempotent)."
            : "Rezolvare inregistrata."}{" "}
          Status release: {lastResult.releaseStatus.replace(/_/g, " ")}.
        </p>
      ) : null}
      <button
        type="button"
        disabled={!canSubmit}
        onClick={() => void handleSubmit()}
        className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-semibold bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white transition-colors"
        data-testid={`owner-decision-resolve-submit-${item.code}`}
      >
        {submitting ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
        Rezolva decizia
      </button>
    </div>
  );
}
