/**
 * BUILD 17 — Operator Safety Confirmation Dialog.
 *
 * Wraps destructive/irreversible actions with a confirmation step.
 * Requires the operator to type a confirmation phrase for high-risk actions.
 */

import React, { useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

type RiskLevel = "low" | "medium" | "high";

interface OperatorSafetyConfirmProps {
  /** The trigger button/element */
  trigger: React.ReactNode;
  /** Dialog title */
  title: string;
  /** Description of the action */
  description: string;
  /** Risk level determines confirmation requirements */
  riskLevel?: RiskLevel;
  /** For high-risk: the phrase the user must type to confirm */
  confirmPhrase?: string;
  /** Called when user confirms */
  onConfirm: () => void;
  /** Whether the action is currently in progress */
  loading?: boolean;
  /** Whether the dialog is disabled */
  disabled?: boolean;
}

export function OperatorSafetyConfirm({
  trigger,
  title,
  description,
  riskLevel = "medium",
  confirmPhrase,
  onConfirm,
  loading = false,
  disabled = false,
}: OperatorSafetyConfirmProps) {
  const [typedPhrase, setTypedPhrase] = useState("");
  const [open, setOpen] = useState(false);

  const needsTypedConfirmation = riskLevel === "high" && confirmPhrase;
  const canConfirm = needsTypedConfirmation
    ? typedPhrase.trim().toLowerCase() === confirmPhrase.trim().toLowerCase()
    : true;

  const riskColors: Record<RiskLevel, string> = {
    low: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    medium: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    high: "bg-red-500/10 text-red-400 border-red-500/20",
  };

  const riskLabels: Record<RiskLevel, string> = {
    low: "Acțiune standard",
    medium: "Acțiune importantă",
    high: "Acțiune ireversibilă",
  };

  const handleConfirm = () => {
    if (canConfirm && !loading && !disabled) {
      onConfirm();
      setOpen(false);
      setTypedPhrase("");
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <AlertDialogTrigger asChild disabled={disabled}>
        {trigger}
      </AlertDialogTrigger>
      <AlertDialogContent className="bg-zinc-900 border-zinc-700">
        <AlertDialogHeader>
          <div className="flex items-center gap-2 mb-1">
            <AlertDialogTitle className="text-zinc-100">
              {title}
            </AlertDialogTitle>
            <Badge variant="outline" className={riskColors[riskLevel]}>
              {riskLabels[riskLevel]}
            </Badge>
          </div>
          <AlertDialogDescription className="text-zinc-400">
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>

        {needsTypedConfirmation && (
          <div className="my-4 space-y-2">
            <p className="text-sm text-zinc-400">
              Pentru a confirma, tastați:{" "}
              <code className="bg-zinc-800 px-1.5 py-0.5 rounded text-red-400 font-mono text-xs">
                {confirmPhrase}
              </code>
            </p>
            <Input
              value={typedPhrase}
              onChange={(e) => setTypedPhrase(e.target.value)}
              placeholder="Tastați fraza de confirmare..."
              className="bg-zinc-800 border-zinc-700 text-zinc-100"
              autoComplete="off"
            />
          </div>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel
            className="bg-zinc-800 border-zinc-700 text-zinc-300 hover:bg-zinc-700"
            onClick={() => setTypedPhrase("")}
          >
            Anulează
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={handleConfirm}
            disabled={!canConfirm || loading || disabled}
            className={
              riskLevel === "high"
                ? "bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
                : "bg-amber-600 hover:bg-amber-700 text-white disabled:opacity-50"
            }
          >
            {loading ? "Se procesează..." : "Confirmă"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}