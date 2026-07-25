/**
 * AuditOnlyNotice — banner indicating read-only / audit-only mode.
 */
import { Eye } from "lucide-react";

export interface AuditOnlyNoticeProps {
  /** Optional detail text */
  detail?: string;
  compact?: boolean;
}

export function AuditOnlyNotice({ detail, compact = false }: AuditOnlyNoticeProps) {
  return (
    <div
      className={`flex items-center gap-2 rounded border border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-300 ${
        compact ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-[11px]"
      }`}
      role="status"
      aria-label="Audit Only"
    >
      <Eye className={compact ? "w-3 h-3 shrink-0" : "w-3.5 h-3.5 shrink-0"} />
      <span className="font-semibold">Audit Only / Read-Only</span>
      {detail && <span className="text-muted-foreground">— {detail}</span>}
    </div>
  );
}