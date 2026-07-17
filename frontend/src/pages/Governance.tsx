import { useState, useMemo, useCallback, useEffect } from "react";
import {
  agents,
  truthHierarchy,
  uiTruthRules,
  moduleStatusFlows,
  systemEvents,
  invalidPatterns,
  productCatalog,
} from "@/lib/governanceData";
import {
  HONESTY_SEPARATION_RULES,
  GOVERNANCE_TAB_HONESTY,
  type GovernanceTabHonestyMeta,
} from "@/lib/truthPagesHonestyBaseline";
import {
  CANONICAL_SPINE_LABELS_RO,
  PRESENT_BOUNDARIES,
  PRESENT_GATES,
  PRESENT_GUARDRAILS,
  PRESENT_OWNERSHIP_ROWS,
  SETTINGS_OWNERSHIP_ROWS,
  governanceStatusBadgeClass,
  presentStatusBadgeClass,
} from "@/lib/currentTruthControlCenter";
import {
  fetchDocumentationIndex,
  type DocumentationIndexFetchResult,
} from "@/api/documentationIndex";
import { ImportantDocumentsSection } from "@/components/workos/ImportantDocumentsSection";
import { SectionHeader } from "@/components/workos/SharedComponents";
import {
  Shield,
  ArrowRight,
  ChevronDown,
  ChevronRight,
  Layers,
  Users,
  Eye,
  Lock,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Info,
  Ban,
  Zap,
  BookOpen,
  GitBranch,
  Package,
  Activity,
  Search,
  X,
  Download,
  FileJson,
  FileSpreadsheet,
} from "lucide-react";

type Tab =
  | "ownership"
  | "boundaries"
  | "agents"
  | "truth"
  | "gates"
  | "guardrails"
  | "ui-rules"
  | "status-flows"
  | "products";

const tabs: { id: Tab; label: string; icon: React.ReactNode }[] = [
  { id: "ownership", label: "Cine deține adevărul", icon: <Shield className="w-3.5 h-3.5" /> },
  { id: "boundaries", label: "Harta limitelor", icon: <Layers className="w-3.5 h-3.5" /> },
  { id: "status-flows", label: "Fluxuri de stare", icon: <Activity className="w-3.5 h-3.5" /> },
  { id: "agents", label: "Autoritatea agenților", icon: <Users className="w-3.5 h-3.5" /> },
  { id: "truth", label: "Surse de adevăr", icon: <Eye className="w-3.5 h-3.5" /> },
  { id: "gates", label: "Owner gates", icon: <Lock className="w-3.5 h-3.5" /> },
  { id: "guardrails", label: "Reguli de protecție", icon: <Shield className="w-3.5 h-3.5" /> },
  { id: "products", label: "Catalog produse (referință)", icon: <Package className="w-3.5 h-3.5" /> },
  { id: "ui-rules", label: "Reguli de adevăr UI", icon: <BookOpen className="w-3.5 h-3.5" /> },
];

function TabHonestyBanner({ meta }: { meta: GovernanceTabHonestyMeta }) {
  const tone =
    meta.status === "HONESTY_BASELINE"
      ? "border-blue-800/40 bg-blue-900/15 text-blue-200/95"
      : meta.status === "STALE_HINT" || meta.status === "OWNER_REVIEW"
        ? "border-amber-800/40 bg-amber-900/15 text-amber-200/95"
        : "border-slate-600/50 bg-slate-800/40 text-slate-300";
  return (
    <div
      className={`flex items-start gap-2 px-3 py-2 rounded-lg border text-[11px] leading-relaxed ${tone}`}
      data-testid={`governance-tab-honesty-${meta.tabId}`}
    >
      <AlertTriangle className="w-3.5 h-3.5 mt-0.5 shrink-0 opacity-80" />
      <div>
        <p className="font-semibold mb-0.5">
          {meta.status} · read-only
        </p>
        <p>{meta.noteRo}</p>
        <p className="mt-1 text-[10px] opacity-80 flex items-center gap-1">
          <BookOpen className="w-3 h-3" />
          Sursă: {meta.source}
        </p>
      </div>
    </div>
  );
}

// --- HIGHLIGHT HELPER ---
function HighlightText({ text, query }: { text: string; query: string }) {
  if (!query.trim()) return <>{text}</>;
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  const parts = text.split(regex);
  return (
    <>
      {parts.map((part, i) =>
        regex.test(part) ? (
          <mark key={i} className="bg-amber-500/30 text-amber-200 rounded-sm px-0.5">
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </>
  );
}

// --- SEARCH INDEX ---
type Severity = "critical" | "warning" | "info" | "none";
type ItemType = "regulă" | "produs" | "agent" | "status" | "gate" | "event";

interface SearchResult {
  category: string;
  categoryIcon: React.ReactNode;
  tab: Tab;
  title: string;
  subtitle: string;
  details: string[];
  severity: Severity;
  module: string;
  itemType: ItemType;
}

function buildSearchIndex(): SearchResult[] {
  const results: SearchResult[] = [];

  // Boundaries (present spine)
  for (const layer of PRESENT_BOUNDARIES) {
    results.push({
      category: "Boundary Map",
      categoryIcon: <Layers className="w-3.5 h-3.5" />,
      tab: "boundaries",
      title: `${layer.technicalAlias} — ${layer.nameRo}`,
      subtitle: layer.truthControlledRo,
      details: [layer.enforcementRo, ...layer.allowedRo, ...layer.forbiddenRo],
      severity: "critical",
      module: layer.technicalAlias,
      itemType: "regulă",
    });
  }

  // Agents
  for (const agent of agents) {
    results.push({
      category: "Agent Authority",
      categoryIcon: <Users className="w-3.5 h-3.5" />,
      tab: "agents",
      title: `${agent.icon} ${agent.shortName} — ${agent.name}`,
      subtitle: agent.role,
      details: [...agent.authority, ...agent.noAuthority, ...agent.escalatesWhen],
      severity: "none",
      module: "System",
      itemType: "agent",
    });
  }

  // Truth Hierarchy
  for (const source of truthHierarchy) {
    results.push({
      category: "Source of Truth",
      categoryIcon: <Eye className="w-3.5 h-3.5" />,
      tab: "truth",
      title: `Nivel ${source.level}: ${source.name}`,
      subtitle: source.role,
      details: [source.truthFor, source.notTruthFor],
      severity: source.level <= 3 ? "critical" : source.level <= 5 ? "warning" : "info",
      module: source.name,
      itemType: "regulă",
    });
  }

  // Owner gates (present policy)
  for (const gate of PRESENT_GATES) {
    results.push({
      category: "Owner gates",
      categoryIcon: <Lock className="w-3.5 h-3.5" />,
      tab: "gates",
      title: gate.nameRo,
      subtitle: gate.status,
      details: [gate.blocksRo, gate.enforcementRo, gate.verificationRo],
      severity: "critical",
      module: "Owner",
      itemType: "gate",
    });
  }

  // Guardrails (present)
  for (const g of PRESENT_GUARDRAILS) {
    results.push({
      category: "Guardrails",
      categoryIcon: <Shield className="w-3.5 h-3.5" />,
      tab: "guardrails",
      title: `${g.id} — ${g.titleRo}`,
      subtitle: g.status,
      details: [g.requirementRo, g.enforcementRo],
      severity: g.status === "POLITICA OWNER" ? "info" : "warning",
      module: "System",
      itemType: "regulă",
    });
  }

  // UI Rules
  for (const rule of uiTruthRules) {
    results.push({
      category: "UI Truth Rules",
      categoryIcon: <BookOpen className="w-3.5 h-3.5" />,
      tab: "ui-rules",
      title: `${rule.id} — ${rule.rule}`,
      subtitle: rule.area,
      details: [...rule.correctExamples, ...rule.incorrectExamples],
      severity: "warning",
      module: "UI",
      itemType: "regulă",
    });
  }

  // Status Flows
  for (const mod of moduleStatusFlows) {
    results.push({
      category: "Status Flows",
      categoryIcon: <Activity className="w-3.5 h-3.5" />,
      tab: "status-flows",
      title: `${mod.shortName} — ${mod.name}`,
      subtitle: `Owner: ${mod.owner}`,
      details: [
        ...mod.statuses,
        ...mod.transitions.map((t) => `${t.from} → ${t.to} (${t.trigger})`),
      ],
      severity: "none",
      module: mod.shortName,
      itemType: "status",
    });
  }

  // System Events
  for (const evt of systemEvents) {
    results.push({
      category: "Status Flows",
      categoryIcon: <Activity className="w-3.5 h-3.5" />,
      tab: "status-flows",
      title: evt.event,
      subtitle: `Source: ${evt.source}`,
      details: [evt.description],
      severity: "info",
      module: evt.source,
      itemType: "event",
    });
  }

  // Products
  for (const cat of productCatalog) {
    for (const prod of cat.products) {
      results.push({
        category: "Product Catalog",
        categoryIcon: <Package className="w-3.5 h-3.5" />,
        tab: "products",
        title: prod.name,
        subtitle: `${cat.name} · ${prod.code}`,
        details: [cat.code, prod.code],
        severity: "none",
        module: "ProductSystem",
        itemType: "produs",
      });
    }
  }

  return results;
}

const searchIndex = buildSearchIndex();

// --- FILTER TYPES ---
interface SearchFilters {
  severity: Severity | "all";
  module: string;
  itemType: ItemType | "all";
}

const allModules = Array.from(new Set(searchIndex.map((r) => r.module))).sort();
const severityOptions: { id: Severity | "all"; label: string; color: string; icon: React.ReactNode }[] = [
  { id: "all", label: "Toate", color: "text-slate-400 border-slate-600 bg-slate-800/50", icon: null },
  { id: "critical", label: "Critical", color: "text-red-400 border-red-700/50 bg-red-900/20", icon: <XCircle className="w-3 h-3" /> },
  { id: "warning", label: "Warning", color: "text-amber-400 border-amber-700/50 bg-amber-900/20", icon: <AlertTriangle className="w-3 h-3" /> },
  { id: "info", label: "Info", color: "text-blue-400 border-blue-700/50 bg-blue-900/20", icon: <Info className="w-3 h-3" /> },
];
const typeOptions: { id: ItemType | "all"; label: string; icon: React.ReactNode }[] = [
  { id: "all", label: "Toate", icon: null },
  { id: "regulă", label: "Regulă", icon: <Shield className="w-3 h-3" /> },
  { id: "produs", label: "Produs", icon: <Package className="w-3 h-3" /> },
  { id: "agent", label: "Agent", icon: <Users className="w-3 h-3" /> },
  { id: "status", label: "Status", icon: <Activity className="w-3 h-3" /> },
  { id: "gate", label: "Gate", icon: <Lock className="w-3 h-3" /> },
  { id: "event", label: "Event", icon: <Zap className="w-3 h-3" /> },
];

function filterResults(query: string, filters: SearchFilters): Map<string, SearchResult[]> {
  const q = query.toLowerCase().trim();
  const grouped = new Map<string, SearchResult[]>();
  const hasTextQuery = q.length > 0;
  const hasActiveFilters = filters.severity !== "all" || filters.module !== "all" || filters.itemType !== "all";

  if (!hasTextQuery && !hasActiveFilters) return new Map();

  for (const item of searchIndex) {
    // Text filter
    if (hasTextQuery) {
      const searchable = [item.title, item.subtitle, ...item.details].join(" ").toLowerCase();
      if (!searchable.includes(q)) continue;
    }

    // Severity filter
    if (filters.severity !== "all" && item.severity !== filters.severity) continue;

    // Module filter
    if (filters.module !== "all" && item.module !== filters.module) continue;

    // Type filter
    if (filters.itemType !== "all" && item.itemType !== filters.itemType) continue;

    const existing = grouped.get(item.category) || [];
    existing.push(item);
    grouped.set(item.category, existing);
  }

  return grouped;
}

// --- FILTER CHIPS ---
function FilterChips({
  filters,
  onFilterChange,
}: {
  filters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
}) {
  return (
    <div className="space-y-2.5 bg-[#111827] border border-[#1E293B] rounded-lg p-3">
      {/* Severity row */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] text-slate-500 uppercase tracking-wide w-16 shrink-0">Severitate</span>
        {severityOptions.map((opt) => (
          <button
            key={opt.id}
            onClick={() => onFilterChange({ ...filters, severity: opt.id })}
            className={`flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all ${
              filters.severity === opt.id
                ? opt.id === "all"
                  ? "bg-blue-600/20 text-blue-400 border-blue-600/50"
                  : opt.color
                : "bg-transparent text-slate-500 border-[#2A3548] hover:border-slate-500"
            }`}
          >
            {opt.icon}
            {opt.label}
          </button>
        ))}
      </div>

      {/* Module row */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] text-slate-500 uppercase tracking-wide w-16 shrink-0">Modul</span>
        <button
          onClick={() => onFilterChange({ ...filters, module: "all" })}
          className={`px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all ${
            filters.module === "all"
              ? "bg-blue-600/20 text-blue-400 border-blue-600/50"
              : "bg-transparent text-slate-500 border-[#2A3548] hover:border-slate-500"
          }`}
        >
          Toate
        </button>
        {allModules.map((mod) => (
          <button
            key={mod}
            onClick={() => onFilterChange({ ...filters, module: filters.module === mod ? "all" : mod })}
            className={`px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all ${
              filters.module === mod
                ? "bg-cyan-600/20 text-cyan-400 border-cyan-600/50"
                : "bg-transparent text-slate-500 border-[#2A3548] hover:border-slate-500"
            }`}
          >
            {mod}
          </button>
        ))}
      </div>

      {/* Type row */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-[10px] text-slate-500 uppercase tracking-wide w-16 shrink-0">Tip</span>
        {typeOptions.map((opt) => (
          <button
            key={opt.id}
            onClick={() => onFilterChange({ ...filters, itemType: opt.id })}
            className={`flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-full border transition-all ${
              filters.itemType === opt.id
                ? "bg-purple-600/20 text-purple-400 border-purple-600/50"
                : "bg-transparent text-slate-500 border-[#2A3548] hover:border-slate-500"
            }`}
          >
            {opt.icon}
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

// --- EXPORT UTILITIES ---
type ExportColumnKey = "title" | "subtitle" | "category" | "severity" | "module" | "type" | "details";

interface ExportRow {
  title: string;
  subtitle: string;
  category: string;
  severity: string;
  module: string;
  type: string;
  details: string;
}

const allExportColumns: { key: ExportColumnKey; label: string }[] = [
  { key: "title", label: "Titlu" },
  { key: "subtitle", label: "Subtitlu" },
  { key: "category", label: "Categorie" },
  { key: "severity", label: "Severitate" },
  { key: "module", label: "Modul" },
  { key: "type", label: "Tip" },
  { key: "details", label: "Detalii" },
];

function flattenResults(results: Map<string, SearchResult[]>): ExportRow[] {
  const rows: ExportRow[] = [];
  for (const [, items] of results) {
    for (const item of items) {
      rows.push({
        title: item.title,
        subtitle: item.subtitle,
        category: item.category,
        severity: item.severity,
        module: item.module,
        type: item.itemType,
        details: item.details.join(" | "),
      });
    }
  }
  return rows;
}

function downloadCSV(rows: ExportRow[], columns: ExportColumnKey[]) {
  if (rows.length === 0 || columns.length === 0) return;
  const headers = columns.map((c) => allExportColumns.find((ac) => ac.key === c)?.label || c);
  const csvContent = [
    headers.join(","),
    ...rows.map((r) =>
      columns.map((c) => `"${(r[c] || "").replace(/"/g, '""')}"`).join(",")
    ),
  ].join("\n");

  const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `governance-export-${new Date().toISOString().slice(0, 10)}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function downloadJSON(rows: ExportRow[], columns: ExportColumnKey[]) {
  if (rows.length === 0 || columns.length === 0) return;
  const filtered = rows.map((r) => {
    const obj: Record<string, string> = {};
    for (const c of columns) obj[c] = r[c] || "";
    return obj;
  });
  const jsonContent = JSON.stringify(filtered, null, 2);
  const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `governance-export-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

// --- EXPORT PREVIEW MODAL ---
function ExportPreviewModal({
  rows,
  onClose,
}: {
  rows: ExportRow[];
  onClose: () => void;
}) {
  const [selectedColumns, setSelectedColumns] = useState<Set<ExportColumnKey>>(
    new Set(allExportColumns.map((c) => c.key))
  );

  const toggleColumn = (key: ExportColumnKey) => {
    setSelectedColumns((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size <= 1) return prev; // keep at least 1
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedColumns.size === allExportColumns.length) {
      setSelectedColumns(new Set(["title"]));
    } else {
      setSelectedColumns(new Set(allExportColumns.map((c) => c.key)));
    }
  };

  const activeColumns = allExportColumns.filter((c) => selectedColumns.has(c.key));
  const previewRows = rows.slice(0, 5);

  const handleExportCSV = () => {
    downloadCSV(rows, activeColumns.map((c) => c.key));
    onClose();
  };

  const handleExportJSON = () => {
    downloadJSON(rows, activeColumns.map((c) => c.key));
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-[#0D1321] border border-[#1E293B] rounded-xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[#1E293B]">
          <div className="flex items-center gap-3">
            <Download className="w-4.5 h-4.5 text-blue-400" />
            <div>
              <h2 className="text-[15px] font-bold text-slate-100">Preview Export</h2>
              <p className="text-[11px] text-slate-500">
                {rows.length} rânduri totale · {activeColumns.length}/{allExportColumns.length} coloane selectate
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 transition-colors text-slate-400 hover:text-slate-200"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Column Selector */}
        <div className="px-5 py-3 border-b border-[#1E293B] bg-[#111827]/50">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-[10px] text-slate-500 uppercase tracking-wide shrink-0">Coloane:</span>
            <button
              onClick={toggleAll}
              className={`px-2 py-0.5 text-[10px] font-medium rounded border transition-all ${
                selectedColumns.size === allExportColumns.length
                  ? "bg-blue-600/20 text-blue-400 border-blue-600/50"
                  : "bg-transparent text-slate-500 border-[#2A3548] hover:border-slate-500"
              }`}
            >
              {selectedColumns.size === allExportColumns.length ? "Deselectează toate" : "Selectează toate"}
            </button>
            <div className="w-px h-4 bg-[#2A3548]" />
            {allExportColumns.map((col) => (
              <button
                key={col.key}
                onClick={() => toggleColumn(col.key)}
                className={`flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded border transition-all ${
                  selectedColumns.has(col.key)
                    ? "bg-emerald-600/15 text-emerald-400 border-emerald-600/40"
                    : "bg-transparent text-slate-600 border-[#2A3548] hover:border-slate-500 line-through"
                }`}
              >
                <span className={`w-2.5 h-2.5 rounded-sm border flex items-center justify-center ${
                  selectedColumns.has(col.key)
                    ? "bg-emerald-500 border-emerald-500"
                    : "border-slate-600"
                }`}>
                  {selectedColumns.has(col.key) && (
                    <CheckCircle2 className="w-2 h-2 text-white" />
                  )}
                </span>
                {col.label}
              </button>
            ))}
          </div>
        </div>

        {/* Preview Table */}
        <div className="flex-1 overflow-auto px-5 py-4">
          <div className="flex items-center gap-2 mb-3">
            <Eye className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-[11px] text-slate-500">
              Previzualizare primele {Math.min(5, rows.length)} din {rows.length} rânduri
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-[#1E293B]">
            <table className="w-full text-left">
              <thead>
                <tr className="bg-[#111827]">
                  <th className="px-3 py-2 text-[10px] text-slate-500 font-semibold uppercase tracking-wide border-b border-[#1E293B] w-8">
                    #
                  </th>
                  {activeColumns.map((col) => (
                    <th
                      key={col.key}
                      className="px-3 py-2 text-[10px] text-slate-500 font-semibold uppercase tracking-wide border-b border-[#1E293B] whitespace-nowrap"
                    >
                      {col.label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewRows.map((row, idx) => (
                  <tr
                    key={idx}
                    className={`${idx % 2 === 0 ? "bg-[#0D1321]" : "bg-[#111827]/40"} hover:bg-[#1A2236] transition-colors`}
                  >
                    <td className="px-3 py-2 text-[11px] text-slate-600 font-mono border-b border-[#1E293B]/50">
                      {idx + 1}
                    </td>
                    {activeColumns.map((col) => (
                      <td
                        key={col.key}
                        className="px-3 py-2 text-[11px] text-slate-300 border-b border-[#1E293B]/50 max-w-[200px] truncate"
                        title={row[col.key]}
                      >
                        {col.key === "severity" && row[col.key] !== "none" ? (
                          <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                            row[col.key] === "critical" ? "bg-red-900/30 text-red-400" :
                            row[col.key] === "warning" ? "bg-amber-900/30 text-amber-400" :
                            "bg-blue-900/30 text-blue-400"
                          }`}>
                            {row[col.key]}
                          </span>
                        ) : (
                          row[col.key] || <span className="text-slate-600">—</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {rows.length > 5 && (
            <p className="text-[10px] text-slate-600 mt-2 text-center">
              ... și încă {rows.length - 5} rânduri care vor fi incluse în export
            </p>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between px-5 py-3.5 border-t border-[#1E293B] bg-[#111827]/50">
          <p className="text-[11px] text-slate-500">
            {rows.length} rânduri × {activeColumns.length} coloane
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 text-[12px] font-medium text-slate-400 hover:text-slate-200 rounded-lg border border-[#2A3548] hover:border-slate-500 transition-all"
            >
              Anulează
            </button>
            <button
              onClick={handleExportCSV}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-lg border border-emerald-700/50 bg-emerald-600/15 text-emerald-400 hover:bg-emerald-600/25 transition-all"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              Descarcă CSV
            </button>
            <button
              onClick={handleExportJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 text-[12px] font-medium rounded-lg border border-amber-700/50 bg-amber-600/15 text-amber-400 hover:bg-amber-600/25 transition-all"
            >
              <FileJson className="w-3.5 h-3.5" />
              Descarcă JSON
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- EXPORT BUTTON ---
function ExportButton({ results }: { results: Map<string, SearchResult[]> }) {
  const [showPreview, setShowPreview] = useState(false);
  const totalCount = Array.from(results.values()).reduce((sum, arr) => sum + arr.length, 0);
  const rows = useMemo(() => flattenResults(results), [results]);

  if (totalCount === 0) return null;

  return (
    <>
      <button
        onClick={() => setShowPreview(true)}
        className="flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-medium rounded-lg border border-[#2A3548] bg-[#111827] text-slate-300 hover:border-slate-500 hover:text-slate-100 transition-all"
      >
        <Download className="w-3.5 h-3.5" />
        Export
      </button>

      {showPreview && (
        <ExportPreviewModal rows={rows} onClose={() => setShowPreview(false)} />
      )}
    </>
  );
}

// --- SEARCH RESULTS VIEW ---
function SearchResultsView({
  query,
  results,
  onNavigate,
  activeFilterCount,
}: {
  query: string;
  results: Map<string, SearchResult[]>;
  onNavigate: (tab: Tab) => void;
  activeFilterCount: number;
}) {
  const totalCount = Array.from(results.values()).reduce((sum, arr) => sum + arr.length, 0);

  if (totalCount === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-slate-500">
        <Search className="w-8 h-8 mb-3 text-slate-600" />
        <p className="text-[14px] font-medium">
          {query ? `Niciun rezultat pentru "${query}"` : "Niciun rezultat cu filtrele selectate"}
        </p>
        <p className="text-[12px] text-slate-600 mt-1">
          {activeFilterCount > 0 ? "Încearcă să elimini unele filtre" : "Încearcă alt termen de căutare"}
        </p>
      </div>
    );
  }

  const severityBadge: Record<Severity, { cls: string; label: string }> = {
    critical: { cls: "bg-red-900/30 text-red-400 border-red-700/50", label: "Critical" },
    warning: { cls: "bg-amber-900/30 text-amber-400 border-amber-700/50", label: "Warning" },
    info: { cls: "bg-blue-900/30 text-blue-400 border-blue-700/50", label: "Info" },
    none: { cls: "bg-slate-800/50 text-slate-500 border-slate-700/50", label: "" },
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-[12px] text-slate-400">
          {totalCount} rezultat{totalCount !== 1 ? "e" : ""} în {results.size} categori{results.size !== 1 ? "i" : "e"}
        </span>
        {activeFilterCount > 0 && (
          <span className="text-[10px] text-purple-400 bg-purple-900/20 px-1.5 py-0.5 rounded border border-purple-700/30">
            {activeFilterCount} filtr{activeFilterCount !== 1 ? "e" : "u"} activ{activeFilterCount !== 1 ? "e" : ""}
          </span>
        )}
        <div className="ml-auto">
          <ExportButton results={results} />
        </div>
      </div>

      {Array.from(results.entries()).map(([category, items]) => (
        <div key={category} className="space-y-2">
          {/* Category header */}
          <div className="flex items-center gap-2 sticky top-0 bg-[#0A0F1C] py-1 z-10">
            <span className="text-slate-400">{items[0]?.categoryIcon}</span>
            <h3 className="text-[13px] font-semibold text-slate-200">{category}</h3>
            <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">
              {items.length}
            </span>
            <button
              onClick={() => onNavigate(items[0].tab)}
              className="ml-auto text-[10px] text-blue-400 hover:text-blue-300 transition-colors"
            >
              Deschide tab →
            </button>
          </div>

          {/* Results */}
          <div className="space-y-1.5">
            {items.slice(0, 10).map((item, idx) => (
              <button
                key={idx}
                onClick={() => onNavigate(item.tab)}
                className="w-full text-left bg-[#111827] border border-[#1E293B] rounded-lg p-3 hover:border-slate-500 transition-colors group"
              >
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-[13px] font-medium text-slate-200 group-hover:text-blue-300 transition-colors flex-1">
                    <HighlightText text={item.title} query={query} />
                  </p>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {item.severity !== "none" && (
                      <span className={`text-[9px] px-1.5 py-0.5 rounded border ${severityBadge[item.severity].cls}`}>
                        {severityBadge[item.severity].label}
                      </span>
                    )}
                    <span className="text-[9px] text-slate-600 bg-slate-800/50 px-1.5 py-0.5 rounded border border-slate-700/30">
                      {item.itemType}
                    </span>
                    <span className="text-[9px] text-cyan-500/70 bg-cyan-900/10 px-1.5 py-0.5 rounded border border-cyan-800/20">
                      {item.module}
                    </span>
                  </div>
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  <HighlightText text={item.subtitle} query={query} />
                </p>
                {/* Show first matching detail */}
                {query &&
                  item.details
                    .filter((d) => d.toLowerCase().includes(query.toLowerCase()))
                    .slice(0, 2)
                    .map((detail, di) => (
                      <p key={di} className="text-[11px] text-slate-400 mt-1 leading-relaxed line-clamp-2">
                        <HighlightText text={detail} query={query} />
                      </p>
                    ))}
              </button>
            ))}
            {items.length > 10 && (
              <p className="text-[11px] text-slate-500 pl-3">
                ... și încă {items.length - 10} rezultate
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

// --- BOUNDARY MAP TAB ---
function BoundaryMapView() {
  return (
    <div className="space-y-4" data-testid="governance-panel-boundaries">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY.boundaries} />
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <SectionHeader title="Harta limitelor — spine activ" icon={<Layers className="w-4 h-4 text-blue-400" />} />
        <p className="text-[11px] text-slate-500 mb-3" data-testid="governance-canonical-spine">
          Spine activ: {CANONICAL_SPINE_LABELS_RO.join(" → ")}
        </p>
        <div className="space-y-3">
          {PRESENT_BOUNDARIES.map((layer) => (
            <div
              key={layer.id}
              className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-4"
              data-testid={`boundary-${layer.id}`}
            >
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <h3 className="text-[14px] font-bold text-slate-100">{layer.nameRo}</h3>
                <span className="text-[10px] text-slate-500">{layer.technicalAlias}</span>
                <span
                  className={`ml-auto px-1.5 py-0.5 text-[9px] font-semibold rounded border ${governanceStatusBadgeClass(layer.status)}`}
                >
                  {layer.status}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mb-2">
                <span className="text-slate-500">Proprietar:</span> {layer.owner}
              </p>
              <p className="text-[12px] text-slate-300 mb-3">{layer.truthControlledRo}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
                <div>
                  <p className="text-[10px] text-emerald-400 uppercase tracking-wide mb-1">Permis</p>
                  <ul className="space-y-1">
                    {layer.allowedRo.map((item) => (
                      <li key={item} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                        <CheckCircle2 className="w-3 h-3 text-emerald-500 mt-0.5 shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <p className="text-[10px] text-red-400 uppercase tracking-wide mb-1">Interzis</p>
                  <ul className="space-y-1">
                    {layer.forbiddenRo.map((item) => (
                      <li key={item} className="text-[11px] text-slate-400 flex items-start gap-1.5">
                        <Ban className="w-3 h-3 text-red-500 mt-0.5 shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
              <dl className="grid grid-cols-1 md:grid-cols-3 gap-2 text-[10px] text-slate-500">
                <div>
                  <dt className="uppercase">Aplicare</dt>
                  <dd className="text-slate-300">{layer.enforcementRo}</dd>
                </div>
                <div>
                  <dt className="uppercase">Owner gate</dt>
                  <dd className="text-slate-300">{layer.ownerGateRo}</dd>
                </div>
                <div>
                  <dt className="uppercase">Verificare</dt>
                  <dd className="text-slate-300">{layer.verificationRo}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- AGENT AUTHORITY TAB ---
function AgentAuthorityView() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  return (
    <div className="space-y-4" data-testid="governance-panel-agents">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY.agents} />
      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
        {agents.map((agent) => (
          <button
            key={agent.id}
            onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
            className={`bg-[#111827] border rounded-lg p-4 text-left transition-all duration-200 hover:border-slate-500 ${
              selectedAgent === agent.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-[#1E293B]"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[18px]">{agent.icon}</span>
              <div>
                <p className={`text-[13px] font-bold ${agent.color}`}>{agent.shortName}</p>
                <p className="text-[10px] text-slate-500">{agent.name}</p>
              </div>
            </div>
            <p className="text-[11px] text-slate-300 leading-relaxed">{agent.role}</p>
            <div className="flex items-center gap-2 mt-3">
              <span className="text-[10px] text-emerald-400 bg-emerald-900/20 px-1.5 py-0.5 rounded">
                {agent.authority.length} autorități
              </span>
              <span className="text-[10px] text-red-400 bg-red-900/20 px-1.5 py-0.5 rounded">
                {agent.noAuthority.length} restricții
              </span>
              {agent.escalatesWhen.length > 0 && (
                <span className="text-[10px] text-amber-400 bg-amber-900/20 px-1.5 py-0.5 rounded">
                  {agent.escalatesWhen.length} escaladări
                </span>
              )}
            </div>
          </button>
        ))}
      </div>

      {/* Selected Agent Detail */}
      {selectedAgent && (() => {
        const agent = agents.find((a) => a.id === selectedAgent);
        if (!agent) return null;
        return (
          <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-5 animate-in fade-in duration-300">
            <div className="flex items-center gap-3 mb-3">
              <span className="text-[24px]">{agent.icon}</span>
              <div>
                <h3 className={`text-[16px] font-bold ${agent.color}`}>{agent.name}</h3>
                <p className="text-[12px] text-slate-400">{agent.role}</p>
              </div>
            </div>

            {/* Owner + Canonical Source (discrete) */}
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mb-4 pl-[36px]">
              <span className="text-[10px] text-slate-500">
                <span className="uppercase tracking-wide">Owner:</span>{" "}
                <span className="text-slate-300 font-medium">{agent.owner}</span>
              </span>
              <span className="text-[10px] text-slate-500">
                <span className="uppercase tracking-wide">Sursă:</span>{" "}
                <a
                  href={`/${agent.sourceOfTruth}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 font-mono underline decoration-dotted underline-offset-2"
                  title={agent.sourceOfTruth}
                >
                  {agent.sourceOfTruth.split("/").pop()}
                </a>
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-[10px] text-emerald-400 uppercase tracking-wide mb-2 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Are autoritate pe
                </p>
                <ul className="space-y-1.5">
                  {agent.authority.map((item, i) => (
                    <li key={i} className="text-[12px] text-slate-300 flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-[10px] text-red-400 uppercase tracking-wide mb-2 flex items-center gap-1">
                  <XCircle className="w-3 h-3" /> Nu are autoritate pe
                </p>
                <ul className="space-y-1.5">
                  {agent.noAuthority.map((item, i) => (
                    <li key={i} className="text-[12px] text-slate-400 flex items-start gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-red-500 mt-1.5 shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-[10px] text-amber-400 uppercase tracking-wide mb-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Escaladează la Nucleu când
                </p>
                {agent.escalatesWhen.length > 0 ? (
                  <ul className="space-y-1.5">
                    {agent.escalatesWhen.map((item, i) => (
                      <li key={i} className="text-[12px] text-slate-400 flex items-start gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                        {item}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-[12px] text-slate-500 italic">Nucleu este nivelul final de arbitraj.</p>
                )}
              </div>
            </div>
          </div>
        );
      })()}

      {/* Authority Rule */}
      <div className="bg-[#0D1321] border border-amber-800/30 rounded-lg p-4">
        <p className="text-[12px] text-amber-400 font-semibold mb-1">⚖️ Regula de autoritate</p>
        <p className="text-[12px] text-slate-300 leading-relaxed">
          Niciun agent nu are voie să își extindă teritoriul prin presupuneri. Nucleu arbitrează, Contracte păzesc handoff-urile,
          Costing/OC păzește adevărul economic, UI/UX traduce fără să schimbe, Implementare execută fără improvizații,
          QA verifică alinierea, Soluții Externe ajută doar dacă merită real.
        </p>
      </div>
    </div>
  );
}

// --- SOURCE OF TRUTH TAB ---
function TruthHierarchyView({
  docsResult,
}: {
  docsResult: DocumentationIndexFetchResult | null;
}) {
  return (
    <div className="space-y-4" data-testid="governance-panel-truth">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY.truth} />
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-5">
        <SectionHeader title="Ierarhia Surselor de Adevăr" icon={<Eye className="w-4 h-4 text-blue-400" />} />
        <p className="text-[11px] text-slate-500 mb-4">
          Când două surse se contrazic, sursa cu nivel mai mic câștigă. Runtime confirmă comportament — nu definește arhitectura.
          UI-ul nu devine sursă de adevăr.
        </p>

        <div className="space-y-2">
          {truthHierarchy.map((source) => (
            <div key={source.level} className="flex items-stretch gap-3 group">
              {/* Level indicator */}
              <div className="flex flex-col items-center w-12 shrink-0">
                <div className={`w-8 h-8 rounded-full ${source.color} flex items-center justify-center text-[12px] font-bold text-white`}>
                  {source.level}
                </div>
                {source.level < 8 && <div className="w-px flex-1 bg-slate-700 mt-1" />}
              </div>

              {/* Content */}
              <div className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3 flex-1 group-hover:border-slate-500 transition-colors">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-[13px] font-bold text-slate-200">{source.name}</p>
                  <span className="text-[10px] text-slate-500 bg-slate-800 px-1.5 py-0.5 rounded">{source.role}</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2">
                  <div>
                    <p className="text-[10px] text-emerald-400 mb-0.5">✓ Source of truth pentru</p>
                    <p className="text-[11px] text-slate-300">{source.truthFor}</p>
                  </div>
                  <div>
                    <p className="text-[10px] text-red-400 mb-0.5">✗ Nu este source of truth pentru</p>
                    <p className="text-[11px] text-slate-400">{source.notTruthFor}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Conflict Resolution */}
      <div className="bg-[#0D1321] border border-blue-800/30 rounded-lg p-4">
        <p className="text-[12px] text-blue-400 font-semibold mb-2">🔀 Regula de conflict</p>
        <p className="text-[12px] text-slate-300 leading-relaxed">
          Dacă UI din Figma spune ceva, dar .md spune altceva → .md câștigă. Dacă Atoms implementează ceva care contrazice Figma sau .md → Figma / .md câștigă.
          Dacă codul și runtime-ul contrazic .md → QA Alignment investighează, Nucleu arbitrează dacă e nevoie.
        </p>
      </div>

      <ImportantDocumentsSection docsResult={docsResult} />
    </div>
  );
}

// --- OWNER GATES TAB ---
function GateView() {
  return (
    <div className="space-y-4" data-testid="governance-panel-gates">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY.gates} />
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-5">
        <SectionHeader title="Owner gates — politică prezentă" icon={<Lock className="w-4 h-4 text-amber-400" />} />
        <p className="text-[11px] text-slate-500 mb-4">
          Gate-uri de aprobare owner. Statusul „Politică owner” înseamnă control de proces — nu motor RBAC în UI.
          Modelul istoric de readiness Blueprint nu mai este prezentat ca gate activ.
        </p>
        <div className="space-y-3">
          {PRESENT_GATES.map((gate) => (
            <div
              key={gate.id}
              className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-4"
              data-testid={`owner-gate-${gate.id}`}
            >
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <p className="text-[14px] font-bold text-slate-200">{gate.nameRo}</p>
                <span
                  className={`ml-auto px-1.5 py-0.5 text-[9px] font-semibold rounded border ${governanceStatusBadgeClass(gate.status)}`}
                >
                  {gate.status}
                </span>
              </div>
              <dl className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-slate-400">
                <div>
                  <dt className="text-[10px] text-slate-500 uppercase">Blochează</dt>
                  <dd className="text-slate-300">{gate.blocksRo}</dd>
                </div>
                <div>
                  <dt className="text-[10px] text-slate-500 uppercase">Aprobator</dt>
                  <dd className="text-slate-300">{gate.approverRo}</dd>
                </div>
                <div>
                  <dt className="text-[10px] text-slate-500 uppercase">Aplicare</dt>
                  <dd>{gate.enforcementRo}</dd>
                </div>
                <div>
                  <dt className="text-[10px] text-slate-500 uppercase">Verificare</dt>
                  <dd>{gate.verificationRo}</dd>
                </div>
                <div className="md:col-span-2">
                  <dt className="text-[10px] text-slate-500 uppercase">Fără aprobare</dt>
                  <dd className="text-amber-200/90">{gate.withoutApprovalRo}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- GUARDRAILS TAB ---
function GuardrailsView() {
  return (
    <div className="space-y-4" data-testid="governance-panel-guardrails">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY.guardrails} />
      <div className="space-y-2">
        {PRESENT_GUARDRAILS.map((g) => (
          <div
            key={g.id}
            className="bg-[#111827] border border-[#1E293B] border-l-2 border-l-amber-500 rounded-lg p-4"
            data-testid={`guardrail-${g.id}`}
          >
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <span className="text-[10px] font-mono text-slate-600">{g.id}</span>
              <p className="text-[13px] font-semibold text-slate-200">{g.titleRo}</p>
              <span
                className={`ml-auto px-1.5 py-0.5 text-[9px] font-semibold rounded border ${governanceStatusBadgeClass(g.status)}`}
              >
                {g.status}
              </span>
            </div>
            <p className="text-[12px] text-slate-300 mt-1 leading-relaxed">{g.requirementRo}</p>
            <dl className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-2 text-[10px] text-slate-500">
              <div>
                <dt className="uppercase">Aplicare</dt>
                <dd className="text-slate-400">{g.enforcementRo}</dd>
              </div>
              <div>
                <dt className="uppercase">Owner gate</dt>
                <dd className="text-slate-400">{g.ownerGateRo}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- UI TRUTH RULES TAB ---
function UITruthRulesView() {
  return (
    <div className="space-y-4" data-testid="governance-panel-ui-rules">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY["ui-rules"]} />
      {uiTruthRules.map((rule) => (
        <div key={rule.id} className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[10px] font-mono text-slate-600">{rule.id}</span>
            <span className="text-[10px] text-purple-400 bg-purple-900/20 px-1.5 py-0.5 rounded">{rule.area}</span>
          </div>
          <p className="text-[14px] font-semibold text-slate-200 mb-3">{rule.rule}</p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="bg-emerald-900/10 border border-emerald-800/30 rounded-lg p-3">
              <p className="text-[10px] text-emerald-400 uppercase tracking-wide mb-2">✓ Corect</p>
              <ul className="space-y-1">
                {rule.correctExamples.map((ex, i) => (
                  <li key={i} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                    <CheckCircle2 className="w-3 h-3 text-emerald-500 mt-0.5 shrink-0" />
                    {ex}
                  </li>
                ))}
              </ul>
            </div>
            <div className="bg-red-900/10 border border-red-800/30 rounded-lg p-3">
              <p className="text-[10px] text-red-400 uppercase tracking-wide mb-2">✗ Incorect</p>
              <ul className="space-y-1">
                {rule.incorrectExamples.map((ex, i) => (
                  <li key={i} className="text-[11px] text-slate-400 flex items-start gap-1.5">
                    <XCircle className="w-3 h-3 text-red-500 mt-0.5 shrink-0" />
                    {ex}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      ))}

      {/* Principle */}
      <div className="bg-[#0D1321] border border-purple-800/30 rounded-lg p-4">
        <p className="text-[12px] text-purple-400 font-semibold mb-1">🎯 Principiul de bază</p>
        <p className="text-[12px] text-slate-300 leading-relaxed">
          UI-ul reflectă adevărul sistemului. UI-ul nu inventează statusuri canonice, nu compensează boundary-uri neclare,
          nu ascunde probleme reale în spatele unei prezentări curate, nu simplifica fals logica doar ca să pară mai ușor de folosit.
        </p>
      </div>
    </div>
  );
}

// --- STATUS FLOWS TAB ---
function StatusFlowsView() {
  const [selectedModule, setSelectedModule] = useState<string | null>(null);

  return (
    <div className="space-y-4" data-testid="governance-panel-status-flows">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY["status-flows"]} />
      <p className="text-[11px] text-slate-500 px-1">
        Tipuri distincte: stare modul (aici) ≠ stare pagină (B3) ≠ stare runtime (health) ≠ stare document ≠ stare Figma.
        Conflicturile nu sunt migrate automat.
      </p>
      {/* Module selector */}
      <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-8 gap-2">
        {moduleStatusFlows.map((mod) => (
          <button
            key={mod.id}
            onClick={() => setSelectedModule(selectedModule === mod.id ? null : mod.id)}
            className={`bg-[#111827] border rounded-lg p-3 text-center transition-all hover:border-slate-500 ${
              selectedModule === mod.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-[#1E293B]"
            }`}
          >
            <p className={`text-[14px] font-bold ${mod.color}`}>{mod.shortName}</p>
            <p className="text-[10px] text-slate-500 mt-0.5">{mod.statuses.length} statusuri</p>
            <p className="text-[10px] text-slate-600">{mod.transitions.length} tranzitii</p>
          </button>
        ))}
      </div>

      {/* Selected module detail */}
      {selectedModule && (() => {
        const mod = moduleStatusFlows.find((m) => m.id === selectedModule);
        if (!mod) return null;

        const statusColors: Record<string, string> = {
          active: "bg-emerald-500", inactive: "bg-slate-500", deprecated: "bg-red-500",
          new: "bg-blue-500", in_review: "bg-cyan-500", needs_info: "bg-amber-500",
          ready_for_quote: "bg-emerald-500", blocked: "bg-red-500", cancelled: "bg-slate-600",
          unresolved: "bg-slate-500", resolving: "bg-blue-500", resolved: "bg-emerald-500",
          invalid_configuration: "bg-red-500", pending: "bg-slate-500", calculating: "bg-blue-500",
          calculated: "bg-emerald-500", failed: "bg-red-500", draft: "bg-slate-500",
          priced: "bg-cyan-500", sent: "bg-blue-500", viewed: "bg-purple-500",
          negotiating: "bg-amber-500", accepted: "bg-emerald-500", rejected: "bg-red-500",
          expired: "bg-slate-600", created: "bg-slate-500", confirmed: "bg-blue-500",
          locked: "bg-purple-500", in_execution: "bg-emerald-500", completed: "bg-emerald-600",
          scheduled: "bg-cyan-500", in_progress: "bg-emerald-500", partial_done: "bg-amber-500",
          done: "bg-emerald-600", assigned: "bg-blue-500",
        };

        return (
          <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-5 animate-in fade-in duration-300">
            <div className="flex items-center gap-3 mb-4">
              <h3 className={`text-[16px] font-bold ${mod.color}`}>{mod.name}</h3>
              <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded">Owner: {mod.owner}</span>
            </div>

            {/* Status pills */}
            <div className="mb-4">
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-2">Statusuri canonice</p>
              <div className="flex flex-wrap gap-2">
                {mod.statuses.map((s) => (
                  <span key={s} className="flex items-center gap-1.5 px-2.5 py-1 bg-[#1A2236] border border-[#2A3548] rounded-md">
                    <span className={`w-2 h-2 rounded-full ${statusColors[s] || "bg-slate-500"}`} />
                    <span className="text-[12px] text-slate-200 font-mono">{s}</span>
                  </span>
                ))}
              </div>
            </div>

            {/* Transitions */}
            <div>
              <p className="text-[10px] text-slate-500 uppercase tracking-wide mb-2">Tranzitii</p>
              <div className="space-y-1.5">
                {mod.transitions.map((t, idx) => (
                  <div key={idx} className="flex items-center gap-2 py-1.5 px-3 bg-[#1A2236] border border-[#2A3548] rounded">
                    <span className="flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${t.from === "*" || t.from === "sent/priced" ? "bg-slate-400" : statusColors[t.from] || "bg-slate-500"}`} />
                      <span className="text-[12px] text-slate-300 font-mono w-28">{t.from}</span>
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
                    <span className="flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${statusColors[t.to] || "bg-slate-500"}`} />
                      <span className="text-[12px] text-slate-300 font-mono w-28">{t.to}</span>
                    </span>
                    <span className="text-[11px] text-slate-500 ml-auto italic">{t.trigger}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      })()}

      {/* System Events */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <SectionHeader title="Evenimente Cross-Module" count={systemEvents.length} icon={<Zap className="w-4 h-4 text-amber-400" />} />
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
          {systemEvents.map((evt) => (
            <div key={evt.event} className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
              <p className="text-[12px] font-mono font-bold text-emerald-400">{evt.event}</p>
              <p className="text-[10px] text-slate-500 mt-0.5">Source: {evt.source}</p>
              <p className="text-[11px] text-slate-400 mt-1">{evt.description}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Invalid Patterns */}
      <div className="bg-[#0D1321] border border-red-800/30 rounded-lg p-4">
        <p className="text-[12px] text-red-400 font-semibold mb-2">🚫 Pattern-uri invalide</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {invalidPatterns.map((p, i) => (
            <span key={i} className="flex items-center gap-2 text-[12px] text-slate-400">
              <XCircle className="w-3.5 h-3.5 text-red-500 shrink-0" />
              {p}
            </span>
          ))}
        </div>
      </div>

      {/* Golden Rules */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <SectionHeader title="Reguli Critice Status" icon={<Shield className="w-4 h-4 text-amber-400" />} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            "Niciun modul NU schimba statusul altui modul",
            "Statusurile NU transporta business logic intre module",
            "Status ≠ UI state",
            "Fiecare tranzitie trebuie sa fie logata (audit)",
          ].map((rule, i) => (
            <div key={i} className="flex items-start gap-2 bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
              <span className="text-amber-400 mt-0.5 shrink-0 text-[12px] font-bold">{i + 1}.</span>
              <p className="text-[12px] text-slate-300">{rule}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- PRODUCT CATALOG TAB ---
function ProductCatalogView() {
  const [expandedCat, setExpandedCat] = useState<string | null>(null);
  const totalProducts = productCatalog.reduce((sum, cat) => sum + cat.products.length, 0);

  return (
    <div className="space-y-4" data-testid="governance-panel-products">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY.products} />
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-5">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <SectionHeader title="Nomenclator local (referință)" icon={<Package className="w-4 h-4 text-blue-400" />} />
          <div className="flex items-center gap-3">
            <span className="text-[10px] px-1.5 py-0.5 rounded border border-slate-600 text-slate-400">
              REFERINȚĂ
            </span>
            <span className="text-[11px] text-slate-400">
              {productCatalog.length} categorii / {totalProducts} rânduri (static)
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          {productCatalog.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setExpandedCat(expandedCat === cat.id ? null : cat.id)}
              className={`bg-[#1A2236] border rounded-lg p-4 text-left transition-all hover:border-slate-500 ${
                expandedCat === cat.id ? "border-blue-500/50 ring-1 ring-blue-500/30" : "border-[#2A3548]"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold text-blue-400 bg-blue-900/20 px-1.5 py-0.5 rounded">
                  {cat.code}
                </span>
                <span className="text-[10px] text-slate-500">{cat.products.length} produse</span>
              </div>
              <p className="text-[13px] font-semibold text-slate-200">{cat.name}</p>
              {expandedCat === cat.id && (
                <div className="mt-3 space-y-1.5 animate-in fade-in duration-200">
                  {cat.products.map((prod) => (
                    <div key={prod.code} className="flex items-center justify-between py-1 border-t border-[#2A3548]/50">
                      <span className="text-[11px] text-slate-300">{prod.name}</span>
                      <span className="text-[10px] font-mono text-slate-500">{prod.code}</span>
                    </div>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Product System Rules */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-lg p-4">
        <SectionHeader title="Regula ProductSystem" icon={<Shield className="w-4 h-4 text-pink-400" />} />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="bg-emerald-900/10 border border-emerald-800/30 rounded-lg p-3">
            <p className="text-[10px] text-emerald-400 uppercase tracking-wide mb-2">✓ ProductSystem defineste</p>
            <ul className="space-y-1">
              {["Tipul produsului", "Structura logica (componente)", "RequiredMaterialSpec", "Reguli de configurare"].map((item, i) => (
                <li key={i} className="text-[12px] text-slate-300 flex items-start gap-1.5">
                  <CheckCircle2 className="w-3 h-3 text-emerald-500 mt-0.5 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="bg-red-900/10 border border-red-800/30 rounded-lg p-3">
            <p className="text-[10px] text-red-400 uppercase tracking-wide mb-2">✗ ProductSystem NU defineste</p>
            <ul className="space-y-1">
              {["Preturi", "Cantitati / consum", "Calcule de cost", "Furnizori"].map((item, i) => (
                <li key={i} className="text-[12px] text-slate-400 flex items-start gap-1.5">
                  <XCircle className="w-3 h-3 text-red-500 mt-0.5 shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Code Structure */}
      <div className="bg-[#0D1321] border border-blue-800/30 rounded-lg p-4">
        <p className="text-[12px] text-blue-400 font-semibold mb-2">📋 Structura Cod Produs</p>
        <p className="text-[12px] text-slate-300 mb-2">Format: <span className="font-mono text-blue-300">[CATEGORIE]-[TIP]-[VARIANTA]</span></p>
        <div className="flex flex-wrap gap-2">
          {["CL-SIMPLU-STD", "LV-FRONTAL-LED", "TOTEM-ILUMINAT-STD", "PRINT-AUTO-LAMINAT", "CNC-PVC-DEBITARE"].map((code) => (
            <span key={code} className="text-[11px] font-mono text-slate-300 bg-[#111827] border border-[#1E293B] px-2 py-1 rounded">
              {code}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

// --- HONESTY BASELINE (W0-B5) ---
function OwnershipHonestyView({
  docsResult,
}: {
  docsResult: DocumentationIndexFetchResult | null;
}) {
  const openQuestions = [
    {
      label: "OWNER REVIEW REQUIRED",
      detail: "Termeni și ownership încă parțiale pe limite resursă (Utilaje / Angajați / Pontaj).",
    },
    {
      label: "NOT VALIDATED",
      detail: "Unele reguli din tab-urile legacy rămân referință locală — nu sunt revalidate prin index B2.",
    },
    {
      label: "STALE",
      detail: "Numărul vechi de documente „canonice” din UI a fost eliminat — nu era dovedit de indexul B2.",
    },
  ];

  return (
    <div className="space-y-4" data-testid="governance-ownership-baseline">
      <TabHonestyBanner meta={GOVERNANCE_TAB_HONESTY.ownership} />
      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="governance-ownership">
        <SectionHeader title="Cine deține adevărul" icon={<Eye className="w-4 h-4 text-amber-400" />} />
        <p className="text-[11px] text-slate-500 mb-3">
          Matrice mică, doar domenii cu sursă. Nu inventăm ownership.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead>
              <tr className="text-[10px] uppercase tracking-wide text-slate-500 border-b border-[#1E293B]">
                <th className="py-2 pr-3 font-medium">Domeniu</th>
                <th className="py-2 pr-3 font-medium">Proprietar</th>
                <th className="py-2 pr-3 font-medium">Semantică</th>
                <th className="py-2 pr-3 font-medium">Scriere</th>
                <th className="py-2 pr-3 font-medium">Citire</th>
                <th className="py-2 pr-3 font-medium">Aplicare</th>
                <th className="py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {PRESENT_OWNERSHIP_ROWS.map((row) => (
                <tr key={row.systemId} className="border-b border-[#1E293B]/60 align-top" data-testid={`ownership-${row.systemId}`}>
                  <td className="py-2 pr-3">
                    <p className="text-slate-200 font-medium">{row.domainRo}</p>
                    <p className="text-[10px] text-slate-500">{row.technicalAlias}</p>
                  </td>
                  <td className="py-2 pr-3 text-slate-300">{row.owner}</td>
                  <td className="py-2 pr-3 text-slate-400 text-[11px]">{row.semanticOwnershipRo}</td>
                  <td className="py-2 pr-3 text-slate-400 text-[11px]">{row.writeAuthorityRo}</td>
                  <td className="py-2 pr-3 text-slate-400 text-[11px]">{row.readOnlyRo}</td>
                  <td className="py-2 pr-3 text-slate-400 text-[11px]">{row.enforcementRo}</td>
                  <td className="py-2">
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded border ${presentStatusBadgeClass(row.status)}`}
                    >
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="governance-settings-ownership">
        <SectionHeader title="Clasificare setări (Litere / Logo / ACM)" icon={<Layers className="w-4 h-4 text-cyan-400" />} />
        <p className="text-[11px] text-slate-500 mb-3">
          Vizibilitate ownership — fără mutare setări în acest build. Conflictele rămân explicite.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12px]">
            <thead>
              <tr className="text-[10px] uppercase tracking-wide text-slate-500 border-b border-[#1E293B]">
                <th className="py-2 pr-3 font-medium">Setare</th>
                <th className="py-2 pr-3 font-medium">Categorie</th>
                <th className="py-2 pr-3 font-medium">Owner actual</th>
                <th className="py-2 pr-3 font-medium">Sursă runtime</th>
                <th className="py-2 pr-3 font-medium">Consumer</th>
                <th className="py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {SETTINGS_OWNERSHIP_ROWS.map((row) => (
                <tr
                  key={row.setting}
                  className="border-b border-[#1E293B]/60 align-top"
                  data-testid={`settings-ownership-${row.setting}`}
                >
                  <td className="py-2 pr-3 text-slate-200 font-medium">{row.setting}</td>
                  <td className="py-2 pr-3 text-slate-400">{row.category}</td>
                  <td className="py-2 pr-3 text-slate-300 text-[11px]">{row.currentOwnerRo}</td>
                  <td className="py-2 pr-3 text-slate-400 text-[11px]">{row.runtimeSourceRo}</td>
                  <td className="py-2 pr-3 text-slate-400 text-[11px]">{row.consumerRo}</td>
                  <td className="py-2 text-amber-300/90 text-[11px]">{row.statusRo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="governance-rules">
        <SectionHeader title="Reguli de separare" icon={<Ban className="w-4 h-4 text-red-400" />} />
        <div className="space-y-2 mt-2">
          {HONESTY_SEPARATION_RULES.map((rule) => (
            <div key={rule.ruleRo} className="bg-[#1A2236] border border-[#2A3548] rounded-lg p-3">
              <p className="text-[13px] text-slate-200 mb-1">{rule.ruleRo}</p>
              <div className="flex flex-wrap gap-2 text-[10px]">
                <span className="px-1.5 py-0.5 rounded border border-slate-600 text-slate-400">
                  Status: {rule.status}
                </span>
                <span className="px-1.5 py-0.5 rounded border border-slate-600 text-slate-400 flex items-center gap-1">
                  <BookOpen className="w-3 h-3" />
                  {rule.source}
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="governance-owner-gates">
        <SectionHeader title="Owner gates (rezumat)" icon={<Lock className="w-4 h-4 text-amber-400" />} />
        <p className="text-[11px] text-slate-500 mb-2">
          Listă read-only — detalii complete în tab-ul Owner gates. Nu este motor de aprobare.
        </p>
        <ul className="space-y-1.5">
          {PRESENT_GATES.map((gate) => (
            <li
              key={gate.id}
              className="flex items-start gap-2 text-[12px] text-slate-300 bg-[#1A2236] border border-[#2A3548] rounded-md px-3 py-2"
            >
              <Lock className="w-3.5 h-3.5 text-amber-400 mt-0.5 shrink-0" />
              <span>
                {gate.nameRo}
                <span className="text-slate-500"> — {gate.status}</span>
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="governance-doc-authority">
        <SectionHeader title="Autoritate documente (index)" icon={<BookOpen className="w-4 h-4 text-blue-400" />} />
        {docsResult === null && (
          <p className="text-[12px] text-slate-400">Se încarcă indexul de documentație...</p>
        )}
        {docsResult?.state === "forbidden" && (
          <p className="text-[12px] text-amber-300" data-testid="governance-docs-forbidden">
            Indexul B2 necesită permisiunea <code className="text-amber-200">system.documentation_read</code>{" "}
            (admin). Etichetele de onestitate de mai sus rămân vizibile; detalii tehnice index = restricționate.
          </p>
        )}
        {docsResult?.state === "unavailable" && (
          <p className="text-[12px] text-red-300" data-testid="governance-docs-unavailable">
            Index documentație indisponibil: {docsResult.message}. Nu afișăm un număr canonic inventat.
          </p>
        )}
        {docsResult?.state === "empty" && (
          <p className="text-[12px] text-slate-400">Index gol — fără documente listate.</p>
        )}
        {docsResult?.state === "ok" && (
          <div data-testid="governance-docs-ok">
            <p className="text-[11px] text-slate-500 mb-2">
              {docsResult.data.count} documente indexate (count din API — nu un badge „canonical” inventat).
              Versiune: {docsResult.data.index_version}
            </p>
            <div className="space-y-1.5 max-h-64 overflow-y-auto">
              {docsResult.data.items.slice(0, 12).map((doc) => (
                <div
                  key={doc.document_id}
                  className="flex flex-wrap items-center gap-2 bg-[#1A2236] border border-[#2A3548] rounded-md px-3 py-2 text-[11px]"
                >
                  <span className="text-slate-200 font-medium">{doc.title || doc.document_id}</span>
                  <span className="px-1.5 py-0.5 rounded border border-slate-600 text-slate-400">
                    {doc.authority}
                  </span>
                  <span className="px-1.5 py-0.5 rounded border border-amber-800/40 text-amber-300/90">
                    {doc.status}
                  </span>
                  {doc.drift_status && doc.drift_status !== "ALIGNED" && (
                    <span className="px-1.5 py-0.5 rounded border border-amber-800/40 text-amber-300">
                      {doc.drift_status}
                    </span>
                  )}
                  <span className="text-slate-500 ml-auto font-mono text-[10px]">{doc.technical_id}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="bg-[#111827] border border-[#1E293B] rounded-lg p-4" data-testid="governance-open-questions">
        <SectionHeader title="Întrebări deschise / review" icon={<AlertTriangle className="w-4 h-4 text-amber-400" />} />
        <div className="space-y-2 mt-2">
          {openQuestions.map((q) => (
            <div key={q.label} className="bg-amber-900/10 border border-amber-800/30 rounded-lg p-3">
              <p className="text-[11px] font-semibold text-amber-300 mb-0.5">{q.label}</p>
              <p className="text-[12px] text-slate-300">{q.detail}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

// --- MAIN PAGE ---
const defaultFilters: SearchFilters = { severity: "all", module: "all", itemType: "all" };

export default function Governance() {
  const [activeTab, setActiveTab] = useState<Tab>("ownership");
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilters>(defaultFilters);
  const [showFilters, setShowFilters] = useState(false);
  const [docsResult, setDocsResult] = useState<DocumentationIndexFetchResult | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchDocumentationIndex().then((result) => {
      if (!cancelled) setDocsResult(result);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const activeFilterCount = (filters.severity !== "all" ? 1 : 0) + (filters.module !== "all" ? 1 : 0) + (filters.itemType !== "all" ? 1 : 0);
  const searchResults = useMemo(() => filterResults(searchQuery, filters), [searchQuery, filters]);
  const isSearching = searchQuery.trim().length > 0 || activeFilterCount > 0;

  const handleNavigate = useCallback((tab: Tab) => {
    setActiveTab(tab);
    setSearchQuery("");
    setFilters(defaultFilters);
    setShowFilters(false);
  }, []);

  const handleClearAll = useCallback(() => {
    setSearchQuery("");
    setFilters(defaultFilters);
    setShowFilters(false);
  }, []);

  const renderTab = () => {
    switch (activeTab) {
      case "ownership":
        return <OwnershipHonestyView docsResult={docsResult} />;
      case "boundaries":
        return <BoundaryMapView />;
      case "status-flows":
        return <StatusFlowsView />;
      case "agents":
        return <AgentAuthorityView />;
      case "truth":
        return <TruthHierarchyView docsResult={docsResult} />;
      case "gates":
        return <GateView />;
      case "guardrails":
        return <GuardrailsView />;
      case "products":
        return <ProductCatalogView />;
      case "ui-rules":
        return <UITruthRulesView />;
    }
  };

  return (
    <div className="space-y-4" data-testid="governance-page">
      {/* Header + Search */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 shrink-0 flex-wrap">
          <Shield className="w-5 h-5 text-amber-400" />
          <h1 className="text-[18px] font-bold text-slate-100">Guvernanța sistemului</h1>
          <span className="text-[11px] text-slate-500" data-testid="governance-alias">
            System Governance
          </span>
          <span className="text-[10px] text-slate-500 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 ml-1">
            read-only
          </span>
        </div>

        {/* Search Bar */}
        <div className="relative flex-1 max-w-md">
          <div className="flex items-center gap-2 bg-[#111827] border border-[#1E293B] rounded-lg px-3 py-2 focus-within:border-blue-500/50 focus-within:ring-1 focus-within:ring-blue-500/30 transition-all">
            <Search className="w-4 h-4 text-slate-500 shrink-0" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Caută reguli, agenți, produse, statusuri..."
              className="bg-transparent text-[13px] text-slate-200 placeholder:text-slate-600 outline-none w-full"
            />
            {/* Filter toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`p-1 rounded transition-colors shrink-0 ${
                showFilters || activeFilterCount > 0
                  ? "bg-purple-600/20 text-purple-400"
                  : "text-slate-500 hover:text-slate-300 hover:bg-slate-700"
              }`}
              title="Filtre avansate"
            >
              <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M1.5 3h13M3.5 7h9M5.5 11h5" strokeLinecap="round" />
              </svg>
              {activeFilterCount > 0 && (
                <span className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-purple-500 text-white text-[8px] font-bold rounded-full flex items-center justify-center">
                  {activeFilterCount}
                </span>
              )}
            </button>
            {isSearching && (
              <button
                onClick={handleClearAll}
                className="p-0.5 rounded hover:bg-slate-700 transition-colors shrink-0"
                title="Șterge tot"
              >
                <X className="w-3.5 h-3.5 text-slate-400" />
              </button>
            )}
          </div>
          {isSearching && (
            <div className="absolute right-0 top-full mt-1">
              <span className="text-[10px] text-slate-500">
                {Array.from(searchResults.values()).reduce((s, a) => s + a.length, 0)} rezultate
              </span>
            </div>
          )}
        </div>
      </div>

      <div
        className="flex items-start gap-2 px-3 py-2.5 bg-amber-900/15 border border-amber-800/40 rounded-lg"
        data-testid="governance-honesty-banner"
      >
        <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
        <p className="text-[12px] text-amber-200/95 leading-relaxed">
          Această pagină afișează reguli și responsabilități din surse controlate. Nu permite modificarea politicilor
          și nu înlocuiește documentele aprobate.
        </p>
      </div>

      {/* Advanced Filter Chips */}
      {showFilters && (
        <FilterChips filters={filters} onFilterChange={setFilters} />
      )}

      {/* Active filter summary chips */}
      {!showFilters && activeFilterCount > 0 && (
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[10px] text-slate-500">Filtre active:</span>
          {filters.severity !== "all" && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] rounded-full border bg-red-900/20 text-red-400 border-red-700/30">
              Severitate: {filters.severity}
              <button onClick={() => setFilters({ ...filters, severity: "all" })} className="ml-0.5 hover:text-red-300">
                <X className="w-2.5 h-2.5" />
              </button>
            </span>
          )}
          {filters.module !== "all" && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] rounded-full border bg-cyan-900/20 text-cyan-400 border-cyan-700/30">
              Modul: {filters.module}
              <button onClick={() => setFilters({ ...filters, module: "all" })} className="ml-0.5 hover:text-cyan-300">
                <X className="w-2.5 h-2.5" />
              </button>
            </span>
          )}
          {filters.itemType !== "all" && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] rounded-full border bg-purple-900/20 text-purple-400 border-purple-700/30">
              Tip: {filters.itemType}
              <button onClick={() => setFilters({ ...filters, itemType: "all" })} className="ml-0.5 hover:text-purple-300">
                <X className="w-2.5 h-2.5" />
              </button>
            </span>
          )}
          <button
            onClick={() => setFilters(defaultFilters)}
            className="text-[10px] text-slate-500 hover:text-slate-300 transition-colors"
          >
            Șterge toate
          </button>
        </div>
      )}

      {/* Tab Bar — hidden during search */}
      {!isSearching && (
        <div className="flex items-center gap-1 bg-[#111827] border border-[#1E293B] rounded-lg p-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.id}
              data-testid={`governance-tab-${tab.id}`}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-1.5 px-3 py-2 text-[12px] font-medium rounded-md transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? "bg-blue-600/20 text-blue-400 border border-blue-600/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent"
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Content: Search Results or Tab Content */}
      {isSearching ? (
        <SearchResultsView
          query={searchQuery}
          results={searchResults}
          onNavigate={handleNavigate}
          activeFilterCount={activeFilterCount}
        />
      ) : (
        renderTab()
      )}
    </div>
  );
}