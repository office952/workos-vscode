import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarDays, ClipboardList, RefreshCw } from "lucide-react";
import { listAttendanceEvents } from "@/api/employeeAttendance";
import { listEmployeeRequestsForReview } from "@/api/employeeRequestReview";

type EmployeeAdminOperationalSummaryProps = {
  employeeId: number;
};

function monthBounds(year: number, month: number): { start: string; end: string; label: string } {
  const lastDay = new Date(year, month, 0).getDate();
  const pad = (n: number) => String(n).padStart(2, "0");
  return {
    start: `${year}-${pad(month)}-01`,
    end: `${year}-${pad(month)}-${pad(lastDay)}`,
    label: `${pad(month)}.${year}`,
  };
}

export default function EmployeeAdminOperationalSummary({
  employeeId,
}: EmployeeAdminOperationalSummaryProps) {
  const now = new Date();
  const monthRange = useMemo(
    () => monthBounds(now.getFullYear(), now.getMonth() + 1),
    [now.getFullYear(), now.getMonth()],
  );

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [requestTotal, setRequestTotal] = useState(0);
  const [requestPending, setRequestPending] = useState(0);
  const [attendanceCount, setAttendanceCount] = useState(0);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [requests, attendance] = await Promise.all([
        listEmployeeRequestsForReview(),
        listAttendanceEvents({
          start_date: monthRange.start,
          end_date: monthRange.end,
          employee_id: employeeId,
        }),
      ]);
      const employeeRequests = requests.filter((row) => row.employee_id === employeeId);
      setRequestTotal(employeeRequests.length);
      setRequestPending(
        employeeRequests.filter((row) => row.status === "submitted" || row.status === "draft").length,
      );
      setAttendanceCount(attendance.length);
    } catch (err) {
      setRequestTotal(0);
      setRequestPending(0);
      setAttendanceCount(0);
      setError(err instanceof Error ? err.message : "Nu am putut încărca contextul operațional.");
    } finally {
      setLoading(false);
    }
  }, [employeeId, monthRange.end, monthRange.start]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <section
      className="bg-[#111827] border border-[#1E293B] rounded-lg p-4 space-y-3"
      data-testid="employee-admin-operational-summary"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-[13px] font-semibold text-slate-100">Context operațional</h3>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Rezumat cereri (review) și pontaj luna {monthRange.label} — read-only.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          disabled={loading}
          className="inline-flex items-center gap-1 px-2 py-1 text-[10px] text-slate-400 border border-[#243044] rounded-md hover:text-slate-200 disabled:opacity-50"
          data-testid="employee-admin-operational-refresh"
        >
          <RefreshCw className="w-3 h-3" aria-hidden />
          Reîncarcă
        </button>
      </div>

      {loading && (
        <p className="text-[11px] text-slate-500" data-testid="employee-admin-operational-loading">
          Se încarcă contextul operațional…
        </p>
      )}

      {!loading && error && (
        <p className="text-[11px] text-amber-300/90" data-testid="employee-admin-operational-error">
          {error}
        </p>
      )}

      {!loading && !error && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div
            className="rounded-lg border border-[#243044] bg-[#0A1020]/60 p-3 space-y-1"
            data-testid="employee-admin-operational-requests"
          >
            <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
              <ClipboardList className="w-3.5 h-3.5 text-blue-400" aria-hidden />
              Cereri angajat
            </div>
            <p className="text-[18px] font-bold text-slate-100">{requestTotal}</p>
            <p className="text-[10px] text-slate-500">
              {requestPending > 0
                ? `${requestPending} în așteptare (draft/trimise)`
                : "Nicio cerere în așteptare"}
            </p>
          </div>
          <div
            className="rounded-lg border border-[#243044] bg-[#0A1020]/60 p-3 space-y-1"
            data-testid="employee-admin-operational-attendance"
          >
            <div className="flex items-center gap-1.5 text-[11px] text-slate-300">
              <CalendarDays className="w-3.5 h-3.5 text-emerald-400" aria-hidden />
              Pontaj luna curentă
            </div>
            <p className="text-[18px] font-bold text-slate-100">{attendanceCount}</p>
            <p className="text-[10px] text-slate-500">
              {attendanceCount > 0
                ? "evenimente înregistrate"
                : "niciun eveniment în luna curentă"}
            </p>
          </div>
        </div>
      )}

      <p className="text-[10px] text-slate-600 leading-relaxed">
        Gestionarea cererilor se face în Employee Mobile (review) sau modulele dedicate — această
        secțiune este doar informativă.
      </p>
    </section>
  );
}
