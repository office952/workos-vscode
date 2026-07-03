import { Link } from "react-router-dom";
import { UserCheck, Users } from "lucide-react";
import { cn } from "@/lib/utils";

function ManagerShortcut({
  to,
  label,
  icon: Icon,
  testId,
}: {
  to: string;
  label: string;
  icon: typeof UserCheck;
  testId: string;
}) {
  return (
    <Link
      to={to}
      className={cn(
        "flex flex-col items-center justify-center gap-1 rounded-xl border border-[#243044]",
        "bg-[#0A1020]/60 px-2 py-2.5 min-h-[64px] text-center",
        "hover:border-slate-500 transition-colors active:scale-[0.99]",
      )}
      data-testid={testId}
    >
      <Icon className="w-4 h-4 text-slate-400" aria-hidden />
      <span className="text-[11px] font-medium text-slate-200 leading-tight">{label}</span>
    </Link>
  );
}

/** Manager/admin shortcuts — Review and Echipa only; shown on Personal hub, not Home. */
export default function EmployeeMobileAdminShortcuts({
  showReview,
  showTeam,
}: {
  showReview?: boolean;
  showTeam?: boolean;
}) {
  if (!showReview && !showTeam) return null;

  return (
    <div
      className={cn("grid gap-2", showReview && showTeam ? "grid-cols-2" : "grid-cols-1")}
      data-testid="employee-mobile-admin-shortcuts"
    >
      {showTeam && (
        <ManagerShortcut
          to="/employee-app/team"
          label="Echipa mea"
          icon={Users}
          testId="employee-mobile-dashboard-team"
        />
      )}
      {showReview && (
        <ManagerShortcut
          to="/employee-app/review"
          label="Review"
          icon={UserCheck}
          testId="employee-mobile-dashboard-review"
        />
      )}
    </div>
  );
}
