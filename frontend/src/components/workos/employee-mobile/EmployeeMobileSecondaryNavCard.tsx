import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

export default function EmployeeMobileSecondaryNavCard({
  to,
  title,
  subtitle,
  hint,
  icon: Icon,
  testId,
}: {
  to: string;
  title: string;
  subtitle: string;
  hint?: string;
  icon: LucideIcon;
  testId: string;
}) {
  return (
    <Link
      to={to}
      className={cn(
        "group flex items-center gap-2.5 rounded-xl border border-[#243044] bg-[#0A1020]/60",
        "px-3 py-2.5 transition-all hover:border-slate-500 active:scale-[0.99]",
      )}
      data-testid={testId}
    >
      <div
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-500/10 text-slate-400 ring-1 ring-slate-500/20"
        aria-hidden
      >
        <Icon className="w-4 h-4" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-semibold text-slate-100 truncate">{title}</p>
        <p className="text-[10px] text-slate-500 truncate">{subtitle}</p>
        {hint ? (
          <p className="text-[9px] text-slate-600 truncate mt-0.5" data-testid={`${testId}-hint`}>
            {hint}
          </p>
        ) : null}
      </div>
      <ChevronRight
        className="w-4 h-4 shrink-0 text-slate-600 group-hover:text-slate-400 transition-colors"
        aria-hidden
      />
    </Link>
  );
}
