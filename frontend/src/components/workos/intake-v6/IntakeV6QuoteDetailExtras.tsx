import { useState, type ReactNode } from "react";
import { ChevronDown, ChevronUp, FolderOpen } from "lucide-react";

type Props = {
  children: ReactNode;
  defaultOpen?: boolean;
};

export default function IntakeV6QuoteDetailExtras({ children, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div
      className="rounded-lg border border-[#1E293B] bg-[#111827] overflow-hidden"
      data-testid="intake-v6-quote-detail-extras"
    >
      <button
        type="button"
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left hover:bg-[#151d2e] transition-colors"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <span className="flex items-center gap-2 text-[12px] font-semibold text-slate-300">
          <FolderOpen className="h-4 w-4 text-slate-500" />
          Documente & preview avansat
        </span>
        {open ? (
          <ChevronUp className="h-4 w-4 text-slate-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-slate-500" />
        )}
      </button>
      {open ? <div className="space-y-4 border-t border-[#1E293B] p-4">{children}</div> : null}
    </div>
  );
}
