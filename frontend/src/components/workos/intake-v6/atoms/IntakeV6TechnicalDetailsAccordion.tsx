import { useState, type ReactNode } from "react";

export interface IntakeV6TechnicalDetailsAccordionProps {
  title?: string;
  children: ReactNode;
  defaultOpen?: boolean;
  testId?: string;
  className?: string;
}

export default function IntakeV6TechnicalDetailsAccordion({
  title = "Detalii tehnice / debug",
  children,
  defaultOpen = false,
  testId = "intake-v6-technical-details",
  className = "mb-4",
}: IntakeV6TechnicalDetailsAccordionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={`rounded border border-[#2A3548] bg-[#0A0F1A]/40 ${className}`.trim()} data-testid={testId}>
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left text-[12px] font-semibold uppercase tracking-wide text-slate-400"
        onClick={() => setOpen((value) => !value)}
        data-testid={`${testId}-toggle`}
        aria-expanded={open}
      >
        <span>{title}</span>
        <span className="text-slate-500">{open ? "▾" : "▸"}</span>
      </button>
      {open ? (
        <div className="border-t border-[#2A3548] px-4 py-3" data-testid={`${testId}-content`}>
          {children}
        </div>
      ) : null}
    </div>
  );
}

