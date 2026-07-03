import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { CalendarDays, ClipboardList, User, UserCheck } from "lucide-react";
import { listMyAttendanceEvents } from "@/api/employeeMobileAttendance";
import { listEmployeeRequests, type EmployeeRequestDTO } from "@/api/employeeMobileRequests";
import { useAuth } from "@/contexts/AuthContext";
import { useEmployeeMobileSelfLink } from "@/hooks/useEmployeeMobileSelfLink";
import EmployeeMobileAttendancePanel from "@/components/workos/employee-mobile/EmployeeMobileAttendancePanel";
import EmployeeMobileInfoAccessPage from "@/components/workos/employee-mobile/EmployeeMobileInfoAccessPage";
import EmployeeMobileProtectedRoute from "@/components/workos/employee-mobile/EmployeeMobileProtectedRoute";
import EmployeeMobileRequestsPanel from "@/components/workos/employee-mobile/EmployeeMobileRequestsPanel";
import EmployeeRequestReviewPanel from "@/components/workos/employee-mobile/EmployeeRequestReviewPanel";
import {
  canAccessRequestReviewWorkspace,
  employeeMobileAuthRoleLabel,
  shouldProbeEmployeeMobileSelfLink,
} from "@/lib/employeeMobileAccess";
import EmployeeMobileV2PageHeader from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PageHeader";
import EmployeeMobileV2PersonalPanelShell from "@/components/workos/employee-mobile-v2/EmployeeMobileV2PersonalPanelShell";
import { emV2Surface } from "@/lib/employeeMobileV2DesignTokens";
import { v2Effects } from "@/lib/employeeMobileV2Effects";
import { cn } from "@/lib/utils";

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

function PersonalRow({
  to,
  label,
  hint,
  icon: Icon,
  accentClass,
  testId,
}: {
  to: string;
  label: string;
  hint?: string;
  icon: typeof User;
  accentClass: string;
  testId: string;
}) {
  return (
    <Link
      to={to}
      className={cn(
        v2Effects.personalRow,
        "flex min-h-[56px] items-center gap-3 px-4 py-3 hover:border-[#2A3A4E]",
      )}
      data-testid={testId}
    >
      <div className={cn("flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px]", accentClass)}>
        <Icon className="w-[18px] h-[18px]" aria-hidden />
      </div>
      <span className="flex-1 text-[15px] font-medium text-slate-100">{label}</span>
      {hint ? <span className="text-[12px] text-slate-500">{hint}</span> : null}
    </Link>
  );
}

function EmployeeMobileV2PersonalHub() {
  const { user } = useAuth();
  const showReview = canAccessRequestReviewWorkspace(user?.role);
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
    <div data-testid="employee-mobile-v2-personal">
      <EmployeeMobileV2PageHeader
        backTo="/employee-app-v2"
        title="Personal"
        subtitle={user?.name ? `${user.name.split(" ")[0]} · ${employeeMobileAuthRoleLabel(user?.role)}` : undefined}
        testId="employee-mobile-v2-personal-header"
      />

      <div className="space-y-2" data-testid="employee-mobile-v2-personal-links">
        <PersonalRow
          to="/employee-app-v2/personal/requests"
          label="Cereri"
          hint={requestHint}
          icon={ClipboardList}
          accentClass="bg-amber-500/12 text-amber-400"
          testId="employee-mobile-v2-personal-requests"
        />
        <PersonalRow
          to="/employee-app-v2/personal/attendance"
          label="Pontaj"
          hint={attendanceHint}
          icon={CalendarDays}
          accentClass="bg-emerald-500/12 text-emerald-400"
          testId="employee-mobile-v2-personal-attendance"
        />
        <PersonalRow
          to="/employee-app-v2/personal/info"
          label="Profil"
          hint={profileHint}
          icon={User}
          accentClass="bg-slate-500/10 text-slate-400"
          testId="employee-mobile-v2-personal-profile-link"
        />
        {showReview ? (
          <PersonalRow
            to="/employee-app-v2/personal/review"
            label="Review cereri"
            icon={UserCheck}
            accentClass="bg-blue-500/12 text-blue-400"
            testId="employee-mobile-v2-personal-review"
          />
        ) : null}
      </div>

      <section
        className={cn(emV2Surface.panel, "mt-4 p-4 space-y-2")}
        data-testid="employee-mobile-v2-personal-profile"
      >
        <p className="text-[13px] font-semibold text-slate-100">Cont</p>
        <p className="text-[13px] text-slate-400 truncate">{user?.email}</p>
        <p
          className="text-[12px] font-medium text-emerald-400/90"
          data-testid="employee-mobile-v2-personal-role"
        >
          {employeeMobileAuthRoleLabel(user?.role)}
        </p>
      </section>
    </div>
  );
}

function PersonalSubpage({
  title,
  children,
  testId,
}: {
  title: string;
  children: React.ReactNode;
  testId: string;
}) {
  return (
    <div data-testid={testId}>
      <EmployeeMobileV2PageHeader
        backTo="/employee-app-v2/personal"
        backLabel="Înapoi la Personal"
        title={title}
        testId={`${testId}-header`}
      />
      {children}
    </div>
  );
}

export default function EmployeeMobileV2PersonalPage() {
  return (
    <Routes>
      <Route index element={<EmployeeMobileV2PersonalHub />} />
      <Route
        path="requests"
        element={
          <PersonalSubpage title="Cereri" testId="employee-mobile-v2-personal-requests-page">
            <EmployeeMobileV2PersonalPanelShell testId="employee-mobile-v2-personal-requests-skin">
              <EmployeeMobileRequestsPanel filterStyle="segmented" />
            </EmployeeMobileV2PersonalPanelShell>
          </PersonalSubpage>
        }
      />
      <Route
        path="attendance"
        element={
          <PersonalSubpage title="Pontaj" testId="employee-mobile-v2-personal-attendance-page">
            <EmployeeMobileV2PersonalPanelShell testId="employee-mobile-v2-personal-attendance-skin">
              <EmployeeMobileAttendancePanel />
            </EmployeeMobileV2PersonalPanelShell>
          </PersonalSubpage>
        }
      />
      <Route
        path="info"
        element={
          <PersonalSubpage title="Cont & acces" testId="employee-mobile-v2-personal-info-page">
            <EmployeeMobileInfoAccessPage />
          </PersonalSubpage>
        }
      />
      <Route
        path="review"
        element={
          <EmployeeMobileProtectedRoute routeKey="review">
            <PersonalSubpage title="Review cereri" testId="employee-mobile-v2-personal-review-page">
              <EmployeeRequestReviewPanel />
            </PersonalSubpage>
          </EmployeeMobileProtectedRoute>
        }
      />
    </Routes>
  );
}
