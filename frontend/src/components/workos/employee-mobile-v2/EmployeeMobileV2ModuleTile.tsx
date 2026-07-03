import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import {
  emV2ModuleIconClass,
  emV2Controls,
  emV2Surface,
  type EmV2ModuleAccent,
} from "@/lib/employeeMobileV2DesignTokens";
import { v2Motion } from "@/lib/employeeMobileV2Effects";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2ModuleTile({
  to,
  title,
  icon: Icon,
  badge,
  accent = "slate",
  disabled = false,
  testId,
}: {
  to?: string;
  title: string;
  icon: LucideIcon;
  badge?: number | string;
  accent?: EmV2ModuleAccent;
  disabled?: boolean;
  testId: string;
}) {
  const showBadge =
    badge !== undefined && badge !== "…" && badge !== 0 && badge !== "0";

  const content = (
    <>
      {showBadge ? (
        <span
          className={emV2Controls.attentionDot}
          aria-label={`${badge} elemente`}
          title={String(badge)}
        />
      ) : null}
      <div className={emV2ModuleIconClass(accent)}>
        <Icon className="w-[22px] h-[22px]" aria-hidden />
      </div>
      <span className="text-[13px] font-medium text-slate-100 text-center leading-tight">
        {title}
      </span>
    </>
  );

  const className = cn(
    "relative flex min-h-[110px] flex-col items-center justify-center gap-2.5 rounded-2xl border p-4",
    disabled
      ? "border-[#1E293B]/60 bg-[#111827]/40 cursor-not-allowed opacity-60"
      : cn(emV2Surface.panel, "hover:border-[#2A3A4E]", v2Motion.moduleTile),
  );

  if (disabled || !to) {
    return (
      <div className={className} data-testid={testId} aria-disabled={disabled}>
        {content}
      </div>
    );
  }

  return (
    <Link to={to} className={className} data-testid={testId}>
      {content}
    </Link>
  );
}
