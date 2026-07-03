/**
 * S30 — Gate Trace Source panel (read-only, collapsible).
 *
 * Displays which registries were consulted during gate evaluation.
 * Read-only: no mutations.
 */

import { useState } from "react";
import { ChevronRight, ChevronDown, Database } from "lucide-react";
import type { GateTraceSource } from "@/types/gate.types";

interface GateTraceSourcePanelProps {
  traceSource: GateTraceSource;
}

export function GateTraceSourcePanel({ traceSource }: GateTraceSourcePanelProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-[#2A3548] rounded-md">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
        <Database className="w-3 h-3" />
        <span className="font-medium uppercase tracking-wide">Trace Source</span>
        <span className="text-slate-600 ml-auto text-[10px]">
          {traceSource.gate_spec_version}
        </span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2 text-[11px] border-t border-[#2A3548] pt-2">
          {/* Order info */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-[#0D1321] rounded px-2 py-1.5 border border-[#1F2A44]">
              <p className="text-slate-500 text-[9px] uppercase">Order ID</p>
              <p className="text-slate-300 font-mono">{traceSource.order.id}</p>
            </div>
            <div className="bg-[#0D1321] rounded px-2 py-1.5 border border-[#1F2A44]">
              <p className="text-slate-500 text-[9px] uppercase">Order Code</p>
              <p className="text-slate-300 font-mono">{traceSource.order.code}</p>
            </div>
            <div className="bg-[#0D1321] rounded px-2 py-1.5 border border-[#1F2A44]">
              <p className="text-slate-500 text-[9px] uppercase">Snapshot</p>
              <p className="text-slate-300 font-mono">
                v{traceSource.order.snapshot_version ?? "—"}
              </p>
            </div>
          </div>

          {/* Product */}
          <div className="bg-[#0D1321] rounded px-2 py-1.5 border border-[#1F2A44]">
            <p className="text-slate-500 text-[9px] uppercase">Product</p>
            <p className="text-slate-300 font-mono">
              {traceSource.product.product_id ?? "null"}{" "}
              <span className="text-slate-500">
                (din {traceSource.product.source})
              </span>
            </p>
          </div>

          {/* Registries consulted */}
          <div>
            <p className="text-slate-500 text-[9px] uppercase mb-1">
              Registre consultate ({traceSource.registries_consulted.length})
            </p>
            {traceSource.registries_consulted.length === 0 ? (
              <p className="text-slate-500 text-[10px]">—</p>
            ) : (
              <div className="space-y-1">
                {traceSource.registries_consulted.map((r, idx) => (
                  <div
                    key={`${r.name}-${idx}`}
                    className="flex items-center gap-2 bg-[#0D1321] rounded px-2 py-1 border border-[#1F2A44]"
                  >
                    <span className="text-emerald-400 font-mono text-[10px]">
                      {r.name}
                    </span>
                    <span className="text-slate-500 text-[10px]">{r.endpoint}</span>
                    <span className="text-slate-600 text-[10px] ml-auto">
                      {r.version}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Registries unavailable */}
          {traceSource.registries_unavailable.length > 0 && (
            <div>
              <p className="text-slate-500 text-[9px] uppercase mb-1">
                Registre indisponibile ({traceSource.registries_unavailable.length})
              </p>
              <div className="flex flex-wrap gap-1.5">
                {traceSource.registries_unavailable.map((name) => (
                  <span
                    key={name}
                    className="inline-block px-1.5 py-0.5 text-[10px] font-mono rounded bg-amber-900/30 text-amber-300 border border-amber-800/40"
                  >
                    {name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}