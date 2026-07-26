/**
 * NextStepPanel — Consistent "Următorul pas" pattern.
 *
 * Shows the operator what to do next with:
 *  - Recommended next step
 *  - Why
 *  - Primary action
 *  - Secondary action
 *  - Blocker if exists
 *
 * Rules:
 *  - Does NOT auto-create anything
 *  - Does NOT auto-approve
 *  - Only guides the operator
 */
import { ArrowRight, AlertTriangle, Info, Lock } from "lucide-react";
import { Link } from "react-router-dom";

interface NextStepAction {
  label: string;
  to?: string;
  onClick?: () => void;
  disabled?: boolean;
  disabledReason?: string;
  variant?: "primary" | "secondary" | "ghost";
}

interface NextStepPanelProps {
  title: string;
  description?: string;
  reason?: string;
  primaryAction?: NextStepAction;
  secondaryAction?: NextStepAction;
  blocker?: string;
  blockerDetails?: string[];
  warning?: string;
  className?: string;
}

function ActionButton({ action, isPrimary }: { action: NextStepAction; isPrimary: boolean }) {
  const variant = action.variant || (isPrimary ? "primary" : "secondary");

  const baseClasses =
    "inline-flex items-center gap-2 px-4 py-2 rounded-lg text-[12px] font-semibold transition-all";

  const variantClasses = {
    primary:
      "bg-blue-600 hover:bg-blue-500 text-white border border-blue-500",
    secondary:
      "bg-wo-hover hover:bg-wo-hover text-slate-300 border border-wo-border-strong",
    ghost:
      "bg-transparent hover:bg-wo-hover text-slate-400 border border-transparent",
  };

  const disabledClasses = "opacity-40 cursor-not-allowed pointer-events-none";

  const classes = `${baseClasses} ${variantClasses[variant]} ${action.disabled ? disabledClasses : ""}`;

  if (action.disabled) {
    return (
      <div className="flex flex-col gap-1">
        <button className={classes} disabled>
          {action.label}
          <Lock className="w-3 h-3" />
        </button>
        {action.disabledReason && (
          <span className="text-[10px] text-slate-500 ml-1">
            {action.disabledReason}
          </span>
        )}
      </div>
    );
  }

  if (action.to) {
    return (
      <Link to={action.to} className={classes}>
        {action.label}
        <ArrowRight className="w-3.5 h-3.5" />
      </Link>
    );
  }

  return (
    <button onClick={action.onClick} className={classes}>
      {action.label}
      <ArrowRight className="w-3.5 h-3.5" />
    </button>
  );
}

export default function NextStepPanel({
  title,
  description,
  reason,
  primaryAction,
  secondaryAction,
  blocker,
  blockerDetails,
  warning,
  className = "",
}: NextStepPanelProps) {
  const hasBorder = blocker
    ? "border-red-900/40"
    : warning
      ? "border-amber-900/40"
      : "border-blue-900/30";

  const hasBg = blocker
    ? "bg-red-950/20"
    : warning
      ? "bg-amber-950/20"
      : "bg-blue-950/20";

  return (
    <div
      className={`rounded-lg border p-4 ${hasBorder} ${hasBg} ${className}`}
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        {blocker ? (
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
        ) : warning ? (
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
        ) : (
          <Info className="w-4 h-4 text-blue-400 shrink-0" />
        )}
        <h4 className="text-[13px] font-semibold text-slate-200">{title}</h4>
      </div>

      {/* Description */}
      {description && (
        <p className="text-[12px] text-slate-400 mb-2 ml-6">{description}</p>
      )}

      {/* Reason */}
      {reason && (
        <p className="text-[11px] text-slate-500 mb-3 ml-6 italic">{reason}</p>
      )}

      {/* Blocker */}
      {blocker && (
        <div className="ml-6 mb-3 p-2 rounded bg-red-950/30 border border-red-900/30">
          <p className="text-[11px] text-red-400 font-medium">{blocker}</p>
          {blockerDetails && blockerDetails.length > 0 && (
            <ul className="mt-1 space-y-0.5">
              {blockerDetails.map((d, i) => (
                <li key={i} className="text-[10px] text-red-400/70 ml-2">
                  • {d}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Warning */}
      {warning && !blocker && (
        <div className="ml-6 mb-3 p-2 rounded bg-amber-950/30 border border-amber-900/30">
          <p className="text-[11px] text-amber-400">{warning}</p>
        </div>
      )}

      {/* Actions */}
      {(primaryAction || secondaryAction) && (
        <div className="flex items-center gap-3 ml-6 mt-3">
          {primaryAction && (
            <ActionButton action={primaryAction} isPrimary={true} />
          )}
          {secondaryAction && (
            <ActionButton action={secondaryAction} isPrimary={false} />
          )}
        </div>
      )}
    </div>
  );
}

/**
 * OperatorHint — Small inline hint for operator guidance.
 * Use within pages for contextual tips.
 */
export function OperatorHint({
  text,
  variant = "info",
}: {
  text: string;
  variant?: "info" | "warning" | "success";
}) {
  const colors = {
    info: "text-blue-400/70 border-blue-900/20 bg-blue-950/10",
    warning: "text-amber-400/70 border-amber-900/20 bg-amber-950/10",
    success: "text-emerald-400/70 border-emerald-900/20 bg-emerald-950/10",
  };

  return (
    <div
      className={`flex items-start gap-2 px-3 py-2 rounded border text-[11px] ${colors[variant]}`}
    >
      <Info className="w-3 h-3 mt-0.5 shrink-0" />
      <span>{text}</span>
    </div>
  );
}

/**
 * AuthErrorState — Friendly error state for 401/403 errors in dev mode.
 */
export function AuthErrorState({
  pageName,
  error,
  suggestions,
}: {
  pageName: string;
  error?: string;
  suggestions?: string[];
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-8">
      <div className="w-16 h-16 rounded-full bg-amber-950/30 border border-amber-900/30 flex items-center justify-center mb-4">
        <AlertTriangle className="w-8 h-8 text-amber-400" />
      </div>
      <h3 className="text-[16px] font-semibold text-slate-200 mb-2">
        {pageName} — Date indisponibile
      </h3>
      {error && (
        <p className="text-[12px] text-slate-400 mb-4 text-center max-w-md">
          {error}
        </p>
      )}
      <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-4 max-w-md w-full">
        <p className="text-[11px] text-slate-500 font-medium mb-2">
          Posibile cauze:
        </p>
        <ul className="space-y-1">
          {(
            suggestions || [
              "Backend-ul nu este pornit sau nu este accesibil",
              "Autentificarea nu este configurată pentru acest mod",
              "Contractul API nu este disponibil încă",
            ]
          ).map((s, i) => (
            <li key={i} className="text-[11px] text-slate-500 flex items-start gap-1.5">
              <span className="text-slate-600 mt-0.5">•</span>
              {s}
            </li>
          ))}
        </ul>
      </div>
      <p className="text-[10px] text-slate-600 mt-4">
        Verificați configurarea backend-ului sau folosiți paginile cu date demo disponibile.
      </p>
    </div>
  );
}