import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface SectionCardProps {
  /** Section title */
  title?: string;
  /** Optional subtitle */
  subtitle?: string;
  /** Right-side header actions */
  actions?: ReactNode;
  /** Card content */
  children: ReactNode;
  /** Additional className */
  className?: string;
  /** Variant */
  variant?: "default" | "inset" | "raised" | "ghost";
  /** No internal padding */
  noPadding?: boolean;
  /** Icon before title */
  icon?: ReactNode;
}

export function SectionCard({
  title,
  subtitle,
  actions,
  children,
  className,
  variant = "default",
  noPadding = false,
  icon,
}: SectionCardProps) {
  const variantClasses = {
    default: "bg-card border border-border shadow-sm",
    inset: "bg-wo-surface-inset border border-border",
    raised: "bg-wo-surface-raised border border-wo-border-strong shadow-md",
    ghost: "bg-transparent",
  };

  return (
    <div className={cn("rounded-lg", variantClasses[variant], className)}>
      {(title || actions) && (
        <div
          className={cn(
            "flex items-center justify-between gap-3",
            noPadding ? "px-4 pt-4 pb-2" : "px-4 pt-4 pb-2"
          )}
        >
          <div className="flex items-center gap-2 min-w-0">
            {icon && <span className="shrink-0 text-muted-foreground">{icon}</span>}
            <div className="min-w-0">
              {title && (
                <h3 className="text-sm font-semibold text-foreground truncate">
                  {title}
                </h3>
              )}
              {subtitle && (
                <p className="text-xs text-muted-foreground mt-0.5">{subtitle}</p>
              )}
            </div>
          </div>
          {actions && (
            <div className="flex items-center gap-2 shrink-0">{actions}</div>
          )}
        </div>
      )}
      <div className={cn(!noPadding && "p-4", title && !noPadding && "pt-2")}>
        {children}
      </div>
    </div>
  );
}