import { cn } from "@/lib/utils";
import { AlertTriangle, ShieldCheck, ShieldAlert } from "lucide-react";
import type { ReactNode } from "react";

export type RiskLevel = "high" | "medium" | "low" | "none";

export interface RiskBadgeProps {
  level: RiskLevel;
  label?: string;
  showIcon?: boolean;
  size?: "sm" | "md";
  className?: string;
}

const riskConfig: Record<
  RiskLevel,
  { bg: string; text: string; border: string; icon: ReactNode; defaultLabel: string }
> = {
  high: {
    bg: "bg-red-50 dark:bg-red-900/50",
    text: "text-red-700 dark:text-red-200",
    border: "border-red-200 dark:border-red-700",
    icon: <ShieldAlert className="w-3 h-3" />,
    defaultLabel: "Risc Ridicat",
  },
  medium: {
    bg: "bg-amber-50 dark:bg-amber-900/50",
    text: "text-amber-700 dark:text-amber-200",
    border: "border-amber-200 dark:border-amber-700",
    icon: <AlertTriangle className="w-3 h-3" />,
    defaultLabel: "Risc Mediu",
  },
  low: {
    bg: "bg-emerald-50 dark:bg-emerald-900/50",
    text: "text-emerald-700 dark:text-emerald-200",
    border: "border-emerald-200 dark:border-emerald-700",
    icon: <ShieldCheck className="w-3 h-3" />,
    defaultLabel: "Risc Scăzut",
  },
  none: {
    bg: "bg-slate-100 dark:bg-slate-800/80",
    text: "text-slate-700 dark:text-slate-300",
    border: "border-slate-300 dark:border-slate-600",
    icon: <ShieldCheck className="w-3 h-3" />,
    defaultLabel: "Fără Risc",
  },
};

const sizeClasses = {
  sm: "px-2 py-0.5 text-[10px] gap-1",
  md: "px-2.5 py-1 text-xs gap-1.5",
};

export function RiskBadge({
  level,
  label,
  showIcon = true,
  size = "sm",
  className,
}: RiskBadgeProps) {
  const config = riskConfig[level] ?? riskConfig.none;
  const displayLabel = label ?? config.defaultLabel;

  return (
    <span
      data-risk-level={level}
      className={cn(
        "inline-flex items-center border font-semibold rounded-[6px]",
        config.bg,
        config.text,
        config.border,
        sizeClasses[size],
        className,
      )}
    >
      {showIcon && config.icon}
      {displayLabel}
    </span>
  );
}