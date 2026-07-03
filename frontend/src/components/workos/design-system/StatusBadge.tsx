import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import {
  getStatusTone,
  getToneClasses,
  normalizeStatusLabel,
  statusBadgeSizeClasses,
  type StatusDomain,
} from "./tokens";

export type { StatusDomain };

export type StatusBadgeProps = {
  domain?: StatusDomain;
  status: string | null | undefined;
  label?: string;
  size?: "sm" | "md" | "lg";
  icon?: ReactNode;
  className?: string;
  title?: string;
};

export function StatusBadge({
  domain = "generic",
  status,
  label,
  size = "sm",
  icon,
  className,
  title,
}: StatusBadgeProps) {
  const tone = getStatusTone(domain, status);
  const toneClasses = getToneClasses(tone);
  const displayLabel = label ?? normalizeStatusLabel(domain, status);

  return (
    <span
      title={title}
      data-status-domain={domain}
      data-status={status ?? ""}
      data-status-tone={tone}
      className={cn(
        "inline-flex items-center gap-1 border font-semibold rounded-[6px]",
        toneClasses.bg,
        toneClasses.text,
        toneClasses.border,
        statusBadgeSizeClasses[size],
        className,
      )}
    >
      {icon}
      {displayLabel}
    </span>
  );
}
