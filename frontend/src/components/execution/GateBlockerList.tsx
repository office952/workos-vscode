/**
 * S30 — Gate Blocker List (read-only).
 *
 * Renders active blockers from the gate evaluation.
 * BLK-12/13/15/16/17 are ProductSystem Operational Linkage blockers.
 * Read-only: no mutations, no resolve buttons.
 */

import { XCircle } from "lucide-react";
import type { GateBlocker } from "@/types/gate.types";

interface GateBlockerListProps {
  blockers: GateBlocker[];
}

// Human-readable labels for known blocker codes
const BLOCKER_LABELS: Record<string, string> = {
  "BLK-01": "Plan deja existent",
  "BLK-02": "Snapshot incomplet",
  "BLK-03": "Produs nedefinit",
  "BLK-04": "Cantitate invalidă",
  "BLK-05": "Material nedefinit",
  "BLK-06": "Mașină nedefinită",
  "BLK-07": "Skill necunoscut în registru",
  "BLK-08": "Workcenter necunoscut în registru",
  "BLK-09": "Task fără skill-uri",
  "BLK-10": "Task fără mașină/workcenter",
  "BLK-11": "Operație fără task-uri",
  "BLK-12": "Task — skill-uri lipsă (ProductSystem)",
  "BLK-13": "Task — mașină/workcenter lipsă (ProductSystem)",
  "BLK-14": "Material necunoscut în registru (deferred)",
  "BLK-15": "Task fără operație sursă (ProductSystem)",
  "BLK-16": "Cod skill inexistent în registru (ProductSystem)",
  "BLK-17": "Cod workcenter inexistent în registru (ProductSystem)",
  "BLK-18": "Stoc material depășit (deferred)",
  "BLK-19": "Capacitate mașină depășită (deferred)",
  "BLK-20": "Rol necunoscut",
  "BLK-21": "Configurație lipsă",
};

// ProductSystem operational linkage group
const PS_LINKAGE_CODES = ["BLK-12", "BLK-13", "BLK-15", "BLK-16", "BLK-17"];

export function GateBlockerList({ blockers }: GateBlockerListProps) {
  const sorted = [...blockers].sort((a, b) => a.code.localeCompare(b.code));
  const psBlockers = sorted.filter((b) => PS_LINKAGE_CODES.includes(b.code));
  const otherBlockers = sorted.filter((b) => !PS_LINKAGE_CODES.includes(b.code));

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <XCircle className="w-4 h-4 text-red-400" />
        <h3 className="text-[12px] font-bold text-red-300 uppercase tracking-wide">
          Blockers ({blockers.length})
        </h3>
      </div>

      {/* ProductSystem Operational Linkage group */}
      {psBlockers.length > 0 && (
        <div className="space-y-2">
          <p className="text-[10px] text-slate-500 uppercase tracking-wide pl-1">
            ProductSystem Operational Linkage
          </p>
          {psBlockers.map((b, idx) => (
            <BlockerCard key={`ps-${b.code}-${idx}`} blocker={b} />
          ))}
        </div>
      )}

      {/* Other blockers */}
      {otherBlockers.length > 0 && (
        <div className="space-y-2">
          {psBlockers.length > 0 && (
            <p className="text-[10px] text-slate-500 uppercase tracking-wide pl-1">
              Gate Blockers
            </p>
          )}
          {otherBlockers.map((b, idx) => (
            <BlockerCard key={`other-${b.code}-${idx}`} blocker={b} />
          ))}
        </div>
      )}
    </div>
  );
}

function BlockerCard({ blocker }: { blocker: GateBlocker }) {
  const label = BLOCKER_LABELS[blocker.code] ?? blocker.code;
  const taskRef =
    typeof blocker.task_ref?.task_template_id === "string"
      ? blocker.task_ref.task_template_id
      : null;
  const sourcePsCode =
    typeof blocker.details?.source_ps_code === "string"
      ? blocker.details.source_ps_code
      : null;

  return (
    <div className="bg-red-900/10 border border-red-800/40 rounded-md px-3 py-2 space-y-1">
      <div className="flex items-center gap-2">
        <span className="inline-block px-1.5 py-0.5 text-[10px] font-bold rounded bg-red-900/60 text-red-300 border border-red-700">
          {blocker.code}
        </span>
        <span className="text-[12px] text-red-200 font-medium">{label}</span>
        {taskRef && (
          <span className="text-[10px] text-slate-400 bg-slate-800 px-1.5 py-0.5 rounded font-mono">
            {taskRef}
          </span>
        )}
      </div>
      <p className="text-[11px] text-slate-300 pl-1">{blocker.message}</p>
      {sourcePsCode && (
        <p className="text-[10px] text-slate-500 pl-1">
          Sursă: <code className="text-slate-400">{sourcePsCode}</code>
        </p>
      )}
    </div>
  );
}