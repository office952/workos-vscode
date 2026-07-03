import { useEffect, useState } from "react";
import { listMyAttendanceEvents } from "@/api/employeeMobileAttendance";
import { listEmployeeRequests } from "@/api/employeeMobileRequests";

export type EmployeeMobileSelfLinkState =
  | "idle"
  | "loading"
  | "linked"
  | "missing"
  | "inactive"
  | "unavailable";

function monthBounds(year: number, month: number): { start: string; end: string } {
  const lastDay = new Date(year, month, 0).getDate();
  const pad = (n: number) => String(n).padStart(2, "0");
  return {
    start: `${year}-${pad(month)}-01`,
    end: `${year}-${pad(month)}-${pad(lastDay)}`,
  };
}

/**
 * Probes existing self-only mobile endpoints to infer employee link status.
 * Does not expose client employee_id — uses server-resolved identity only.
 */
export function useEmployeeMobileSelfLink(enabled: boolean) {
  const [state, setState] = useState<EmployeeMobileSelfLinkState>("idle");
  const [employeeName, setEmployeeName] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setState("idle");
      setEmployeeName(null);
      return;
    }

    let cancelled = false;

    const probe = async () => {
      setState("loading");
      setEmployeeName(null);
      try {
        await listEmployeeRequests();
        if (cancelled) return;

        setState("linked");

        const now = new Date();
        const range = monthBounds(now.getFullYear(), now.getMonth() + 1);
        try {
          const events = await listMyAttendanceEvents({
            start_date: range.start,
            end_date: range.end,
          });
          const name = events.find((ev) => ev.employee_name)?.employee_name ?? null;
          if (!cancelled && name) setEmployeeName(name);
        } catch {
          // Attendance empty/error does not invalidate link confirmed by requests.
        }
      } catch (err) {
        if (cancelled) return;
        const message = err instanceof Error ? err.message.toLowerCase() : "";
        if (message.includes("nu este legat") || message.includes("employee_link_missing")) {
          setState("missing");
          return;
        }
        if (message.includes("not eligible") || message.includes("employee_not_active")) {
          setState("inactive");
          return;
        }
        setState("unavailable");
      }
    };

    void probe();

    return () => {
      cancelled = true;
    };
  }, [enabled]);

  return { state, employeeName };
}
