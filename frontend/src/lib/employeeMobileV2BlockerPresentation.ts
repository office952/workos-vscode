import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";

/** Backend-only taxonomy — display ordering only, no policy authority. */
export type EmV2BlockerCategory =
  | "productie"
  | "pregatire"
  | "materiale"
  | "alocare"
  | "stare_task";

export type EmV2PrimaryReadinessState =
  | "pregatit"
  | "nepregatit"
  | "blocat_pentru_productie"
  | "in_asteptarea_altei_operatii"
  | "materiale_lipsa"
  | "alocat_altui_coleg"
  | "in_lucru"
  | "finalizat";

export interface EmV2BlockerItem {
  category: EmV2BlockerCategory;
  label: string;
  detail?: string;
  code?: string;
}

export interface EmV2TaskBlockerPresentation {
  primaryState: EmV2PrimaryReadinessState;
  primaryLabel: string;
  shortReason: string | null;
  secondaryReasons: string[];
  blockerCount: number;
  showProductionBadge: boolean;
  productionBadgeLabel: string;
  showManagerEscalation: boolean;
  managerEscalationText: string;
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>;
  canStartFromBackend: boolean;
  canStartExplanation: string;
  diagnosticCodes: string[];
  activeSessionLabel: string | null;
}

export const MANAGER_ESCALATION_TEXT =
  "Această decizie trebuie rezolvată de un manager în WorkOS desktop.";

const CATEGORY_LABELS: Record<EmV2BlockerCategory, string> = {
  productie: "Producție",
  pregatire: "Pregătire",
  materiale: "Materiale",
  alocare: "Alocare",
  stare_task: "Stare task",
};

const PRIMARY_LABELS: Record<EmV2PrimaryReadinessState, string> = {
  pregatit: "Pregătit",
  nepregatit: "Nepregătit",
  blocat_pentru_productie: "Blocat pentru producție",
  in_asteptarea_altei_operatii: "În așteptarea altei operații",
  materiale_lipsa: "Materiale lipsă",
  alocat_altui_coleg: "Alocat altui coleg",
  in_lucru: "În lucru",
  finalizat: "Finalizat",
};

const READINESS_STATUS = {
  DONE: "done",
  IN_PROGRESS: "in_progress",
  BLOCKED_MANUAL: "blocked_manual",
  WAITING_PREDECESSOR: "waiting_predecessor",
  WAITING_MATERIAL: "waiting_material",
  WAITING_FILE: "waiting_file",
  WAITING_TEMPLATE_DECISION: "waiting_template_decision",
  WAITING_DOCUMENT: "waiting_document",
  WAITING_WORKSHOP_INFO: "waiting_workshop_info",
  ELIGIBLE: "eligible",
  ASSIGNED_NOT_MINE: "assigned_not_mine",
  UNASSIGNED: "unassigned",
} as const;

const REASON_CODE = {
  PREDECESSOR_NOT_DONE: "predecessor_not_done",
  PREDECESSOR_IN_PROGRESS: "predecessor_not_done_while_in_progress",
  MATERIAL_PROCUREMENT: "material_procurement_block",
} as const;

function emptyCategories(): Record<EmV2BlockerCategory, EmV2BlockerItem[]> {
  return {
    productie: [],
    pregatire: [],
    materiale: [],
    alocare: [],
    stare_task: [],
  };
}

function readinessStatusOf(task: EmployeeMobileTaskDTO): string {
  return String(task.readiness_status || "").trim().toLowerCase();
}

function reasonCodeOf(reason: { code?: string }): string {
  return String(reason.code || "").trim().toLowerCase();
}

function classifyReasonCategory(
  code: string,
  readinessStatus: string,
): EmV2BlockerCategory {
  if (
    code === REASON_CODE.MATERIAL_PROCUREMENT ||
    readinessStatus === READINESS_STATUS.WAITING_MATERIAL
  ) {
    return "materiale";
  }
  if (
    code === REASON_CODE.PREDECESSOR_NOT_DONE ||
    code === REASON_CODE.PREDECESSOR_IN_PROGRESS ||
    readinessStatus === READINESS_STATUS.WAITING_PREDECESSOR ||
    readinessStatus === READINESS_STATUS.WAITING_FILE ||
    readinessStatus === READINESS_STATUS.WAITING_TEMPLATE_DECISION ||
    readinessStatus === READINESS_STATUS.WAITING_DOCUMENT ||
    readinessStatus === READINESS_STATUS.WAITING_WORKSHOP_INFO
  ) {
    return "pregatire";
  }
  if (
    readinessStatus === READINESS_STATUS.ASSIGNED_NOT_MINE ||
    readinessStatus === READINESS_STATUS.UNASSIGNED
  ) {
    return "alocare";
  }
  if (
    readinessStatus === READINESS_STATUS.IN_PROGRESS ||
    readinessStatus === READINESS_STATUS.DONE ||
    readinessStatus === READINESS_STATUS.BLOCKED_MANUAL
  ) {
    return "stare_task";
  }
  return "pregatire";
}

function buildReasonItems(task: EmployeeMobileTaskDTO): EmV2BlockerItem[] {
  const items: EmV2BlockerItem[] = [];
  const status = readinessStatusOf(task);
  for (const raw of task.readiness_reasons ?? []) {
    if (!raw || typeof raw !== "object") continue;
    const code = reasonCodeOf(raw);
    const label =
      String(raw.label || raw.message || raw.task_name || "").trim() ||
      String(task.readiness_label || "").trim();
    if (!label && !code) continue;
    items.push({
      category: classifyReasonCategory(code, status),
      label: label || code,
      detail: raw.task_name || raw.message || undefined,
      code: code || undefined,
    });
  }
  return items;
}

function addProductionBlockers(
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
  task: EmployeeMobileTaskDTO,
): void {
  if (!task.production_release_blocked) return;
  const summary = task.production_blocker_summary?.trim();
  categories.productie.push({
    category: "productie",
    label: "Producție blocată",
    detail: summary || "Decizie manager necesară pe desktop.",
    code: "production_release_blocked",
  });
}

function addPreparationBlockers(
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
  task: EmployeeMobileTaskDTO,
): void {
  const status = readinessStatusOf(task);
  if (task.dependency_warning?.trim()) {
    categories.pregatire.push({
      category: "pregatire",
      label: task.dependency_warning.trim(),
      code: status || "dependency_warning",
    });
  }
  for (const blocker of task.blocking_tasks ?? []) {
    categories.pregatire.push({
      category: "pregatire",
      label: blocker.name || blocker.task_id,
      detail: "Task anterior nefinalizat",
      code: REASON_CODE.PREDECESSOR_NOT_DONE,
    });
  }
}

function addMaterialBlockers(
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
  task: EmployeeMobileTaskDTO,
): void {
  if (task.material_warning?.trim()) {
    categories.materiale.push({
      category: "materiale",
      label: task.material_warning.trim(),
      code: REASON_CODE.MATERIAL_PROCUREMENT,
    });
  }
}

function addAssignmentBlockers(
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
  task: EmployeeMobileTaskDTO,
): void {
  const status = readinessStatusOf(task);
  if (status === READINESS_STATUS.ASSIGNED_NOT_MINE) {
    const name = task.employee_name?.trim();
    categories.alocare.push({
      category: "alocare",
      label: name ? `Atribuit lui ${name}` : "Atribuit altui coleg",
      code: "assigned_not_mine",
    });
    return;
  }
  if (task.is_available_for_claim && !task.is_assigned_to_current_employee) {
    if (!task.can_claim && !task.claimable) {
      categories.alocare.push({
        category: "alocare",
        label: "Nu poate fi preluat",
        code: "not_claimable",
      });
    }
    return;
  }
  if (!task.is_assigned_to_current_employee && task.assigned_employee_id) {
    const name = task.employee_name?.trim();
    categories.alocare.push({
      category: "alocare",
      label: name ? `Atribuit lui ${name}` : "Atribuit altui angajat",
      code: "task_owned_by_other_employee",
    });
  }
}

function addTaskStateBlockers(
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
  task: EmployeeMobileTaskDTO,
): void {
  if (task.status === "blocked" && task.blocked_reason?.trim()) {
    categories.stare_task.push({
      category: "stare_task",
      label: "Blocat manual",
      detail: task.blocked_reason.trim(),
      code: READINESS_STATUS.BLOCKED_MANUAL,
    });
  }
  if (task.status === "paused") {
    categories.stare_task.push({
      category: "stare_task",
      label: "Task în pauză",
      code: "paused",
    });
  }
}

function resolvePrimaryState(
  task: EmployeeMobileTaskDTO,
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
): EmV2PrimaryReadinessState {
  const status = readinessStatusOf(task);
  if (task.status === "done" || status === READINESS_STATUS.DONE) return "finalizat";
  if (task.status === "in_progress" || status === READINESS_STATUS.IN_PROGRESS) return "in_lucru";
  if (task.production_release_blocked) return "blocat_pentru_productie";
  if (status === READINESS_STATUS.ASSIGNED_NOT_MINE) return "alocat_altui_coleg";
  if (
    status === READINESS_STATUS.WAITING_MATERIAL ||
    categories.materiale.length > 0
  ) {
    return "materiale_lipsa";
  }
  if (
    status === READINESS_STATUS.WAITING_PREDECESSOR ||
    status === READINESS_STATUS.WAITING_FILE ||
    status === READINESS_STATUS.WAITING_TEMPLATE_DECISION ||
    status === READINESS_STATUS.WAITING_DOCUMENT ||
    status === READINESS_STATUS.WAITING_WORKSHOP_INFO ||
    categories.pregatire.some((item) => item.code?.includes("predecessor"))
  ) {
    return "in_asteptarea_altei_operatii";
  }
  if (task.is_startable === true && !task.production_release_blocked) return "pregatit";
  return "nepregatit";
}

function buildShortReason(
  primary: EmV2PrimaryReadinessState,
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
  task: EmployeeMobileTaskDTO,
): string | null {
  if (primary === "finalizat") return "Task finalizat";
  if (primary === "in_lucru") return task.started_at ? "Sesiune activă" : "Task în lucru";
  if (primary === "blocat_pentru_productie") {
    const count = categories.productie.length;
    return count > 1 ? `${count} blocaje producție` : "Producție blocată";
  }
  if (primary === "alocat_altui_coleg") {
    return categories.alocare[0]?.label ?? "Atribuit altui coleg";
  }
  if (primary === "materiale_lipsa") {
    return categories.materiale[0]?.label ?? task.material_warning ?? "Materiale lipsă";
  }
  if (primary === "in_asteptarea_altei_operatii") {
    return (
      categories.pregatire[0]?.label ??
      task.dependency_warning ??
      task.readiness_label ??
      "Așteaptă pregătire"
    );
  }
  if (primary === "pregatit") return null;
  return task.readiness_label?.trim() || categories.pregatire[0]?.label || null;
}

function buildSecondaryReasons(
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
  primary: EmV2PrimaryReadinessState,
): string[] {
  const all = [
    ...categories.productie,
    ...categories.pregatire,
    ...categories.materiale,
    ...categories.alocare,
    ...categories.stare_task,
  ];
  const primaryCategory =
    primary === "blocat_pentru_productie"
      ? "productie"
      : primary === "materiale_lipsa"
        ? "materiale"
        : primary === "alocat_altui_coleg"
          ? "alocare"
          : primary === "in_asteptarea_altei_operatii"
            ? "pregatire"
            : null;
  return all
    .filter((item) => item.category !== primaryCategory)
    .map((item) => item.detail || item.label)
    .filter((line, index, arr) => line && arr.indexOf(line) === index)
    .slice(0, 3);
}

function buildCanStartExplanation(
  task: EmployeeMobileTaskDTO,
  presentation: Pick<EmV2TaskBlockerPresentation, "primaryState" | "categories">,
): string {
  if (task.is_startable === true) {
    return "Backend confirmă că taskul poate fi pornit.";
  }
  if (task.status === "in_progress") {
    return "Taskul este deja în lucru — nu poate fi pornit din nou.";
  }
  if (task.status === "done") {
    return "Taskul este finalizat.";
  }
  if (task.production_release_blocked) {
    return MANAGER_ESCALATION_TEXT;
  }
  if (presentation.categories.alocare.length > 0) {
    return presentation.categories.alocare[0].detail || presentation.categories.alocare[0].label;
  }
  if (presentation.categories.materiale.length > 0) {
    return presentation.categories.materiale[0].label;
  }
  if (presentation.categories.pregatire.length > 0) {
    return presentation.categories.pregatire[0].detail || presentation.categories.pregatire[0].label;
  }
  if (task.readiness_label?.trim()) return task.readiness_label.trim();
  return "Taskul nu este încă pregătit pentru start.";
}

function collectDiagnosticCodes(
  task: EmployeeMobileTaskDTO,
  categories: Record<EmV2BlockerCategory, EmV2BlockerItem[]>,
): string[] {
  const codes = new Set<string>();
  if (task.readiness_status) codes.add(`readiness_status:${task.readiness_status}`);
  if (task.production_release_blocked) codes.add("production_release_blocked");
  for (const reason of task.readiness_reasons ?? []) {
    const code = reasonCodeOf(reason);
    if (code) codes.add(code);
  }
  for (const items of Object.values(categories)) {
    for (const item of items) {
      if (item.code) codes.add(item.code);
    }
  }
  return [...codes];
}

/** Display-only projection from backend truth fields. */
export function buildEmployeeMobileV2BlockerPresentation(
  task: EmployeeMobileTaskDTO,
): EmV2TaskBlockerPresentation {
  const categories = emptyCategories();
  for (const item of buildReasonItems(task)) {
    categories[item.category].push(item);
  }
  addProductionBlockers(categories, task);
  addPreparationBlockers(categories, task);
  addMaterialBlockers(categories, task);
  addAssignmentBlockers(categories, task);
  addTaskStateBlockers(categories, task);

  const primaryState = resolvePrimaryState(task, categories);
  const primaryLabel = PRIMARY_LABELS[primaryState];
  const shortReason = buildShortReason(primaryState, categories, task);
  const secondaryReasons = buildSecondaryReasons(categories, primaryState);
  const blockerCount = Object.values(categories).reduce((sum, items) => sum + items.length, 0);
  const showProductionBadge = Boolean(task.production_release_blocked);
  const showManagerEscalation = showProductionBadge;

  return {
    primaryState,
    primaryLabel,
    shortReason,
    secondaryReasons,
    blockerCount,
    showProductionBadge,
    productionBadgeLabel: "Producție blocată",
    showManagerEscalation,
    managerEscalationText: MANAGER_ESCALATION_TEXT,
    categories,
    canStartFromBackend: task.is_startable === true,
    canStartExplanation: buildCanStartExplanation(task, { primaryState, categories }),
    diagnosticCodes: collectDiagnosticCodes(task, categories),
    activeSessionLabel:
      task.status === "in_progress"
        ? task.started_at
          ? `Început la ${new Date(task.started_at).toLocaleString("ro-RO")}`
          : "Sesiune activă"
        : null,
  };
}

export function categorySectionLabel(category: EmV2BlockerCategory): string {
  return CATEGORY_LABELS[category];
}

export function primaryStateTone(
  state: EmV2PrimaryReadinessState,
): "ready" | "active" | "warning" | "waiting" | "neutral" {
  switch (state) {
    case "pregatit":
      return "ready";
    case "in_lucru":
    case "finalizat":
      return "active";
    case "blocat_pentru_productie":
    case "nepregatit":
    case "materiale_lipsa":
      return "warning";
    case "in_asteptarea_altei_operatii":
    case "alocat_altui_coleg":
      return "waiting";
    default:
      return "neutral";
  }
}
