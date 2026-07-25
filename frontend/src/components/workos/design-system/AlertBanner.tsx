import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { AlertTriangle, XCircle, Info, CheckCircle2 } from "lucide-react";

type AlertVariant = "info" | "warning" | "error" | "success";

interface AlertBannerProps {
  /** Alert type */
  variant: AlertVariant;
  /** Title text */
  title?: string;
  /** Description/message */
  children: ReactNode;
  /** Additional className */
  className?: string;
  /** Custom icon override */
  icon?: ReactNode;
  /** Right-side action */
  action?: ReactNode;
  /** Compact single-line mode */
  compact?: boolean;
}

const variantConfig: Record<
  AlertVariant,
  { bg: string; border: string; text: string; icon: typeof Info }
> = {
  info: {
    bg: "bg-wo-info-muted",
    border: "border-wo-info/30",
    text: "text-wo-info",
    icon: Info,
  },
  warning: {
    bg: "bg-wo-warning-muted",
    border: "border-wo-warning/30",
    text: "text-wo-warning",
    icon: AlertTriangle,
  },
  error: {
    bg: "bg-wo-error-muted",
    border: "border-wo-error/30",
    text: "text-wo-error",
    icon: XCircle,
  },
  success: {
    bg: "bg-wo-success-muted",
    border: "border-wo-success/30",
    text: "text-wo-success",
    icon: CheckCircle2,
  },
};

export function AlertBanner({
  variant,
  title,
  children,
  className,
  icon,
  action,
  compact = false,
}: AlertBannerProps) {
  const config = variantConfig[variant];
  const IconComponent = config.icon;

  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-lg border",
        config.bg,
        config.border,
        compact ? "px-3 py-2" : "px-4 py-3",
        className
      )}
      role="alert"
    >
      <span className={cn("shrink-0 mt-0.5", config.text)}>
        {icon || <IconComponent className={compact ? "w-4 h-4" : "w-5 h-5"} />}
      </span>
      <div className="flex-1 min-w-0">
        {title && (
          <p className={cn("font-semibold text-foreground", compact ? "text-xs" : "text-sm")}>
            {title}
          </p>
        )}
        <div className={cn("text-muted-foreground", compact ? "text-xs" : "text-sm", title && "mt-0.5")}>
          {children}
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}