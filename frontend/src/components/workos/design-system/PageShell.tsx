import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface PageShellProps {
  /** Page title */
  title: string;
  /** Optional subtitle/description */
  subtitle?: string;
  /** Right-side header actions (buttons, filters, etc.) */
  actions?: ReactNode;
  /** Page content */
  children: ReactNode;
  /** Additional className for the wrapper */
  className?: string;
  /** Compact mode — less padding */
  compact?: boolean;
}

export function PageShell({
  title,
  subtitle,
  actions,
  children,
  className,
  compact = false,
}: PageShellProps) {
  return (
    <div className={cn("flex flex-col gap-6", compact && "gap-4", className)}>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-xl font-bold text-foreground tracking-tight truncate">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>
          )}
        </div>
        {actions && (
          <div className="flex items-center gap-2 shrink-0">{actions}</div>
        )}
      </div>

      {/* Page Content */}
      <div className="flex flex-col gap-4">{children}</div>
    </div>
  );
}