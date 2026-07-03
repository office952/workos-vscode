import { AlertTriangle } from "lucide-react";

export interface WorkspaceAlertsProps {
  statusConflict?: boolean;
  error?: string | null;
  persistError?: string | null;
  source?: string;
}

export default function WorkspaceAlerts({
  statusConflict,
  error,
  persistError,
  source,
}: WorkspaceAlertsProps) {
  return (
    <>
      {statusConflict && (
        <div
          className="flex items-start gap-2 px-3 py-2 bg-amber-900/20 border border-amber-800/40 rounded-lg"
          data-testid="status-readiness-conflict"
        >
          <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-amber-300">
            Statusul salvat pare mai avansat decât datele completate.
          </p>
        </div>
      )}
      {error && source !== "mock" && (
        <div className="flex items-start gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-red-300">{error}</p>
        </div>
      )}
      {persistError && (
        <div className="flex items-start gap-2 px-3 py-2 bg-red-900/20 border border-red-800/40 rounded-lg">
          <AlertTriangle className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
          <p className="text-[11px] text-red-300">{persistError}</p>
        </div>
      )}
    </>
  );
}
