import { AlertTriangle } from "lucide-react";
import { Link } from "react-router-dom";
import {
  LEGACY_QUOTE_PRICE_INTAKE_V6_HREF,
  LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO,
} from "@/lib/legacyQuotePriceRetirement";

/** Operator-facing notice when legacy CostEngine quote pricing is shown but disabled. */
export function LegacyQuotePriceRetiredBanner({
  testId = "legacy-quote-price-retired-banner",
}: {
  testId?: string;
}) {
  return (
    <div
      className="flex items-start gap-2 px-3 py-2.5 bg-amber-50 border border-amber-200 rounded-lg text-[12px] text-amber-800 dark:bg-amber-950/40 dark:border-amber-800/50 dark:text-amber-100"
      data-testid={testId}
      role="status"
    >
      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
      <div className="space-y-1 min-w-0">
        <p className="font-semibold text-amber-900 dark:text-amber-200">Flux comercial retras</p>
        <p className="text-amber-700 dark:text-amber-100/90">{LEGACY_QUOTE_PRICE_RETIRED_MESSAGE_RO}</p>
        <Link
          to={LEGACY_QUOTE_PRICE_INTAKE_V6_HREF}
          className="inline-flex text-[11px] font-semibold text-sky-600 hover:text-sky-500 dark:text-sky-300 dark:hover:text-sky-200 underline-offset-2 hover:underline"
        >
          Deschide Intake V6
        </Link>
      </div>
    </div>
  );
}
