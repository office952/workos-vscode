/**
 * InternalCostNotice — clarifies that a cost is internal, not a client tariff.
 */
import { Lock } from "lucide-react";

export interface InternalCostNoticeProps {
  /** Optional custom message */
  message?: string;
  compact?: boolean;
}

export function InternalCostNotice({
  message = "Acest cost este intern — nu reprezintă tarif client.",
  compact = false,
}: InternalCostNoticeProps) {
  return (
    <div
      className={`flex items-center gap-2 rounded border border-blue-200 bg-blue-50 text-blue-700 dark:border-blue-700 dark:bg-blue-900/30 dark:text-blue-300 ${
        compact ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-[11px]"
      }`}
      role="note"
      aria-label="Internal cost notice"
    >
      <Lock className={compact ? "w-3 h-3 shrink-0" : "w-3.5 h-3.5 shrink-0"} />
      <span>{message}</span>
    </div>
  );
}