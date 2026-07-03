import { Link } from "react-router-dom";
import { Home, ShieldOff } from "lucide-react";
import {
  getEmployeeMobileRouteBlockedMessage,
  type EmployeeMobileRouteKey,
} from "@/lib/employeeMobileAccess";

type EmployeeMobileRouteBlockedProps = {
  routeKey: EmployeeMobileRouteKey;
};

export default function EmployeeMobileRouteBlocked({ routeKey }: EmployeeMobileRouteBlockedProps) {
  const message = getEmployeeMobileRouteBlockedMessage(routeKey);

  return (
    <div
      className="rounded-2xl border border-[#1E293B] bg-[#111827] p-5 space-y-4"
      data-testid="employee-mobile-route-blocked"
      data-route-key={routeKey}
    >
      <div className="flex items-start gap-3">
        <div
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400 ring-1 ring-amber-500/20"
          aria-hidden
        >
          <ShieldOff className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1 space-y-1.5">
          <h2 className="text-[15px] font-semibold text-slate-100">
            Această zonă nu este disponibilă pentru contul tău
          </h2>
          <p className="text-[12px] text-slate-400 leading-relaxed">{message}</p>
        </div>
      </div>
      <Link
        to="/employee-app"
        className="inline-flex items-center justify-center gap-2 rounded-xl border border-blue-800/40 bg-blue-950/30 px-4 py-2.5 text-[12px] font-medium text-blue-200 hover:bg-blue-950/50 transition-colors min-h-[44px]"
        data-testid="employee-mobile-route-blocked-home"
      >
        <Home className="w-4 h-4" aria-hidden />
        Înapoi la acasă
      </Link>
    </div>
  );
}
