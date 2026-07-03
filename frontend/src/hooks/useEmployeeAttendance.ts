import { useCallback, useEffect, useRef, useState } from "react";
import {
  employeeAttendanceApi,
  type AttendanceEventDTO,
  type AttendanceEventPayload,
  type AttendanceMonthSummaryDTO,
} from "@/api/employeeAttendance";

function monthBounds(year: number, month: number): { start: string; end: string } {
  const start = `${year}-${String(month).padStart(2, "0")}-01`;
  const lastDay = new Date(year, month, 0).getDate();
  const end = `${year}-${String(month).padStart(2, "0")}-${String(lastDay).padStart(2, "0")}`;
  return { start, end };
}

export interface UseEmployeeAttendanceState {
  summary: AttendanceMonthSummaryDTO | null;
  events: AttendanceEventDTO[];
  loading: boolean;
  eventsLoading: boolean;
  error: string | null;
  refreshSummary: () => Promise<void>;
  loadEvents: (employeeId: number | null) => Promise<void>;
  createEvent: (payload: AttendanceEventPayload) => Promise<void>;
  updateEvent: (id: number, payload: Partial<AttendanceEventPayload>) => Promise<void>;
  deleteEvent: (id: number) => Promise<void>;
}

export function useEmployeeAttendance(year: number, month: number): UseEmployeeAttendanceState {
  const [summary, setSummary] = useState<AttendanceMonthSummaryDTO | null>(null);
  const [events, setEvents] = useState<AttendanceEventDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const filterEmployeeIdRef = useRef<number | null>(null);

  const refreshSummary = useCallback(async () => {
    const data = await employeeAttendanceApi.summary(year, month);
    setSummary(data);
  }, [year, month]);

  const loadEvents = useCallback(
    async (employeeId: number | null) => {
      filterEmployeeIdRef.current = employeeId;
      const { start, end } = monthBounds(year, month);
      setEventsLoading(true);
      try {
        const rows = await employeeAttendanceApi.listEvents({
          start_date: start,
          end_date: end,
          employee_id: employeeId ?? undefined,
        });
        setEvents(rows);
      } finally {
        setEventsLoading(false);
      }
    },
    [year, month]
  );

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    void employeeAttendanceApi
      .summary(year, month)
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setSummary(null);
          setError(err instanceof Error ? err.message : "Nu s-a putut încărca pontajul.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    void loadEvents(filterEmployeeIdRef.current);

    return () => {
      cancelled = true;
    };
  }, [year, month, loadEvents]);

  const createEvent = useCallback(
    async (payload: AttendanceEventPayload) => {
      await employeeAttendanceApi.createEvent(payload);
      await refreshSummary();
      await loadEvents(filterEmployeeIdRef.current);
    },
    [refreshSummary, loadEvents]
  );

  const updateEvent = useCallback(
    async (id: number, payload: Partial<AttendanceEventPayload>) => {
      await employeeAttendanceApi.updateEvent(id, payload);
      await refreshSummary();
      await loadEvents(filterEmployeeIdRef.current);
    },
    [refreshSummary, loadEvents]
  );

  const deleteEvent = useCallback(
    async (id: number) => {
      await employeeAttendanceApi.deleteEvent(id);
      await refreshSummary();
      await loadEvents(filterEmployeeIdRef.current);
    },
    [refreshSummary, loadEvents]
  );

  return {
    summary,
    events,
    loading,
    eventsLoading,
    error,
    refreshSummary,
    loadEvents,
    createEvent,
    updateEvent,
    deleteEvent,
  };
}
