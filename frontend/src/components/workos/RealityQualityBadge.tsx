/**
 * BUILD 18 — RealityQualityBadge.
 *
 * Displays the data quality status of an ExecutionReality record.
 * Shows invalid badge, reason, and provides invalidation/restoration actions
 * for users with appropriate permissions.
 */

import { useState, useEffect, useCallback } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  RotateCcw,
  AlertCircle,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { useCurrentPermissions } from "@/hooks/useCurrentPermissions";
import {
  getQualityStatus,
  invalidateReality,
  restoreReality,
  type QualityStatus,
} from "@/api/executionRealityQuality";

interface RealityQualityBadgeProps {
  realityId: number;
  /** Compact mode shows only the badge without action buttons */
  compact?: boolean;
  /** Callback when quality status changes */
  onStatusChange?: (status: QualityStatus) => void;
}

type QualityHttpLikeError = {
  status: number;
  message?: string;
};

function isQualityHttpLikeError(value: unknown): value is QualityHttpLikeError {
  return (
    !!value &&
    typeof value === "object" &&
    "status" in value &&
    typeof (value as { status: unknown }).status === "number"
  );
}

export default function RealityQualityBadge({
  realityId,
  compact = false,
  onStatusChange,
}: RealityQualityBadgeProps) {
  const { can: hasPermission } = useCurrentPermissions();
  const [status, setStatus] = useState<QualityStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorKind, setErrorKind] = useState<"auth" | "empty" | "server" | null>(null);

  // Dialog state
  const [showInvalidateDialog, setShowInvalidateDialog] = useState(false);
  const [showRestoreDialog, setShowRestoreDialog] = useState(false);
  const [reason, setReason] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const canInvalidate = hasPermission("reality.invalidate");
  const canRestore = hasPermission("reality.restore_valid");

  const fetchStatus = useCallback(async () => {
    if (!realityId || realityId <= 0) return;
    try {
      setLoading(true);
      setError(null);
      setErrorKind(null);
      const result = await getQualityStatus(realityId);
      setStatus(result);
      onStatusChange?.(result);
    } catch (err) {
      if (isQualityHttpLikeError(err)) {
        if (err.status === 401 || err.status === 403) {
          setErrorKind("auth");
          setError("Sesiune invalidă sau expirată");
        } else if (err.status === 404) {
          setErrorKind("empty");
          setError("Status calitate indisponibil");
        } else {
          setErrorKind("server");
          setError(err.message || "Eroare la încărcarea statusului");
        }
      } else {
        setErrorKind("server");
        setError(err instanceof Error ? err.message : "Eroare la încărcarea statusului");
      }
    } finally {
      setLoading(false);
    }
  }, [realityId, onStatusChange]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const handleInvalidate = async () => {
    if (!reason.trim()) {
      setActionError("Motivul este obligatoriu");
      return;
    }
    try {
      setActionLoading(true);
      setActionError(null);
      const result = await invalidateReality(realityId, { reason: reason.trim() });
      setStatus(result);
      onStatusChange?.(result);
      setShowInvalidateDialog(false);
      setReason("");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Eroare la invalidare");
    } finally {
      setActionLoading(false);
    }
  };

  const handleRestore = async () => {
    if (!reason.trim()) {
      setActionError("Motivul restaurării este obligatoriu");
      return;
    }
    try {
      setActionLoading(true);
      setActionError(null);
      const result = await restoreReality(realityId, { reason: reason.trim() });
      setStatus(result);
      onStatusChange?.(result);
      setShowRestoreDialog(false);
      setReason("");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Eroare la restaurare");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <Badge variant="outline" className="animate-pulse">
        Se verifică...
      </Badge>
    );
  }

  if (error) {
    if (errorKind === "auth") {
      return (
        <Badge variant="outline" className="gap-1 border-amber-500 text-amber-500">
          <AlertCircle className="h-3 w-3" />
          Sesiune expirată
        </Badge>
      );
    }

    if (errorKind === "empty") {
      return (
        <Badge variant="outline" className="gap-1 text-slate-400">
          <AlertCircle className="h-3 w-3" />
          Fără status calitate
        </Badge>
      );
    }

    return (
      <Badge variant="destructive" className="gap-1">
        <AlertCircle className="h-3 w-3" />
        Eroare calitate
      </Badge>
    );
  }

  if (!status) return null;

  return (
    <div className="flex flex-col gap-2">
      {/* Status Badge */}
      <div className="flex items-center gap-2 flex-wrap">
        {status.is_invalid ? (
          <>
            <Badge variant="destructive" className="gap-1">
              <ShieldAlert className="h-3 w-3" />
              INVALIDATĂ
            </Badge>
            {status.stock_reconciliation_required && (
              <Badge variant="outline" className="gap-1 border-amber-500 text-amber-500">
                <AlertTriangle className="h-3 w-3" />
                Reconciliere stoc necesară
              </Badge>
            )}
          </>
        ) : (
          <Badge variant="outline" className="gap-1 border-emerald-500 text-emerald-500">
            <ShieldCheck className="h-3 w-3" />
            Validă
          </Badge>
        )}
      </div>

      {/* Invalid details */}
      {status.is_invalid && status.invalid_reason && (
        <div className="text-xs text-muted-foreground bg-destructive/10 rounded p-2">
          <span className="font-medium">Motiv:</span> {status.invalid_reason}
          {status.invalidated_by && (
            <span className="ml-2 opacity-70">— {status.invalidated_by}</span>
          )}
          {status.invalidated_at && (
            <span className="ml-1 opacity-50">
              ({new Date(status.invalidated_at).toLocaleString("ro-RO")})
            </span>
          )}
        </div>
      )}

      {/* Warnings */}
      {status.warnings.length > 0 && (
        <div className="flex flex-col gap-1">
          {status.warnings.map((w, i) => (
            <div
              key={i}
              className="text-xs text-amber-500 flex items-center gap-1"
            >
              <AlertTriangle className="h-3 w-3 flex-shrink-0" />
              {w}
            </div>
          ))}
        </div>
      )}

      {/* Restoration info */}
      {status.restored_at && !status.is_invalid && (
        <div className="text-xs text-muted-foreground bg-emerald-500/10 rounded p-2">
          <span className="font-medium">Restaurată:</span>{" "}
          {status.restored_reason}
          {status.restored_by && (
            <span className="ml-2 opacity-70">— {status.restored_by}</span>
          )}
        </div>
      )}

      {/* Action buttons */}
      {!compact && (
        <div className="flex gap-2 mt-1">
          {!status.is_invalid && canInvalidate && (
            <Button
              variant="destructive"
              size="sm"
              onClick={() => {
                setReason("");
                setActionError(null);
                setShowInvalidateDialog(true);
              }}
            >
              <ShieldAlert className="h-3 w-3 mr-1" />
              Invalidează Reality
            </Button>
          )}
          {status.is_invalid && canRestore && !status.stock_reconciliation_required && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setReason("");
                setActionError(null);
                setShowRestoreDialog(true);
              }}
            >
              <RotateCcw className="h-3 w-3 mr-1" />
              Restaurează
            </Button>
          )}
        </div>
      )}

      {/* Invalidation Dialog */}
      <Dialog open={showInvalidateDialog} onOpenChange={setShowInvalidateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-destructive">
              <ShieldAlert className="h-5 w-5" />
              Invalidare ExecutionReality
            </DialogTitle>
            <DialogDescription>
              Această acțiune marchează reality ca invalidă. Ea va fi exclusă din
              rapoarte și deduceri stoc. Înregistrarea NU va fi ștearsă.
              {status.stock_deducted && (
                <span className="block mt-2 text-amber-500 font-medium">
                  ⚠️ Stocul a fost deja dedus din această reality. Invalidarea va
                  marca reconciliere stoc necesară.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <label className="text-sm font-medium">
              Motiv invalidare <span className="text-destructive">*</span>
            </label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Descrieți motivul invalidării..."
              rows={3}
            />
            {actionError && (
              <p className="text-xs text-destructive">{actionError}</p>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowInvalidateDialog(false)}
              disabled={actionLoading}
            >
              Anulează
            </Button>
            <Button
              variant="destructive"
              onClick={handleInvalidate}
              disabled={actionLoading || !reason.trim()}
            >
              {actionLoading ? "Se procesează..." : "Confirmă Invalidarea"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Restore Dialog */}
      <Dialog open={showRestoreDialog} onOpenChange={setShowRestoreDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <RotateCcw className="h-5 w-5" />
              Restaurare ExecutionReality
            </DialogTitle>
            <DialogDescription>
              Această acțiune restaurează reality la starea validă. Ea va fi din
              nou inclusă în rapoarte și eligibilă pentru deduceri stoc.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <label className="text-sm font-medium">
              Motiv restaurare <span className="text-destructive">*</span>
            </label>
            <Textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Descrieți motivul restaurării..."
              rows={3}
            />
            {actionError && (
              <p className="text-xs text-destructive">{actionError}</p>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowRestoreDialog(false)}
              disabled={actionLoading}
            >
              Anulează
            </Button>
            <Button
              onClick={handleRestore}
              disabled={actionLoading || !reason.trim()}
            >
              {actionLoading ? "Se procesează..." : "Confirmă Restaurarea"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}