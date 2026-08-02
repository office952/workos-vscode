/** Romanian-first labels for F3/F4 closure and cost reason codes. */

const REASON_RO: Record<string, string> = {
  active_session_open: "Există o sesiune de lucru activă — închide sesiunea înainte de close.",
  required_tasks_incomplete: "Nu toate task-urile operaționale necesare sunt terminate.",
  actual_material_cost_missing: "Lipsește consumul material canonic (mișcare reală).",
  material_valuation_unavailable: "Evaluarea materialului nu este înghețată — cost indisponibil.",
  material_return_unresolved: "Există retururi nerezolvate față de consumul original.",
  actual_labor_cost_incomplete: "Costul de muncă real nu este complet / înghețat.",
  closure_checklist_not_authorized: "Închiderea trebuie autorizată explicit.",
  reopen_reason_required: "Redeschiderea cere un motiv.",
  job_not_closed: "Jobul nu este închis.",
  actor_not_authorized: "Rolul curent nu are autoritate pentru această acțiune.",
};

export function closureReasonRo(code: string | null | undefined): string {
  if (!code) return "Motiv necunoscut.";
  return REASON_RO[code] ?? `Blocat: ${code}`;
}

export function closureStateLabel(args: {
  ready: boolean | null;
  closed: boolean;
  loading: boolean;
}): { title: string; tone: "ready" | "blocked" | "closed" | "loading" } {
  if (args.loading) return { title: "Se verifică pregătirea…", tone: "loading" };
  if (args.closed) return { title: "Job operațional închis", tone: "closed" };
  if (args.ready) return { title: "Pregătit pentru închidere autorizată", tone: "ready" };
  return { title: "Închiderea este blocată", tone: "blocked" };
}
