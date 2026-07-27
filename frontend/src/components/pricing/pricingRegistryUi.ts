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
      ? "border-wo-info/50 ring-1 ring-wo-info/30"
      : "border-wo-border-subtle hover:border-wo-border-strong hover:bg-wo-hover",
  ].join(" ");
}

export function statusSeverityBadgeClass(severity: StatusSeverity): string {
  switch (severity) {
    case "ok":
      return "bg-wo-success-muted text-wo-success border-wo-success/35";
    case "warn":
      return "bg-wo-warning-muted text-wo-warning border-wo-warning/35";
    case "bad":
      return "bg-wo-error-muted text-wo-error border-wo-error/35";
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
