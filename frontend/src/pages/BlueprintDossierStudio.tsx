import { useEffect, useState, useCallback, useMemo, useRef, lazy, Suspense } from "react";
import { Link } from "react-router-dom";
import {
  productTemplatesApi,
  type ProductTemplateEntity,
} from "@/lib/api";
import {
  filterActiveTemplatesForQuote,
  filterArchivedExperimentalTemplates,
  isActiveTemplateForQuote,
  isOwnerValidActiveTemplate,
  OWNER_VALID_ACTIVE_TEMPLATE_CODE,
} from "@/lib/activeTemplateScope";
import {
  blueprintDossierApi,
  classifyDossierError,
  DOSSIER_SECTIONS,
  ALLOWED_STATUS_TRANSITIONS,
  STATUS_CONFIG,
  SECTION_STATE_CONFIG,
  safeStringifyJson,
  countPopulatedSections,
  getCompletionStates,
  type BlueprintDossierEntity,
  type DossierStatus,
  type DossierSectionMeta,
  type SectionCompletionState,
} from "@/api/blueprintDossier";
import {
  productTemplateModuleLinksApi,
  type ProductTemplateModuleLinkEntity,
} from "@/api/productTemplateModuleLinks";
import { getProductReadiness, type ProductReadinessDto } from "@/api/productReadiness";
import { isDevAuthFallback } from "@/lib/mockGuard";
import { ProductAggregateOverviewPanel } from "@/features/product-system/ProductAggregateOverviewPanel";
import { useProductAggregate } from "@/features/product-system/useProductAggregate";
import type { ProductAggregate } from "@/api/productAggregate";
import { ProductTemplatePublicationPanel } from "@/features/product-system/ProductTemplatePublicationPanel";
import { ProductE2EReadinessPanel } from "@/features/product-system/ProductE2EReadinessPanel";
import { ComponentContractUsedByPanel } from "@/features/product-system/ComponentContractUsedByPanel";
import {
  DossierSectionEditorShell,
  VariantsEditor,
  TaskRulesEditor,
  TimeAssumptionsEditor,
  CostEngineMappingEditor,
  QcCheckpointsEditor,
  RisksEditor,
  ProductionNotesEditor,
  CompletionStateEditor,
  DossierValidationSummary,
} from "@/components/dossier/DossierSectionEditors";
import {
  FileText,
  Plus,
  Save,
  X,
  ChevronRight,
  ChevronDown,
  Search,
  ArrowLeft,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Shield,
  Eye,
  Trash2,
  Hash,
  Layers,
  ArrowRightLeft,
  Info,
  Package,
  Lock,
  Ban,
  RotateCcw,
  Wifi,
  WifiOff,
  ChevronUp,
  User,
  UserCheck,
} from "lucide-react";

// ============================================================
// CONSTANTS
// ============================================================
const DEFERRED_SECTION_KEYS = new Set([
  "output_blocks_json",
  "visual_prompt_blocks_json",
]);

const ACTIVE_SECTION_KEYS = DOSSIER_SECTIONS
  .filter((s) => !DEFERRED_SECTION_KEYS.has(s.key) && s.key !== "completion_state_json")
  .map((s) => s.key);

const DOSSIER_SECTION_GROUPS = [
  {
    key: "quote",
    title: "Contract Ofertare",
    authority: "Contract runtime",
    description: "Contractul minim verificat lângă Readiness Authority. Prețul real rămâne în Product Template + Pricing Registry.",
    sectionKeys: ["variants_json", "costengine_mapping_json", "quote_readiness_json"],
  },
  {
    key: "production",
    title: "Contract Producție",
    authority: "Ghid producție",
    description: "Instrucțiuni pentru lucru și verificare. Nu creează task-uri și nu mută stoc.",
    sectionKeys: ["task_rules_json", "qc_checkpoints_json", "production_notes_json"],
  },
  {
    key: "documentation",
    title: "Documentație Tehnică",
    authority: "Documentație",
    description: "Context util pentru oameni. Nu este autoritate de cost, materiale, operații sau ofertare.",
    sectionKeys: ["sections_json", "layers_json", "time_assumptions_json", "risks_json"],
  },
  {
    key: "advanced",
    title: "Avansat / Output",
    authority: "Opțional / amânat",
    description: "Preview output, prompturi vizuale și progres editorial. Nu decide readiness sau ofertare.",
    sectionKeys: ["output_blocks_json", "visual_prompt_blocks_json", "completion_state_json"],
  },
] as const;

type DossierSectionGroupMeta = (typeof DOSSIER_SECTION_GROUPS)[number];

const ORDERED_DOSSIER_SECTION_KEYS = DOSSIER_SECTION_GROUPS.flatMap((group) => group.sectionKeys);
const DOSSIER_SECTION_BY_KEY = new Map(DOSSIER_SECTIONS.map((section) => [section.key, section]));
const SECTION_GROUP_BY_KEY = new Map<string, DossierSectionGroupMeta>(
  DOSSIER_SECTION_GROUPS.flatMap((group) =>
    group.sectionKeys.map((key): [string, DossierSectionGroupMeta] => [key, group]),
  ),
);
const QUOTE_CONTRACT_SECTION_KEYS = new Set<string>(
  DOSSIER_SECTION_GROUPS.find((group) => group.key === "quote")?.sectionKeys ?? [],
);
const DEFAULT_VISIBLE_DOSSIER_GROUP_KEYS = new Set(["quote", "production"]);

// ============================================================
// ERROR CLASSIFIER
// ============================================================
interface ClassifiedError {
  code: number;
  message: string;
  detail: string;
  type: "permission" | "not_found" | "conflict" | "validation" | "network" | "unknown";
}

function classifyError(e: unknown): ClassifiedError {
  const msg = e instanceof Error ? e.message : String(e);

  // Network errors
  if (msg.includes("Failed to fetch") || msg.includes("NetworkError") || msg.includes("ERR_")) {
    return { code: 0, message: "Eroare de rețea", detail: msg, type: "network" };
  }
  if (msg.includes("403")) {
    const detail = msg.replace(/^API 403:\s*/, "");
    return { code: 403, message: "Nu ai drept de editare pentru acest dossier. Modul este read-only.", detail, type: "permission" };
  }
  if (msg.includes("404")) {
    const detail = msg.replace(/^API 404:\s*/, "");
    return { code: 404, message: "Resursa nu a fost găsită.", detail, type: "not_found" };
  }
  if (msg.includes("409")) {
    const detail = msg.replace(/^API 409:\s*/, "");
    return { code: 409, message: "Conflict detectat.", detail, type: "conflict" };
  }
  if (msg.includes("422")) {
    const detail = msg.replace(/^API 422:\s*/, "");
    return { code: 422, message: "Validare eșuată pe server.", detail, type: "validation" };
  }
  return { code: 0, message: msg, detail: msg, type: "unknown" };
}

function errorIcon(type: ClassifiedError["type"]) {
  switch (type) {
    case "permission": return <Lock className="w-4 h-4 text-amber-400 shrink-0" />;
    case "not_found": return <Search className="w-4 h-4 text-slate-400 shrink-0" />;
    case "conflict": return <Ban className="w-4 h-4 text-orange-400 shrink-0" />;
    case "validation": return <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />;
    case "network": return <WifiOff className="w-4 h-4 text-red-400 shrink-0" />;
    default: return <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />;
  }
}

function errorBgClass(type: ClassifiedError["type"]) {
  switch (type) {
    case "permission": return "bg-amber-900/20 border-amber-800/40 text-amber-300";
    case "not_found": return "bg-slate-800/40 border-slate-700/40 text-slate-300";
    case "conflict": return "bg-orange-900/20 border-orange-800/40 text-orange-300";
    case "validation": return "bg-red-900/20 border-red-800/40 text-red-300";
    case "network": return "bg-red-900/20 border-red-800/40 text-red-300";
    default: return "bg-red-900/20 border-red-800/40 text-red-300";
  }
}

function errorCodeBadge(type: ClassifiedError["type"], code: number) {
  if (code === 0) return null;
  const colors: Record<string, string> = {
    permission: "text-amber-400 bg-amber-900/20",
    conflict: "text-orange-400 bg-orange-900/20",
    validation: "text-red-400 bg-red-900/20",
    not_found: "text-slate-400 bg-slate-800/40",
    network: "text-red-400 bg-red-900/20",
    unknown: "text-red-400 bg-red-900/20",
  };
  return (
    <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${colors[type] || colors.unknown}`}>
      {code}
    </span>
  );
}

// ============================================================
// SECTION JSON HELPERS
// ============================================================
function getJsonPayloadInfo(value: string | null): {
  type: "object" | "array" | "empty" | "null" | "invalid";
  count?: number;
} {
  if (value === null || value === undefined) return { type: "null" };
  const trimmed = value.trim();
  if (trimmed.length === 0) return { type: "empty" };
  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed)) return { type: "array", count: parsed.length };
    if (parsed && typeof parsed === "object") return { type: "object", count: Object.keys(parsed).length };
    return { type: "object" };
  } catch {
    return { type: "invalid" };
  }
}

// ============================================================
// SCOPE META — aligned with ProductSystem header chips
// ============================================================
function DossierScopeMetaBar({
  templates,
  selectedDossier,
}: {
  templates: ProductTemplateEntity[];
  selectedDossier: BlueprintDossierEntity | null;
}) {
  const activeCount = filterActiveTemplatesForQuote(templates).length;
  const archivedCount = filterArchivedExperimentalTemplates(templates).length;
  const dossierStatus = selectedDossier
    ? STATUS_CONFIG[selectedDossier.status as DossierStatus]?.label ?? selectedDossier.status
    : "—";

  return (
    <div className="flex flex-wrap items-center gap-2">
      {[
        { label: "Live DB" },
        { label: `${activeCount} activ` },
        { label: `${archivedCount} arhivate` },
        { label: `Dossier: ${dossierStatus}` },
        { label: "Design-time" },
      ].map((chip) => (
        <span
          key={chip.label}
          className="px-2 py-1 text-[10px] font-semibold text-slate-500 bg-[#111827] border border-[#1E293B] rounded-md"
        >
          {chip.label}
        </span>
      ))}
    </div>
  );
}

function DossierTemplateFocusPanel({
  template,
  dossier,
  onCreateDossier,
  onOpenDossier,
}: {
  template: ProductTemplateEntity;
  dossier: BlueprintDossierEntity | null;
  onCreateDossier: () => void;
  onOpenDossier: () => void;
}) {
  const isActive = isActiveTemplateForQuote(template);
  const statusCfg = dossier ? STATUS_CONFIG[dossier.status as DossierStatus] : null;

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-6 space-y-4">
      <div>
        <p className="text-[10px] font-bold text-purple-400 uppercase tracking-wide mb-1">
          Șablon selectat
        </p>
        <h2 className="text-[15px] font-bold text-slate-100 font-mono">{template.template_code}</h2>
        <p className="text-[12px] text-slate-300 mt-0.5">{template.family_name || "—"}</p>
        <span
          className={`inline-block mt-2 px-2 py-0.5 text-[9px] font-bold uppercase rounded-full border ${
            isActive
              ? "bg-emerald-900/30 text-emerald-400 border-emerald-700/40"
              : "bg-slate-800/60 text-slate-400 border-slate-600/40"
          }`}
        >
          {isActive ? "Template activ" : "Template arhivat"}
        </span>
      </div>

      {!isActive ? (
        <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg border border-amber-800/35 bg-amber-950/20 text-amber-300/90">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <p className="text-[11px] leading-relaxed">
            Template arhivat — dossier doar pentru istoric, nu pentru ofertare activă.
          </p>
        </div>
      ) : null}

      <div className="border-t border-[#1E293B] pt-4 space-y-2">
        <p className="text-[10px] text-slate-500 uppercase tracking-wide font-bold">Status dossier</p>
        {dossier && statusCfg ? (
          <p className={`text-[12px] font-semibold ${statusCfg.color}`}>
            {statusCfg.emoji} {statusCfg.label} · v{dossier.dossier_version}
          </p>
        ) : (
          <p className="text-[12px] text-slate-400">Niciun dossier tehnic creat încă.</p>
        )}
      </div>

      <div className="flex flex-wrap gap-2 pt-1">
        <Link
          to="/product-system"
          className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-lg text-[11px] font-semibold transition-colors"
        >
          <Package className="w-3.5 h-3.5" /> Deschide în Blueprint Studio
        </Link>
        {dossier ? (
          <button
            type="button"
            onClick={onOpenDossier}
            className="flex items-center gap-1.5 px-3 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-[11px] font-bold transition-colors"
          >
            <FileText className="w-3.5 h-3.5" /> Deschide dossier
          </button>
        ) : (
          <button
            type="button"
            onClick={onCreateDossier}
            className="flex items-center gap-1.5 px-3 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[11px] font-bold transition-colors"
          >
            <Plus className="w-3.5 h-3.5" /> Creează dossier
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================
// TEMPLATE ROW — polished with reviewer/reviewed_at
// ============================================================
function TemplateRow({
  template,
  dossier,
  selected,
  onSelect,
  onCreateDossier,
  aggregate,
}: {
  template: ProductTemplateEntity;
  dossier: BlueprintDossierEntity | null;
  selected: boolean;
  onSelect: () => void;
  onCreateDossier: () => void;
  aggregate?: ProductAggregate | null;
}) {
  const componentsCount = useMemo(() => {
    if (aggregate?.components?.length) {
      return aggregate.components.length;
    }
    try {
      const arr = JSON.parse(template.components_json || "[]");
      return Array.isArray(arr) ? arr.length : 0;
    } catch { return 0; }
  }, [template.components_json, aggregate]);

  const operationsCount = useMemo(() => {
    if (aggregate?.operations?.length) {
      return aggregate.operations.length;
    }
    try {
      const arr = JSON.parse(template.operations_json || "[]");
      return Array.isArray(arr) ? arr.length : 0;
    } catch { return 0; }
  }, [template.operations_json, aggregate]);

  const materialsCount = useMemo(() => {
    if (aggregate?.materials?.length) {
      return aggregate.materials.length;
    }
    try {
      const arr = JSON.parse(template.required_materials_json || "[]");
      return Array.isArray(arr) ? arr.length : 0;
    } catch { return 0; }
  }, [template.required_materials_json, aggregate]);

  const statusCfg = dossier ? (STATUS_CONFIG[dossier.status as DossierStatus] || STATUS_CONFIG.draft) : null;
  const fmtDate = (d: string | null | undefined) => {
    if (!d) return "—";
    try { return new Date(d).toLocaleDateString("ro-RO"); } catch { return "—"; }
  };

  const quoteActive = isActiveTemplateForQuote(template);

  return (
    <div
      className={`rounded-xl border p-3 transition-all duration-200 cursor-pointer ${
        selected
          ? "border-purple-500/50 ring-2 ring-purple-500/20 bg-purple-900/10"
          : "border-[#1E293B] bg-[#111827] hover:border-slate-500 hover:bg-[#131B2E]"
      }`}
      onClick={onSelect}
    >
      {/* Row 1: Code + Status */}
      <div className="flex items-start justify-between gap-2 mb-1.5">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <Package className="w-3.5 h-3.5 text-blue-400 shrink-0" />
            <span className="text-[12px] font-mono text-blue-400 font-bold truncate">
              {template.template_code}
            </span>
            {quoteActive ? (
              <span className="px-1.5 py-0.5 text-[8px] font-bold bg-emerald-900/30 text-emerald-400 border border-emerald-700/40 rounded">
                ACTIV
              </span>
            ) : (
              <span className="px-1.5 py-0.5 text-[8px] font-bold bg-slate-700/50 text-slate-500 border border-slate-600/40 rounded">
                ARHIVAT
              </span>
            )}
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 truncate">
            {template.family_name || "—"}
          </p>
        </div>
        {dossier ? (
          <span className={`px-2 py-0.5 text-[9px] font-bold rounded-full shrink-0 border ${statusCfg!.bgColor} ${statusCfg!.borderColor} ${statusCfg!.color}`}>
            {statusCfg!.emoji} {statusCfg!.label}
          </span>
        ) : (
          <span className="px-2 py-0.5 text-[9px] font-bold rounded-full shrink-0 border border-slate-600/40 bg-slate-700/30 text-slate-500">
            — Fără Dossier
          </span>
        )}
      </div>

      {/* Row 2: Counts + Dossier metadata */}
      <div className="flex items-center gap-2 text-[9px] text-slate-500 mb-1.5 flex-wrap">
        <span className="flex items-center gap-0.5">
          <Layers className="w-3 h-3" /> {componentsCount}
        </span>
        <span className="flex items-center gap-0.5">⚙️ {operationsCount}</span>
        <span className="flex items-center gap-0.5">📦 {materialsCount}</span>
        {aggregate ? (
          <span className="px-1 py-0.5 rounded border border-purple-700/40 bg-purple-900/20 text-purple-300 font-bold">
            AGG
          </span>
        ) : null}
        {dossier && (
          <>
            <span className="text-slate-600">|</span>
            <span className="flex items-center gap-0.5">
              <Hash className="w-3 h-3" /> v{dossier.dossier_version}
            </span>
            <span className="flex items-center gap-0.5" title="Proprietar">
              <User className="w-3 h-3" /> {dossier.owner_role || "—"}
            </span>
            <span className="flex items-center gap-0.5" title="Revizor">
              <UserCheck className="w-3 h-3" /> {dossier.reviewer_role || "—"}
            </span>
          </>
        )}
      </div>

      {/* Row 3: Dates */}
      {dossier && (
        <div className="flex items-center gap-3 text-[9px] text-slate-600 mb-2">
          <span className="flex items-center gap-0.5" title="Actualizat">
            <Clock className="w-3 h-3" /> {fmtDate(dossier.updated_at)}
          </span>
          <span className="flex items-center gap-0.5" title="Revizuit">
            <Eye className="w-3 h-3" /> {dossier.reviewed_at ? fmtDate(dossier.reviewed_at) : "nerevizuit"}
          </span>
        </div>
      )}

      {/* Row 4: Actions */}
      <div className="flex items-center gap-2">
        <Link
          to="/product-system"
          onClick={(e) => e.stopPropagation()}
          className="flex items-center gap-1 px-2 py-1 bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 rounded-lg text-[10px] font-semibold transition-colors"
        >
          <Package className="w-3 h-3" /> Șablon
        </Link>
        {dossier ? (
          <button
            onClick={(e) => { e.stopPropagation(); onSelect(); }}
            className="flex items-center gap-1 px-2 py-1 bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 rounded-lg text-[10px] font-semibold transition-colors"
          >
            <FileText className="w-3 h-3" /> Editează
          </button>
        ) : (
          <button
            onClick={(e) => { e.stopPropagation(); onCreateDossier(); }}
            className="flex items-center gap-1 px-2 py-1 bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 rounded-lg text-[10px] font-semibold transition-colors"
          >
            <Plus className="w-3 h-3" /> Creează Dossier
          </button>
        )}
      </div>
    </div>
  );
}

// ============================================================
// SECTION NAV SIDEBAR — quick jump to sections
// ============================================================
function SectionNav({
  sections,
  activeSectionKey,
  onSelect,
  localSections,
  completionStates,
}: {
  sections: DossierSectionMeta[];
  activeSectionKey: string | null;
  onSelect: (key: string) => void;
  localSections: Record<string, string | null>;
  completionStates: Record<string, { status: SectionCompletionState }>;
}) {
  return (
    <div className="bg-[#0D1321] border border-[#1E293B] rounded-xl p-2 space-y-0.5">
      <p className="text-[9px] text-slate-600 uppercase tracking-wide font-bold px-2 py-1">
        Navigare Secțiuni
      </p>
      {sections.map((section) => {
        const isDeferred = DEFERRED_SECTION_KEYS.has(section.key);
        const cleanKey = section.key.replace("_json", "");
        const state = completionStates[cleanKey]?.status || "not_started";
        const stateCfg = SECTION_STATE_CONFIG[state];
        const value = localSections[section.key] ?? null;
        const jsonInfo = getJsonPayloadInfo(value);
        const isActive = activeSectionKey === section.key;
        const hasContent = jsonInfo.type !== "null" && jsonInfo.type !== "empty";
        const isInvalid = jsonInfo.type === "invalid";

        return (
          <button
            key={section.key}
            onClick={() => !isDeferred && onSelect(section.key)}
            disabled={isDeferred}
            className={`w-full text-left flex items-center gap-2 px-2 py-1.5 rounded-lg text-[10px] transition-all ${
              isDeferred
                ? "opacity-40 cursor-not-allowed"
                : isActive
                ? "bg-purple-500/15 border border-purple-500/30 text-purple-300"
                : "hover:bg-slate-800/50 text-slate-400 border border-transparent"
            }`}
          >
            <span className="text-sm shrink-0">{section.emoji}</span>
            <span className="flex-1 truncate font-semibold">{section.label}</span>
            <div className="flex items-center gap-1 shrink-0">
              {isDeferred ? (
                <span className="px-1 py-0.5 text-[7px] font-bold bg-slate-700/50 text-slate-600 rounded">DEF</span>
              ) : (
                <>
                  {isInvalid && <span className="w-1.5 h-1.5 rounded-full bg-red-500" title="JSON invalid" />}
                  {!isInvalid && hasContent && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" title="Are conținut" />}
                  {!isInvalid && !hasContent && <span className="w-1.5 h-1.5 rounded-full bg-slate-600" title="Gol" />}
                  <span className={`text-[8px] ${stateCfg.color}`}>{stateCfg.emoji}</span>
                </>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}

// ============================================================
// SECTION CARD — summary card for a section
// ============================================================
function SectionCard({
  section,
  value,
  completionState,
  isDeferred,
  dossierStatus,
}: {
  section: DossierSectionMeta;
  value: string | null;
  completionState: SectionCompletionState;
  isDeferred: boolean;
  dossierStatus: DossierStatus;
}) {
  const stateCfg = SECTION_STATE_CONFIG[completionState];
  const jsonInfo = getJsonPayloadInfo(value);
  const group = SECTION_GROUP_BY_KEY.get(section.key);
  const isQuoteContract = QUOTE_CONTRACT_SECTION_KEYS.has(section.key);
  const isEmpty = jsonInfo.type === "null" || jsonInfo.type === "empty";
  const showApprovedWarning = dossierStatus === "approved" && isEmpty && isQuoteContract && !isDeferred;

  return (
    <div className={`rounded-lg border px-3 py-2 ${
      isDeferred
        ? "border-slate-700/30 bg-slate-800/20 opacity-50"
        : jsonInfo.type === "invalid"
        ? "border-red-700/30 bg-red-900/10"
        : "border-[#1E293B] bg-[#111827]"
    }`}>
      <div className="flex items-center gap-2 mb-1">
        <span className="text-sm">{section.emoji}</span>
        <span className={`text-[10px] font-bold ${section.color} flex-1 truncate`}>{section.label}</span>
        {isDeferred && <span className="px-1 py-0.5 text-[7px] font-bold bg-slate-700/50 text-slate-600 rounded">DEFERRED</span>}
        {isQuoteContract && !isDeferred && <span className="px-1 py-0.5 text-[7px] font-bold bg-emerald-900/30 text-emerald-400 rounded">QUOTE</span>}
        {!isQuoteContract && section.priority && !isDeferred && <span className="px-1 py-0.5 text-[7px] font-bold bg-slate-700/40 text-slate-500 rounded">DOC</span>}
      </div>
      <div className="flex items-center gap-2 text-[9px]">
        <span className={`${stateCfg.color}`}>{stateCfg.emoji} {stateCfg.label}</span>
        <span className="text-slate-600">·</span>
        {jsonInfo.type === "invalid" ? (
          <span className="text-red-400">⚠ JSON invalid</span>
        ) : jsonInfo.type === "null" || jsonInfo.type === "empty" ? (
          <span className="text-slate-600">gol</span>
        ) : (
          <span className="text-slate-400">
            {jsonInfo.type === "array" ? `array [${jsonInfo.count}]` : `object {${jsonInfo.count}}`}
          </span>
        )}
        {showApprovedWarning && (
          <>
            <span className="text-slate-600">·</span>
            <span className="text-amber-400">⚠ contract ofertare gol</span>
          </>
        )}
        {!showApprovedWarning && isEmpty && group?.key !== "quote" && (
          <>
            <span className="text-slate-600">·</span>
            <span className="text-slate-600">opțional</span>
          </>
        )}
      </div>
    </div>
  );
}

// ============================================================
// COMPLETION PROGRESS BAR
// ============================================================
function CompletionProgress({ dossier, localCompletionState }: {
  dossier: BlueprintDossierEntity;
  localCompletionState: Record<string, { status: SectionCompletionState }>;
}) {
  const sectionKeys = DOSSIER_SECTIONS
    .filter((s) => s.key !== "completion_state_json" && !DEFERRED_SECTION_KEYS.has(s.key))
    .map((s) => s.key.replace("_json", ""));

  let complete = 0;
  let inProgress = 0;
  let blocked = 0;
  const total = sectionKeys.length;

  sectionKeys.forEach((key) => {
    const st = localCompletionState[key]?.status || "not_started";
    if (st === "complete") complete++;
    else if (st === "draft" || st === "needs_review") inProgress++;
    else if (st === "blocked") blocked++;
  });

  const pctComplete = total > 0 ? Math.round((complete / total) * 100) : 0;
  const pctInProgress = total > 0 ? Math.round((inProgress / total) * 100) : 0;
  const pctBlocked = total > 0 ? Math.round((blocked / total) * 100) : 0;

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-[10px] text-slate-500 uppercase tracking-wide font-bold">
          Progres Completare (din completion_state_json)
        </span>
        <span className="text-[11px] text-slate-300 font-bold">
          {complete}/{total} secțiuni complete ({pctComplete}%)
        </span>
      </div>
      <div className="h-2 bg-[#1E293B] rounded-full overflow-hidden flex">
        {pctComplete > 0 && <div className="bg-emerald-500 h-full transition-all duration-500" style={{ width: `${pctComplete}%` }} />}
        {pctInProgress > 0 && <div className="bg-amber-500 h-full transition-all duration-500" style={{ width: `${pctInProgress}%` }} />}
        {pctBlocked > 0 && <div className="bg-red-500 h-full transition-all duration-500" style={{ width: `${pctBlocked}%` }} />}
      </div>
      <div className="flex items-center gap-3 text-[9px]">
        <span className="flex items-center gap-1 text-emerald-400"><span className="w-2 h-2 rounded-full bg-emerald-500" /> {complete} complete</span>
        <span className="flex items-center gap-1 text-amber-400"><span className="w-2 h-2 rounded-full bg-amber-500" /> {inProgress} în lucru</span>
        <span className="flex items-center gap-1 text-red-400"><span className="w-2 h-2 rounded-full bg-red-500" /> {blocked} blocate</span>
        <span className="flex items-center gap-1 text-slate-500"><span className="w-2 h-2 rounded-full bg-slate-600" /> {total - complete - inProgress - blocked} neîncepute</span>
      </div>
    </div>
  );
}

function DossierContractOverview({
  localSections,
}: {
  localSections: Record<string, string | null>;
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
      {DOSSIER_SECTION_GROUPS.filter((group) => group.key !== "advanced").map((group) => {
        let populated = 0;
        let invalid = 0;
        let empty = 0;

        group.sectionKeys.forEach((key) => {
          const info = getJsonPayloadInfo(localSections[key] ?? null);
          if (info.type === "invalid") invalid++;
          else if (info.type === "null" || info.type === "empty") empty++;
          else populated++;
        });

        return (
          <div key={group.key} className="bg-[#111827] border border-[#1E293B] rounded-xl p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-[11px] font-bold text-slate-200">{group.title}</p>
                <p className="text-[8px] text-emerald-400 uppercase tracking-wide font-bold mt-0.5">{group.authority}</p>
                <p className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">{group.description}</p>
              </div>
              <span className="text-[10px] font-bold text-slate-400 bg-slate-800/70 border border-slate-700 rounded-lg px-2 py-1 shrink-0">
                {populated}/{group.sectionKeys.length}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-3 text-[9px]">
              <span className="text-emerald-400">{populated} completate</span>
              {empty > 0 && <span className="text-slate-500">{empty} goale</span>}
              {invalid > 0 && <span className="text-red-400">{invalid} invalide</span>}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function parseModuleLinkJson(value: string | null | undefined): unknown {
  if (!value) return null;
  try {
    return JSON.parse(value);
  } catch {
    return null;
  }
}

function formatModuleLinkValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return JSON.stringify(value);
}

function TemplateModuleLinksPanel({
  links,
}: {
  links: ProductTemplateModuleLinkEntity[];
}) {
  if (links.length === 0) return null;

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-3 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[10px] font-bold text-slate-300 uppercase tracking-wide">Module atașabile</p>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Contracte declarative între șabloane. Părintele nu calculează modulul; doar îl cere când trigger-ul este activ.
          </p>
        </div>
        <span className="px-2 py-1 text-[9px] font-bold text-emerald-300 bg-emerald-900/20 border border-emerald-700/30 rounded-lg">
          {links.length} activ
        </span>
      </div>
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-2">
        {links.map((link) => {
          const triggerValue = parseModuleLinkJson(link.trigger_value_json);
          const inputMapping = parseModuleLinkJson(link.input_mapping_json);
          const defaultValues = parseModuleLinkJson(link.default_values_json);
          const mappingEntries = inputMapping && typeof inputMapping === "object" && !Array.isArray(inputMapping)
            ? Object.entries(inputMapping as Record<string, unknown>)
            : [];
          const defaultEntries = defaultValues && typeof defaultValues === "object" && !Array.isArray(defaultValues)
            ? Object.entries(defaultValues as Record<string, unknown>)
            : [];

          return (
            <div key={link.id} className="rounded-lg border border-emerald-800/25 bg-emerald-950/10 p-3 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-[11px] font-mono font-bold text-emerald-300 truncate">{link.module_template_code}</p>
                  <p className="text-[9px] text-slate-500 mt-0.5">{link.relation_type} · {link.pricing_mode} · {link.execution_mode}</p>
                </div>
                <span className="px-1.5 py-0.5 text-[8px] font-bold bg-slate-800 text-slate-400 border border-slate-700 rounded">
                  {link.active ? "ACTIV" : "INACTIV"}
                </span>
              </div>
              <div className="rounded-md bg-[#0D1321] border border-[#1E293B] px-2 py-1.5">
                <p className="text-[9px] text-slate-500 uppercase font-bold">Trigger</p>
                <p className="text-[10px] text-slate-300 font-mono">{link.trigger_field} = {formatModuleLinkValue(triggerValue)}</p>
              </div>
              {mappingEntries.length > 0 && (
                <div>
                  <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Mapare inputuri</p>
                  <div className="flex flex-wrap gap-1.5">
                    {mappingEntries.map(([from, to]) => (
                      <span key={from} className="px-2 py-1 text-[9px] font-mono bg-slate-900/60 border border-slate-700/50 text-slate-300 rounded">
                        {from} → {formatModuleLinkValue(to)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {defaultEntries.length > 0 && (
                <div>
                  <p className="text-[9px] text-slate-500 uppercase font-bold mb-1">Valori implicite</p>
                  <div className="flex flex-wrap gap-1.5">
                    {defaultEntries.map(([key, value]) => (
                      <span key={key} className="px-2 py-1 text-[9px] font-mono bg-slate-900/60 border border-slate-700/50 text-slate-400 rounded">
                        {key}: {formatModuleLinkValue(value)}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {link.notes ? <p className="text-[10px] text-slate-500 leading-relaxed">{link.notes}</p> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// STATUS TRANSITION CONTROLS
// ============================================================
function StatusTransitionBar({
  dossier,
  onTransition,
  saving,
  readOnly,
}: {
  dossier: BlueprintDossierEntity;
  onTransition: (newStatus: DossierStatus) => void;
  saving: boolean;
  readOnly: boolean;
}) {
  const current = dossier.status as DossierStatus;
  const allowed = ALLOWED_STATUS_TRANSITIONS[current] || [];
  const currentCfg = STATUS_CONFIG[current];

  return (
    <div className="bg-[#0D1321] border border-[#1E293B] rounded-xl p-3">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Shield className="w-4 h-4 text-purple-400" />
          <span className="text-[11px] font-bold text-slate-200">Ciclu de Viață Dossier</span>
        </div>
        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${currentCfg.bgColor} ${currentCfg.borderColor}`}>
          <span className="text-sm">{currentCfg.emoji}</span>
          <span className={`text-[11px] font-bold ${currentCfg.color}`}>{currentCfg.label}</span>
          <span className="text-[9px] text-slate-500 ml-1">v{dossier.dossier_version}</span>
        </div>
      </div>

      {readOnly ? (
        <div className="flex items-center gap-2 px-3 py-2 bg-amber-900/10 border border-amber-800/20 rounded-lg">
          <Lock className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <p className="text-[10px] text-amber-300">
            Nu ai drept de editare pentru acest dossier. Modul este read-only.
          </p>
        </div>
      ) : allowed.length > 0 ? (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[9px] text-slate-500 uppercase tracking-wide font-bold shrink-0">Tranziții permise:</span>
          {allowed.map((target) => {
            const cfg = STATUS_CONFIG[target];
            return (
              <button
                key={target}
                onClick={() => onTransition(target)}
                disabled={saving}
                className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg border text-[10px] font-bold transition-all disabled:opacity-50 ${cfg.bgColor} ${cfg.borderColor} ${cfg.color} hover:brightness-125`}
              >
                <ArrowRightLeft className="w-3 h-3" />
                {cfg.emoji} {cfg.label}
              </button>
            );
          })}
        </div>
      ) : null}

      {current === "approved" && !readOnly && (
        <div className="flex items-center gap-2 mt-2 px-3 py-2 bg-emerald-900/10 border border-emerald-800/20 rounded-lg">
          <Info className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <p className="text-[10px] text-emerald-300">
            Tranziția la &quot;Aprobat&quot; auto-incrementează versiunea dossier-ului.
          </p>
        </div>
      )}
    </div>
  );
}

// ============================================================
// METADATA PANEL — polished
// ============================================================
function MetadataPanel({ dossier, templateCode }: { dossier: BlueprintDossierEntity; templateCode?: string }) {
  const fmtDate = (d: string | null) => {
    if (!d) return "—";
    try { return new Date(d).toLocaleString("ro-RO"); } catch { return d; }
  };

  const items: { label: string; value: string; readOnly?: boolean }[] = [
    { label: "Status", value: `${STATUS_CONFIG[dossier.status as DossierStatus]?.emoji || ""} ${STATUS_CONFIG[dossier.status as DossierStatus]?.label || dossier.status}` },
    { label: "Versiune", value: String(dossier.dossier_version), readOnly: true },
    { label: "Template Code", value: templateCode || dossier.template_code, readOnly: true },
    { label: "Template ID", value: String(dossier.template_id), readOnly: true },
    { label: "Proprietar", value: dossier.owner_role || "— nesetat" },
    { label: "Revizor", value: dossier.reviewer_role || "— nesetat" },
    { label: "Creat la", value: fmtDate(dossier.created_at) },
    { label: "Actualizat la", value: fmtDate(dossier.updated_at) },
    { label: "Revizuit la", value: dossier.reviewed_at ? fmtDate(dossier.reviewed_at) : "— nerevizuit" },
  ];

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-3">
      <p className="text-[9px] text-slate-600 uppercase tracking-wide font-bold mb-2">Metadate Dossier</p>
      <div className="grid grid-cols-3 gap-x-4 gap-y-1.5">
        {items.map((it) => (
          <div key={it.label}>
            <span className="text-[9px] text-slate-600 block">{it.label} {it.readOnly && <Lock className="w-2 h-2 inline text-slate-700" />}</span>
            <span className="text-[11px] text-slate-300 font-mono">{it.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================
// DOSSIER DETAIL EDITOR — stabilized
// ============================================================
function DossierEditor({
  dossier,
  moduleLinks,
  onSave,
  onDelete,
  onCancel,
  saving,
  readOnly,
  lastBackendError,
}: {
  dossier: BlueprintDossierEntity;
  moduleLinks: ProductTemplateModuleLinkEntity[];
  onSave: (updates: Partial<BlueprintDossierEntity>) => void;
  onDelete: () => void;
  onCancel: () => void;
  saving: boolean;
  readOnly: boolean;
  lastBackendError: ClassifiedError | null;
}) {
  const [localSections, setLocalSections] = useState<Record<string, string | null>>({});
  const [localCompletionState, setLocalCompletionState] = useState<Record<string, { status: SectionCompletionState }>>({});
  const [ownerRole, setOwnerRole] = useState(dossier.owner_role || "");
  const [reviewerRole, setReviewerRole] = useState(dossier.reviewer_role || "");
  const [dirty, setDirty] = useState(false);
  const [hasJsonError, setHasJsonError] = useState(false);
  const [sectionJsonErrors, setSectionJsonErrors] = useState<Record<string, boolean>>({});
  const [activeSectionKey, setActiveSectionKey] = useState<string | null>(null);
  const [sectionDirty, setSectionDirty] = useState<Record<string, boolean>>({});
  const [visibleGroupKeys, setVisibleGroupKeys] = useState<Set<string>>(() => new Set(DEFAULT_VISIBLE_DOSSIER_GROUP_KEYS));

  useEffect(() => {
    const anyError = Object.values(sectionJsonErrors).some(Boolean);
    setHasJsonError(anyError);
  }, [sectionJsonErrors]);

  // Initialize from dossier
  useEffect(() => {
    const sections: Record<string, string | null> = {};
    DOSSIER_SECTIONS.forEach((s) => {
      sections[s.key] = (dossier as unknown as Record<string, unknown>)[s.key] as string | null ?? null;
    });
    setLocalSections(sections);
    setLocalCompletionState(getCompletionStates(dossier));
    setOwnerRole(dossier.owner_role || "");
    setReviewerRole(dossier.reviewer_role || "");
    setDirty(false);
    setSectionJsonErrors({});
    setSectionDirty({});
  }, [dossier]);

  const handleSectionChange = (key: string, value: string | null) => {
    setLocalSections((prev) => ({ ...prev, [key]: value }));
    setSectionDirty((prev) => ({ ...prev, [key]: true }));
    if (value === null || value === undefined) {
      setSectionJsonErrors((prev) => ({ ...prev, [key]: false }));
    } else {
      try {
        JSON.parse(value);
        setSectionJsonErrors((prev) => ({ ...prev, [key]: false }));
      } catch {
        setSectionJsonErrors((prev) => ({ ...prev, [key]: true }));
      }
    }
    setDirty(true);
  };

  const handleCompletionChange = (sectionKey: string, state: SectionCompletionState) => {
    const cleanKey = sectionKey.replace("_json", "");
    setLocalCompletionState((prev) => ({
      ...prev,
      [cleanKey]: { status: state },
    }));
    setDirty(true);
  };

  const handleSave = () => {
    if (readOnly || hasJsonError) return;
    const updates: Partial<BlueprintDossierEntity> = {};

    DOSSIER_SECTIONS.forEach((s) => {
      if (s.key === "completion_state_json") return;
      if (DEFERRED_SECTION_KEYS.has(s.key)) return;
      const current = (dossier as unknown as Record<string, unknown>)[s.key] as string | null ?? null;
      const next = localSections[s.key] ?? null;
      if (current !== next) {
        (updates as Record<string, unknown>)[s.key] = next;
      }
    });

    const newCompletionJson = safeStringifyJson(localCompletionState);
    if (newCompletionJson !== dossier.completion_state_json) {
      updates.completion_state_json = newCompletionJson;
    }

    if (ownerRole !== (dossier.owner_role || "")) {
      updates.owner_role = ownerRole || (undefined as unknown as string);
    }
    if (reviewerRole !== (dossier.reviewer_role || "")) {
      updates.reviewer_role = reviewerRole || (undefined as unknown as string);
    }

    onSave(updates);
  };

  const handleRefresh = () => {
    // Reset to server state
    const sections: Record<string, string | null> = {};
    DOSSIER_SECTIONS.forEach((s) => {
      sections[s.key] = (dossier as unknown as Record<string, unknown>)[s.key] as string | null ?? null;
    });
    setLocalSections(sections);
    setLocalCompletionState(getCompletionStates(dossier));
    setOwnerRole(dossier.owner_role || "");
    setReviewerRole(dossier.reviewer_role || "");
    setDirty(false);
    setSectionJsonErrors({});
    setSectionDirty({});
  };

  const canDelete = dossier.status === "draft" || dossier.status === "deprecated";
  const deleteDisabledReason = !canDelete
    ? `Ștergerea nu este permisă pentru status "${STATUS_CONFIG[dossier.status as DossierStatus]?.label || dossier.status}". Doar draft sau deprecated pot fi șterse.`
    : null;

  const visibleGroups = DOSSIER_SECTION_GROUPS.filter((group) => visibleGroupKeys.has(group.key));
  const visibleSectionKeys = visibleGroups.flatMap((group) => group.sectionKeys);

  const toggleVisibleGroup = (groupKey: string) => {
    setVisibleGroupKeys((prev) => {
      const next = new Set(prev);
      if (next.has(groupKey)) {
        next.delete(groupKey);
      } else {
        next.add(groupKey);
      }
      return next.size > 0 ? next : prev;
    });
  };

  const scrollToSection = (key: string) => {
    setActiveSectionKey(key);
    const el = document.getElementById(`section-${key}`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  // Validation summary
  const validationSummary = useMemo(() => {
    let valid = 0;
    let invalid = 0;
    let empty = 0;
    let deferred = 0;
    DOSSIER_SECTIONS.forEach((s) => {
      if (s.key === "completion_state_json") return;
      if (DEFERRED_SECTION_KEYS.has(s.key)) { deferred++; return; }
      const val = localSections[s.key] ?? null;
      const info = getJsonPayloadInfo(val);
      if (info.type === "invalid") invalid++;
      else if (info.type === "null" || info.type === "empty") empty++;
      else valid++;
    });
    return { valid, invalid, empty, deferred };
  }, [localSections]);

  return (
    <div className="space-y-4">
      {/* Header bar with save controls */}
      <div className="flex items-center justify-between bg-[#111827] border border-[#1E293B] rounded-xl px-4 py-3 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <FileText className="w-5 h-5 text-purple-400" />
          <div>
            <h2 className="text-[14px] font-bold text-slate-100">
              Blueprint Dossier — {dossier.template_code}
            </h2>
            <p className="text-[10px] text-slate-500">
              v{dossier.dossier_version} · {STATUS_CONFIG[dossier.status as DossierStatus]?.emoji} {STATUS_CONFIG[dossier.status as DossierStatus]?.label}
            </p>
          </div>
          {readOnly && (
            <span className="px-2 py-1 text-[9px] font-bold bg-amber-900/20 text-amber-400 border border-amber-700/30 rounded-lg flex items-center gap-1">
              <Lock className="w-3 h-3" /> READ-ONLY
            </span>
          )}
          {dirty && !readOnly && (
            <span className="px-2 py-1 text-[9px] font-bold bg-amber-900/20 text-amber-400 border border-amber-700/30 rounded-lg">
              ● MODIFICĂRI NESALVATE
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {/* Validation summary badge */}
          <div className="flex items-center gap-1.5 px-2 py-1.5 bg-slate-800/50 rounded-lg text-[9px]">
            <span className="text-emerald-400">{validationSummary.valid} ✓</span>
            {validationSummary.invalid > 0 && <span className="text-red-400">{validationSummary.invalid} ✗</span>}
            <span className="text-slate-500">{validationSummary.empty} gol</span>
          </div>

          <button
            onClick={onCancel}
            disabled={saving}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-[11px] font-semibold transition-colors disabled:opacity-50"
          >
            <X className="w-3.5 h-3.5" /> Închide
          </button>
          {!readOnly && (
            <>
              <button
                onClick={handleRefresh}
                disabled={saving}
                className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-[11px] font-semibold transition-colors disabled:opacity-50"
                title="Resetează la ultima salvare"
              >
                <RotateCcw className="w-3.5 h-3.5" />
              </button>
              <div className="relative group">
                <button
                  onClick={canDelete ? onDelete : undefined}
                  disabled={saving || !canDelete}
                  className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-[11px] font-semibold transition-colors disabled:opacity-50 ${
                    canDelete ? "bg-red-700 hover:bg-red-600 text-white" : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
                  }`}
                >
                  <Trash2 className="w-3.5 h-3.5" /> Șterge
                </button>
                {deleteDisabledReason && (
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-[10px] text-slate-300 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 shadow-xl">
                    {deleteDisabledReason}
                  </div>
                )}
              </div>
              <button
                onClick={handleSave}
                disabled={!dirty || saving || hasJsonError}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-[11px] font-bold transition-colors ${
                  dirty && !saving && !hasJsonError
                    ? "bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/30"
                    : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
                }`}
              >
                <Save className="w-3.5 h-3.5" />
                {saving ? "Salvare..." : hasJsonError ? "JSON Invalid — Salvare blocată" : dirty ? "Salvează" : "Salvat"}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Backend error display */}
      {lastBackendError && (
        <div className={`flex items-start gap-2 px-4 py-3 rounded-xl border ${errorBgClass(lastBackendError.type)}`}>
          {errorIcon(lastBackendError.type)}
          <div className="flex-1">
            <p className="text-[12px] font-semibold">{lastBackendError.message}</p>
            {lastBackendError.detail !== lastBackendError.message && (
              <p className="text-[10px] opacity-80 mt-0.5">{lastBackendError.detail}</p>
            )}
            {lastBackendError.type === "permission" && (
              <p className="text-[10px] text-amber-400 mt-1">Toate controalele de editare sunt dezactivate.</p>
            )}
            {lastBackendError.type === "network" && (
              <p className="text-[10px] text-slate-400 mt-1">Datele locale nesalvate sunt păstrate. Reîncearcă când conexiunea este restabilită.</p>
            )}
            {lastBackendError.type === "validation" && (
              <p className="text-[10px] text-slate-400 mt-1">Backend-ul este autoritatea finală de validare.</p>
            )}
          </div>
          {errorCodeBadge(lastBackendError.type, lastBackendError.code)}
        </div>
      )}

      {/* Metadata panel */}
      <MetadataPanel dossier={dossier} />

      <DossierContractOverview localSections={localSections} />

      <TemplateModuleLinksPanel links={moduleLinks} />

      {/* Authoring rail: same Product System authority — dossier is not a second SoT */}
      <div className="space-y-3" data-testid="blueprint-dossier-authoring-rail">
        <p className="text-[10px] text-slate-500 px-1">
          Dossier = documentație + dovezi review + punți aprobate. Publicarea șablonului și E2E Readiness rămân pe Product Template.
        </p>
        <ProductTemplatePublicationPanel templateCode={dossier.template_code} />
        <ComponentContractUsedByPanel templateCode={dossier.template_code} />
        <ProductE2EReadinessPanel templateCode={dossier.template_code} />
      </div>

      <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-3">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <p className="text-[10px] font-bold text-slate-300 uppercase tracking-wide">Afișaj selectiv</p>
            <p className="text-[10px] text-slate-500 mt-0.5">
              Implicit se afișează doar contractele utile zilnic. Documentația și output-ul rămân păstrate în dossier.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setVisibleGroupKeys(new Set(DOSSIER_SECTION_GROUPS.map((group) => group.key)))}
            className="px-2.5 py-1.5 text-[10px] font-bold text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg transition-colors"
          >
            Afișează tot
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2">
          {DOSSIER_SECTION_GROUPS.map((group) => {
            const checked = visibleGroupKeys.has(group.key);
            const important = group.key === "quote" || group.key === "production";
            return (
              <label
                key={group.key}
                className={`flex items-start gap-2 rounded-lg border px-3 py-2 cursor-pointer transition-colors ${
                  checked
                    ? "bg-emerald-900/10 border-emerald-700/30 text-slate-200"
                    : "bg-slate-900/30 border-slate-700/30 text-slate-500"
                }`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleVisibleGroup(group.key)}
                  className="mt-0.5 h-3.5 w-3.5 accent-emerald-500"
                />
                <span className="min-w-0">
                  <span className="flex items-center gap-2 text-[11px] font-bold">
                    {group.title}
                    {important ? <span className="text-[8px] text-emerald-400 bg-emerald-900/20 px-1.5 py-0.5 rounded">IMPORTANT</span> : null}
                  </span>
                  <span className="block text-[9px] text-slate-500 mt-0.5">{group.authority}</span>
                </span>
              </label>
            );
          })}
        </div>
      </div>

      {/* Ownership fields */}
      {!readOnly && (
        <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-3">
          <p className="text-[9px] text-slate-600 uppercase tracking-wide font-bold mb-2">Proprietate & Revizuire</p>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[10px] text-slate-500 block mb-1">Rol Proprietar</label>
              <input
                type="text"
                value={ownerRole}
                onChange={(e) => { setOwnerRole(e.target.value); setDirty(true); }}
                placeholder="ex: product_manager"
                className="w-full bg-[#0D1321] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 font-mono outline-none focus:border-purple-500/50"
              />
            </div>
            <div>
              <label className="text-[10px] text-slate-500 block mb-1">Rol Revizor</label>
              <input
                type="text"
                value={reviewerRole}
                onChange={(e) => { setReviewerRole(e.target.value); setDirty(true); }}
                placeholder="ex: tech_lead"
                className="w-full bg-[#0D1321] border border-[#2A3548] rounded-lg px-3 py-2 text-[12px] text-slate-200 font-mono outline-none focus:border-purple-500/50"
              />
            </div>
          </div>
        </div>
      )}

      {/* Section navigation + Section cards + Section editors */}
      <div className="grid grid-cols-1 lg:grid-cols-[200px_1fr] gap-4">
        {/* Left: Section nav */}
        <div className="space-y-3">
          <SectionNav
            sections={visibleSectionKeys.map((key) => DOSSIER_SECTION_BY_KEY.get(key)).filter(Boolean) as DossierSectionMeta[]}
            activeSectionKey={activeSectionKey}
            onSelect={scrollToSection}
            localSections={localSections}
            completionStates={localCompletionState}
          />
        </div>

        {/* Right: Section cards summary + editors */}
        <div className="space-y-3">
          {/* Section cards summary */}
          <div className="space-y-3">
            {visibleGroups.map((group) => (
              <div key={group.key} className="bg-[#0D1321] border border-[#1E293B] rounded-xl p-3">
                <div className="flex items-start justify-between gap-3 mb-2">
                  <div>
                    <p className="text-[11px] font-bold text-slate-200">{group.title}</p>
                    <p className="text-[8px] text-emerald-400 uppercase tracking-wide font-bold mt-0.5">{group.authority}</p>
                    <p className="text-[10px] text-slate-500 mt-0.5">{group.description}</p>
                  </div>
                  {group.key === "advanced" && (
                    <span className="px-2 py-1 text-[8px] font-bold bg-slate-700/50 text-slate-500 border border-slate-600/40 rounded">OPȚIONAL</span>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
                  {group.sectionKeys.map((sectionKey) => {
                    const section = DOSSIER_SECTION_BY_KEY.get(sectionKey);
                    if (!section || section.key === "completion_state_json") return null;
                    const cleanKey = section.key.replace("_json", "");
                    const isDeferred = DEFERRED_SECTION_KEYS.has(section.key);
                    return (
                      <SectionCard
                        key={section.key}
                        section={section}
                        value={localSections[section.key] ?? null}
                        completionState={localCompletionState[cleanKey]?.status || "not_started"}
                        isDeferred={isDeferred}
                        dossierStatus={dossier.status as DossierStatus}
                      />
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* Dossier-level validation summary */}
          <DossierValidationSummary
            localSections={localSections}
            completionStates={localCompletionState}
            dossierStatus={dossier.status}
            backendError={lastBackendError?.type === "validation" ? lastBackendError.detail : null}
            deferredKeys={DEFERRED_SECTION_KEYS}
            allSectionKeys={DOSSIER_SECTIONS.map((s) => s.key)}
          />

          {/* Section editors */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              <h3 className="text-[13px] font-bold text-slate-100">Secțiuni Dossier</h3>
              <span className="text-[10px] text-purple-400 bg-purple-500/10 px-2 py-0.5 rounded-full font-bold">
                {visibleSectionKeys.length}/{ORDERED_DOSSIER_SECTION_KEYS.length}
              </span>
            </div>

            {visibleSectionKeys.map((sectionKey) => {
              const section = DOSSIER_SECTION_BY_KEY.get(sectionKey);
              if (!section) return null;
              const cleanKey = section.key.replace("_json", "");
              const currentState = localCompletionState[cleanKey]?.status || "not_started";
              const isDeferred = DEFERRED_SECTION_KEYS.has(section.key);
              const sectionValue = localSections[section.key] ?? null;
              const backendErr = lastBackendError?.type === "validation" ? lastBackendError.detail : null;

              // Completion state editor (special)
              if (section.key === "completion_state_json") {
                return (
                  <DossierSectionEditorShell
                    key={section.key}
                    sectionKey={section.key}
                    label={section.label}
                    emoji={section.emoji}
                    color={section.color}
                    description={section.description}
                    priority={section.priority}
                    safetyLabel="Doar progres editorial — nu blochează oferte/comenzi și nu calculează readiness."
                    value={sectionValue}
                    onChange={(val) => handleSectionChange(section.key, val)}
                    completionState={currentState}
                    onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                    readOnly={readOnly}
                    deferred={false}
                    dirty={!!sectionDirty[section.key]}
                    backendError={backendErr}
                  >
                    {() => (
                      <CompletionStateEditor
                        value={sectionValue}
                        onChange={(val) => handleSectionChange(section.key, val)}
                        readOnly={readOnly}
                        sectionKeys={ACTIVE_SECTION_KEYS.map((k) => k.replace("_json", ""))}
                      />
                    )}
                  </DossierSectionEditorShell>
                );
              }

              // Structured editors for priority sections
              if (section.key === "variants_json") {
                return (
                  <DossierSectionEditorShell
                    key={section.key}
                    sectionKey={section.key}
                    label={section.label}
                    emoji={section.emoji}
                    color={section.color}
                    description={section.description}
                    priority={section.priority}
                    value={sectionValue}
                    onChange={(val) => handleSectionChange(section.key, val)}
                    completionState={currentState}
                    onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                    readOnly={readOnly}
                    deferred={isDeferred}
                    dirty={!!sectionDirty[section.key]}
                    backendError={backendErr}
                  >
                    {() => (
                      <VariantsEditor
                        value={sectionValue}
                        onChange={(val) => handleSectionChange(section.key, val)}
                        readOnly={readOnly}
                      />
                    )}
                  </DossierSectionEditorShell>
                );
              }

              if (section.key === "task_rules_json") {
                return (
                  <DossierSectionEditorShell
                    key={section.key}
                    sectionKey={section.key}
                    label={section.label}
                    emoji={section.emoji}
                    color={section.color}
                    description={section.description}
                    priority={section.priority}
                    safetyLabel="Doar documentație — nu creează task-uri în producție."
                    value={sectionValue}
                    onChange={(val) => handleSectionChange(section.key, val)}
                    completionState={currentState}
                    onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                    readOnly={readOnly}
                    deferred={isDeferred}
                    dirty={!!sectionDirty[section.key]}
                    backendError={backendErr}
                  >
                    {() => (
                      <TaskRulesEditor
                        value={sectionValue}
                        onChange={(val) => handleSectionChange(section.key, val)}
                        readOnly={readOnly}
                      />
                    )}
                  </DossierSectionEditorShell>
                );
              }

              if (section.key === "time_assumptions_json") {
                return (
                  <DossierSectionEditorShell
                    key={section.key}
                    sectionKey={section.key}
                    label={section.label}
                    emoji={section.emoji}
                    color={section.color}
                    description={section.description}
                    priority={section.priority}
                    safetyLabel="Doar documentație — nu calculează cost."
                    value={sectionValue}
                    onChange={(val) => handleSectionChange(section.key, val)}
                    completionState={currentState}
                    onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                    readOnly={readOnly}
                    deferred={isDeferred}
                    dirty={!!sectionDirty[section.key]}
                    backendError={backendErr}
                  >
                    {() => (
                      <TimeAssumptionsEditor
                        value={sectionValue}
                        onChange={(val) => handleSectionChange(section.key, val)}
                        readOnly={readOnly}
                      />
                    )}
                  </DossierSectionEditorShell>
                );
              }

              if (section.key === "costengine_mapping_json") {
                return (
                  <DossierSectionEditorShell
                    key={section.key}
                    sectionKey={section.key}
                    label={section.label}
                    emoji={section.emoji}
                    color={section.color}
                    description={section.description}
                    priority={section.priority}
                    safetyLabel="Mapare pentru audit/viitor CostEngine — nu rulează calculul de cost."
                    value={sectionValue}
                    onChange={(val) => handleSectionChange(section.key, val)}
                    completionState={currentState}
                    onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                    readOnly={readOnly}
                    deferred={isDeferred}
                    dirty={!!sectionDirty[section.key]}
                    backendError={backendErr}
                  >
                    {() => (
                      <CostEngineMappingEditor
                        value={sectionValue}
                        onChange={(val) => handleSectionChange(section.key, val)}
                        readOnly={readOnly}
                      />
                    )}
                  </DossierSectionEditorShell>
                );
              }

              if (section.key === "qc_checkpoints_json") {
                return (
                  <DossierSectionEditorShell
                    key={section.key}
                    sectionKey={section.key}
                    label={section.label}
                    emoji={section.emoji}
                    color={section.color}
                    description={section.description}
                    priority={section.priority}
                    safetyLabel="Doar documentație — nu creează task-uri QC și nu blochează execuția."
                    value={sectionValue}
                    onChange={(val) => handleSectionChange(section.key, val)}
                    completionState={currentState}
                    onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                    readOnly={readOnly}
                    deferred={isDeferred}
                    dirty={!!sectionDirty[section.key]}
                    backendError={backendErr}
                  >
                    {() => (
                      <QcCheckpointsEditor
                        value={sectionValue}
                        onChange={(val) => handleSectionChange(section.key, val)}
                        readOnly={readOnly}
                      />
                    )}
                  </DossierSectionEditorShell>
                );
              }

              if (section.key === "risks_json") {
                return (
                  <DossierSectionEditorShell
                    key={section.key}
                    sectionKey={section.key}
                    label={section.label}
                    emoji={section.emoji}
                    color={section.color}
                    description={section.description}
                    priority={section.priority}
                    safetyLabel="Doar documentație — nu creează incidente și nu blochează comenzi."
                    value={sectionValue}
                    onChange={(val) => handleSectionChange(section.key, val)}
                    completionState={currentState}
                    onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                    readOnly={readOnly}
                    deferred={isDeferred}
                    dirty={!!sectionDirty[section.key]}
                    backendError={backendErr}
                  >
                    {() => (
                      <RisksEditor
                        value={sectionValue}
                        onChange={(val) => handleSectionChange(section.key, val)}
                        readOnly={readOnly}
                      />
                    )}
                  </DossierSectionEditorShell>
                );
              }

              if (section.key === "production_notes_json") {
                return (
                  <DossierSectionEditorShell
                    key={section.key}
                    sectionKey={section.key}
                    label={section.label}
                    emoji={section.emoji}
                    color={section.color}
                    description={section.description}
                    priority={section.priority}
                    safetyLabel="Note structurate — nu modifică inventarul sau execuția."
                    value={sectionValue}
                    onChange={(val) => handleSectionChange(section.key, val)}
                    completionState={currentState}
                    onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                    readOnly={readOnly}
                    deferred={isDeferred}
                    dirty={!!sectionDirty[section.key]}
                    backendError={backendErr}
                  >
                    {() => (
                      <ProductionNotesEditor
                        value={sectionValue}
                        onChange={(val) => handleSectionChange(section.key, val)}
                        readOnly={readOnly}
                      />
                    )}
                  </DossierSectionEditorShell>
                );
              }

              // Fallback: non-priority sections use the shell with no structured editor (JSON only)
              return (
                <DossierSectionEditorShell
                  key={section.key}
                  sectionKey={section.key}
                  label={section.label}
                  emoji={section.emoji}
                  color={section.color}
                  description={section.description}
                  priority={section.priority}
                  value={sectionValue}
                  onChange={(val) => handleSectionChange(section.key, val)}
                  completionState={currentState}
                  onCompletionChange={(state) => handleCompletionChange(section.key, state)}
                  readOnly={readOnly}
                  deferred={isDeferred}
                  dirty={!!sectionDirty[section.key]}
                  backendError={backendErr}
                >
                  {() => (
                    <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/30 border border-slate-700/30 rounded-lg">
                      <Info className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="text-[10px] text-slate-500">
                        Folosește tab-ul JSON Advanced pentru a edita această secțiune.
                      </span>
                    </div>
                  )}
                </DossierSectionEditorShell>
              );
            })}
          </div>
        </div>
      </div>

      {/* Sticky footer — save / validate / E2E / publish (template authority, not dossier SoT) */}
      <div
        className="sticky bottom-0 z-20 flex flex-wrap items-center justify-between gap-2 rounded-xl border border-violet-800/40 bg-[#0B1220]/95 px-4 py-3 backdrop-blur"
        data-testid="blueprint-dossier-sticky-publish-footer"
      >
        <div className="text-[10px] text-slate-400">
          <span className="font-semibold text-violet-200">Product Template</span>
          {" · "}
          {dossier.template_code}
          {" · "}
          dossier status {dossier.status} (documentație)
          {" · "}
          publicare = lifecycle șablon + E2E Readiness
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Link
            to={`/product-system/products/${encodeURIComponent(dossier.template_code)}`}
            className="rounded-lg border border-slate-700 px-3 py-1.5 text-[11px] font-semibold text-slate-200 hover:bg-slate-800"
            data-testid="blueprint-dossier-footer-open-template"
          >
            Deschide șablonul
          </Link>
          <button
            type="button"
            onClick={handleSave}
            disabled={!dirty || saving || hasJsonError || readOnly}
            className={`rounded-lg px-3 py-1.5 text-[11px] font-bold ${
              dirty && !saving && !hasJsonError && !readOnly
                ? "bg-emerald-600 text-white"
                : "bg-slate-800 text-slate-500"
            }`}
            data-testid="blueprint-dossier-footer-save"
          >
            Salvează dossier
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// CREATE DOSSIER DIALOG
// ============================================================
function CreateDossierPanel({
  template,
  onCreate,
  onCancel,
  saving,
}: {
  template: ProductTemplateEntity;
  onCreate: (templateId: number, templateCode: string) => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const isActive = isActiveTemplateForQuote(template);

  return (
    <div className="bg-[#111827] border border-purple-500/30 rounded-xl p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Plus className="w-5 h-5 text-purple-400" />
        <h3 className="text-[14px] font-bold text-slate-100">Creează dossier tehnic</h3>
      </div>
      {!isActive ? (
        <div className="flex items-start gap-2 px-3 py-2.5 rounded-lg border border-amber-800/35 bg-amber-950/20 text-amber-300/90">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <p className="text-[11px] leading-relaxed">
            Template arhivat — dossier doar pentru istoric, nu pentru ofertare activă.
          </p>
        </div>
      ) : null}
      <div className="flex items-center gap-2 px-3 py-2 bg-purple-900/10 border border-purple-700/30 rounded-lg">
        <Info className="w-3.5 h-3.5 text-purple-400 shrink-0" />
        <p className="text-[11px] text-purple-300">
          Dossier-ul va fi creat pentru <strong>{template.template_code}</strong> ({template.family_name || "—"}) cu status &quot;draft&quot; și versiune 1.
        </p>
      </div>
      <div className="flex items-center gap-2 justify-end">
        <button
          onClick={onCancel}
          className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-[12px] font-semibold transition-colors"
        >
          Anulează
        </button>
        <button
          onClick={() => onCreate(template.id, template.template_code)}
          disabled={saving}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-[12px] font-bold transition-colors ${
            !saving ? "bg-purple-600 hover:bg-purple-500 text-white shadow-lg shadow-purple-900/20" : "bg-slate-700/60 text-slate-500 cursor-not-allowed"
          }`}
        >
          <Plus className="w-3.5 h-3.5" /> Creează Dossier
        </button>
      </div>
    </div>
  );
}

// ============================================================
// BOUNDARY WARNING — collapsible
// ============================================================
function BoundaryWarning() {
  const [collapsed, setCollapsed] = useState(true);
  return (
    <div className="bg-slate-800/30 border border-slate-700/40 rounded-xl px-4 py-2.5">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="w-full flex items-start gap-2 text-left"
      >
        <Shield className="w-4 h-4 text-slate-500 shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="text-[10px] text-slate-400 font-bold">Limită de autoritate — Blueprint Dossier</p>
          {!collapsed && (
            <p className="text-[10px] text-slate-500 leading-relaxed mt-0.5">
              Blueprint Dossier este fundație de documentație/config în ProductSystem.
              Nu calculează cost, nu creează oferte/comenzi, nu generează task-uri și nu mută stoc.
            </p>
          )}
        </div>
        {collapsed ? <ChevronDown className="w-3 h-3 text-slate-600 shrink-0 mt-1" /> : <ChevronUp className="w-3 h-3 text-slate-600 shrink-0 mt-1" />}
      </button>
    </div>
  );
}

// ============================================================
// MAIN PAGE
// ============================================================
export default function BlueprintDossierStudio() {
  const [dossiers, setDossiers] = useState<BlueprintDossierEntity[]>([]);
  const [templates, setTemplates] = useState<ProductTemplateEntity[]>([]);
  const [moduleLinks, setModuleLinks] = useState<ProductTemplateModuleLinkEntity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Partial loading: separate warning for dossiers when templates load OK
  const [dossierWarning, setDossierWarning] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [listTab, setListTab] = useState<"active" | "archived">("active");
  const [selectedTemplateId, setSelectedTemplateId] = useState<number | null>(null);
  const [selectedDossierId, setSelectedDossierId] = useState<number | null>(null);
  const [createForTemplate, setCreateForTemplate] = useState<ProductTemplateEntity | null>(null);
  const initialFocusDone = useRef(false);
  const [saving, setSaving] = useState(false);
  const [readOnly, setReadOnly] = useState(false);
  const [lastBackendError, setLastBackendError] = useState<ClassifiedError | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string; errorType?: ClassifiedError["type"]; code?: number } | null>(null);
  const [readiness, setReadiness] = useState<ProductReadinessDto | null>(null);
  const [readinessError, setReadinessError] = useState<string | null>(null);

  /**
   * TASK 12 FIX: Partial loading resilience.
   * Templates and dossiers are loaded independently via Promise.allSettled.
   * - If templates fail → show main error (page cannot function without templates).
   * - If only dossiers fail → show template list + dossier warning with retry.
   * - If both succeed → normal display.
   * - Empty results are treated as empty state, NOT errors.
   */
  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setDossierWarning(null);

    if (isDevAuthFallback()) {
      setTemplates([]);
      setDossiers([]);
      setLoading(false);
      return;
    }

    const [templateResult, dossierResult, moduleLinkResult] = await Promise.allSettled([
      productTemplatesApi.list(),
      blueprintDossierApi.list({ limit: 500, sort: "-updated_at" }),
      productTemplateModuleLinksApi.list({ limit: 500, query: { active: true }, sort: "parent_template_code" }),
    ]);

    // Detect dev/preview mode with no real auth token.
    // In this mode, 401/403 from backend is expected (SDK sends no Authorization header)
    // and should be treated as "backend unavailable in preview" — NOT as a real permission denial.
    const devFallback = isDevAuthFallback();
    let templateAuthDevFallback = false;

    // --- Templates ---
    if (templateResult.status === "fulfilled") {
      const items = templateResult.value;
      setTemplates(Array.isArray(items) ? items : []);
    } else {
      console.error("Failed to load product templates", templateResult.reason);
      const classified = classifyDossierError(templateResult.reason);
      if (classified.type === "auth" && devFallback) {
        // Dev/preview mode without real token — backend is unavailable, not a real permission issue.
        // Show warning + empty state instead of blocking auth error so the UI remains usable.
        console.info("[BlueprintDossierStudio] Auth error in dev fallback mode — treating as empty state");
        templateAuthDevFallback = true;
        setDossierWarning(null);
        setTemplates([]);
      } else if (classified.type === "network") {
        setError("Eroare de rețea — nu s-au putut încărca șabloanele. Verifică conexiunea.");
        setTemplates([]);
      } else if (classified.type === "auth") {
        // Production: real permission denial
        setError("Nu ai permisiune să accesezi șabloanele. Autentifică-te și reîncearcă.");
        setTemplates([]);
      } else {
        setError(`Nu s-au putut încărca șabloanele: ${classified.message}`);
        setTemplates([]);
      }
    }

    // --- Dossiers ---
    if (dossierResult.status === "fulfilled") {
      const data = dossierResult.value;
      setDossiers(Array.isArray(data?.items) ? data.items : []);
    } else {
      console.error("Failed to load blueprint dossiers", dossierResult.reason);
      const classified = classifyDossierError(dossierResult.reason);
      if (classified.type === "auth" && devFallback) {
        // Dev/preview mode — expected, set warning only if not already set by template fallback
        console.info("[BlueprintDossierStudio] Dossier auth error in dev fallback mode — treating as empty");
        if (!templateAuthDevFallback && templateResult.status === "fulfilled") {
          setDossierWarning(null);
        }
      } else if (templateResult.status === "fulfilled" || templateAuthDevFallback) {
        // Only set dossier warning if templates loaded OK (or were dev-fallback empty)
        if (classified.type === "network") {
          setDossierWarning("Nu s-au putut încărca dosarele blueprint — eroare de rețea.");
        } else if (classified.type === "auth") {
          setDossierWarning("Nu ai permisiune să accesezi dosarele blueprint.");
        } else if (classified.type === "not_found") {
          // 404 on list endpoint — treat as empty (endpoint may not exist yet)
          setDossierWarning(null);
        } else {
          setDossierWarning(`Nu s-au putut încărca dosarele blueprint: ${classified.message}`);
        }
      }
      // If templates also failed (non-dev), the main error already covers it
      setDossiers([]);
    }

    if (moduleLinkResult.status === "fulfilled") {
      const data = moduleLinkResult.value;
      setModuleLinks(Array.isArray(data?.items) ? data.items : []);
    } else {
      console.error("Failed to load product template module links", moduleLinkResult.reason);
      setModuleLinks([]);
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!message) return;
    const t = setTimeout(() => setMessage(null), 6000);
    return () => clearTimeout(t);
  }, [message]);

  const dossierByTemplateId = useMemo(() => {
    const map = new Map<number, BlueprintDossierEntity>();
    dossiers.forEach((d) => map.set(d.template_id, d));
    return map;
  }, [dossiers]);

  const selectedDossier = useMemo(
    () => dossiers.find((d) => d.id === selectedDossierId) ?? null,
    [dossiers, selectedDossierId]
  );

  const selectedTemplate = useMemo(
    () => templates.find((t) => t.id === selectedTemplateId) ?? null,
    [templates, selectedTemplateId]
  );

  const aggregateTemplateCode =
    selectedDossier?.template_code ?? selectedTemplate?.template_code ?? null;
  const {
    aggregate,
    usingFallback: aggregateUsingFallback,
    fallbackReason: aggregateFallbackReason,
    isLoading: aggregateLoading,
  } = useProductAggregate(aggregateTemplateCode);

  const activeTemplates = useMemo(
    () => filterActiveTemplatesForQuote(templates),
    [templates]
  );
  const archivedTemplates = useMemo(
    () => filterArchivedExperimentalTemplates(templates),
    [templates]
  );

  const selectedModuleLinks = useMemo(
    () => moduleLinks.filter((link) => link.parent_template_id === selectedDossier?.template_id),
    [moduleLinks, selectedDossier]
  );

  useEffect(() => {
    if (loading || templates.length === 0 || initialFocusDone.current) return;
    const preferred =
      templates.find((t) => isOwnerValidActiveTemplate(t.template_code)) ??
      activeTemplates[0] ??
      null;
    if (!preferred) return;
    setSelectedTemplateId(preferred.id);
    setListTab("active");
    const dossier = dossierByTemplateId.get(preferred.id);
    if (dossier) setSelectedDossierId(dossier.id);
    initialFocusDone.current = true;
  }, [loading, templates, activeTemplates, dossierByTemplateId]);

  useEffect(() => {
    let cancelled = false;

    async function loadReadiness() {
      if (!selectedDossier) {
        setReadiness(null);
        setReadinessError(null);
        return;
      }

      try {
        const data = await getProductReadiness(selectedDossier.template_id);
        if (!cancelled) {
          setReadiness(data);
          setReadinessError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setReadiness(null);
          setReadinessError(err instanceof Error ? err.message : "Readiness unavailable");
        }
      }
    }

    void loadReadiness();
    return () => {
      cancelled = true;
    };
  }, [selectedDossier]);

  const scopedTemplates = useMemo(
    () => (listTab === "active" ? activeTemplates : archivedTemplates),
    [listTab, activeTemplates, archivedTemplates]
  );

  const filteredTemplates = useMemo(() => {
    if (!search.trim()) return scopedTemplates;
    const q = search.toLowerCase();
    return scopedTemplates.filter((t) => {
      const d = dossierByTemplateId.get(t.id);
      return (
        t.template_code.toLowerCase().includes(q) ||
        (t.family_name || "").toLowerCase().includes(q) ||
        String(t.id).includes(q) ||
        (d?.status || "").toLowerCase().includes(q) ||
        (d?.owner_role || "").toLowerCase().includes(q) ||
        (d?.reviewer_role || "").toLowerCase().includes(q)
      );
    });
  }, [scopedTemplates, search, dossierByTemplateId]);

  const showError = (e: unknown) => {
    const classified = classifyError(e);
    setLastBackendError(classified);
    if (classified.type === "permission") {
      setReadOnly(true);
      setMessage({ type: "error", text: classified.message, errorType: classified.type, code: classified.code });
    } else if (classified.type === "conflict") {
      setMessage({ type: "error", text: `Conflict: ${classified.detail}`, errorType: classified.type, code: classified.code });
    } else if (classified.type === "validation") {
      setMessage({ type: "error", text: `Validare eșuată: ${classified.detail}`, errorType: classified.type, code: classified.code });
    } else if (classified.type === "not_found") {
      setMessage({ type: "error", text: `Resursă negăsită: ${classified.detail}`, errorType: classified.type, code: classified.code });
    } else if (classified.type === "network") {
      setMessage({ type: "error", text: "Eroare de rețea. Datele locale sunt păstrate. Reîncearcă.", errorType: classified.type, code: 0 });
    } else {
      setMessage({ type: "error", text: classified.message, errorType: classified.type, code: classified.code });
    }
  };

  const handleCreate = async (templateId: number, templateCode: string) => {
    setSaving(true);
    setLastBackendError(null);
    try {
      const created = await blueprintDossierApi.create({
        template_id: templateId,
        template_code: templateCode,
        dossier_version: 1,
        status: "draft",
      });
      setMessage({ type: "success", text: `Dossier creat: ${created.template_code} (ID: ${created.id})` });
      await loadData();
      setSelectedDossierId(created.id);
      setCreateForTemplate(null);
      setReadOnly(false);
    } catch (e: unknown) {
      console.error("Create dossier failed", e);
      showError(e);
    } finally {
      setSaving(false);
    }
  };

  const handleSave = async (updates: Partial<BlueprintDossierEntity>) => {
    if (!selectedDossier) return;
    if (Object.keys(updates).length === 0) {
      setMessage({ type: "success", text: "Nicio modificare de salvat." });
      return;
    }
    setSaving(true);
    setLastBackendError(null);
    try {
      await blueprintDossierApi.update(selectedDossier.id, updates);
      setMessage({ type: "success", text: `Dossier actualizat: ${selectedDossier.template_code}` });
      await loadData();
    } catch (e: unknown) {
      console.error("Update dossier failed", e);
      showError(e);
    } finally {
      setSaving(false);
    }
  };

  const handleStatusTransition = async (newStatus: DossierStatus) => {
    if (!selectedDossier) return;
    setSaving(true);
    setLastBackendError(null);
    try {
      await blueprintDossierApi.update(selectedDossier.id, { status: newStatus });
      const label = STATUS_CONFIG[newStatus].label;
      setMessage({ type: "success", text: `Status schimbat la: ${label}` });
      await loadData();
    } catch (e: unknown) {
      console.error("Status transition failed", e);
      showError(e);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!selectedDossier) return;
    if (!confirm(`Ștergi dossier-ul ${selectedDossier.template_code} (v${selectedDossier.dossier_version})? Această acțiune nu poate fi anulată.`)) {
      return;
    }
    setSaving(true);
    setLastBackendError(null);
    try {
      await blueprintDossierApi.delete(selectedDossier.id);
      setMessage({ type: "success", text: `Dossier șters: ${selectedDossier.template_code}` });
      setSelectedDossierId(null);
      setLastBackendError(null);
      await loadData();
    } catch (e: unknown) {
      console.error("Delete dossier failed", e);
      showError(e);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setSelectedDossierId(null);
    setCreateForTemplate(null);
    setReadOnly(false);
    setLastBackendError(null);
  };

  const selectTemplate = (template: ProductTemplateEntity) => {
    setSelectedTemplateId(template.id);
    const dossier = dossierByTemplateId.get(template.id) ?? null;
    if (dossier) {
      setSelectedDossierId(dossier.id);
      setCreateForTemplate(null);
    } else {
      setSelectedDossierId(null);
      setCreateForTemplate(null);
    }
    setReadOnly(false);
    setLastBackendError(null);
  };

  return (
    <div className="space-y-4">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-[11px] text-slate-500">
        <Link to="/dashboard" className="flex items-center gap-1 hover:text-slate-300 transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" /> Dashboard
        </Link>
        <ChevronRight className="w-3 h-3" />
        <Link to="/product-system" className="hover:text-slate-300 transition-colors">ProductSystem</Link>
        <ChevronRight className="w-3 h-3" />
        <span className="text-slate-300">Blueprint Dossier Studio</span>
      </div>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="p-2 bg-purple-500/10 rounded-xl shrink-0">
            <FileText className="w-6 h-6 text-purple-400" />
          </div>
          <div className="min-w-0">
            <h1 className="text-[18px] font-bold text-slate-100">
              ProductSystem / Blueprint Dossier
            </h1>
            <p className="text-[11px] text-slate-500">
              Dosare tehnice pentru șabloane validate.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Link
            to="/product-system"
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-600 rounded-lg text-[12px] font-semibold transition-colors"
          >
            <Package className="w-3.5 h-3.5" /> Blueprint Studio
          </Link>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg text-[12px] font-semibold transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} /> Reîncarcă
          </button>
        </div>
      </div>

      {!loading && !error ? (
        <DossierScopeMetaBar templates={templates} selectedDossier={selectedDossier} />
      ) : null}

      {/* Dossier-only warning (partial loading: templates OK, dossiers failed) */}
      {dossierWarning && !error && !loading && (
        <div className="flex items-center gap-2 px-4 py-3 rounded-xl border bg-amber-900/15 border-amber-800/30 text-amber-300">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span className="text-[12px] font-semibold flex-1">{dossierWarning}</span>
          <button
            onClick={loadData}
            className="flex items-center gap-1 px-2.5 py-1 bg-amber-700/30 hover:bg-amber-700/50 text-amber-200 rounded-lg text-[11px] font-bold transition-colors"
          >
            <RefreshCw className="w-3 h-3" /> Reîncearcă dosarele
          </button>
        </div>
      )}

      {/* Boundary warning */}
      {(templates.length > 0 || dossiers.length > 0 || selectedDossierId !== null || createForTemplate !== null) && (
        <BoundaryWarning />
      )}

      {/* Message toast */}
      {message && (
        <div
          className={`flex items-center gap-2 px-4 py-3 rounded-xl border transition-all ${
            message.type === "success"
              ? "bg-emerald-900/20 border-emerald-800/40 text-emerald-300"
              : errorBgClass(message.errorType || "unknown")
          }`}
        >
          {message.type === "success"
            ? <CheckCircle2 className="w-4 h-4" />
            : errorIcon(message.errorType || "unknown")
          }
          <span className="text-[12px] font-semibold flex-1">{message.text}</span>
          {message.code ? errorCodeBadge(message.errorType || "unknown", message.code) : null}
          <button onClick={() => setMessage(null)} className="text-slate-400 hover:text-slate-200 transition-colors">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="flex flex-col items-center gap-3 px-6 py-8 bg-red-900/10 border border-red-800/30 rounded-xl text-center">
          <WifiOff className="w-8 h-8 text-red-400" />
          <p className="text-[13px] text-red-300 font-semibold">{error}</p>
          <button
            onClick={loadData}
            className="flex items-center gap-1.5 px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded-lg text-[12px] font-bold transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Reîncearcă
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center gap-3 py-12">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-500" />
          <p className="text-[12px] text-slate-500">Se încarcă datele Blueprint Studio...</p>
        </div>
      )}

      {/* Main content */}
      {!loading && !error && (
        <div className="grid grid-cols-1 lg:grid-cols-[380px_1fr] gap-4">
          {/* Left: Template list */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 bg-[#111827] border border-[#1E293B] rounded-xl px-3 py-2.5 focus-within:border-purple-500/50">
              <Search className="w-4 h-4 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Caută șablon / dossier / proprietar..."
                className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
              />
            </div>

            <div className="flex gap-1 bg-[#0D1321] p-1 rounded-lg border border-[#1E293B]">
              <button
                type="button"
                onClick={() => setListTab("active")}
                className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-colors ${
                  listTab === "active"
                    ? "bg-purple-600/30 text-purple-200"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                Active ({activeTemplates.length})
              </button>
              <button
                type="button"
                onClick={() => setListTab("archived")}
                className={`px-3 py-1.5 rounded-md text-[11px] font-bold transition-colors ${
                  listTab === "archived"
                    ? "bg-purple-600/30 text-purple-200"
                    : "text-slate-500 hover:text-slate-300"
                }`}
              >
                Arhivate ({archivedTemplates.length})
              </button>
            </div>

            <div className="flex items-center gap-2 px-1">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wide">
                {listTab === "active" ? "Șabloane active" : "Șabloane arhivate"} ({filteredTemplates.length})
              </span>
            </div>

            {filteredTemplates.length === 0 ? (
              <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-6 text-center">
                <Package className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                <p className="text-[12px] text-slate-500">
                  {search.trim() ? "Niciun șablon găsit pentru căutarea curentă." : "Nu există șabloane încă. Creează unul din ProductSystem."}
                </p>
                {!search.trim() && (
                  <Link
                    to="/product-system"
                    className="inline-flex items-center gap-1 mt-3 px-3 py-1.5 bg-purple-600/20 text-purple-300 rounded-lg text-[11px] font-semibold hover:bg-purple-600/30 transition-colors"
                  >
                    <Package className="w-3 h-3" /> Deschide ProductSystem
                  </Link>
                )}
              </div>
            ) : (
              <div className="space-y-2 max-h-[calc(100vh-420px)] overflow-y-auto pr-1">
                {filteredTemplates.map((t) => {
                  const d = dossierByTemplateId.get(t.id) ?? null;
                  return (
                    <TemplateRow
                      key={t.id}
                      template={t}
                      dossier={d}
                      selected={selectedTemplateId === t.id}
                      aggregate={selectedTemplateId === t.id ? aggregate : null}
                      onSelect={() => selectTemplate(t)}
                      onCreateDossier={() => {
                        setSelectedTemplateId(t.id);
                        setCreateForTemplate(t);
                        setSelectedDossierId(null);
                        setReadOnly(false);
                        setLastBackendError(null);
                      }}
                    />
                  );
                })}
              </div>
            )}
          </div>

          {/* Right: Editor or create panel or placeholder */}
          <div>
            {createForTemplate ? (
              <CreateDossierPanel
                template={createForTemplate}
                onCreate={handleCreate}
                onCancel={handleCancel}
                saving={saving}
              />
            ) : selectedDossier ? (
              <div className="space-y-4">
                <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-[12px] font-bold text-slate-200">Readiness Authority (Backend)</p>
                    {readiness ? (
                      <span className="text-[10px] px-2 py-1 rounded border border-slate-600 text-slate-300 bg-slate-800/60">
                        source: {readiness.source}
                      </span>
                    ) : null}
                  </div>
                  {readinessError ? (
                    <p className="text-[11px] text-amber-300">Readiness contract unavailable: {readinessError}</p>
                  ) : readiness ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] text-slate-300">
                      <p>overall_status: {readiness.overall_status}</p>
                      <p>ready_for_quote: {String(readiness.ready_for_quote)}</p>
                      <p>technical: {readiness.technical_readiness.status}</p>
                      <p>costengine: {readiness.costengine_readiness.status}</p>
                      <p>document_output: {readiness.document_output_readiness.status}</p>
                      <p>visual_prompt: {readiness.visual_prompt_readiness.status}</p>
                      <p>execution_preparation: {readiness.execution_preparation_readiness.status}</p>
                      <p>contract_version: {readiness.contract_version}</p>
                    </div>
                  ) : (
                    <p className="text-[11px] text-slate-500">Se încarcă readiness backend...</p>
                  )}
                </div>
                <StatusTransitionBar
                  dossier={selectedDossier}
                  onTransition={handleStatusTransition}
                  saving={saving}
                  readOnly={readOnly}
                />
                {aggregateLoading ? (
                  <div className="text-[11px] text-slate-500">Se încarcă ProductAggregate…</div>
                ) : (
                  <ProductAggregateOverviewPanel
                    aggregate={aggregate}
                    fallbackMessage={aggregateUsingFallback ? aggregateFallbackReason : null}
                    showLegacyFallbackNote={aggregateUsingFallback}
                  />
                )}
                <DossierEditor
                  dossier={selectedDossier}
                  moduleLinks={selectedModuleLinks}
                  onSave={handleSave}
                  onDelete={handleDelete}
                  onCancel={handleCancel}
                  saving={saving}
                  readOnly={readOnly}
                  lastBackendError={lastBackendError}
                />
              </div>
            ) : selectedTemplate ? (
              <DossierTemplateFocusPanel
                template={selectedTemplate}
                dossier={dossierByTemplateId.get(selectedTemplate.id) ?? null}
                onCreateDossier={() => {
                  setCreateForTemplate(selectedTemplate);
                  setSelectedDossierId(null);
                }}
                onOpenDossier={() => {
                  const d = dossierByTemplateId.get(selectedTemplate.id);
                  if (d) setSelectedDossierId(d.id);
                }}
              />
            ) : (
              <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-12 text-center">
                <div className="w-16 h-16 bg-purple-500/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <Eye className="w-8 h-8 text-purple-400" />
                </div>
                <p className="text-[15px] text-slate-300 font-bold mb-1">
                  Selectează {OWNER_VALID_ACTIVE_TEMPLATE_CODE}
                </p>
                <p className="text-[12px] text-slate-500 mb-4 max-w-md mx-auto">
                  Dosarul tehnic continuă fluxul din Blueprint Studio. Începe cu șablonul activ,
                  verifică statusul dossier-ului și creează sau deschide documentația.
                </p>
                <Link
                  to="/product-system"
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-purple-600/20 text-purple-300 rounded-lg text-[12px] font-semibold hover:bg-purple-600/30 transition-colors"
                >
                  <Package className="w-3.5 h-3.5" /> Deschide Blueprint Studio
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}