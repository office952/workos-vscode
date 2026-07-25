import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, AlertTriangle, Circle } from "lucide-react";
import type { ReactNode } from "react";

export type ReadinessItemStatus = "pass" | "fail" | "warning" | "pending";

export interface ReadinessItem {
  id: string;
  label: string;
  status: ReadinessItemStatus;
  detail?: string;
}

export interface ReadinessPanelProps {
  title: string;
  subtitle?: string;
  items: ReadinessItem[];
  icon?: ReactNode;
  className?: string;
  /** Show summary counts */
  showSummary?: boolean;
}

const statusConfig: Record<
  ReadinessItemStatus,
  { icon: ReactNode; color: string }
> = {
  pass: {
    icon: <CheckCircle2 className="w-3.5 h-3.5" />,
    color: "text-emerald-600 dark:text-emerald-400",
  },
  fail: {
    icon: <XCircle className="w-3.5 h-3.5" />,
    color: "text-red-600 dark:text-red-400",
  },
  warning: {
    icon: <AlertTriangle className="w-3.5 h-3.5" />,
    color: "text-amber-600 dark:text-amber-400",
  },
  pending: {
    icon: <Circle className="w-3.5 h-3.5" />,
    color: "text-slate-400 dark:text-slate-500",
  },
};

export function ReadinessPanel({
  title,
  subtitle,
  items,
  icon,
  className,
  showSummary = true,
}: ReadinessPanelProps) {
  const counts = {
    pass: items.filter((i) => i.status === "pass").length,
    fail: items.filter((i) => i.status === "fail").length,
    warning: items.filter((i) => i.status === "warning").length,
    pending: items.filter((i) => i.status === "pending").length,
  };

  const overallStatus: ReadinessItemStatus =
    counts.fail > 0
      ? "fail"
      : counts.warning > 0
        ? "warning"
        : counts.pending > 0
          ? "pending"
          : "pass";

  const overallBorder = {
    pass: "border-emerald-200 dark:border-emerald-800",
    fail: "border-red-200 dark:border-red-800",
    warning: "border-amber-200 dark:border-amber-800",
    pending: "border-border",
  };

  return (
    <div
      className={cn(
        "rounded-lg border bg-card p-4",
        overallBorder[overallStatus],
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 min-w-0">
          {icon && <span className="text-muted-foreground shrink-0">{icon}</span>}
          <div className="min-w-0">
            <h4 className="text-sm font-semibold text-foreground truncate">
              {title}
            </h4>
            {subtitle && (
              <p className="text-[11px] text-muted-foreground">{subtitle}</p>
            )}
          </div>
        </div>
        {showSummary && (
          <div className="flex items-center gap-2 text-[10px] font-medium shrink-0">
            {counts.pass > 0 && (
              <span className="text-emerald-600 dark:text-emerald-400">
                {counts.pass} ✓
              </span>
            )}
            {counts.fail > 0 && (
              <span className="text-red-600 dark:text-red-400">
                {counts.fail} ✗
              </span>
            )}
            {counts.warning > 0 && (
              <span className="text-amber-600 dark:text-amber-400">
                {counts.warning} ⚠
              </span>
            )}
          </div>
        )}
      </div>

      {/* Items */}
      <div className="space-y-1.5">
        {items.map((item) => {
          const config = statusConfig[item.status];
          return (
            <div
              key={item.id}
              className="flex items-start gap-2 py-1"
            >
              <span className={cn("shrink-0 mt-0.5", config.color)}>
                {config.icon}
              </span>
              <div className="min-w-0 flex-1">
                <span className="text-xs font-medium text-foreground">
                  {item.label}
                </span>
                {item.detail && (
                  <p className="text-[10px] text-muted-foreground mt-0.5">
                    {item.detail}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}