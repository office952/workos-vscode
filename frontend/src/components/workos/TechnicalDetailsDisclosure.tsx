/**
 * TechnicalDetailsDisclosure — secondary diagnostics under "Detalii tehnice".
 * Keeps raw/dev details out of the primary operator fold.
 */
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface TechnicalDetailsDisclosureProps {
  children: ReactNode;
  title?: string;
  defaultOpen?: boolean;
  className?: string;
  testId?: string;
}

export default function TechnicalDetailsDisclosure({
  children,
  title = "Detalii tehnice",
  defaultOpen = false,
  className,
  testId = "technical-details-disclosure",
}: TechnicalDetailsDisclosureProps) {
  return (
    <details
      className={cn(
        "rounded-lg border border-wo-border-strong bg-wo-surface-inset",
        className,
      )}
      data-testid={testId}
      open={defaultOpen || undefined}
    >
      <summary className="cursor-pointer select-none px-3 py-2 text-[11px] font-semibold text-wo-text-secondary hover:text-wo-text-primary">
        {title}
      </summary>
      <div className="space-y-2 border-t border-wo-border-subtle px-3 py-2 text-[11px] text-wo-text-muted">
        {children}
      </div>
    </details>
  );
}
