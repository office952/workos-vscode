import { Route, Routes, Outlet, useParams, Navigate } from "react-router-dom";
import EmployeeMobileHomeDashboard from "@/components/workos/employee-mobile/EmployeeMobileHomeDashboard";
import EmployeeMobileAttendancePanel from "@/components/workos/employee-mobile/EmployeeMobileAttendancePanel";
import EmployeeMobileOrderBlueprintPage from "@/components/workos/employee-mobile/EmployeeMobileOrderBlueprintPage";
import EmployeeMobileTasksPanel from "@/components/workos/employee-mobile/EmployeeMobileTasksPanel";
import EmployeeMobileInfoAccessPage from "@/components/workos/employee-mobile/EmployeeMobileInfoAccessPage";
import EmployeeMobilePersonalHub from "@/components/workos/employee-mobile/EmployeeMobilePersonalHub";
import EmployeeMobileRequestsPanel, {
  EmployeeMobileRequestsTabs,
} from "@/components/workos/employee-mobile/EmployeeMobileRequestsPanel";
import EmployeeRequestReviewPanel from "@/components/workos/employee-mobile/EmployeeRequestReviewPanel";
import EmployeeManagerTeamWorkspace from "@/pages/EmployeeManagerTeamWorkspace";
import {
  EmployeeMobileBottomNav,
  EmployeeMobileHeader,
} from "@/components/workos/employee-mobile/EmployeeMobileShell";
import EmployeeMobileProtectedRoute from "@/components/workos/employee-mobile/EmployeeMobileProtectedRoute";
import { EmployeeMobileEmptyState } from "@/components/workos/employee-mobile/EmployeeMobileStates";

export type EmployeeMobileSectionStatus =
  | "Blueprint"
  | "Read-only planned"
  | "Needs auth"
  | "Needs backend"
  | "Foundation in backend"
  | "Self-only live"
  | "Manager review live";

export type EmployeeMobileSection = {
  id: string;
  title: string;
  description: string;
  path: string;
  status: EmployeeMobileSectionStatus;
};

/** Blueprint sections — not on main dashboard; routes kept for future builds. */
export const EMPLOYEE_MOBILE_SECTIONS: EmployeeMobileSection[] = [
  {
    id: "today",
    title: "Azi",
    description: "Program, pontaj, taskuri și montaje pentru ziua curentă.",
    path: "today",
    status: "Blueprint",
  },
  {
    id: "tasks",
    title: "Taskurile mele",
    description: "Taskuri alocate din execuție / producție — start, blocare, finalizare.",
    path: "tasks",
    status: "Self-only live",
  },
  {
    id: "installations",
    title: "Montaje",
    description: "Lucrări pe teren, echipă, checklist, materiale.",
    path: "installations",
    status: "Needs backend",
  },
  {
    id: "attendance",
    title: "Pontaj",
    description: "Vizualizare read-only a pontajului propriu.",
    path: "attendance",
    status: "Self-only live",
  },
  {
    id: "requests",
    title: "Cereri",
    description: "Cererile mele — listă, creare și anulare self-only.",
    path: "requests",
    status: "Self-only live",
  },
  {
    id: "review",
    title: "Review cereri",
    description: "Inbox manager/admin — aprobare/respingere fără side effects.",
    path: "review",
    status: "Manager review live",
  },
  {
    id: "balances",
    title: "Solduri interne",
    description: "Sold ledger intern — read-only.",
    path: "balances",
    status: "Needs auth",
  },
  {
    id: "payments",
    title: "Plăți interne",
    description: "Plăți interne confirmate — fără payroll fiscal.",
    path: "payments",
    status: "Needs auth",
  },
  {
    id: "notes",
    title: "Note",
    description: "Anunțuri, note manager, observații task.",
    path: "notes",
    status: "Blueprint",
  },
];

function EmployeeMobileBlueprintPage({ section }: { section: EmployeeMobileSection }) {
  return (
    <div className="space-y-4" data-testid={`employee-mobile-section-${section.id}`}>
      <h2 className="text-[15px] font-semibold text-slate-100">{section.title}</h2>
      <p className="text-[13px] text-slate-300">{section.description}</p>
      <EmployeeMobileEmptyState message="Secțiune planificată — disponibilă într-un build viitor." />
    </div>
  );
}

function EmployeeMobileOrderBlueprintRoute() {
  const { orderId } = useParams();
  const parsed = Number(orderId);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return <Navigate to="/employee-app/tasks" replace />;
  }
  return <EmployeeMobileOrderBlueprintPage orderId={parsed} />;
}

function EmployeeMobileLayout() {
  return (
    <div
      className="mx-auto w-full max-w-lg min-h-[100dvh] space-y-3 pb-[calc(7rem+env(safe-area-inset-bottom,0px))] pt-[calc(0.5rem+env(safe-area-inset-top,0px))] px-3 sm:px-4 bg-[#070B14]"
      data-testid="employee-mobile-shell"
    >
      <EmployeeMobileHeader />
      <Outlet />
      <EmployeeMobileBottomNav />
    </div>
  );
}

export default function EmployeeMobileApp() {
  return (
    <Routes>
      <Route element={<EmployeeMobileLayout />}>
        <Route index element={<EmployeeMobileHomeDashboard />} />
        <Route path="requests" element={<EmployeeMobileRequestsPanel />} />
        <Route
          path="team"
          element={
            <EmployeeMobileProtectedRoute routeKey="team">
              <EmployeeManagerTeamWorkspace />
            </EmployeeMobileProtectedRoute>
          }
        />
        <Route
          path="review"
          element={
            <EmployeeMobileProtectedRoute routeKey="review">
              <div className="space-y-4" data-testid="employee-mobile-section-review">
                <EmployeeMobileRequestsTabs />
                <EmployeeRequestReviewPanel />
              </div>
            </EmployeeMobileProtectedRoute>
          }
        />
        <Route
          path="attendance"
          element={
            <div className="space-y-4" data-testid="employee-mobile-section-attendance">
              <EmployeeMobileAttendancePanel />
            </div>
          }
        />
        <Route
          path="tasks/orders/:orderId/blueprint"
          element={<EmployeeMobileOrderBlueprintRoute />}
        />
        <Route
          path="tasks"
          element={
            <div className="space-y-4" data-testid="employee-mobile-section-tasks-shell">
              <EmployeeMobileTasksPanel />
            </div>
          }
        />
        <Route
          path="personal"
          element={
            <div className="space-y-4" data-testid="employee-mobile-section-personal">
              <EmployeeMobilePersonalHub />
            </div>
          }
        />
        <Route
          path="info"
          element={
            <div className="space-y-4" data-testid="employee-mobile-section-info">
              <EmployeeMobileInfoAccessPage />
            </div>
          }
        />
        {EMPLOYEE_MOBILE_SECTIONS.filter(
          (s) => !["requests", "review", "attendance", "tasks"].includes(s.id),
        ).map((section) => (
          <Route
            key={section.id}
            path={section.path}
            element={<EmployeeMobileBlueprintPage section={section} />}
          />
        ))}
      </Route>
    </Routes>
  );
}
