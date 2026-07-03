/**
 * BUILD 11 — Snapshot Governance Status Component.
 *
 * Displays the eligibility status of quote output snapshot candidates.
 * Read-only display — no mutations.
 *
 * Rules:
 *   - No Quote mutation
 *   - No Order creation
 *   - No status change
 *   - No contract generation
 *   - Pure display of governance evaluation
 */

import { useState, useCallback } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Info,
  Loader2,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import {
  getSnapshotEligibility,
  type EligibilityStatus,
  type SnapshotEligibilityResponse,
} from "@/api/quoteOutputSnapshotGovernance";

interface Props {
  quoteId: number;
}

const STATUS_CONFIG: Record<
  EligibilityStatus,
  {
    label: string;
    icon: typeof CheckCircle2;
    colorClass: string;
    bgClass: string;
    borderClass: string;
  }
> = {
  eligible: {
    label: "Eligibil",
    icon: ShieldCheck,
    colorClass: "text-emerald-400",
    bgClass: "bg-emerald-950/30",
    borderClass: "border-emerald-800/50",
  },
  blocked: {
    label: "Blocat",
    icon: XCircle,
    colorClass: "text-red-400",
    bgClass: "bg-red-950/30",
    borderClass: "border-red-800/50",
  },
  needs_review: {
    label: "Necesită Verificare",
    icon: AlertTriangle,
    colorClass: "text-amber-400",
    bgClass: "bg-amber-950/30",
    borderClass: "border-amber-800/50",
  },
  missing: {
    label: "Lipsă",
    icon: ShieldAlert,
    colorClass: "text-zinc-400",
    bgClass: "bg-zinc-900/30",
    borderClass: "border-zinc-700/50",
  },
};

export default function SnapshotGovernanceStatus({ quoteId }: Props) {
  const [eligibility, setEligibility] = useState<SnapshotEligibilityResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const loadEligibility = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSnapshotEligibility(quoteId);
      setEligibility(data);
      setLoaded(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Eroare la evaluarea eligibilității"
      );
    } finally {
      setLoading(false);
    }
  }, [quoteId]);

  // --- Loading state ---
  if (loading) {
    return (
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center gap-2">
          <Loader2 className="h-4 w-4 text-blue-400 animate-spin" />
          <span className="text-sm text-zinc-300">
            Se evaluează eligibilitatea...
          </span>
        </div>
      </div>
    );
  }

  // --- Error state ---
  if (error) {
    return (
      <div className="border border-red-900/50 rounded-lg p-4 bg-red-950/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <XCircle className="h-4 w-4 text-red-400" />
            <span className="text-sm text-red-300">{error}</span>
          </div>
          <button
            onClick={loadEligibility}
            className="text-xs text-zinc-400 hover:text-zinc-300"
          >
            Reîncearcă
          </button>
        </div>
      </div>
    );
  }

  // --- Not loaded state ---
  if (!loaded && !loading) {
    return (
      <div className="border border-zinc-800 rounded-lg p-4 bg-zinc-900/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-zinc-400" />
            <span className="text-sm font-medium text-zinc-300">
              Guvernanță Snapshot Output
            </span>
          </div>
          <button
            onClick={loadEligibility}
            className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 transition-colors"
            data-testid="governance-load-btn"
          >
            <RefreshCw className="h-3 w-3" />
            Evaluează Eligibilitate
          </button>
        </div>
        <p className="text-xs text-zinc-500 mt-2">
          Verifică dacă snapshot-urile aprobate sunt eligibile pentru integrare viitoare.
        </p>
      </div>
    );
  }

  // --- Loaded state ---
  if (!eligibility) return null;

  const config = STATUS_CONFIG[eligibility.eligibility_status];
  const StatusIcon = config.icon;

  return (
    <div
      className={`border ${config.borderClass} rounded-lg p-4 ${config.bgClass}`}
      data-testid="governance-status-panel"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <StatusIcon className={`h-5 w-5 ${config.colorClass}`} />
          <span className={`text-sm font-semibold ${config.colorClass}`}>
            {config.label}
          </span>
          <span className="text-xs text-zinc-500 ml-2">
            ({eligibility.total_snapshots} snapshot-uri total)
          </span>
        </div>
        <button
          onClick={loadEligibility}
          className="text-xs text-zinc-400 hover:text-zinc-300 transition-colors"
          title="Reîncarcă"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      </div>

      {/* Reasons */}
      {eligibility.reasons.length > 0 && (
        <div className="mb-3">
          <ul className="space-y-1">
            {eligibility.reasons.map((reason, idx) => (
              <li
                key={idx}
                className="flex items-start gap-1.5 text-xs text-zinc-300"
              >
                <Info className="h-3 w-3 text-zinc-500 mt-0.5 shrink-0" />
                {reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Approved snapshot info */}
      {eligibility.approved_snapshot_id && (
        <div className="mb-3 p-2 bg-zinc-800/50 rounded border border-zinc-700/50">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
            <span className="text-xs font-medium text-zinc-200">
              Snapshot Aprobat
            </span>
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-zinc-400">
            <span>Cod: {eligibility.approved_snapshot_code}</span>
            <span>Versiune: {eligibility.approved_snapshot_version}</span>
            {eligibility.source_template_code && (
              <span>Template: {eligibility.source_template_code}</span>
            )}
            {eligibility.source_dossier_id && (
              <span>Dosar: #{eligibility.source_dossier_id}</span>
            )}
          </div>
          <div className="mt-1">
            <span
              className={`text-xs ${
                eligibility.source_metadata_present
                  ? "text-emerald-400"
                  : "text-amber-400"
              }`}
            >
              Metadate sursă:{" "}
              {eligibility.source_metadata_present ? "✓ Complete" : "⚠ Incomplete"}
            </span>
          </div>
        </div>
      )}

      {/* Blockers */}
      {eligibility.blockers.length > 0 && (
        <div className="mb-3">
          <div className="flex items-center gap-1 mb-1">
            <XCircle className="h-3 w-3 text-red-400" />
            <span className="text-xs font-medium text-red-300">Blocaje</span>
          </div>
          <ul className="space-y-0.5 pl-4">
            {eligibility.blockers.map((b, idx) => (
              <li key={idx} className="text-xs text-red-300/80">
                • {b}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {eligibility.warnings.length > 0 && (
        <div className="mb-3">
          <div className="flex items-center gap-1 mb-1">
            <AlertTriangle className="h-3 w-3 text-amber-400" />
            <span className="text-xs font-medium text-amber-300">Avertismente</span>
          </div>
          <ul className="space-y-0.5 pl-4">
            {eligibility.warnings.map((w, idx) => (
              <li key={idx} className="text-xs text-amber-300/80">
                • {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Conflict IDs */}
      {eligibility.conflict_snapshot_ids.length > 0 && (
        <div className="mb-3">
          <div className="flex items-center gap-1 mb-1">
            <ShieldAlert className="h-3 w-3 text-amber-400" />
            <span className="text-xs font-medium text-amber-300">
              Conflict Snapshot-uri
            </span>
          </div>
          <span className="text-xs text-zinc-400">
            ID-uri în conflict: {eligibility.conflict_snapshot_ids.join(", ")}
          </span>
        </div>
      )}

      {/* Status breakdown */}
      {Object.keys(eligibility.snapshots_by_status).length > 0 && (
        <div className="pt-2 border-t border-zinc-700/50">
          <span className="text-xs text-zinc-500">Distribuție status:</span>
          <div className="flex flex-wrap gap-2 mt-1">
            {Object.entries(eligibility.snapshots_by_status).map(
              ([status, count]) => (
                <span
                  key={status}
                  className="text-xs px-1.5 py-0.5 bg-zinc-800 rounded text-zinc-400"
                >
                  {status}: {count}
                </span>
              )
            )}
          </div>
        </div>
      )}

      {/* Governance metadata footer */}
      <div className="mt-3 pt-2 border-t border-zinc-700/30 flex items-center gap-2">
        <span className="text-[10px] text-zinc-600">
          Governance {eligibility.governance_version} • Read-only • No mutations
        </span>
      </div>
    </div>
  );
}