/**
 * CapacityNotice — clarifies that data is about capacity/feasibility, not commercial pricing.
 */
import { Gauge } from "lucide-react";

export interface CapacityNoticeProps {
  /** Optional custom message */
  message?: string;
  compact?: boolean;
}

export function CapacityNotice({
  message = "Capacity / Feasibility — nu pricing comercial.",
  compact = false,
}: CapacityNoticeProps) {
  return (
    <div
      className={`flex items-center gap-2 rounded border border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-700 dark:bg-amber-900/30 dark:text-amber-300 ${
        compact ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-[11px]"
      }`}
      role="note"
      aria-label="Capacity notice"
    >
      <Gauge className={compact ? "w-3 h-3 shrink-0" : "w-3.5 h-3.5 shrink-0"} />
      <span>{message}</span>
    </div>
  );
}