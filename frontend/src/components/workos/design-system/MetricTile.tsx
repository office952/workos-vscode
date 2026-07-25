import { cn } from "@/lib/utils";
import type { ReactNode } from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

export interface MetricTileProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "flat";
  trendValue?: string;
  icon?: ReactNode;
  variant?: "default" | "compact" | "highlight";
  className?: string;
}

const trendConfig = {
  up: {
    icon: <TrendingUp className="w-3 h-3" />,
    color: "text-emerald-600 dark:text-emerald-400",
  },
  down: {
    icon: <TrendingDown className="w-3 h-3" />,
    color: "text-red-600 dark:text-red-400",
  },
  flat: {
    icon: <Minus className="w-3 h-3" />,
    color: "text-slate-500 dark:text-slate-400",
  },
};

export function MetricTile({
  label,
  value,
  unit,
  trend,
  trendValue,
  icon,
  variant = "default",
  className,
}: MetricTileProps) {
  const variantClasses = {
    default: "bg-card border border-border",
    compact: "bg-wo-surface-inset border border-border",
    highlight: "bg-primary/5 border border-primary/20 dark:bg-primary/10",
  };

  return (
    <div
      className={cn(
        "rounded-lg p-3 flex flex-col gap-1.5",
        variantClasses[variant],
        className,
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide truncate">
          {label}
        </span>
        {icon && (
          <span className="text-muted-foreground shrink-0">{icon}</span>
        )}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-xl font-bold text-foreground leading-none">
          {value}
        </span>
        {unit && (
          <span className="text-xs text-muted-foreground">{unit}</span>
        )}
      </div>
      {trend && (
        <div className={cn("flex items-center gap-1 text-[10px] font-medium", trendConfig[trend].color)}>
          {trendConfig[trend].icon}
          {trendValue && <span>{trendValue}</span>}
        </div>
      )}
    </div>
  );
}