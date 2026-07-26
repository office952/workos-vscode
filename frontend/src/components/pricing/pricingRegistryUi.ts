/**
 * Pricing Registry UI tokens — shared across tabs (Oferte-like card rows).
 */
import type { PricingMainView, StatusSeverity } from "@/lib/pricingRegistry";

export const PRICING_VIEW_TAB_META: Record<
  PricingMainView,
  { label: string; title: string; hint: string }
> = {
  coverage: {
    label: "Acoperire template",
    title: "Acoperire template",
    hint: "Stack-ul de prețuri folosit de template-ul selectat — materiale, operații și adaos.",
  },
  all: {
    label: "Toate intrările",
    title: "Toate intrările — audit global",
    hint: "Vedere secundară: toate intrările din registry, indiferent de template.",
  },
  verify: {
    label: "Verificare",
    title: "Verificare — lipsuri și review",
    hint: "Coadă de probleme: prețuri/rate lipsă, estimări de confirmat, blocaje calcul.",
  },
  markup: {
    label: "Adaos comercial",
    title: "Adaos comercial",
    hint: "Reguli de adaos vizibile aici; editarea rămâne într-un flux dedicat.",
  },
  audit: {
    label: "Istoric / audit",
    title: "Istoric / audit",
    hint: "Schimbări recente de preț pentru materialul selectat din listă.",
  },
};

/** Card-row shell — mirrors Quotes QuoteCard rhythm. */
export function entryRowClass(selected: boolean): string {
  return [
    "bg-wo-surface-raised border rounded-lg p-4 cursor-pointer transition-all",
    selected
      ? "border-blue-500/50 ring-1 ring-blue-500/30"
      : "border-wo-border-subtle hover:border-slate-500",
  ].join(" ");
}

export function statusSeverityBadgeClass(severity: StatusSeverity): string {
  switch (severity) {
    case "ok":
      return "bg-emerald-500/15 text-emerald-700 border-emerald-600/40 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700/50";
    case "warn":
      return "bg-amber-500/15 text-amber-800 border-amber-600/40 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700/50";
    case "bad":
      return "bg-red-500/15 text-red-700 border-red-600/40 dark:bg-red-900/30 dark:text-red-300 dark:border-red-700/50";
    default: {
      const _exhaustive: never = severity;
      return _exhaustive;
    }
  }
}

export const FAVORITE_TEMPLATES_STORAGE_KEY = "pricing-registry-favorite-templates";

export function toggleFavoriteTemplate(codes: string[], code: string, max = 8): string[] {
  if (codes.includes(code)) {
    return codes.filter((c) => c !== code);
  }
  return [code, ...codes].slice(0, max);
}
