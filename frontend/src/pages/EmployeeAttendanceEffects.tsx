/**
 * Admin/operator console — generate and apply attendance effects from approved requests.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { AlertTriangle, ChevronLeft, Loader2, RefreshCw } from "lucide-react";
import {
  applyAttendanceEffect,
  generateAttendanceEffect,
  listAttendanceEffectGenerationCandidates,
  listAttendanceEffects,
  type AttendanceEffectDTO,
  type AttendanceEffectGenerationCandidateDTO,
  type AttendanceEffectStatus,
} from "@/api/employeeAttendance";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

type ConsoleTab = "candidates" | "effects";
type EffectFilter = AttendanceEffectStatus | "all";

const EFFECT_FILTERS: { value: EffectFilter; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "conflict", label: "Conflict" },
  { value: "applied", label: "Aplicat" },
  { value: "cancelled", label: "Anulat" },
  { value: "all", label: "Toate" },
];

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-amber-900/40 text-amber-200 border-amber-700/50",
  conflict: "bg-red-900/40 text-red-200 border-red-700/50",
  applied: "bg-emerald-900/40 text-emerald-200 border-emerald-700/50",
  cancelled: "bg-slate-800 text-slate-400 border-slate-600",
};

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const part = value.slice(0, 10);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(part)) return value;
  const [y, m, d] = part.split("-");
  return `${d}.${m}.${y}`;
}

function formatRange(start?: string | null, end?: string | null): string {
  if (!start) return "—";
  const s = formatDate(start);
  const e = formatDate(end ?? start);
  return s === e ? s : `${s} – ${e}`;
}

function formatEffectRange(effect: AttendanceEffectDTO): string {
  return formatRange(effect.date_start, effect.date_end);
}

function parseErrorMessage(err: unknown, context: "apply" | "generate" | "list" = "list"): string {
  if (!(err instanceof Error)) return "A apărut o eroare.";
  const msg = err.message.toLowerCase();
  if (msg.includes("409") || msg.includes("conflict")) {
    return context === "generate"
      ? "Conflict detectat la generare — verifică datele cererii sau pontajul existent."
      : "Conflict — efectul nu poate fi aplicat. Verifică pontajul existent.";
  }
  if (msg.includes("422") || msg.includes("unsupported") || msg.includes("not approved") || msg.includes("request_type_skipped") || msg.includes("only approved employee")) {
    return context === "generate"
      ? "Cererea nu poate genera efect (netrimisă, neaprobată sau tip neacceptat)."
      : "Tip de efect neacceptat pentru apply în acest moment.";
  }
  if (msg.includes("403") || msg.includes("forbidden")) {
    return "Acces refuzat — rol admin sau operator necesar.";
  }
  return err instanceof Error ? err.message : "A apărut o eroare.";
}

export default function EmployeeAttendanceEffects() {
  const [tab, setTab] = useState<ConsoleTab>("candidates");
  const [filter, setFilter] = useState<EffectFilter>("pending");
  const [candidates, setCandidates] = useState<AttendanceEffectGenerationCandidateDTO[]>([]);
  const [effects, setEffects] = useState<AttendanceEffectDTO[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(true);
  const [effectsLoading, setEffectsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [applyingId, setApplyingId] = useState<number | null>(null);
  const [generatingRequestId, setGeneratingRequestId] = useState<number | null>(null);

  const loadCandidates = useCallback(async () => {
    setCandidatesLoading(true);
    setError(null);
    try {
      const rows = await listAttendanceEffectGenerationCandidates();
      setCandidates(rows);
    } catch (err) {
      setCandidates([]);
      setError(parseErrorMessage(err, "list"));
    } finally {
      setCandidatesLoading(false);
    }
  }, []);

  const loadEffects = useCallback(async () => {
    setEffectsLoading(true);
    setError(null);
    try {
      const rows = await listAttendanceEffects(filter === "all" ? {} : { status: filter });
      setEffects(rows);
    } catch (err) {
      setEffects([]);
      setError(parseErrorMessage(err, "list"));
    } finally {
      setEffectsLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    if (tab === "candidates") {
      void loadCandidates();
    } else {
      void loadEffects();
    }
  }, [tab, loadCandidates, loadEffects]);

  const counts = useMemo(() => {
    const map: Record<string, number> = { all: effects.length };
    for (const row of effects) {
      map[row.status] = (map[row.status] ?? 0) + 1;
    }
    return map;
  }, [effects]);

  const handleGenerate = async (candidate: AttendanceEffectGenerationCandidateDTO) => {
    setGeneratingRequestId(candidate.employee_request_id);
    setError(null);
    setSuccess(null);
    try {
      const result = await generateAttendanceEffect(candidate.employee_request_id);
      setSuccess(
        result.already_exists
          ? `Efectul pentru cererea #${candidate.employee_request_id} există deja (status: ${result.status}).`
          : `Efect generat pentru cererea #${candidate.employee_request_id} (status: ${result.status}).`,
      );
      setTab("effects");
      setFilter(result.status === "conflict" ? "conflict" : "pending");
      await loadCandidates();
    } catch (err) {
      setError(parseErrorMessage(err, "generate"));
    } finally {
      setGeneratingRequestId(null);
    }
  };

  const handleApply = async (effect: AttendanceEffectDTO) => {
    if (
      !window.confirm(
        `Aplici efectul #${effect.id} pentru cererea #${effect.employee_request_id}?`,
      )
    ) {
      return;
    }
    setApplyingId(effect.id);
    setError(null);
    setSuccess(null);
    try {
      const result = await applyAttendanceEffect(effect.id);
      setSuccess(
        result.already_applied
          ? `Efectul #${effect.id} era deja aplicat (event ${result.attendance_event_id}).`
          : `Efect aplicat — eveniment pontaj #${result.attendance_event_id}.`,
      );
      await loadEffects();
    } catch (err) {
      setError(parseErrorMessage(err, "apply"));
      await loadEffects();
    } finally {
      setApplyingId(null);
    }
  };

  return (
    <div className="space-y-6 p-6" data-testid="attendance-effects-console">
      <div className="flex items-center gap-3 flex-wrap">
        <Link to="/attendance" className="inline-flex items-center gap-1 text-sm text-blue-400">
          <ChevronLeft className="w-4 h-4" aria-hidden />
          Pontaj intern
        </Link>
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-slate-100">Efecte pontaj din cereri</h1>
        <p className="text-sm text-slate-400">
          Console operațională — generează efecte din cereri aprobate, apoi aplică manual în pontaj.
          Fără auto-generate la approve și fără auto-apply.
        </p>
      </div>

      <div className="flex items-start gap-2 px-3 py-2 bg-amber-900/15 border border-amber-800/30 rounded-lg">
        <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" aria-hidden />
        <p className="text-xs text-amber-300/90">
          Generarea pregătește efectul de pontaj. Aplicarea se face separat. Apply scrie în pontaj —
          fără reversal în acest build.
        </p>
      </div>

      <div className="flex gap-2 border-b border-[#1E293B] pb-2">
        <button
          type="button"
          data-testid="attendance-effects-tab-candidates"
          className={cn(
            "px-3 py-1.5 text-xs font-medium rounded-t-lg border-b-2 transition-colors",
            tab === "candidates"
              ? "text-blue-200 border-blue-500"
              : "text-slate-500 border-transparent hover:text-slate-300",
          )}
          onClick={() => setTab("candidates")}
        >
          De generat
        </button>
        <button
          type="button"
          data-testid="attendance-effects-tab-effects"
          className={cn(
            "px-3 py-1.5 text-xs font-medium rounded-t-lg border-b-2 transition-colors",
            tab === "effects"
              ? "text-blue-200 border-blue-500"
              : "text-slate-500 border-transparent hover:text-slate-300",
          )}
          onClick={() => setTab("effects")}
        >
          Efecte
        </button>
      </div>

      {success && (
        <p className="text-sm text-emerald-300" data-testid="attendance-effects-success">
          {success}
        </p>
      )}

      {error && (
        <p
          className="text-sm text-red-300 rounded-lg border border-red-900/40 bg-red-950/20 px-3 py-2"
          data-testid="attendance-effects-error"
        >
          {error}
        </p>
      )}

      {tab === "candidates" && (
        <section className="space-y-4" data-testid="attendance-effects-candidates-section">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <h2 className="text-sm font-semibold text-slate-200">
              Cereri aprobate fără efect de pontaj
            </h2>
            <button
              type="button"
              className="inline-flex items-center gap-1 text-xs text-blue-400"
              data-testid="attendance-effects-candidates-refresh"
              onClick={() => void loadCandidates()}
              disabled={candidatesLoading}
            >
              <RefreshCw
                className={cn("w-3.5 h-3.5", candidatesLoading && "animate-spin")}
                aria-hidden
              />
              Reîmprospătează
            </button>
          </div>

          {candidatesLoading && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              Se încarcă cererile candidate…
            </div>
          )}

          {!candidatesLoading && candidates.length === 0 && (
            <p className="text-sm text-slate-500" data-testid="attendance-effects-candidates-empty">
              Niciun candidat fără efect generat.
            </p>
          )}

          {!candidatesLoading && candidates.length > 0 && (
            <div className="grid gap-3" data-testid="attendance-effects-candidates-list">
              {candidates.map((candidate) => (
                <article
                  key={candidate.employee_request_id}
                  className="rounded-xl border border-[#1E293B] bg-[#111827] p-4 space-y-3"
                  data-testid={`attendance-effect-candidate-${candidate.employee_request_id}`}
                >
                  <div>
                    <p className="text-sm font-medium text-slate-100">
                      {candidate.employee_name} · Cerere #{candidate.employee_request_id}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      {candidate.request_type} · {formatRange(candidate.start_date, candidate.end_date)}{" "}
                      · {candidate.status}
                    </p>
                    {candidate.title && (
                      <p className="text-xs text-slate-400 mt-1">{candidate.title}</p>
                    )}
                  </div>
                  <button
                    type="button"
                    className="rounded-lg bg-violet-700 hover:bg-violet-600 text-xs font-medium text-white px-3 py-2 disabled:opacity-50"
                    data-testid={`attendance-effect-generate-${candidate.employee_request_id}`}
                    disabled={generatingRequestId === candidate.employee_request_id}
                    onClick={() => void handleGenerate(candidate)}
                  >
                    {generatingRequestId === candidate.employee_request_id
                      ? "Se generează…"
                      : "Generează efect"}
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>
      )}

      {tab === "effects" && (
        <>
          <div className="flex flex-wrap gap-2 items-center">
            {EFFECT_FILTERS.map((item) => (
              <button
                key={item.value}
                type="button"
                data-testid={`attendance-effects-filter-${item.value}`}
                className={cn(
                  "px-3 py-1.5 text-xs rounded-lg border transition-colors",
                  filter === item.value
                    ? "bg-blue-900/40 text-blue-200 border-blue-700/50"
                    : "bg-[#111827] text-slate-400 border-[#243044] hover:border-slate-500",
                )}
                onClick={() => setFilter(item.value)}
              >
                {item.label}
              </button>
            ))}
            <button
              type="button"
              className="inline-flex items-center gap-1 ml-auto text-xs text-blue-400"
              data-testid="attendance-effects-refresh"
              onClick={() => void loadEffects()}
              disabled={effectsLoading}
            >
              <RefreshCw
                className={cn("w-3.5 h-3.5", effectsLoading && "animate-spin")}
                aria-hidden
              />
              Reîmprospătează
            </button>
          </div>

          {effectsLoading && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
              Se încarcă efectele…
            </div>
          )}

          {!effectsLoading && !error && effects.length === 0 && (
            <p className="text-sm text-slate-500" data-testid="attendance-effects-empty">
              Niciun efect pentru filtrul selectat.
            </p>
          )}

          {!effectsLoading && effects.length > 0 && (
            <div className="grid gap-3" data-testid="attendance-effects-list">
              {effects.map((effect) => (
                <article
                  key={effect.id}
                  className="rounded-xl border border-[#1E293B] bg-[#111827] p-4 space-y-3"
                  data-testid={`attendance-effect-card-${effect.id}`}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium text-slate-100">
                        Angajat #{effect.employee_id} · Cerere #{effect.employee_request_id}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {effect.request_type} → {effect.effect_type} · {formatEffectRange(effect)}
                      </p>
                    </div>
                    <Badge className={STATUS_BADGE[effect.status] ?? STATUS_BADGE.pending}>
                      {effect.status}
                    </Badge>
                  </div>

                  {effect.conflict_reason && (
                    <p className="text-xs text-red-300/90">Conflict: {effect.conflict_reason}</p>
                  )}

                  {effect.applied_at && (
                    <p className="text-xs text-slate-500">
                      Aplicat: {formatDate(effect.applied_at)}
                      {effect.applied_by_user_id ? ` · ${effect.applied_by_user_id}` : ""}
                    </p>
                  )}

                  {effect.status === "pending" && (
                    <button
                      type="button"
                      className="rounded-lg bg-blue-700 hover:bg-blue-600 text-xs font-medium text-white px-3 py-2 disabled:opacity-50"
                      data-testid={`attendance-effect-apply-${effect.id}`}
                      disabled={applyingId === effect.id}
                      onClick={() => void handleApply(effect)}
                    >
                      {applyingId === effect.id ? "Se aplică…" : "Aplică în pontaj"}
                    </button>
                  )}
                </article>
              ))}
            </div>
          )}

          {filter !== "all" && counts[filter] != null && (
            <p className="text-[10px] text-slate-600">{counts[filter]} efect(e) în listă</p>
          )}
        </>
      )}
    </div>
  );
}
