/**
 * Non-blocking naming hints for Material Price Registry — suggestions only.
 */

import { useMemo } from "react";
import { AlertTriangle, Info } from "lucide-react";
import { getCanonicalMaterialSuggestion } from "./materialCanonicalAnalysis";

export function MaterialNamingHints({ name }: { name: string }) {
  const suggestion = useMemo(() => getCanonicalMaterialSuggestion(name), [name]);

  if (!name.trim() || suggestion.messages.length === 0) {
    return null;
  }

  return (
    <div
      className="rounded-md border border-amber-800/40 bg-amber-900/10 px-3 py-2 space-y-1.5"
      data-testid="material-naming-hints"
    >
      <p className="text-[11px] font-semibold text-amber-200 flex items-center gap-1.5">
        <Info className="w-3.5 h-3.5 shrink-0" />
        Sugestii denumire canonică (non-blocking)
      </p>
      <ul className="space-y-1">
        {suggestion.messages.map((message) => (
          <li
            key={message}
            className="text-[11px] text-amber-100/90 flex items-start gap-1.5 leading-snug"
          >
            <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0 text-amber-300/80" />
            <span>{message}</span>
          </li>
        ))}
      </ul>
      {suggestion.canonicalLabelSuggestion && (
        <p className="text-[10px] text-slate-500 pt-0.5">
          Familie recomandată: {suggestion.canonicalLabelSuggestion}
          {suggestion.families[0]?.family.recommended_sku_pattern
            ? ` · SKU: ${suggestion.families[0].family.recommended_sku_pattern}`
            : ""}
        </p>
      )}
    </div>
  );
}
