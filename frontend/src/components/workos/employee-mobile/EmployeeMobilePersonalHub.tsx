import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CalendarDays, ClipboardList, User } from "lucide-react";
import { listMyAttendanceEvents } from "@/api/employeeMobileAttendance";
import { listEmployeeRequests, type EmployeeRequestDTO } from "@/api/employeeMobileRequests";
import { useAuth } from "@/contexts/AuthContext";
import { useEmployeeMobileSelfLink } from "@/hooks/useEmployeeMobileSelfLink";
import {
  canAccessManagerTeamWorkspace,
  canAccessRequestReviewWorkspace,
  employeeMobileAuthRoleLabel,
  shouldProbeEmployeeMobileSelfLink,
} from "@/lib/employeeMobileAccess";
import EmployeeMobileAdminShortcuts from "@/components/workos/employee-mobile/EmployeeMobileAdminShortcuts";
import EmployeeMobileSecondaryNavCard from "@/components/workos/employee-mobile/EmployeeMobileSecondaryNavCard";
import { EmployeeMobileStatusBadge } from "@/components/workos/employee-mobile/EmployeeMobileStates";

function monthBounds(year: number, month: number): { start: string; end: string } {
  const lastDay = new Date(year, month, 0).getDate();
  const pad = (n: number) => String(n).padStart(2, "0");
  return {
    start: `${year}-${pad(month)}-01`,
    end: `${year}-${pad(month)}-${pad(lastDay)}`,
  };
}

function summarizeRequests(rows: EmployeeRequestDTO[]) {
  const pending = rows.filter((r) => r.status === "submitted" || r.status === "draft").length;
  return { pending, total: rows.length };
}

export default function EmployeeMobilePersonalHub() {
  const { user } = useAuth();
  const showReview = canAccessRequestReviewWorkspace(user?.role);
  const showTeam = canAccessManagerTeamWorkspace(user?.role);
  const probeSelfLink = shouldProbeEmployeeMobileSelfLink(user?.role);
  const { state: linkState, employeeName } = useEmployeeMobileSelfLink(probeSelfLink);

  const monthRange = useMemo(() => {
    const now = new Date();
    return monthBounds(now.getFullYear(), now.getMonth() + 1);
  }, []);

  const [requestHint, setRequestHint] = useState<string | undefined>();
  const [attendanceHint, setAttendanceHint] = useState<string | undefined>();

  const loadHints = useCallback(async () => {
    try {
      const [requests, attendance] = await Promise.all([
        listEmployeeRequests(),
        listMyAttendanceEvents({
          start_date: monthRange.start,
          end_date: monthRange.end,
        }),
      ]);
      const summary = summarizeRequests(requests);
      setRequestHint(
        summary.total === 0 ? "Nicio cerere" : `${summary.pending} în așteptare`,
      );
      setAttendanceHint(
        attendance.length === 0 ? "Luna curentă" : `${attendance.length} evenimente`,
      );
    } catch {
      setRequestHint(undefined);
      setAttendanceHint(undefined);
    }
  }, [monthRange.end, monthRange.start]);

  useEffect(() => {
    void loadHints();
  }, [loadHints]);

  const profileHint =
    employeeName ??
    (linkState === "linked" ? user?.name : undefined) ??
    (probeSelfLink && linkState === "missing" ? "Profil nelinkat" : undefined);

  return (
    <div className="space-y-4" data-testid="employee-mobile-personal-hub">
      <div className="px-0.5">
        <h2 className="text-[15px] font-semibold text-slate-100">Personal</h2>
        <p className="text-[11px] text-slate-500 mt-0.5">Cereri, pontaj și profilul tău</p>
      </div>

      <div className="space-y-2" data-testid="employee-mobile-personal-links">
        <EmployeeMobileSecondaryNavCard
          to="/employee-app/requests"
          title="Cereri"
          subtitle="Concedii, avansuri, alte solicitări"
          hint={requestHint}
          icon={ClipboardList}
          testId="employee-mobile-personal-requests"
        />
        <EmployeeMobileSecondaryNavCard
          to="/employee-app/attendance"
          title="Pontaj"
          subtitle="Evenimente luna curentă — read-only"
          hint={attendanceHint}
          icon={CalendarDays}
          testId="employee-mobile-personal-attendance"
        />
      </div>

      <section
        className="rounded-xl border border-[#243044] bg-[#0A1020]/60 px-3 py-3 space-y-2"
        data-testid="employee-mobile-personal-profile"
      >
        <div className="flex items-start gap-2.5">
          <div
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-500/10 text-slate-400 ring-1 ring-slate-500/20"
            aria-hidden
          >
            <User className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-[13px] font-semibold text-slate-100">Profil</p>
            <p className="text-[11px] text-slate-300 truncate mt-0.5">
              {user?.name ?? user?.email ?? "Utilizator"}
            </p>
            {user?.email && user.name ? (
              <p className="text-[10px] text-slate-500 truncate">{user.email}</p>
            ) : null}
            {profileHint && employeeName ? (
              <p className="text-[10px] text-emerald-300/90 mt-1">{employeeName}</p>
            ) : null}
          </div>
          <EmployeeMobileStatusBadge
            label={employeeMobileAuthRoleLabel(user?.role)}
            variant="live"
            testId="employee-mobile-personal-profile-role"
          />
        </div>
        <Link
          to="/employee-app/info"
          className="inline-flex text-[11px] font-medium text-blue-300 hover:text-blue-200"
          data-testid="employee-mobile-personal-profile-info-link"
        >
          Cont, acces și instalare →
        </Link>
      </section>

      {(showReview || showTeam) && (
        <section className="space-y-2 pt-1" data-testid="employee-mobile-personal-manager">
          <p className="text-[11px] font-medium text-slate-400 px-0.5">Management</p>
          <EmployeeMobileAdminShortcuts showReview={showReview} showTeam={showTeam} />
        </section>
      )}
    </div>
  );
}
