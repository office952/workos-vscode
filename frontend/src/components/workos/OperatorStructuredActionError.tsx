import {
  blockerLabelFromStructured,
  structuredErrorHeadline,
  type StructuredActionError,
} from "@/lib/operatorProductionBlockerPresentation";
import { AlertTriangle } from "lucide-react";

type Props = {
  error: StructuredActionError | null;
  taskLabel?: string | null;
  testId?: string;
};

export function OperatorStructuredActionError({ error, taskLabel, testId }: Props) {
  if (!error) return null;

  return (
    <div
      role="alert"
      className="rounded-md border border-red-800/60 bg-red-950/25 px-3 py-2 space-y-1.5"
      data-testid={testId || "operator-structured-action-error"}
    >
      <div className="flex items-start gap-2">
        <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
        <div className="min-w-0">
          <p className="text-[12px] font-semibold text-red-200">{structuredErrorHeadline(error)}</p>
          {taskLabel ? (
            <p className="text-[10px] text-slate-400 mt-0.5">Task: {taskLabel}</p>
          ) : null}
          <p className="text-[11px] text-red-100/90 mt-1">{error.message}</p>
          {error.readinessLabel ? (
            <p className="text-[10px] text-amber-200/90 mt-1">Readiness: {error.readinessLabel}</p>
          ) : null}
          {error.blockers.length > 0 ? (
            <ul className="mt-1.5 space-y-1">
              {error.blockers.map((blocker, idx) => {
                const code = typeof blocker.code === "string" ? blocker.code : `blocker-${idx}`;
                return (
                  <li key={code} className="text-[10px] text-red-100/80">
                    · {blockerLabelFromStructured(blocker)}
                  </li>
                );
              })}
            </ul>
          ) : null}
          <p className="text-[9px] text-slate-500 mt-1">
            HTTP {error.httpStatus} · <span className="font-mono">{error.rawCode}</span>
          </p>
        </div>
      </div>
    </div>
  );
}
