import { Link } from "react-router-dom";
import { ChevronLeft } from "lucide-react";
import { v2Motion } from "@/lib/employeeMobileV2Effects";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2PageHeader({
  backTo,
  backLabel = "Înapoi",
  title,
  subtitle,
  testId,
}: {
  backTo: string;
  backLabel?: string;
  title: string;
  subtitle?: string | null;
  testId?: string;
}) {
  return (
    <div className="mb-5 space-y-1" data-testid={testId}>
      <Link
        to={backTo}
        className={cn(
          "inline-flex min-h-[44px] items-center gap-1.5 text-[13px] text-slate-400 hover:text-slate-200",
          v2Motion.tapTarget,
        )}
        data-testid={testId ? `${testId}-back` : undefined}
      >
        <ChevronLeft className="w-4 h-4" aria-hidden />
        {backLabel}
      </Link>
      <h2 className="text-xl font-bold text-slate-100">{title}</h2>
      {subtitle ? <p className="text-[13px] text-slate-400">{subtitle}</p> : null}
    </div>
  );
}
