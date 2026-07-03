import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

type NavAccent = "emerald" | "blue" | "amber" | "red" | "violet" | "slate";

const ACCENT_STYLES: Record<NavAccent, { icon: string; border: string; count: string }> = {
  emerald: {
    icon: "bg-emerald-500/15 text-emerald-400 ring-emerald-500/25",
    border: "hover:border-emerald-700/40",
    count: "text-emerald-300",
  },
  blue: {
    icon: "bg-blue-500/15 text-blue-400 ring-blue-500/25",
    border: "hover:border-blue-700/40",
    count: "text-blue-300",
  },
  amber: {
    icon: "bg-amber-500/15 text-amber-400 ring-amber-500/25",
    border: "hover:border-amber-700/40",
    count: "text-amber-300",
  },
  red: {
    icon: "bg-red-500/15 text-red-400 ring-red-500/25",
    border: "hover:border-red-700/40",
    count: "text-red-300",
  },
  violet: {
    icon: "bg-violet-500/15 text-violet-400 ring-violet-500/25",
    border: "hover:border-violet-700/40",
    count: "text-violet-300",
  },
  slate: {
    icon: "bg-slate-500/15 text-slate-300 ring-slate-500/25",
    border: "hover:border-slate-600/40",
    count: "text-slate-200",
  },
};

export default function EmployeeMobileNavCard({
  to,
  title,
  subtitle,
  count,
  icon: Icon,
  accent = "slate",
  prominent = false,
  testId,
}: {
  to: string;
  title: string;
  subtitle: string;
  count: number | string;
  icon: LucideIcon;
  accent?: NavAccent;
  prominent?: boolean;
  testId: string;
}) {
  const styles = ACCENT_STYLES[accent];

  return (
    <Link
      to={to}
      className={cn(
        "group flex items-center gap-3 rounded-xl border bg-[#0A1020]/80 px-3 py-3 transition-all active:scale-[0.99]",
        prominent ? "border-red-800/50 bg-red-950/20" : "border-[#243044]",
        styles.border,
      )}
      data-testid={testId}
    >
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ring-1",
          styles.icon,
        )}
        aria-hidden
      >
        <Icon className="w-5 h-5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex items-center justify-between gap-2">
          <p className="text-[13px] font-semibold text-slate-100 truncate">{title}</p>
          <span className={cn("text-[15px] font-bold tabular-nums shrink-0", styles.count)}>
            {count}
          </span>
        </div>
        <p className="text-[10px] text-slate-500 truncate mt-0.5">{subtitle}</p>
      </div>
      <ChevronRight
        className="w-4 h-4 shrink-0 text-slate-600 group-hover:text-slate-400 transition-colors"
        aria-hidden
      />
    </Link>
  );
}
