/**
 * StockMovementsPanel — BUILD 16: Inventory Operational Loop.
 *
 * Displays recent stock movements (audit trail) on the Inventory page.
 * Read-only — no mutations from this component.
 */

import { useState, useEffect, useCallback } from "react";
import {
  getRecentMovements,
  type StockMovement,
} from "@/api/inventoryDeduction";
import {
  Activity,
  ArrowDownCircle,
  ArrowUpCircle,
  Circle,
  RefreshCw,
  Loader2,
} from "lucide-react";

function formatDelta(value: number): string {
  if (value > 0) return `+${value}`;
  if (value < 0) return `${value}`;
  return "0";
}

function movementTypeLabel(movementType: string): string {
  if (movementType === "consumption" || movementType === "deduction") return "Consum producție";
  if (movementType === "reversal") return "Restituire";
  return "Mișcare stoc";
}

export default function StockMovementsPanel() {
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchMovements = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecentMovements(30);
      setMovements(data.movements);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Eroare la încărcarea mișcărilor de stoc");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMovements();
  }, [fetchMovements]);

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-zinc-100">Mișcări Stoc Recente</h3>
        </div>
        <button
          onClick={fetchMovements}
          disabled={loading}
          className="p-1.5 text-zinc-400 hover:text-zinc-200 transition-colors disabled:opacity-50"
          title="Reîncarcă"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      {/* Loading */}
      {loading && movements.length === 0 && (
        <div className="flex items-center gap-2 text-zinc-400 text-xs py-4 justify-center">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Se încarcă...</span>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded p-2 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && movements.length === 0 && (
        <div className="text-center py-6 text-zinc-500 text-xs">
          <ArrowDownCircle className="w-8 h-8 mx-auto mb-2 opacity-30" />
          <p>Nicio mișcare de stoc înregistrată.</p>
          <p className="mt-1 text-zinc-600">Deducerile din ExecutionReality vor apărea aici.</p>
        </div>
      )}

      {/* Movements list */}
      {movements.length > 0 && (
        <div className="space-y-1 max-h-80 overflow-y-auto">
          {movements.map((m) => (
            (() => {
              const delta = Number(m.new_stock) - Number(m.old_stock);
              const deltaClass = delta > 0 ? "text-emerald-400" : delta < 0 ? "text-amber-400" : "text-zinc-400";
              const label = movementTypeLabel(m.movement_type);
              const Icon = delta > 0 ? ArrowUpCircle : delta < 0 ? ArrowDownCircle : Circle;

              return (
                <div
                  key={m.id}
                  className="flex items-center justify-between px-3 py-2 bg-zinc-800/50 rounded text-xs border border-zinc-700/50"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${deltaClass}`} />
                    <span className="truncate text-zinc-200 font-medium">ID #{m.id}</span>
                    <span className="text-zinc-500 text-[10px]">Mat #{m.material_id}</span>
                    <span className={`font-semibold ${deltaClass}`}>{formatDelta(delta)} {m.unit}</span>
                    <span className="text-zinc-500 text-[10px]">{label}</span>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <span className="text-zinc-500">{m.old_stock} → {m.new_stock}</span>
                    <span className="text-zinc-600 text-[10px]">
                      {m.performed_at ? new Date(m.performed_at).toLocaleString("ro-RO", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" }) : "—"}
                    </span>
                    {m.order_id && (
                      <span className="text-zinc-500 text-[10px]">Cmd #{m.order_id}</span>
                    )}
                  </div>
                </div>
              );
            })()
          ))}
        </div>
      )}
    </div>
  );
}