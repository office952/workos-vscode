import { ChevronDown } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

export interface IntakeV6TechnicalDetailsAccordionProps {
  title?: string;
  children: ReactNode;
  defaultOpen?: boolean;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  itemCount?: number;
  hint?: string;
  testId?: string;
  className?: string;
}

export default function IntakeV6TechnicalDetailsAccordion({
  title = "Detalii tehnice / debug",
  children,
  defaultOpen = false,
  open: controlledOpen,
  onOpenChange,
  itemCount,
  hint,
  testId = "intake-v6-technical-details",
  className = "mb-4",
}: IntakeV6TechnicalDetailsAccordionProps) {
  const [internalOpen, setInternalOpen] = useState(defaultOpen);
  const isControlled = controlledOpen !== undefined;
  const open = isControlled ? controlledOpen : internalOpen;

  useEffect(() => {
    if (!isControlled) setInternalOpen(defaultOpen);
  }, [defaultOpen, isControlled]);

  function setOpen(next: boolean) {
    if (!isControlled) setInternalOpen(next);
    onOpenChange?.(next);
  }

  const countLabel =
    itemCount != null
      ? `${itemCount} ${itemCount === 1 ? "element" : "elemente"}`
      : null;

  return (
    <div
      className={`rounded border border-[#2A3548]/80 bg-[#0A0F1A]/35 ${className}`.trim()}
      data-testid={testId}
      data-expanded={open ? "true" : "false"}
    >
      <button
        type="button"
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
        onClick={() => setOpen(!open)}
        data-testid={`${testId}-toggle`}
        aria-expanded={open}
        aria-label={`${title}${open ? " — expandat" : " — restrâns"}`}
      >
        <div className="min-w-0 flex-1">
          <span className="block text-[12px] font-semibold text-slate-300">{title}</span>
          {hint && !open ? (
            <span className="mt-0.5 block text-[10px] font-normal normal-case text-slate-500">{hint}</span>
          ) : null}
        </div>
        {countLabel ? (
          <span
            className="shrink-0 rounded-full border border-[#2A3548] bg-[#111827]/80 px-2 py-0.5 text-[10px] font-semibold tabular-nums text-slate-400"
            data-testid={`${testId}-count`}
          >
            {countLabel}
          </span>
        ) : null}
        <ChevronDown
          className={`h-4 w-4 shrink-0 text-slate-500 transition ${open ? "rotate-180" : ""}`}
          aria-hidden
        />
      </button>
      {open ? (
        <div className="border-t border-[#2A3548] px-4 py-3" data-testid={`${testId}-content`}>
          {children}
        </div>
      ) : null}
    </div>
  );
}
