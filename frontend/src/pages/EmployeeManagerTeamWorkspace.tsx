import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  listManagerTeamAttendance,
  listManagerTeamRequests,
  type ManagerTeamAttendanceEventDTO,
  type ManagerTeamRequestDTO,
} from "@/api/employeeManagerTeam";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
  EmployeeMobileSectionCard,
  EmployeeMobileStatusBadge,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";

type TeamTab = "attendance" | "requests";

function monthBounds(year: number, month: number): { start: string; end: string; label: string } {
  const lastDay = new Date(year, month, 0).getDate();
  const pad = (n: number) => String(n).padStart(2, "0");
  return {
    start: `${year}-${pad(month)}-01`,
    end: `${year}-${pad(month)}-${pad(lastDay)}`,
    label: `${pad(month)}.${year}`,
  };
}

const REQUEST_STATUS_OPTIONS = [
  { value: "", label: "Toate statusurile" },
  { value: "submitted", label: "În așteptare" },
  { value: "approved", label: "Aprobate" },
  { value: "rejected", label: "Respinse" },
  { value: "cancelled", label: "Anulate" },
];

function formatDateRange(start?: string | null, end?: string | null): string {
  if (!start) return "—";
  if (!end || end === start) return start;
  return `${start} → ${end}`;
}

export default function EmployeeManagerTeamWorkspace() {
  const now = new Date();
  const defaultMonth = useMemo(
    () => monthBounds(now.getFullYear(), now.getMonth() + 1),
    [now.getFullYear(), now.getMonth()],
  );

  const [tab, setTab] = useState<TeamTab>("attendance");
  const [monthLabel, setMonthLabel] = useState(defaultMonth.label);
  const [rangeStart, setRangeStart] = useState(defaultMonth.start);
  const [rangeEnd, setRangeEnd] = useState(defaultMonth.end);
  const [requestStatus, setRequestStatus] = useState("");

  const [attendanceLoading, setAttendanceLoading] = useState(true);
  const [attendanceError, setAttendanceError] = useState<string | null>(null);
  const [attendanceRows, setAttendanceRows] = useState<ManagerTeamAttendanceEventDTO[]>([]);

  const [requestsLoading, setRequestsLoading] = useState(true);
  const [requestsError, setRequestsError] = useState<string | null>(null);
  const [requestRows, setRequestRows] = useState<ManagerTeamRequestDTO[]>([]);

  const loadAttendance = useCallback(async () => {
    setAttendanceLoading(true);
    setAttendanceError(null);
    try {
      const rows = await listManagerTeamAttendance({
        start_date: rangeStart,
        end_date: rangeEnd,
      });
      setAttendanceRows(rows);
    } catch (err) {
      setAttendanceRows([]);
      setAttendanceError(
        err instanceof Error ? err.message : "Nu am putut încărca pontajul echipei.",
      );
    } finally {
      setAttendanceLoading(false);
    }
  }, [rangeEnd, rangeStart]);

  const loadRequests = useCallback(async () => {
    setRequestsLoading(true);
    setRequestsError(null);
    try {
      const rows = await listManagerTeamRequests({
        status: requestStatus || undefined,
      });
      setRequestRows(rows);
    } catch (err) {
      setRequestRows([]);
      setRequestsError(
        err instanceof Error ? err.message : "Nu am putut încărca cererile echipei.",
      );
    } finally {
      setRequestsLoading(false);
    }
  }, [requestStatus]);

  useEffect(() => {
    if (tab === "attendance") {
      void loadAttendance();
    }
  }, [tab, loadAttendance]);

  useEffect(() => {
    if (tab === "requests") {
      void loadRequests();
    }
  }, [tab, loadRequests]);

  const pendingCount = useMemo(
    () => requestRows.filter((r) => r.status === "submitted").length,
    [requestRows],
  );

  return (
    <div className="space-y-4" data-testid="employee-manager-team-workspace">
      <div className="space-y-1">
        <h2 className="text-[16px] font-semibold text-slate-100">Echipa mea</h2>
        <p className="text-[12px] text-slate-400" data-testid="employee-manager-team-subtitle">
          Vizualizare read-only pentru angajații care raportează direct către tine.
        </p>
        <p
          className="text-[11px] text-slate-500"
          data-testid="employee-manager-team-readonly-guard"
        >
          Această zonă este doar pentru vizualizare. Modificările de pontaj rămân disponibile doar
          pentru admin/operator.
        </p>
      </div>

      <div
        className="flex gap-2 border-b border-wo-border-subtle pb-2"
        role="tablist"
        data-testid="employee-manager-team-tabs"
      >
        <button
          type="button"
          role="tab"
          aria-selected={tab === "attendance"}
          className={
            tab === "attendance"
              ? "rounded-lg bg-blue-900/40 px-3 py-1.5 text-[12px] font-medium text-blue-200"
              : "rounded-lg px-3 py-1.5 text-[12px] text-slate-400 hover:text-slate-200"
          }
          onClick={() => setTab("attendance")}
          data-testid="employee-manager-team-tab-attendance"
        >
          Pontaj echipă
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === "requests"}
          className={
            tab === "requests"
              ? "rounded-lg bg-blue-900/40 px-3 py-1.5 text-[12px] font-medium text-blue-200"
              : "rounded-lg px-3 py-1.5 text-[12px] text-slate-400 hover:text-slate-200"
          }
          onClick={() => setTab("requests")}
          data-testid="employee-manager-team-tab-requests"
        >
          Cereri echipă
        </button>
      </div>

      {tab === "attendance" && (
        <section className="space-y-3" data-testid="employee-manager-team-attendance-panel">
          <div className="flex flex-wrap items-center gap-2">
            <EmployeeMobileStatusBadge label="Read-only" variant="readonly" />
            <label className="text-[11px] text-slate-400">
              Lună
              <input
                type="month"
                className="ml-2 rounded border border-wo-border-subtle bg-[#0A1020] px-2 py-1 text-[11px] text-slate-200"
                defaultValue={`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`}
                onChange={(e) => {
                  const [y, m] = e.target.value.split("-").map(Number);
                  const bounds = monthBounds(y, m);
                  setRangeStart(bounds.start);
                  setRangeEnd(bounds.end);
                  setMonthLabel(bounds.label);
                }}
                data-testid="employee-manager-team-attendance-month"
              />
            </label>
            <span className="text-[10px] text-slate-500">{monthLabel}</span>
          </div>

          {attendanceLoading && (
            <EmployeeMobileLoadingState
              message="Se încarcă pontajul echipei…"
              testId="employee-manager-team-attendance-loading"
            />
          )}
          {!attendanceLoading && attendanceError && (
            <EmployeeMobileErrorState
              message={attendanceError}
              testId="employee-manager-team-attendance-error"
            />
          )}
          {!attendanceLoading && !attendanceError && attendanceRows.length === 0 && (
            <EmployeeMobileEmptyState
              message="Nu ai angajați alocați ca raportare directă sau nu există date pentru filtrele selectate."
              testId="employee-manager-team-attendance-empty"
            />
          )}
          {!attendanceLoading && !attendanceError && attendanceRows.length > 0 && (
            <ul className="space-y-2" data-testid="employee-manager-team-attendance-list">
              {attendanceRows.map((row) => (
                <li
                  key={row.id}
                  className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised p-3 space-y-1"
                  data-testid={`employee-manager-team-attendance-row-${row.id}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[13px] font-medium text-slate-100">{row.employee_name}</span>
                    <EmployeeMobileStatusBadge label={row.event_type} variant="readonly" />
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {formatDateRange(row.start_date, row.end_date)} · {row.event_status}
                  </p>
                  <p className="text-[10px] text-slate-500">Sursă: {row.source}</p>
                  {row.notes && (
                    <p className="text-[10px] text-slate-500 truncate">{row.notes}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      {tab === "requests" && (
        <section className="space-y-3" data-testid="employee-manager-team-requests-panel">
          <div className="flex flex-wrap items-center gap-2">
            <label className="text-[11px] text-slate-400">
              Status
              <select
                className="ml-2 rounded border border-wo-border-subtle bg-[#0A1020] px-2 py-1 text-[11px] text-slate-200"
                value={requestStatus}
                onChange={(e) => setRequestStatus(e.target.value)}
                data-testid="employee-manager-team-requests-status"
              >
                {REQUEST_STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value || "all"} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
            {pendingCount > 0 && (
              <Link
                to="/employee-app/review"
                className="text-[11px] text-blue-300 hover:underline"
                data-testid="employee-manager-team-review-link"
              >
                {pendingCount} în așteptare — deschide review
              </Link>
            )}
          </div>

          {requestsLoading && (
            <EmployeeMobileLoadingState
              message="Se încarcă cererile echipei…"
              testId="employee-manager-team-requests-loading"
            />
          )}
          {!requestsLoading && requestsError && (
            <EmployeeMobileErrorState
              message={requestsError}
              testId="employee-manager-team-requests-error"
            />
          )}
          {!requestsLoading && !requestsError && requestRows.length === 0 && (
            <EmployeeMobileEmptyState
              message="Nu ai angajați alocați ca raportare directă sau nu există date pentru filtrele selectate."
              testId="employee-manager-team-requests-empty"
            />
          )}
          {!requestsLoading && !requestsError && requestRows.length > 0 && (
            <ul className="space-y-2" data-testid="employee-manager-team-requests-list">
              {requestRows.map((row) => (
                <li
                  key={row.id}
                  className="rounded-lg border border-wo-border-subtle bg-wo-surface-raised p-3 space-y-1"
                  data-testid={`employee-manager-team-request-row-${row.id}`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[13px] font-medium text-slate-100">{row.employee_name}</span>
                    <EmployeeMobileStatusBadge
                      label={row.status}
                      variant={row.status === "submitted" ? "review" : "readonly"}
                    />
                  </div>
                  <p className="text-[11px] text-slate-400">
                    {row.request_type} · {formatDateRange(row.start_date, row.end_date)}
                  </p>
                  {row.title && (
                    <p className="text-[11px] text-slate-300">{row.title}</p>
                  )}
                  {row.status === "submitted" && (
                    <Link
                      to="/employee-app/review"
                      className="inline-block text-[10px] text-blue-300 hover:underline"
                      data-testid={`employee-manager-team-request-review-${row.id}`}
                    >
                      Review în inbox
                    </Link>
                  )}
                </li>
              ))}
            </ul>
          )}
        </section>
      )}

      <EmployeeMobileSectionCard
        title="Review cereri"
        description="Aprobarea și respingerea se fac în inbox-ul de review — nu din această zonă."
        to="/employee-app/review"
        badge={<EmployeeMobileStatusBadge label="Review" variant="review" />}
        testId="employee-manager-team-review-card"
      />
    </div>
  );
}
