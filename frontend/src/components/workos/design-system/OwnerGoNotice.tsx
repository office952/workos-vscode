/**
 * OwnerGoNotice — indicates that Owner GO is required for activation/release.
 */
import { ShieldAlert } from "lucide-react";

export interface OwnerGoNoticeProps {
  /** Optional detail */
  detail?: string;
  compact?: boolean;
}

export function OwnerGoNotice({
  detail = "Necesită Owner GO pentru activare.",
  compact = false,
}: OwnerGoNoticeProps) {
  return (
    <div
      className={`flex items-center gap-2 rounded border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-700 dark:bg-rose-900/30 dark:text-rose-300 ${
        compact ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-[11px]"
      }`}
      role="alert"
      aria-label="Owner GO required"
    >
      <ShieldAlert className={compact ? "w-3 h-3 shrink-0" : "w-3.5 h-3.5 shrink-0"} />
      <span className="font-medium">{detail}</span>
    </div>
  );
}