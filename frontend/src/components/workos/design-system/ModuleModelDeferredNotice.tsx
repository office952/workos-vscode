/**
 * ModuleModelDeferredNotice — Owner policy: full Module produs model is not live SoT UI.
 * Active path remains Product Template + Structură produs (Față / Volum / Spate / LED).
 * Chrome/copy only — does not activate module-model runtime.
 */
import { PauseCircle } from "lucide-react";

/** Keep in sync with productTemplateModulesVocabulary.MODULE_MODEL_STATUS */
export const MODULE_MODEL_DEFERRED_STATUS = "MODULE_MODEL_DEFERRED" as const;

const DEFAULT_DETAIL_RO =
  "Calea activă: Product Template + structură Față / Volum / Spate / LED. Modelul complet „Module produs” egale este amânat — nu este SoT UI live.";

export interface ModuleModelDeferredNoticeProps {
  /** Override detail (defaults to Owner policy RO copy). */
  detail?: string;
  compact?: boolean;
}

export function ModuleModelDeferredNotice({
  detail = DEFAULT_DETAIL_RO,
  compact = false,
}: ModuleModelDeferredNoticeProps) {
  return (
    <div
      className={`flex items-start gap-2 rounded border border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-700/60 dark:bg-amber-950/30 dark:text-amber-100 ${
        compact ? "px-2 py-1 text-[10px]" : "px-3 py-1.5 text-[11px]"
      }`}
      role="status"
      aria-label={MODULE_MODEL_DEFERRED_STATUS}
      data-testid="module-model-deferred-notice"
      data-policy={MODULE_MODEL_DEFERRED_STATUS}
    >
      <PauseCircle
        className={`shrink-0 mt-0.5 ${compact ? "w-3 h-3" : "w-3.5 h-3.5"}`}
        aria-hidden
      />
      <div className="min-w-0 leading-snug">
        <span className="font-semibold font-mono tracking-wide">{MODULE_MODEL_DEFERRED_STATUS}</span>
        {detail ? <span className="text-amber-700/90 dark:text-amber-100/85"> — {detail}</span> : null}
      </div>
    </div>
  );
}
