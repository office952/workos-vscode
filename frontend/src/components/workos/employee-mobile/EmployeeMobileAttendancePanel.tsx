import { useCallback, useEffect, useMemo, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { listMyAttendanceEvents } from "@/api/employeeMobileAttendance";
import type { AttendanceEventDTO } from "@/api/employeeAttendance";
import {
  EmployeeMobileEmptyState,
  EmployeeMobileErrorState,
  EmployeeMobileLoadingState,
  EmployeeMobileStatusBadge,
} from "@/components/workos/employee-mobile/EmployeeMobileStates";
import {
  ATTENDANCE_EVENT_STATUS_LABELS,
  ATTENDANCE_EVENT_TYPE_LABELS,
  formatDisplayDate,
  formatMonthYearLabel,
} from "@/lib/employeeMobileUiHelpers";
import { cn } from "@/lib/utils";

const STATUS_STYLES: Record<string, string> = {
  planned: "bg-slate-700/60 text-slate-300 border-slate-600",
  approved: "bg-blue-900/30 text-blue-300 border-blue-800/40",
  confirmed: "bg-emerald-900/30 text-emerald-300 border-emerald-800/40",
  cancelled: "bg-red-900/20 text-red-300 border-red-800/40",
};

function monthBounds(year: number, month: number): { start: string; end: string } {
  const lastDay = new Date(year, month, 0).getDate();
  const pad = (n: number) => String(n).padStart(2, "0");
  return {
    start: `${year}-${pad(month)}-01`,
    end: `${year}-${pad(month)}-${pad(lastDay)}`,
  };
}

function formatRange(ev: AttendanceEventDTO): string {
  const start = formatDisplayDate(ev.start_date);
  const end = formatDisplayDate(ev.end_date);
  if (!start) return "—";
  return start === end ? start : `${start} – ${end}`;
}

function summarizeEventTypes(events: AttendanceEventDTO[]) {
  const counts = new Map<string, number>();
  for (const ev of events) {
    const label = ATTENDANCE_EVENT_TYPE_LABELS[ev.event_type] ?? ev.event_type;
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

export default function EmployeeMobileAttendancePanel() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [events, setEvents] = useState<AttendanceEventDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const range = useMemo(() => monthBounds(year, month), [year, month]);
  const isCurrentMonth = year === now.getFullYear() && month === now.getMonth() + 1;
  const monthLabel = formatMonthYearLabel(year, month);

  const sortedEvents = useMemo(
    () => [...events].sort((a, b) => a.start_date.localeCompare(b.start_date)),
    [events],
  );
  const typeSummary = useMemo(() => summarizeEventTypes(events), [events]);

  const loadEvents = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listMyAttendanceEvents({
        start_date: range.start,
        end_date: range.end,
      });
      setEvents(rows);
    } catch (err) {
      setEvents([]);
      setError(err instanceof Error ? err.message : "Nu am putut încărca pontajul.");
    } finally {
      setLoading(false);
    }
  }, [range.end, range.start]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  const shiftMonth = (delta: number) => {
    const d = new Date(year, month - 1 + delta, 1);
    setYear(d.getFullYear());
    setMonth(d.getMonth() + 1);
  };

  return (
    <div className="space-y-4" data-testid="employee-mobile-attendance-panel">
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <div className="flex items-center gap-2">
            <CalendarDays className="w-4 h-4 text-blue-400" aria-hidden />
            <h2 className="text-[15px] font-semibold text-slate-100">Pontajul meu</h2>
          </div>
          <EmployeeMobileStatusBadge label="Read-only" variant="readonly" testId="employee-mobile-attendance-readonly-badge" />
        </div>
        <p className="text-[12px] text-slate-400 leading-relaxed">
          Evenimente de prezență, absență, concediu sau ore suplimentare — doar vizualizare. Pentru
          corecții, folosește o cerere de tip „Corecție pontaj”.
        </p>
        <p className="sr-only" data-testid="employee-mobile-attendance-no-employee-id">
          Identitatea angajatului este rezolvată server-side.
        </p>
      </div>

      <div className="flex items-center justify-between gap-2 flex-wrap rounded-2xl border border-[#1E293B] bg-[#111827] p-3">
        <div className="flex items-center gap-2 min-w-0">
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[#243044] text-slate-300 hover:border-slate-500 hover:bg-[#0A1020]"
            aria-label="Luna anterioară"
            onClick={() => shiftMonth(-1)}
          >
            <ChevronLeft className="w-4 h-4" aria-hidden />
          </button>
          <div className="min-w-0 text-center">
            <p className="text-[12px] text-slate-200 font-medium tabular-nums truncate">{monthLabel}</p>
            {isCurrentMonth && (
              <p className="text-[10px] text-blue-400/90" data-testid="employee-mobile-attendance-current-month">
                Luna curentă
              </p>
            )}
          </div>
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[#243044] text-slate-300 hover:border-slate-500 hover:bg-[#0A1020]"
            aria-label="Luna următoare"
            onClick={() => shiftMonth(1)}
          >
            <ChevronRight className="w-4 h-4" aria-hidden />
          </button>
        </div>
        <button
          type="button"
          className="inline-flex items-center gap-1.5 text-[11px] text-blue-400 hover:text-blue-300 disabled:opacity-50 min-h-[32px] px-2"
          data-testid="employee-mobile-attendance-refresh"
          onClick={() => void loadEvents()}
          disabled={loading}
        >
          <RefreshCw className={cn("w-3.5 h-3.5", loading && "animate-spin")} aria-hidden />
          Reîmprospătează
        </button>
      </div>

      <section className="rounded-xl border border-[#1E293B] bg-[#111827] p-4 space-y-3">
        {loading && (
          <EmployeeMobileLoadingState
            message="Se încarcă pontajul…"
            testId="employee-mobile-attendance-loading"
          />
        )}

        {!loading && error && (
          <EmployeeMobileErrorState message={error} testId="employee-mobile-attendance-error" />
        )}

        {!loading && !error && events.length === 0 && (
          <EmployeeMobileEmptyState
            message={`Nu există evenimente de pontaj în ${monthLabel.toLowerCase()}.`}
            testId="employee-mobile-attendance-empty"
          />
        )}

        {!loading && !error && events.length > 0 && (
          <>
            {typeSummary.length > 0 && (
              <div
                className="flex flex-wrap gap-1.5"
                data-testid="employee-mobile-attendance-summary"
              >
                {typeSummary.map(([label, count]) => (
                  <span
                    key={label}
                    className="inline-flex px-2 py-1 text-[10px] rounded-full border border-[#243044] bg-[#0A1020] text-slate-400"
                  >
                    {label}: {count}
                  </span>
                ))}
              </div>
            )}
            <ul className="space-y-3" data-testid="employee-mobile-attendance-list">
              {sortedEvents.map((ev) => (
                <li
                  key={ev.id}
                  className="rounded-xl border border-[#243044] bg-[#0A1020] p-3 space-y-2"
                  data-testid={`employee-mobile-attendance-item-${ev.id}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <p className="text-[12px] font-semibold text-slate-100">
                        {ATTENDANCE_EVENT_TYPE_LABELS[ev.event_type] ?? ev.event_type}
                      </p>
                      <p className="text-[11px] text-slate-400">{formatRange(ev)}</p>
                    </div>
                    <span
                      className={cn(
                        "inline-flex px-2 py-0.5 text-[9px] font-semibold rounded-full border uppercase shrink-0",
                        STATUS_STYLES[ev.event_status] ?? STATUS_STYLES.planned,
                      )}
                    >
                      {ATTENDANCE_EVENT_STATUS_LABELS[ev.event_status] ?? ev.event_status}
                    </span>
                  </div>
                  {ev.notes && <p className="text-[11px] text-slate-500">{ev.notes}</p>}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>
    </div>
  );
}
