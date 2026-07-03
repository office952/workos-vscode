/**
 * S30 — Gate Warning List (read-only).
 *
 * Renders warnings from the gate evaluation.
 * BLK-14/18/19 are displayed here as WRN-02/WRN-03 (unresolved, deferred).
 * Read-only: no mutations, no dismiss buttons.
 */

import { AlertTriangle } from "lucide-react";
import type { GateWarning } from "@/types/gate.types";

interface GateWarningListProps {
  warnings: GateWarning[];
}

// Human-readable labels for known warning codes
const WARNING_LABELS: Record<string, string> = {
  "WRN-01": "Registru indisponibil (degradare grațioasă)",
  "WRN-02": "Materials Registry (M22) nu este încă live — BLK-14/BLK-18 deferred",
  "WRN-03": "Machines Registry (M19) nu este încă live — BLK-19 deferred",
};

export function GateWarningList({ warnings }: GateWarningListProps) {
  const sorted = [...warnings].sort((a, b) => a.code.localeCompare(b.code));

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-amber-400" />
        <h3 className="text-[12px] font-bold text-amber-300 uppercase tracking-wide">
          Warnings ({warnings.length})
        </h3>
      </div>

      {sorted.map((w, idx) => (
        <WarningCard key={`${w.code}-${idx}`} warning={w} />
      ))}
    </div>
  );
}

function WarningCard({ warning }: { warning: GateWarning }) {
  const label = WARNING_LABELS[warning.code] ?? warning.code;

  return (
    <div className="bg-amber-900/10 border border-amber-800/40 rounded-md px-3 py-2 space-y-1">
      <div className="flex items-center gap-2">
        <span className="inline-block px-1.5 py-0.5 text-[10px] font-bold rounded bg-amber-900/60 text-amber-300 border border-amber-700">
          {warning.code}
        </span>
        <span className="text-[12px] text-amber-200 font-medium">{label}</span>
      </div>
      <p className="text-[11px] text-slate-300 pl-1">{warning.message}</p>
    </div>
  );
}