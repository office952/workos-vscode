import { Smartphone, UserCheck, UserX } from "lucide-react";
import {
  getEmployeeMobileAccessDisplay,
  type EmployeeMobileAccessVariant,
} from "@/lib/employeeAdminAccess";
import type { EmployeeDTO } from "@/api/costEngine";
import { cn } from "@/lib/utils";

const VARIANT_STYLES: Record<
  EmployeeMobileAccessVariant,
  { className: string; Icon: typeof Smartphone }
> = {
  active: {
    className: "text-emerald-300 bg-emerald-900/25 border-emerald-700/45",
    Icon: Smartphone,
  },
  linked: {
    className: "text-amber-300 bg-amber-900/20 border-amber-700/40",
    Icon: UserCheck,
  },
  unlinked: {
    className: "text-slate-400 bg-slate-800/60 border-slate-600",
    Icon: UserX,
  },
};

type EmployeeMobileAccessBadgeProps = {
  employee: EmployeeDTO;
  compact?: boolean;
};

export default function EmployeeMobileAccessBadge({
  employee,
  compact = false,
}: EmployeeMobileAccessBadgeProps) {
  const access = getEmployeeMobileAccessDisplay(employee);
  const styles = VARIANT_STYLES[access.variant];
  const Icon = styles.Icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 text-[10px] font-semibold rounded-full border px-2 py-0.5",
        styles.className,
        compact && "px-1.5",
      )}
      data-testid="employee-mobile-access-badge"
      data-access-variant={access.variant}
      title={access.description}
    >
      <Icon className="w-3 h-3 shrink-0" aria-hidden />
      {access.label}
    </span>
  );
}
