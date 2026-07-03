/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * API client for Product Blueprint Dossier CRUD.
 *
 * Talks to: /api/v1/entities/product-blueprint-dossiers
 * Backend: product_blueprint_dossier_service.py + router
 *
 * TASK 12 FIX: Replaced custom apiFetch with SDK client.entities pattern
 * to align with the rest of the application (see lib/api.ts makeCrud).
 * Root cause: custom apiFetch bypassed SDK auth (no getToken method exists)
 * and SDK base URL resolution, causing 401/fetch failures.
 */

import { client } from "@/lib/api";

// ============================================================
// TYPES
// ============================================================

export type DossierStatus = "draft" | "needs_review" | "approved" | "blocked" | "deprecated";

export type SectionCompletionState = "not_started" | "draft" | "needs_review" | "complete" | "blocked" | "deprecated";

export interface BlueprintDossierEntity {
  id: number;
  template_id: number;
  template_code: string;
  dossier_version: number;
  status: DossierStatus;
  sections_json: string | null;
  variants_json: string | null;
  layers_json: string | null;
  task_rules_json: string | null;
  time_assumptions_json: string | null;
  costengine_mapping_json: string | null;
  quote_readiness_json: string | null;
  output_blocks_json: string | null;
  visual_prompt_blocks_json: string | null;
  production_notes_json: string | null;
  qc_checkpoints_json: string | null;
  risks_json: string | null;
  completion_state_json: string | null;
  owner_role: string | null;
  reviewer_role: string | null;
  reviewed_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface DossierListResponse {
  items: BlueprintDossierEntity[];
  total: number;
  skip: number;
  limit: number;
}

// ============================================================
// SECTION METADATA — UI config for each JSON section
// ============================================================

export interface DossierSectionMeta {
  key: string;           // JSON field name (e.g. "variants_json")
  label: string;         // Romanian display label
  description: string;   // Short description
  emoji: string;         // Visual identifier
  color: string;         // Tailwind color class
  priority: boolean;     // Whether it has semantic validation on approval
}

export const DOSSIER_SECTIONS: DossierSectionMeta[] = [
  {
    key: "sections_json",
    label: "Secțiuni (Registru)",
    description: "Registrul secțiunilor — ordinea, secțiunile active/amânate",
    emoji: "📋",
    color: "text-slate-400",
    priority: false,
  },
  {
    key: "variants_json",
    label: "Variante / Opțiuni",
    description: "Contract de opțiuni expus la ofertare; valorile operaționale rămân în șablon.",
    emoji: "🔀",
    color: "text-purple-400",
    priority: true,
  },
  {
    key: "layers_json",
    label: "Straturi / Logica Construcției",
    description: "Documentație de construcție; nu este sursă de materiale, operații sau preț.",
    emoji: "🧱",
    color: "text-blue-400",
    priority: false,
  },
  {
    key: "task_rules_json",
    label: "Reguli Sarcini",
    description: "Ghid de execuție; nu generează automat task-uri de producție.",
    emoji: "📐",
    color: "text-cyan-400",
    priority: true,
  },
  {
    key: "time_assumptions_json",
    label: "Estimări Timp",
    description: "Ipoteze documentare; costul real vine din Pricing Registry / rate operații.",
    emoji: "⏱️",
    color: "text-amber-400",
    priority: true,
  },
  {
    key: "costengine_mapping_json",
    label: "Mapare CostEngine",
    description: "Contract de mapare pentru audit; calculul real nu rulează din Dossier.",
    emoji: "💰",
    color: "text-emerald-400",
    priority: true,
  },
  {
    key: "quote_readiness_json",
    label: "Pregătire Ofertare",
    description: "Politică declarată; verdictul real vine din Readiness Authority backend.",
    emoji: "✅",
    color: "text-green-400",
    priority: false,
  },
  {
    key: "output_blocks_json",
    label: "Blocuri Output",
    description: "Preview document ofertă; nu schimbă oferta comercială salvată.",
    emoji: "📄",
    color: "text-indigo-400",
    priority: false,
  },
  {
    key: "visual_prompt_blocks_json",
    label: "Blocuri Prompt Vizual",
    description: "Arhivă prompt vizual; nu există runtime activ de generare.",
    emoji: "🎨",
    color: "text-pink-400",
    priority: false,
  },
  {
    key: "production_notes_json",
    label: "Note Producție",
    description: "Note de lucru; nu mută stoc, task-uri sau statusuri de execuție.",
    emoji: "📝",
    color: "text-orange-400",
    priority: false,
  },
  {
    key: "qc_checkpoints_json",
    label: "Puncte Control Calitate",
    description: "Listă de verificări; nu blochează automat execuția.",
    emoji: "🔍",
    color: "text-teal-400",
    priority: true,
  },
  {
    key: "risks_json",
    label: "Riscuri / Greșeli Comune",
    description: "Note de risc; nu creează incidente și nu blochează comenzi.",
    emoji: "⚠️",
    color: "text-red-400",
    priority: true,
  },
  {
    key: "completion_state_json",
    label: "Stare Completare",
    description: "Progres editorial; nu este readiness score și nu decide ofertarea.",
    emoji: "📊",
    color: "text-violet-400",
    priority: false,
  },
];

// ============================================================
// STATUS TRANSITIONS (mirrors backend hardening §10)
// ============================================================

export const ALLOWED_STATUS_TRANSITIONS: Record<DossierStatus, DossierStatus[]> = {
  draft: ["needs_review", "blocked", "deprecated"],
  needs_review: ["approved", "draft", "blocked", "deprecated"],
  approved: ["needs_review", "deprecated"],
  blocked: ["draft", "needs_review", "deprecated"],
  deprecated: ["draft"],
};

export const STATUS_CONFIG: Record<DossierStatus, { label: string; color: string; bgColor: string; borderColor: string; emoji: string }> = {
  draft: { label: "Ciornă", color: "text-slate-400", bgColor: "bg-slate-500/10", borderColor: "border-slate-500/30", emoji: "📝" },
  needs_review: { label: "Necesită Revizuire", color: "text-amber-400", bgColor: "bg-amber-500/10", borderColor: "border-amber-500/30", emoji: "👀" },
  approved: { label: "Aprobat", color: "text-emerald-400", bgColor: "bg-emerald-500/10", borderColor: "border-emerald-500/30", emoji: "✅" },
  blocked: { label: "Blocat", color: "text-red-400", bgColor: "bg-red-500/10", borderColor: "border-red-500/30", emoji: "🚫" },
  deprecated: { label: "Depreciat", color: "text-slate-500", bgColor: "bg-slate-600/10", borderColor: "border-slate-600/30", emoji: "🗄️" },
};

export const SECTION_STATE_CONFIG: Record<SectionCompletionState, { label: string; color: string; emoji: string }> = {
  not_started: { label: "Neînceput", color: "text-slate-500", emoji: "⬜" },
  draft: { label: "Ciornă", color: "text-slate-400", emoji: "📝" },
  needs_review: { label: "De revizuit", color: "text-amber-400", emoji: "👀" },
  complete: { label: "Complet", color: "text-emerald-400", emoji: "✅" },
  blocked: { label: "Blocat", color: "text-red-400", emoji: "🚫" },
  deprecated: { label: "Depreciat", color: "text-slate-500", emoji: "🗄️" },
};

// ============================================================
// HELPERS
// ============================================================

export function safeParseJson(jsonStr: string | null | undefined): any {
  if (!jsonStr || !jsonStr.trim()) return null;
  try {
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
}

export function safeStringifyJson(value: any): string | null {
  if (value === null || value === undefined) return null;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return null;
  }
}

/** Count how many sections have non-null/non-empty content */
export function countPopulatedSections(dossier: BlueprintDossierEntity): number {
  const sectionKeys = DOSSIER_SECTIONS.map((s) => s.key);
  let count = 0;
  for (const key of sectionKeys) {
    const val = (dossier as any)[key];
    if (val && typeof val === "string" && val.trim().length > 0) {
      count++;
    }
  }
  return count;
}

/** Get completion state map from completion_state_json */
export function getCompletionStates(dossier: BlueprintDossierEntity): Record<string, { status: SectionCompletionState }> {
  const parsed = safeParseJson(dossier.completion_state_json);
  if (!parsed || typeof parsed !== "object") return {};
  return parsed;
}

// ============================================================
// ERROR CLASSIFICATION — granular error types for UI
// ============================================================

export type DossierErrorType =
  | "network"
  | "auth"
  | "not_found"
  | "conflict"
  | "validation"
  | "server"
  | "shape"
  | "unknown";

export interface ClassifiedDossierError {
  type: DossierErrorType;
  status?: number;
  message: string;
  raw?: unknown;
}

export function classifyDossierError(e: unknown): ClassifiedDossierError {
  if (e instanceof TypeError && e.message?.includes("fetch")) {
    return { type: "network", message: "Eroare de rețea — verifică conexiunea.", raw: e };
  }
  if (e && typeof e === "object") {
    const err = e as any;
    // Axios-style error from SDK
    const status: number | undefined =
      err.response?.status ?? err.status ?? undefined;
    if (status === 401 || status === 403) {
      return { type: "auth", status, message: "Nu ai permisiune pentru această acțiune.", raw: e };
    }
    if (status === 404) {
      return { type: "not_found", status, message: "Resursa nu a fost găsită.", raw: e };
    }
    if (status === 409) {
      return { type: "conflict", status, message: "Conflict — resursa a fost modificată.", raw: e };
    }
    if (status === 422) {
      const detail = err.response?.data?.detail || err.message || "Validare eșuată.";
      return { type: "validation", status, message: String(detail), raw: e };
    }
    if (status && status >= 500) {
      return { type: "server", status, message: "Eroare server — reîncearcă mai târziu.", raw: e };
    }
    if (status && status >= 400) {
      const detail = err.response?.data?.detail || err.message || "Eroare API.";
      return { type: "unknown", status, message: String(detail), raw: e };
    }
  }
  const msg = e instanceof Error ? e.message : String(e);
  return { type: "unknown", message: msg, raw: e };
}

// ============================================================
// API CLIENT — uses SDK client.entities pattern (aligned with makeCrud)
// ============================================================

/**
 * Entity name matches the backend router prefix:
 *   /api/v1/entities/product-blueprint-dossiers
 *
 * The SDK Proxy creates entity modules on demand using the key as the
 * URL segment: client.entities["product-blueprint-dossiers"] →
 *   GET  /api/v1/entities/product-blueprint-dossiers
 *   GET  /api/v1/entities/product-blueprint-dossiers/:id
 *   POST /api/v1/entities/product-blueprint-dossiers
 *   PUT  /api/v1/entities/product-blueprint-dossiers/:id
 *   DELETE /api/v1/entities/product-blueprint-dossiers/:id
 *
 * Auth is handled automatically by the SDK's axios interceptors
 * (reads token from localStorage, same as all other entities).
 */
const ENTITY_NAME = "product-blueprint-dossiers";
const entityClient = client.entities[ENTITY_NAME];

export const blueprintDossierApi = {
  /** List dossiers with optional filtering */
  list: async (opts: {
    skip?: number;
    limit?: number;
    query?: Record<string, unknown>;
    sort?: string;
  } = {}): Promise<DossierListResponse> => {
    const res = await entityClient.query({
      query: opts.query,
      sort: opts.sort ?? "-updated_at",
      limit: opts.limit ?? 500,
      skip: opts.skip ?? 0,
    });
    // The backend returns { items, total, skip, limit }.
    // The SDK wraps it in res.data. Handle both shapes defensively.
    const data = res?.data;
    if (data && Array.isArray(data.items)) {
      return data as DossierListResponse;
    }
    // Fallback: if the SDK returns the items directly (shouldn't happen
    // with this backend, but defensive)
    if (Array.isArray(data)) {
      return { items: data, total: data.length, skip: 0, limit: data.length };
    }
    // If data has an `items` key from a nested wrapper
    if (data?.data && Array.isArray(data.data.items)) {
      return data.data as DossierListResponse;
    }
    // Empty fallback
    return { items: [], total: 0, skip: 0, limit: 0 };
  },

  /** Get dossier by ID */
  get: async (id: number): Promise<BlueprintDossierEntity> => {
    const res = await entityClient.get({ id: String(id) });
    return (res?.data ?? res) as BlueprintDossierEntity;
  },

  /** Get dossier by template_id — uses apiCall.invoke for custom endpoint */
  getByTemplate: async (templateId: number): Promise<BlueprintDossierEntity | null> => {
    try {
      const res = await client.apiCall.invoke({
        url: `/api/v1/entities/${ENTITY_NAME}/by-template/${templateId}`,
        method: "GET",
      });
      return (res?.data ?? res) as BlueprintDossierEntity;
    } catch (e: any) {
      const status = e?.response?.status ?? e?.status;
      if (status === 404) return null;
      // Also check error message for 404 pattern
      if (e?.message?.includes("404")) return null;
      throw e;
    }
  },

  /** Create a new dossier */
  create: async (data: Partial<BlueprintDossierEntity>): Promise<BlueprintDossierEntity> => {
    const res = await entityClient.create({ data: data as Record<string, unknown> });
    return (res?.data ?? res) as BlueprintDossierEntity;
  },

  /** Update an existing dossier */
  update: async (id: number, data: Partial<BlueprintDossierEntity>): Promise<BlueprintDossierEntity> => {
    const res = await entityClient.update({ id: String(id), data: data as Record<string, unknown> });
    return (res?.data ?? res) as BlueprintDossierEntity;
  },

  /** Delete a dossier (only draft/deprecated allowed) */
  delete: async (id: number): Promise<void> => {
    await entityClient.delete({ id: String(id) });
  },
};