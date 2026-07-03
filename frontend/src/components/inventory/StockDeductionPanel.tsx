/**
 * StockDeductionPanel — BUILD 16: Inventory Operational Loop.
 *
 * Displays material deduction eligibility and allows explicit operator deduction.
 * Shown in ExecutionDetail page when an ExecutionReality has material rows.
 *
 * Rules:
 *   - Read-only status check on mount (no mutation).
 *   - Deduction requires explicit button click (never automatic).
 *   - Free-text rows shown as "observational" (no deduction possible).
 *   - Already-deducted rows shown with checkmark.
 *   - Insufficient stock shown with warning.
 */

import { useState, useCallback, useEffect } from "react";
import {
  getDeductionStatus,
  deductMaterials,
  type DeductionStatusResponse,
  type DeductionResponse,
  type DeductionRowStatus,
} from "@/api/inventoryDeduction";
import {
  Package,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  MinusCircle,
  Loader2,
  ArrowDownCircle,
} from "lucide-react";

interface StockDeductionPanelProps {
  orderId: number;
}

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; label: string; cls: string }> = {
  eligible: {
    icon: <Package className="w-4 h-4" />,
    label: "Eligibil",
    cls: "text-blue-400 bg-blue-900/30 border-blue-700",
  },
  not_linked: {
    icon: <MinusCircle className="w-4 h-4" />,
    label: "Observațional",
    cls: "text-zinc-400 bg-zinc-800/50 border-zinc-700",
  },
  already_deducted: {
    icon: <CheckCircle2 className="w-4 h-4" />,
    label: "Dedus",
    cls: "text-emerald-400 bg-emerald-900/30 border-emerald-700",
  },
  insufficient_stock: {
    icon: <AlertTriangle className="w-4 h-4" />,
    label: "Stoc insuficient",
    cls: "text-amber-400 bg-amber-900/30 border-amber-700",
  },
  material_not_found: {
    icon: <XCircle className="w-4 h-4" />,
    label: "Material inexistent",
    cls: "text-red-400 bg-red-900/30 border-red-700",
  },
};

export default function StockDeductionPanel({ orderId }: StockDeductionPanelProps) {
  const [status, setStatus] = useState<DeductionStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [deducting, setDeducting] = useState(false);
  const [lastResult, setLastResult] = useState<DeductionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDeductionStatus(orderId);
      setStatus(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Eroare la verificarea statusului");
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleDeductAll = useCallback(async () => {
    if (!status?.reality_exists) return;
    setDeducting(true);
    setError(null);
    try {
      const result = await deductMaterials(orderId, {
        reason: "Deducere operațională din ExecutionReality",
      });
      setLastResult(result);
      // Refresh status after deduction
      await fetchStatus();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Eroare la deducere");
    } finally {
      setDeducting(false);
    }
  }, [orderId, status, fetchStatus]);

  const handleDeductRow = useCallback(async (index: number) => {
    setDeducting(true);
    setError(null);
    try {
      const result = await deductMaterials(orderId, {
        material_indices: [index],
        reason: "Deducere individuală din ExecutionReality",
      });
      setLastResult(result);
      await fetchStatus();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Eroare la deducere");
    } finally {
      setDeducting(false);
    }
  }, [orderId, fetchStatus]);

  if (loading) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <div className="flex items-center gap-2 text-zinc-400">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span>Se verifică eligibilitatea deducerii...</span>
        </div>
      </div>
    );
  }

  if (!status || !status.reality_exists) {
    return (
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
        <p className="text-zinc-500 text-sm">
          Nu există ExecutionReality pentru această comandă. Deducerea stocului nu este disponibilă.
        </p>
      </div>
    );
  }

  const eligibleCount = status.rows.filter(r => r.status === "eligible").length;
  const hasEligible = eligibleCount > 0;

  return (
    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ArrowDownCircle className="w-5 h-5 text-blue-400" />
          <h3 className="text-sm font-semibold text-zinc-100">Deducere Stoc din Inventar</h3>
        </div>
        {hasEligible && (
          <button
            onClick={handleDeductAll}
            disabled={deducting}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {deducting ? (
              <Loader2 className="w-3 h-3 animate-spin" />
            ) : (
              <ArrowDownCircle className="w-3 h-3" />
            )}
            Deduce toate eligibile ({eligibleCount})
          </button>
        )}
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-2 text-xs">
        <div className="bg-zinc-800/50 rounded p-2 text-center">
          <div className="text-zinc-400">Total</div>
          <div className="text-zinc-100 font-semibold">{status.summary.total}</div>
        </div>
        <div className="bg-blue-900/20 rounded p-2 text-center">
          <div className="text-blue-400">Eligibile</div>
          <div className="text-blue-100 font-semibold">{status.summary.eligible}</div>
        </div>
        <div className="bg-zinc-800/50 rounded p-2 text-center">
          <div className="text-zinc-400">Observ.</div>
          <div className="text-zinc-100 font-semibold">{status.summary.not_linked}</div>
        </div>
        <div className="bg-emerald-900/20 rounded p-2 text-center">
          <div className="text-emerald-400">Deduse</div>
          <div className="text-emerald-100 font-semibold">{status.summary.already_deducted}</div>
        </div>
      </div>

      {/* Material rows */}
      <div className="space-y-1.5">
        {status.rows.map((row: DeductionRowStatus) => {
          const cfg = STATUS_CONFIG[row.status] || STATUS_CONFIG.not_linked;
          return (
            <div
              key={row.index}
              className={`flex items-center justify-between px-3 py-2 rounded border text-xs ${cfg.cls}`}
            >
              <div className="flex items-center gap-2 min-w-0">
                {cfg.icon}
                <span className="truncate font-medium">{row.material_name || "—"}</span>
                {row.quantity != null && (
                  <span className="text-zinc-400 flex-shrink-0">
                    {row.quantity} {row.unit || ""}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-[10px] opacity-75">{cfg.label}</span>
                {row.status === "eligible" && (
                  <button
                    onClick={() => handleDeductRow(row.index)}
                    disabled={deducting}
                    className="px-2 py-0.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-[10px] font-medium disabled:opacity-50"
                  >
                    Deduce
                  </button>
                )}
                {row.status === "insufficient_stock" && row.current_stock != null && (
                  <span className="text-[10px] text-amber-300">
                    (stoc: {row.current_stock})
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded p-2 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Last result feedback */}
      {lastResult && !error && (
        <div className="bg-emerald-900/20 border border-emerald-700/50 rounded p-2 text-xs text-emerald-300">
          Rezultat: {lastResult.deducted_count} deduse, {lastResult.skipped_count} omise, {lastResult.blocked_count} blocate
        </div>
      )}
    </div>
  );
}