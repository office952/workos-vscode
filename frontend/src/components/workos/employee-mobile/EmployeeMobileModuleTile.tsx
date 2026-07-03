import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { emModuleBadgeClass, emSurface } from "@/lib/employeeMobileDesignTokens";
import { cn } from "@/lib/utils";

export default function EmployeeMobileModuleTile({
  to,
  title,
  icon: Icon,
  badge,
  disabled = false,
  disabledLabel,
  testId,
}: {
  to?: string;
  title: string;
  icon: LucideIcon;
  badge?: number | string;
  disabled?: boolean;
  disabledLabel?: string;
  testId: string;
}) {
  const showBadge =
    badge !== undefined && badge !== "…" && badge !== 0 && badge !== "0" && badge !== "→";
  const content = (
    <>
      <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-[#111827]/80 ring-1 ring-[#243044]">
        <Icon
          className={cn("w-6 h-6", disabled ? "text-slate-600" : "text-slate-200")}
          aria-hidden
        />
        {showBadge ? (
          <span className={emModuleBadgeClass()}>{badge}</span>
        ) : null}
      </div>
      <span
        className={cn(
          "text-[13px] font-medium leading-tight text-center",
          disabled ? "text-slate-600" : "text-slate-200",
        )}
      >
        {title}
      </span>
      {disabled && disabledLabel ? (
        <span className="text-[10px] text-slate-600">{disabledLabel}</span>
      ) : null}
    </>
  );

  const className = cn(
    "flex flex-col items-center justify-center gap-2 rounded-xl border px-3 py-4 min-h-[112px] transition-colors",
    disabled
      ? "border-[#243044]/40 bg-[#0A1020]/30 cursor-not-allowed"
      : cn(emSurface.panel, "hover:border-slate-500 hover:bg-[#0A1020]/90"),
  );

  if (disabled || !to) {
    return (
      <div className={className} data-testid={testId} aria-disabled={disabled}>
        {content}
      </div>
    );
  }

  return (
    <Link to={to} className={className} data-testid={testId}>
      {content}
    </Link>
  );
}
