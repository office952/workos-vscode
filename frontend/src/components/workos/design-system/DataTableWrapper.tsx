import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export interface DataTableWrapperProps {
  children: ReactNode;
  /** Table title */
  title?: string;
  /** Subtitle / row count */
  subtitle?: string;
  /** Actions (filters, export, etc.) */
  actions?: ReactNode;
  /** Density: compact for operational tables, comfortable for admin */
  density?: "compact" | "comfortable";
  /** Additional className */
  className?: string;
  /** Show border around table */
  bordered?: boolean;
}

export function DataTableWrapper({
  children,
  title,
  subtitle,
  actions,
  density = "compact",
  className,
  bordered = true,
}: DataTableWrapperProps) {
  return (
    <div
      className={cn(
        "rounded-lg overflow-hidden",
        bordered && "border border-border",
        className,
      )}
    >
      {(title || actions) && (
        <div className="flex items-center justify-between gap-3 px-4 py-3 bg-card border-b border-border">
          <div className="min-w-0">
            {title && (
              <h3 className="text-sm font-semibold text-foreground truncate">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-[11px] text-muted-foreground mt-0.5">
                {subtitle}
              </p>
            )}
          </div>
          {actions && (
            <div className="flex items-center gap-2 shrink-0">{actions}</div>
          )}
        </div>
      )}
      <div
        className={cn(
          "overflow-x-auto bg-card",
          density === "compact" && "[&_table]:text-xs [&_th]:px-3 [&_th]:py-2 [&_td]:px-3 [&_td]:py-1.5",
          density === "comfortable" && "[&_table]:text-sm [&_th]:px-4 [&_th]:py-3 [&_td]:px-4 [&_td]:py-2.5",
        )}
      >
        {children}
      </div>
    </div>
  );
}