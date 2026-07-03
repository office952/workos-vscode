import { useState } from "react";
import { HelpCircle, Loader2 } from "lucide-react";
import {
  createEmployeeMobileTaskClarification,
  type TaskClarificationRequestDTO,
} from "@/api/employeeMobileTaskClarifications";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import {
  EmployeeMobileErrorState,
  EmployeeMobileSuccessState,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import { emSecondaryLinkClass } from "@/lib/employeeMobileDesignTokens";
import { emV2Controls } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";

export default function EmployeeMobileTaskClarificationPanel({
  task,
  onSubmitted,
  variant = "card",
  visualVariant = "v1",
}: {
  task: EmployeeMobileTaskDTO;
  onSubmitted: () => Promise<void>;
  variant?: "card" | "footer";
  visualVariant?: "v1" | "v2";
}) {
  const openRequest = task.clarification_request as TaskClarificationRequestDTO | null | undefined;
  const hasOpen = openRequest?.status === "open";
  const footer = variant === "footer";
  const isV2 = visualVariant === "v2";
  const openFormClass = isV2 ? emV2Controls.textAction : emSecondaryLinkClass();

  const [expanded, setExpanded] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const submit = async () => {
    const trimmed = message.trim();
    if (!trimmed) {
      setError("Scrie pe scurt ce informații ai nevoie.");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const created = await createEmployeeMobileTaskClarification(task.task_id, task.order_id, trimmed);
      setSuccess(
        created.routed_to_responsible
          ? "Solicitarea a fost trimisă către responsabilul comenzii."
          : "Solicitarea a fost trimisă.",
      );
      setMessage("");
      setExpanded(false);
      await onSubmitted();
    } catch (err) {
      const e = err as Error & { status?: number; payload?: { error?: string } };
      if (e.status === 409 || e.payload?.error === "open_clarification_exists") {
        setSuccess("Solicitare de informații trimisă.");
        setExpanded(false);
        await onSubmitted();
        return;
      }
      setError(e instanceof Error ? e.message : "Nu am putut trimite solicitarea.");
    } finally {
      setLoading(false);
    }
  };

  const form = expanded ? (
    <div className="space-y-2 pt-1" data-testid="employee-mobile-task-clarification-form">
      <label className="block text-sm text-slate-300" htmlFor="employee-mobile-clarification-message">
        Mesaj
      </label>
      <textarea
        id="employee-mobile-clarification-message"
        value={message}
        onChange={(event) => setMessage(event.target.value)}
        rows={3}
        required
        placeholder="Scrie ce lipsește sau ce trebuie clarificat..."
        className="w-full rounded-lg border border-[#243044] bg-[#070B14] px-3 py-2.5 text-base text-slate-100"
        data-testid="employee-mobile-task-clarification-message"
      />
      <div className="flex gap-2">
        <button
          type="button"
          disabled={loading || !message.trim()}
          onClick={() => void submit()}
          className={cn(
            "flex-1 min-h-[44px] rounded-lg text-base font-semibold text-white hover:bg-blue-600 disabled:opacity-50",
            isV2 ? emV2Controls.primaryAction : "rounded-xl bg-blue-700",
          )}
          data-testid="employee-mobile-task-clarification-submit"
        >
          {loading ? (
            <span className="inline-flex items-center justify-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              Se trimite…
            </span>
          ) : (
            "Trimite solicitarea"
          )}
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={() => {
            setExpanded(false);
            setError(null);
          }}
          className={cn(
            "min-h-[44px] rounded-lg border border-[#243044] px-3 text-sm text-slate-400",
            isV2 && "border-[#1E293B]",
          )}
          data-testid="employee-mobile-task-clarification-cancel"
        >
          Anulează
        </button>
      </div>
    </div>
  ) : null;

  if (footer) {
    return (
      <div className="space-y-2" data-testid="employee-mobile-task-clarification">
        {hasOpen ? (
          <p
            className="text-sm text-amber-300/90 px-1"
            data-testid="employee-mobile-task-clarification-open"
          >
            Solicitare de informații trimisă
          </p>
        ) : null}
        {error ? (
          <EmployeeMobileErrorState message={error} testId="employee-mobile-task-clarification-error" />
        ) : null}
        {success ? (
          <EmployeeMobileSuccessState
            message={success}
            testId="employee-mobile-task-clarification-success"
          />
        ) : null}
        {!hasOpen && !expanded ? (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className={openFormClass}
            data-testid="employee-mobile-task-clarification-open-form"
          >
            <HelpCircle className="w-4 h-4" aria-hidden />
            Cer clarificare
          </button>
        ) : null}
        {form}
      </div>
    );
  }

  return (
    <section
      className="rounded-xl border border-[#243044] bg-[#0A1020]/60 px-3.5 py-3 space-y-2"
      data-testid="employee-mobile-task-clarification"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-200">Ai nevoie de detalii?</h3>
          {hasOpen && (
            <p
              className="text-sm text-amber-300 mt-1"
              data-testid="employee-mobile-task-clarification-open"
            >
              Solicitare de informații trimisă
            </p>
          )}
        </div>
        {!hasOpen && !expanded && (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className={cn(openFormClass, !isV2 && "shrink-0 px-3 border border-[#243044] rounded-lg")}
            data-testid="employee-mobile-task-clarification-open-form"
          >
            <HelpCircle className="w-4 h-4" aria-hidden />
            Solicit informații
          </button>
        )}
      </div>

      {error && (
        <EmployeeMobileErrorState message={error} testId="employee-mobile-task-clarification-error" />
      )}
      {success && (
        <EmployeeMobileSuccessState
          message={success}
          testId="employee-mobile-task-clarification-success"
        />
      )}

      {!hasOpen && form}
    </section>
  );
}
