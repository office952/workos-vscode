/**
 * Pontaj Intern — default present + exception events.
 *
 * EVIDENȚĂ INTERNĂ — NU este document fiscal/contabil.
 */
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Calendar,
  Users,
  Clock,
  AlertTriangle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Info,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  ListChecks,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useOperationalEmployees } from "@/hooks/useOperationalEmployees";
import { useEmployeeAttendance } from "@/hooks/useEmployeeAttendance";
import type {
  AttendanceEventDTO,
  AttendanceEventStatus,
  AttendanceEventType,
} from "@/api/employeeAttendance";

const MONTHS = [
  "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
  "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie",
];

const EVENT_TYPE_OPTIONS: { value: AttendanceEventType; label: string }[] = [
  { value: "absent", label: "Absent" },
  { value: "leave", label: "Concediu" },
  { value: "sick", label: "Medical" },
  { value: "partial", label: "Zi parțială" },
  { value: "overtime", label: "Ore suplimentare" },
  { value: "correction", label: "Corecție manuală" },
];

const EVENT_BADGE: Record<AttendanceEventType, string> = {
  absent: "bg-red-900/50 text-red-300",
  leave: "bg-cyan-900/50 text-cyan-300",
  sick: "bg-orange-900/50 text-orange-300",
  partial: "bg-amber-900/50 text-amber-300",
  overtime: "bg-blue-900/50 text-blue-300",
  correction: "bg-purple-900/50 text-purple-300",
};

const STATUS_OPTIONS: { value: AttendanceEventStatus; label: string }[] = [
  { value: "planned", label: "Planificat" },
  { value: "approved", label: "Aprobat" },
  { value: "confirmed", label: "Confirmat" },
  { value: "cancelled", label: "Anulat" },
];

const SINGLE_DAY_TYPES: AttendanceEventType[] = ["partial", "overtime", "correction"];
const RANGE_TYPES: AttendanceEventType[] = ["absent", "leave", "sick"];

function eventTypeLabel(t: AttendanceEventType): string {
  return EVENT_TYPE_OPTIONS.find((o) => o.value === t)?.label ?? t;
}

function defaultStatusForType(t: AttendanceEventType): AttendanceEventStatus {
  if (t === "leave" || t === "sick") return "planned";
  return "confirmed";
}

function formatEventRange(ev: AttendanceEventDTO): string {
  return ev.start_date === ev.end_date ? ev.start_date : `${ev.start_date} → ${ev.end_date}`;
}

export default function Attendance() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const { employees, loading: employeesLoading, error: employeesError } = useOperationalEmployees();
  const {
    summary,
    events,
    loading: attendanceLoading,
    eventsLoading,
    error: attendanceError,
    loadEvents,
    createEvent,
    updateEvent,
    deleteEvent,
  } = useEmployeeAttendance(year, month);

  const [formOpen, setFormOpen] = useState(false);
  const [editingEventId, setEditingEventId] = useState<number | null>(null);
  const [formSaving, setFormSaving] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [formEmployeeId, setFormEmployeeId] = useState<number | "">("");
  const [formStartDate, setFormStartDate] = useState("");
  const [formEndDate, setFormEndDate] = useState("");
  const [formType, setFormType] = useState<AttendanceEventType>("absent");
  const [formStatus, setFormStatus] = useState<AttendanceEventStatus>("confirmed");
  const [formHoursOverride, setFormHoursOverride] = useState("");
  const [formHoursDelta, setFormHoursDelta] = useState("");
  const [formNotes, setFormNotes] = useState("");

  const isSingleDayForm = SINGLE_DAY_TYPES.includes(formType);
  const isRangeForm = RANGE_TYPES.includes(formType);

  const activeEmployees = useMemo(
    () => employees.filter((e) => e.status === "active"),
    [employees]
  );

  const rows = useMemo(() => {
    const byId = new Map((summary?.employees ?? []).map((s) => [s.employee_id, s]));
    return activeEmployees.map((emp) => {
      const s = byId.get(emp.id);
      return {
        employeeId: emp.id,
        employeeName: emp.name,
        role: emp.role,
        department: emp.department,
        standard_work_days: s?.standard_work_days ?? 0,
        standard_hours: s?.standard_hours ?? 0,
        present_days: s?.present_days ?? 0,
        absent_days: s?.absent_days ?? 0,
        leave_days: s?.leave_days ?? 0,
        sick_days: s?.sick_days ?? 0,
        partial_days: s?.partial_days ?? 0,
        overtime_hours: s?.overtime_hours ?? 0,
        total_hours: s?.total_hours ?? 0,
        event_count: s?.event_count ?? 0,
      };
    });
  }, [activeEmployees, summary]);

  const totalStandardHours = rows.reduce((s, r) => s + r.standard_hours, 0);
  const totalWorkedHours = rows.reduce((s, r) => s + r.total_hours, 0);
  const totalEvents = rows.reduce((s, r) => s + r.event_count, 0);
  const totalAbsentLeaveSick =
    rows.reduce((s, r) => s + r.absent_days + r.leave_days + r.sick_days, 0);

  const hasAnyEvents = totalEvents > 0;
  const loading = employeesLoading || attendanceLoading;
  const error = employeesError ?? attendanceError;

  function prevMonth() {
    if (month === 1) setYear(year - 1), setMonth(12);
    else setMonth(month - 1);
  }

  function nextMonth() {
    if (month === 12) setYear(year + 1), setMonth(1);
    else setMonth(month + 1);
  }

  function openForm(prefill?: AttendanceEventDTO) {
    setFormError(null);
    if (prefill) {
      setEditingEventId(prefill.id);
      setFormEmployeeId(prefill.employee_id);
      setFormStartDate(prefill.start_date);
      setFormEndDate(prefill.end_date);
      setFormType(prefill.event_type);
      setFormStatus(prefill.event_status);
      setFormHoursOverride(
        prefill.hours_override != null ? String(prefill.hours_override) : ""
      );
      setFormHoursDelta(prefill.hours_delta != null ? String(prefill.hours_delta) : "");
      setFormNotes(prefill.notes ?? "");
    } else {
      setEditingEventId(null);
      setFormEmployeeId(activeEmployees[0]?.id ?? "");
      const today = new Date();
      const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
      setFormStartDate(todayStr);
      setFormEndDate(todayStr);
      setFormType("absent");
      setFormStatus("confirmed");
      setFormHoursOverride("");
      setFormHoursDelta("");
      setFormNotes("");
    }
    setFormOpen(true);
  }

  async function handleSaveForm() {
    if (formEmployeeId === "" || !formStartDate) {
      setFormError("Selectează angajat și dată.");
      return;
    }
    const endDate = isSingleDayForm ? formStartDate : formEndDate || formStartDate;
    if (!isSingleDayForm && endDate < formStartDate) {
      setFormError("Data finală trebuie să fie după data de start.");
      return;
    }
    setFormSaving(true);
    setFormError(null);
    try {
      const payload = {
        employee_id: Number(formEmployeeId),
        start_date: formStartDate,
        end_date: endDate,
        event_type: formType,
        event_status: formStatus,
        notes: formNotes.trim() || null,
        hours_override: undefined as number | null | undefined,
        hours_delta: undefined as number | null | undefined,
      };
      if (formType === "partial" || formType === "correction") {
        if (formHoursOverride.trim()) {
          payload.hours_override = Number(formHoursOverride);
        }
      }
      if (formType === "overtime" || formType === "correction") {
        if (formHoursDelta.trim()) {
          payload.hours_delta = Number(formHoursDelta);
        }
      }
      if (editingEventId != null) {
        await updateEvent(editingEventId, payload);
      } else {
        await createEvent(payload);
      }
      setFormOpen(false);
      setEditingEventId(null);
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Salvare eșuată.");
    } finally {
      setFormSaving(false);
    }
  }

  async function handleFilterEvents(employeeId: number | null) {
    await loadEvents(employeeId);
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 gap-2 text-slate-400 text-sm">
        <Loader2 className="w-5 h-5 animate-spin" />
        Se încarcă pontajul și angajații live...
      </div>
    );
  }

  if (error) {
    return (
      <Alert className="bg-red-900/20 border-red-700/50 text-red-100">
        <AlertTriangle className="h-4 w-4 text-red-400" />
        <AlertDescription className="text-[12px]">{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <Calendar className="w-5 h-5 text-blue-400" />
            <h1 className="text-[18px] font-bold text-slate-100">Pontaj</h1>
            <Badge className="text-[10px] uppercase tracking-wide bg-emerald-900/50 text-emerald-300 border-emerald-600/60">
              LIVE DB
            </Badge>
            <Badge className="text-[10px] uppercase tracking-wide bg-slate-800 text-slate-200 border-slate-600">
              EVIDENȚĂ INTERNĂ
            </Badge>
          </div>
          <p className="text-[13px] text-slate-300 pl-7">
            Evidență internă — program standard implicit, excepții introduse manual.
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Link
            to="/attendance/effects"
            className="flex items-center gap-2 px-3 py-2 text-[12px] font-medium text-slate-100 bg-violet-700 hover:bg-violet-600 rounded-md"
            data-testid="attendance-effects-console-link"
          >
            <ListChecks className="w-4 h-4" />
            Efecte din cereri
          </Link>
          <button
            type="button"
            onClick={() => openForm()}
            className="flex items-center gap-2 px-3 py-2 text-[12px] font-medium text-slate-100 bg-blue-600 hover:bg-blue-500 rounded-md"
          >
            <Plus className="w-4 h-4" />
            Adaugă eveniment
          </button>
        </div>
      </div>

      <Alert className="bg-emerald-900/20 border-emerald-700/50 text-emerald-100">
        <Info className="h-4 w-4 text-emerald-400" />
        <AlertDescription className="text-[12px] text-emerald-100/90">
          Angajații activi sunt considerați prezenți implicit conform programului standard. Adaugă
          doar absențe, concedii, medicale, zile parțiale, ore suplimentare sau corecții.
        </AlertDescription>
      </Alert>

      <div className="flex items-center gap-4">
        <button type="button" onClick={prevMonth} className="p-2 rounded-lg bg-wo-surface-raised border border-wo-border-strong">
          <ChevronLeft className="w-4 h-4 text-slate-300" />
        </button>
        <p className="text-[18px] font-bold text-slate-100">{MONTHS[month - 1]} {year}</p>
        <button type="button" onClick={nextMonth} className="p-2 rounded-lg bg-wo-surface-raised border border-wo-border-strong">
          <ChevronRight className="w-4 h-4 text-slate-300" />
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiCard label="Ore standard (total)" value={totalStandardHours} icon={<Clock className="w-4 h-4 text-slate-400" />} suffix="h" />
        <KpiCard label="Ore estimate lucrate" value={totalWorkedHours} icon={<CheckCircle2 className="w-4 h-4 text-emerald-400" />} suffix="h" />
        <KpiCard label="Evenimente (lună)" value={totalEvents} icon={<ListChecks className="w-4 h-4 text-blue-400" />} />
        <KpiCard label="Absențe / concedii / medicale" value={totalAbsentLeaveSick} icon={<AlertTriangle className="w-4 h-4 text-amber-400" />} alert={totalAbsentLeaveSick > 0} />
      </div>

      {!hasAnyEvents && (
        <div className="bg-wo-surface-raised border border-dashed border-wo-border-strong rounded-lg p-6 text-center space-y-3">
          <p className="text-[13px] text-slate-400">
            Nicio excepție înregistrată. Toți angajații activi sunt considerați prezenți conform
            programului standard.
          </p>
          <button
            type="button"
            onClick={() => openForm()}
            className="inline-flex items-center gap-2 px-4 py-2 text-[12px] font-medium text-slate-100 bg-blue-600 hover:bg-blue-500 rounded-md"
          >
            <Plus className="w-4 h-4" />
            Adaugă eveniment
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 space-y-2">
          <h2 className="text-[13px] font-semibold text-slate-400 uppercase tracking-wide">
            Sumar pontaj / angajat
          </h2>
          <div className="space-y-2">
            {rows.map((row) => (
              <div
                key={row.employeeId}
                className="w-full bg-wo-surface-raised border border-wo-border-subtle rounded-lg px-4 py-3"
              >
                <div className="flex items-center gap-3 flex-wrap">
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-[11px] font-bold text-slate-300 shrink-0">
                    {row.employeeName.split(" ").map((n) => n[0]).slice(0, 2).join("")}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[13px] font-semibold text-slate-200">{row.employeeName}</p>
                    <p className="text-[10px] text-slate-500">{row.role ?? "—"} · {row.department ?? "—"}</p>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] flex-wrap">
                    <StatCell label="Zile std." value={row.standard_work_days} color="text-slate-400" />
                    <StatCell label="Ore std." value={row.standard_hours} color="text-slate-400" suffix="h" />
                    <StatCell label="Evenim." value={row.event_count} color="text-blue-400" />
                    <StatCell label="Absent" value={row.absent_days} color="text-red-400" />
                    <StatCell label="Parțial" value={row.partial_days} color="text-amber-400" />
                    <StatCell label="Overtime" value={row.overtime_hours} color="text-cyan-400" suffix="h" />
                    <StatCell label="Total ore" value={row.total_hours} color="text-emerald-400" suffix="h" />
                  </div>
                  <button
                    type="button"
                    onClick={() => handleFilterEvents(row.employeeId)}
                    className="text-[10px] text-blue-400 hover:text-blue-300 shrink-0"
                  >
                    Vezi evenimente
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-[13px] font-semibold text-slate-400 uppercase tracking-wide">
              Evenimente lună
            </h2>
            <button
              type="button"
              onClick={() => handleFilterEvents(null)}
              className="text-[10px] text-slate-500 hover:text-slate-300"
            >
              Toți
            </button>
          </div>
          <div className="bg-wo-surface-raised border border-wo-border-subtle rounded-lg p-3 space-y-1 max-h-[420px] overflow-y-auto">
            {eventsLoading ? (
              <div className="flex items-center gap-2 text-slate-500 text-[12px] py-4 justify-center">
                <Loader2 className="w-4 h-4 animate-spin" />
                Se încarcă...
              </div>
            ) : events.length === 0 ? (
              <p className="text-[12px] text-slate-500 py-4 text-center">
                Nicio excepție înregistrată pentru filtrul curent.
              </p>
            ) : (
              events.map((ev) => (
                <div key={ev.id} className="flex items-center gap-2 px-2 py-1.5 rounded bg-wo-surface-raised">
                  <span className="text-[10px] text-slate-500 font-mono min-w-[88px]">
                    {formatEventRange(ev)}
                  </span>
                  <span className={`px-1.5 py-0.5 text-[9px] font-bold rounded ${EVENT_BADGE[ev.event_type]}`}>
                    {eventTypeLabel(ev.event_type)}
                  </span>
                  <span className="text-[9px] text-slate-500 uppercase">{ev.event_status}</span>
                  <span className="text-[10px] text-slate-300 flex-1 truncate">
                    {ev.employee_name ?? `#${ev.employee_id}`}
                  </span>
                  <span className="text-[10px] text-slate-500">
                    {ev.hours_override != null ? `${ev.hours_override}h` : ""}
                    {ev.hours_delta != null ? `${ev.hours_delta > 0 ? "+" : ""}${ev.hours_delta}h` : ""}
                  </span>
                  <button type="button" onClick={() => openForm(ev)} className="p-1 text-slate-500 hover:text-blue-400">
                    <Pencil className="w-3 h-3" />
                  </button>
                  {ev.event_status !== "cancelled" && (
                    <button
                      type="button"
                      title="Anulează eveniment"
                      onClick={() => void updateEvent(ev.id, { event_status: "cancelled" })}
                      className="text-[9px] text-amber-400 hover:text-amber-300 px-1"
                    >
                      Anulează
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => void deleteEvent(ev.id)}
                    className="p-1 text-slate-500 hover:text-red-400"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <Dialog open={formOpen} onOpenChange={setFormOpen}>
        <DialogContent className="bg-wo-surface-raised border-wo-border-strong text-slate-100">
          <DialogHeader>
            <DialogTitle>Adaugă eveniment pontaj</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-[13px]">
            <Field label="Angajat">
              <select
                value={formEmployeeId}
                onChange={(e) =>
                  setFormEmployeeId(e.target.value === "" ? "" : Number(e.target.value))
                }
                className="w-full bg-wo-surface-raised border border-wo-border-strong rounded px-3 py-2"
              >
                <option value="">Selectează...</option>
                {activeEmployees.map((emp) => (
                  <option key={emp.id} value={emp.id}>{emp.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Tip eveniment">
              <select
                value={formType}
                onChange={(e) => {
                  const t = e.target.value as AttendanceEventType;
                  setFormType(t);
                  setFormStatus(defaultStatusForType(t));
                  if (SINGLE_DAY_TYPES.includes(t)) {
                    setFormEndDate(formStartDate);
                  }
                }}
                className="w-full bg-wo-surface-raised border border-wo-border-strong rounded px-3 py-2"
              >
                {EVENT_TYPE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Status">
              <select
                value={formStatus}
                onChange={(e) => setFormStatus(e.target.value as AttendanceEventStatus)}
                className="w-full bg-wo-surface-raised border border-wo-border-strong rounded px-3 py-2"
              >
                {STATUS_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </Field>
            <Field label="Dată start">
              <input
                type="date"
                value={formStartDate}
                onChange={(e) => {
                  setFormStartDate(e.target.value);
                  if (isSingleDayForm) setFormEndDate(e.target.value);
                }}
                className="w-full bg-wo-surface-raised border border-wo-border-strong rounded px-3 py-2"
              />
            </Field>
            {!isSingleDayForm && (
              <Field label="Dată finală">
                <input
                  type="date"
                  value={formEndDate}
                  onChange={(e) => setFormEndDate(e.target.value)}
                  className="w-full bg-wo-surface-raised border border-wo-border-strong rounded px-3 py-2"
                />
              </Field>
            )}
            {isRangeForm && (
              <p className="text-[11px] text-slate-500">
                Se aplică doar zilelor lucrătoare din interval (luni–vineri).
              </p>
            )}
            {(formType === "partial" || formType === "correction") && (
              <Field label="Ore (override)">
                <input
                  type="number"
                  min={0}
                  max={24}
                  step={0.5}
                  value={formHoursOverride}
                  onChange={(e) => setFormHoursOverride(e.target.value)}
                  className="w-full bg-wo-surface-raised border border-wo-border-strong rounded px-3 py-2"
                  placeholder="ex. 4 pentru zi parțială"
                />
              </Field>
            )}
            {(formType === "overtime" || formType === "correction") && (
              <Field label="Ore delta (+/-)">
                <input
                  type="number"
                  min={-24}
                  max={24}
                  step={0.5}
                  value={formHoursDelta}
                  onChange={(e) => setFormHoursDelta(e.target.value)}
                  className="w-full bg-wo-surface-raised border border-wo-border-strong rounded px-3 py-2"
                  placeholder="ex. +2 ore suplimentare"
                />
              </Field>
            )}
            <Field label="Observații">
              <textarea
                value={formNotes}
                onChange={(e) => setFormNotes(e.target.value)}
                rows={2}
                className="w-full bg-wo-surface-raised border border-wo-border-strong rounded px-3 py-2"
                placeholder={formType === "correction" ? "Obligatoriu pentru corecție" : ""}
              />
            </Field>
            {formError && <p className="text-[12px] text-red-400">{formError}</p>}
          </div>
          <DialogFooter className="gap-2">
            <button type="button" onClick={() => setFormOpen(false)} className="px-3 py-2 text-[12px] border border-wo-border-strong rounded-md">
              Anulează
            </button>
            <button
              type="button"
              disabled={formSaving}
              onClick={() => void handleSaveForm()}
              className="px-3 py-2 text-[12px] font-medium text-white bg-blue-600 rounded-md disabled:opacity-50"
            >
              {formSaving ? "Se salvează..." : "Salvează"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function KpiCard({
  label,
  value,
  icon,
  suffix,
  alert,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  suffix?: string;
  alert?: boolean;
}) {
  return (
    <div className={`bg-wo-surface-raised border rounded-lg p-3 ${alert ? "border-amber-800/40" : "border-wo-border-strong"}`}>
      <div className="flex items-center gap-2 mb-1">{icon}<span className="text-[10px] text-slate-500 uppercase">{label}</span></div>
      <p className="text-[22px] font-bold text-slate-100">{value}{suffix}</p>
    </div>
  );
}

function StatCell({
  label,
  value,
  color,
  suffix,
}: {
  label: string;
  value: number;
  color: string;
  suffix?: string;
}) {
  return (
    <div className="text-center min-w-[40px]">
      <p className={`font-bold ${color}`}>{value}{suffix}</p>
      <p className="text-[9px] text-slate-600">{label}</p>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block space-y-1">
      <span className="text-slate-400">{label}</span>
      {children}
    </label>
  );
}
