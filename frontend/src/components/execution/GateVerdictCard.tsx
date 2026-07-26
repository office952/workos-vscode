/**
 * S30 — Gate Verdict Card (read-only).
 *
 * Displays the gate evaluation status for an order.
 * Read-only: no mutations, no forms, no POST/PUT/PATCH/DELETE.
 */

import { ShieldCheck, ShieldX, RefreshCw } from "lucide-react";
import type { GateEvaluation } from "@/types/gate.types";
import { GateBlockerList } from "./GateBlockerList";
import { GateWarningList } from "./GateWarningList";
import { GateTraceSourcePanel } from "./GateTraceSource";

interface GateVerdictCardProps {
  gate: GateEvaluation;
  loading: boolean;
  onRefresh: () => void;
}

function fmtDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleString("ro-RO");
  } catch {
    return value;
  }
}

export function GateVerdictCard({ gate, loading, onRefresh }: GateVerdictCardProps) {
  const isReady = gate.can_generate;

  return (
    <section className="bg-wo-surface-raised border border-wo-border-strong rounded-lg">
      <header className="flex items-center justify-between px-4 py-3 border-b border-wo-border-strong">
        <div className="flex items-center gap-2">
          {isReady ? (
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          ) : (
            <ShieldX className="w-4 h-4 text-red-400" />
          )}
          <h2 className="text-[13px] font-bold text-slate-200 uppercase tracking-wide">
            Poarta Generare Plan
          </h2>
        </div>
        <div className="flex items-center gap-3">
          <span
            className={`inline-block px-2.5 py-0.5 text-[11px] font-bold rounded border ${
              isReady
                ? "bg-emerald-900/40 text-emerald-300 border-emerald-700"
                : "bg-red-900/40 text-red-300 border-red-700"
            }`}
          >
            {isReady ? "READY" : "BLOCKED"}
          </span>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] font-medium rounded bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-slate-300 transition-colors"
            title="Reîmprospătare gate"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </header>

      <div className="p-4 space-y-4">
        {/* Summary row */}
        <div className="grid grid-cols-4 gap-2 text-[11px]">
          <div className="bg-wo-surface-raised rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Evaluat la</p>
            <p className="mt-1 text-slate-300 font-semibold">
              {fmtDateTime(gate.evaluated_at)}
            </p>
          </div>
          <div className="bg-wo-surface-raised rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Blockers</p>
            <p className={`mt-1 font-bold ${gate.blockers.length > 0 ? "text-red-300" : "text-emerald-300"}`}>
              {gate.blockers.length}
            </p>
          </div>
          <div className="bg-wo-surface-raised rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Warnings</p>
            <p className={`mt-1 font-bold ${gate.warnings.length > 0 ? "text-amber-300" : "text-slate-400"}`}>
              {gate.warnings.length}
            </p>
          </div>
          <div className="bg-wo-surface-raised rounded px-2.5 py-2 border border-[#1F2A44]">
            <p className="text-slate-500 uppercase text-[9px] tracking-wide">Acțiune</p>
            <p className="mt-1 text-slate-300 text-[10px]">
              {gate.required_next_action || "—"}
            </p>
          </div>
        </div>

        {/* Blockers */}
        {gate.blockers.length > 0 && (
          <GateBlockerList blockers={gate.blockers} />
        )}

        {/* Warnings */}
        {gate.warnings.length > 0 && (
          <GateWarningList warnings={gate.warnings} />
        )}

        {/* No blockers state */}
        {gate.blockers.length === 0 && (
          <div className="flex items-center gap-2 bg-emerald-900/20 border border-emerald-800/60 rounded-md px-3 py-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <p className="text-[12px] text-emerald-200">
              Niciun blocker activ — planul poate fi generat.
            </p>
          </div>
        )}

        {/* Trace source */}
        <GateTraceSourcePanel traceSource={gate.trace_source} />
      </div>
    </section>
  );
}