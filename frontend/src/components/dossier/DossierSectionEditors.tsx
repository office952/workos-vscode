/**
 * Phase 2 — Structured Section Editors for Blueprint Dossier
 *
 * Implements hybrid structured editors + advanced JSON mode for 8 priority sections:
 * 1. variants_json
 * 2. task_rules_json
 * 3. time_assumptions_json
 * 4. costengine_mapping_json
 * 5. qc_checkpoints_json
 * 6. risks_json
 * 7. production_notes_json
 * 8. completion_state_json
 *
 * Each editor:
 * - Displays structured editor as primary mode
 * - Preserves advanced JSON mode
 * - Synchronizes structured editor <-> JSON
 * - Handles invalid JSON safely (blocks save, shows error)
 * - Backend remains final authority
 * - Save sends valid payload to existing API
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import {
  Plus,
  Trash2,
  AlertTriangle,
  Copy,
  RotateCcw,
  Info,
  Code,
  List,
  ChevronDown,
  ChevronUp,
  Lightbulb,
} from "lucide-react";
import type { SectionCompletionState } from "@/api/blueprintDossier";
import { SECTION_STATE_CONFIG } from "@/api/blueprintDossier";

// ============================================================
// TYPES
// ============================================================

interface StructuredEditorProps {
  value: string | null;
  onChange: (val: string | null) => void;
  readOnly: boolean;
}

// ============================================================
// SHARED: Editor Shell with Tabs (Structured / Advanced JSON)
// ============================================================

type EditorTab = "structured" | "json";

interface EditorShellProps {
  sectionKey: string;
  label: string;
  emoji: string;
  color: string;
  description: string;
  priority: boolean;
  safetyLabel?: string;
  value: string | null;
  onChange: (val: string | null) => void;
  completionState: SectionCompletionState;
  onCompletionChange: (state: SectionCompletionState) => void;
  readOnly: boolean;
  deferred: boolean;
  dirty: boolean;
  backendError: string | null;
  children: (props: { parsedData: unknown; setParsedData: (data: unknown) => void }) => React.ReactNode;
}

function safeParseForEditor(value: string | null): { valid: boolean; data: unknown } {
  if (!value || !value.trim()) return { valid: true, data: null };
  try {
    return { valid: true, data: JSON.parse(value) };
  } catch {
    return { valid: false, data: null };
  }
}

export function DossierSectionEditorShell({
  sectionKey,
  label,
  emoji,
  color,
  description,
  priority,
  safetyLabel,
  value,
  onChange,
  completionState,
  onCompletionChange,
  readOnly,
  deferred,
  dirty,
  backendError,
  children,
}: EditorShellProps) {
  const [activeTab, setActiveTab] = useState<EditorTab>("structured");
  const [jsonText, setJsonText] = useState(value ?? "");
  const [jsonError, setJsonError] = useState<string | null>(null);
  const [showExample, setShowExample] = useState(false);

  // Sync from external value
  useEffect(() => {
    setJsonText(value ?? "");
    if (value && value.trim()) {
      try { JSON.parse(value); setJsonError(null); } catch (e: unknown) {
        setJsonError(e instanceof Error ? e.message : "JSON invalid");
      }
    } else {
      setJsonError(null);
    }
  }, [value]);

  const { valid: isJsonValid, data: parsedData } = useMemo(() => safeParseForEditor(value), [value]);

  const setParsedData = useCallback((data: unknown) => {
    if (data === null || data === undefined) {
      onChange(null);
    } else {
      const json = JSON.stringify(data, null, 2);
      onChange(json);
    }
  }, [onChange]);

  // JSON tab handlers
  const handleJsonChange = (text: string) => {
    setJsonText(text);
    if (!text.trim()) {
      setJsonError(null);
      onChange(null);
      return;
    }
    try {
      JSON.parse(text);
      setJsonError(null);
      onChange(text);
    } catch (e: unknown) {
      setJsonError(e instanceof Error ? e.message : "JSON invalid");
    }
  };

  const formatJson = () => {
    if (!jsonText.trim()) return;
    try {
      const parsed = JSON.parse(jsonText);
      const formatted = JSON.stringify(parsed, null, 2);
      setJsonText(formatted);
      onChange(formatted);
      setJsonError(null);
    } catch (e: unknown) {
      setJsonError(e instanceof Error ? e.message : "JSON invalid");
    }
  };

  const resetToSaved = () => {
    setJsonText(value ?? "");
    if (value && value.trim()) {
      try { JSON.parse(value); setJsonError(null); } catch (e: unknown) {
        setJsonError(e instanceof Error ? e.message : "JSON invalid");
      }
    } else {
      setJsonError(null);
    }
  };

  const copyJson = () => {
    if (jsonText) navigator.clipboard?.writeText(jsonText);
  };

  const allStates: SectionCompletionState[] = ["not_started", "draft", "needs_review", "complete", "blocked", "deprecated"];
  const stateConfig = SECTION_STATE_CONFIG[completionState] || SECTION_STATE_CONFIG.not_started;

  // Deferred
  if (deferred) {
    return (
      <div className="rounded-xl border border-[#1E293B] bg-[#111827] opacity-50 cursor-not-allowed" id={`section-${sectionKey}`}>
        <div className="px-4 py-3 flex items-center gap-3">
          <span className="text-lg shrink-0">{emoji}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={`text-[12px] font-bold ${color}`}>{label}</span>
              <span className="px-1.5 py-0.5 text-[8px] font-bold bg-slate-700/50 text-slate-500 border border-slate-600/40 rounded">AMÂNAT</span>
            </div>
            <p className="text-[10px] text-slate-600 mt-0.5">
              Amânat — nu este activ în faza curentă. Nu există runtime de generare.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[#1E293B] bg-[#0D1321] overflow-hidden" id={`section-${sectionKey}`}>
      {/* Header */}
      <div className="px-4 py-3 flex items-center gap-3 border-b border-[#1E293B]">
        <span className="text-lg shrink-0">{emoji}</span>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`text-[12px] font-bold ${color}`}>{label}</span>
            {priority && (
              <span className="px-1.5 py-0.5 text-[8px] font-bold bg-amber-900/30 text-amber-400 border border-amber-700/40 rounded">PRIORITAR</span>
            )}
            {readOnly && (
              <span className="px-1.5 py-0.5 text-[8px] font-bold bg-slate-700/50 text-slate-500 border border-slate-600/40 rounded">DOAR CITIRE</span>
            )}
            {dirty && !readOnly && (
              <span className="px-1.5 py-0.5 text-[8px] font-bold bg-amber-900/30 text-amber-400 border border-amber-700/40 rounded">MODIFICAT</span>
            )}
          </div>
          <p className="text-[10px] text-slate-500 mt-0.5 truncate">{description}</p>
        </div>
        {/* Completion state */}
        <span className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[9px] font-bold ${stateConfig.color}`}>
          {stateConfig.emoji} {stateConfig.label}
        </span>
      </div>

      {/* Safety label */}
      {safetyLabel && (
        <div className="px-4 py-1.5 bg-slate-800/30 border-b border-[#1E293B]">
          <span className="text-[9px] text-slate-500 italic">{safetyLabel}</span>
        </div>
      )}

      {/* Tabs */}
      <div className="px-4 pt-3 flex items-center gap-1 border-b border-[#1E293B] pb-0">
        <button
          onClick={() => setActiveTab("structured")}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-[10px] font-bold transition-all border-b-2 ${
            activeTab === "structured"
              ? "bg-purple-500/10 text-purple-300 border-purple-500"
              : "text-slate-500 border-transparent hover:text-slate-300 hover:bg-slate-800/30"
          }`}
        >
          <List className="w-3 h-3" /> Editor Structurat
        </button>
        <button
          onClick={() => setActiveTab("json")}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-t-lg text-[10px] font-bold transition-all border-b-2 ${
            activeTab === "json"
              ? "bg-blue-500/10 text-blue-300 border-blue-500"
              : "text-slate-500 border-transparent hover:text-slate-300 hover:bg-slate-800/30"
          }`}
        >
          <Code className="w-3 h-3" /> JSON avansat
        </button>
        <div className="flex-1" />
        {/* Completion state selector */}
        <div className="flex items-center gap-1 pb-1">
          {allStates.map((s) => {
            const cfg = SECTION_STATE_CONFIG[s];
            const isActive = completionState === s;
            return (
              <button
                key={s}
                onClick={() => !readOnly && onCompletionChange(s)}
                disabled={readOnly}
                title={cfg.label}
                className={`px-1.5 py-1 rounded text-[8px] font-bold transition-all border disabled:opacity-50 disabled:cursor-not-allowed ${
                  isActive
                    ? `${cfg.color} bg-white/5 border-current`
                    : "text-slate-600 border-transparent hover:text-slate-400"
                }`}
              >
                {cfg.emoji}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 pb-4 pt-3">
        {activeTab === "structured" ? (
          <div className="space-y-3">
            {!isJsonValid && (
              <div className="flex items-center gap-2 px-3 py-2 bg-red-900/20 border border-red-800/30 rounded-lg">
                <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                <div>
                  <p className="text-[10px] text-red-300 font-bold">JSON invalid — editorul structurat afișează ultimul state valid</p>
                  <p className="text-[9px] text-slate-500">Corectează JSON-ul în tab-ul JSON avansat pentru a sincroniza.</p>
                </div>
              </div>
            )}
            {children({ parsedData: isJsonValid ? parsedData : null, setParsedData })}
          </div>
        ) : (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-slate-500 uppercase tracking-wide font-bold">Mod JSON avansat</span>
              <div className="flex items-center gap-2">
                {!readOnly && (
                  <>
                    <button onClick={formatJson} className="text-[9px] text-blue-400 hover:text-blue-300 font-bold">Formatează</button>
                    <button onClick={resetToSaved} className="text-[9px] text-slate-500 hover:text-slate-400 font-bold flex items-center gap-0.5">
                      <RotateCcw className="w-3 h-3" /> Reset
                    </button>
                  </>
                )}
                <button onClick={copyJson} className="text-[9px] text-slate-500 hover:text-slate-400 font-bold flex items-center gap-0.5">
                  <Copy className="w-3 h-3" /> Copiază
                </button>
              </div>
            </div>
            <textarea
              value={jsonText}
              onChange={(e) => !readOnly && handleJsonChange(e.target.value)}
              readOnly={readOnly}
              rows={8}
              spellCheck={false}
              placeholder={readOnly ? "— read-only —" : '[\n  { "key": "value" }\n]'}
              className={`w-full bg-[#0A0F1A] border rounded-lg px-3 py-2 text-[11px] text-slate-200 font-mono outline-none resize-y min-h-[120px] ${
                readOnly ? "opacity-60 cursor-not-allowed border-[#2A3548]" :
                jsonError ? "border-red-500/50 focus:border-red-500" : "border-[#2A3548] focus:border-purple-500/50"
              }`}
            />
            {jsonError && !readOnly && (
              <div className="flex items-center gap-1.5 px-2 py-1 bg-red-900/20 border border-red-800/30 rounded-lg">
                <AlertTriangle className="w-3 h-3 text-red-400 shrink-0" />
                <span className="text-[10px] text-red-300">{jsonError}</span>
                <span className="text-[9px] text-slate-500 ml-auto">Salvare blocată</span>
              </div>
            )}
          </div>
        )}

        {/* Backend error */}
        {backendError && (
          <div className="flex items-start gap-1.5 mt-3 px-2 py-1.5 bg-red-900/20 border border-red-800/30 rounded-lg">
            <AlertTriangle className="w-3 h-3 text-red-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-[9px] text-red-400 font-bold uppercase">Eroare Backend (422):</span>
              <span className="text-[10px] text-red-300 block">{backendError}</span>
              <span className="text-[9px] text-slate-500 block mt-0.5">Backend-ul este autoritatea finală de validare.</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ============================================================
// SAFE EXAMPLE BUTTON
// ============================================================

function SafeExampleButton({
  readOnly,
  example,
  onInsert,
}: {
  readOnly: boolean;
  example: unknown;
  onInsert: (data: unknown) => void;
}) {
  const [confirming, setConfirming] = useState(false);

  if (readOnly) return null;

  return (
    <div className="flex items-center gap-2">
      {!confirming ? (
        <button
          onClick={() => setConfirming(true)}
          className="flex items-center gap-1 px-2 py-1 bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 hover:text-slate-300 rounded-lg text-[9px] font-bold transition-colors border border-slate-700/40"
        >
          <Lightbulb className="w-3 h-3" /> Inserează exemplu
        </button>
      ) : (
        <div className="flex items-center gap-2 px-2 py-1.5 bg-amber-900/10 border border-amber-800/30 rounded-lg">
          <span className="text-[9px] text-amber-300">Exemplele sunt placeholder-uri, nu valori business reale. Confirmi?</span>
          <button
            onClick={() => { onInsert(example); setConfirming(false); }}
            className="px-2 py-0.5 bg-amber-600/30 hover:bg-amber-600/50 text-amber-200 rounded text-[9px] font-bold"
          >
            Da, inserează
          </button>
          <button
            onClick={() => setConfirming(false)}
            className="px-2 py-0.5 bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 rounded text-[9px] font-bold"
          >
            Anulează
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================
// GENERIC LIST ITEM EDITOR
// ============================================================

interface ListItemField {
  key: string;
  label: string;
  type: "text" | "number" | "boolean" | "select" | "tags";
  options?: string[];
  placeholder?: string;
  required?: boolean;
}

function GenericListEditor({
  items,
  onItemsChange,
  fields,
  readOnly,
  itemLabel,
}: {
  items: Record<string, unknown>[];
  onItemsChange: (items: Record<string, unknown>[]) => void;
  fields: ListItemField[];
  readOnly: boolean;
  itemLabel: string;
}) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const addItem = () => {
    const newItem: Record<string, unknown> = {};
    fields.forEach((f) => {
      if (f.type === "boolean") newItem[f.key] = false;
      else if (f.type === "number") newItem[f.key] = 0;
      else if (f.type === "tags") newItem[f.key] = [];
      else newItem[f.key] = "";
    });
    onItemsChange([...items, newItem]);
    setExpandedIdx(items.length);
  };

  const removeItem = (idx: number) => {
    const next = items.filter((_, i) => i !== idx);
    onItemsChange(next);
    if (expandedIdx === idx) setExpandedIdx(null);
  };

  const updateItem = (idx: number, key: string, value: unknown) => {
    const next = [...items];
    next[idx] = { ...next[idx], [key]: value };
    onItemsChange(next);
  };

  return (
    <div className="space-y-2">
      {items.length === 0 && (
        <div className="flex items-center gap-2 px-3 py-2 bg-slate-800/30 border border-slate-700/30 rounded-lg">
          <Info className="w-3 h-3 text-slate-500 shrink-0" />
          <span className="text-[10px] text-slate-500">Niciun {itemLabel} adăugat. Apasă butonul de mai jos pentru a adăuga.</span>
        </div>
      )}
      {items.map((item, idx) => {
        const isExpanded = expandedIdx === idx;
        const primaryField = fields[0];
        const primaryValue = String(item[primaryField?.key] || `${itemLabel} ${idx + 1}`);

        return (
          <div key={idx} className="border border-[#1E293B] rounded-lg bg-[#111827] overflow-hidden">
            {/* Item header */}
            <div
              className="flex items-center gap-2 px-3 py-2 cursor-pointer hover:bg-slate-800/30 transition-colors"
              onClick={() => setExpandedIdx(isExpanded ? null : idx)}
            >
              {isExpanded ? <ChevronUp className="w-3 h-3 text-slate-500" /> : <ChevronDown className="w-3 h-3 text-slate-500" />}
              <span className="text-[11px] text-slate-300 font-mono flex-1 truncate">{primaryValue || `(gol)`}</span>
              <span className="text-[9px] text-slate-600">#{idx + 1}</span>
              {!readOnly && (
                <button
                  onClick={(e) => { e.stopPropagation(); removeItem(idx); }}
                  className="p-1 hover:bg-red-900/30 rounded text-red-400/60 hover:text-red-400 transition-colors"
                  title="Șterge"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </div>
            {/* Item fields */}
            {isExpanded && (
              <div className="px-3 pb-3 pt-1 space-y-2 border-t border-[#1E293B]">
                {fields.map((field) => (
                  <FieldEditor
                    key={field.key}
                    field={field}
                    value={item[field.key]}
                    onChange={(val) => updateItem(idx, field.key, val)}
                    readOnly={readOnly}
                  />
                ))}
              </div>
            )}
          </div>
        );
      })}
      {!readOnly && (
        <button
          onClick={addItem}
          className="flex items-center gap-1.5 px-3 py-2 bg-purple-600/10 hover:bg-purple-600/20 text-purple-300 rounded-lg text-[10px] font-bold transition-colors border border-purple-700/30 w-full justify-center"
        >
          <Plus className="w-3 h-3" /> Adaugă {itemLabel}
        </button>
      )}
    </div>
  );
}

function FieldEditor({
  field,
  value,
  onChange,
  readOnly,
}: {
  field: ListItemField;
  value: unknown;
  onChange: (val: unknown) => void;
  readOnly: boolean;
}) {
  const [tagInputVal, setTagInputVal] = useState("");

  if (field.type === "boolean") {
    return (
      <div className="flex items-center gap-2">
        <label className="text-[10px] text-slate-500 w-32 shrink-0">{field.label}</label>
        <button
          onClick={() => !readOnly && onChange(!value)}
          disabled={readOnly}
          className={`px-2 py-1 rounded text-[9px] font-bold border transition-colors disabled:opacity-50 ${
            value
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-700/40"
              : "bg-slate-800/50 text-slate-500 border-slate-700/40"
          }`}
        >
          {value ? "Da" : "Nu"}
        </button>
      </div>
    );
  }

  if (field.type === "select" && field.options) {
    return (
      <div className="flex items-center gap-2">
        <label className="text-[10px] text-slate-500 w-32 shrink-0">{field.label}{field.required && <span className="text-red-400">*</span>}</label>
        <select
          value={String(value || "")}
          onChange={(e) => onChange(e.target.value)}
          disabled={readOnly}
          className="flex-1 bg-[#0A0F1A] border border-[#2A3548] rounded px-2 py-1 text-[11px] text-slate-200 outline-none disabled:opacity-50"
        >
          <option value="">— selectează —</option>
          {field.options.map((opt) => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      </div>
    );
  }

  if (field.type === "number") {
    return (
      <div className="flex items-center gap-2">
        <label className="text-[10px] text-slate-500 w-32 shrink-0">{field.label}{field.required && <span className="text-red-400">*</span>}</label>
        <input
          type="number"
          value={value === null || value === undefined ? "" : String(value)}
          onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
          readOnly={readOnly}
          min={0}
          placeholder={field.placeholder || "0"}
          className="flex-1 bg-[#0A0F1A] border border-[#2A3548] rounded px-2 py-1 text-[11px] text-slate-200 font-mono outline-none read-only:opacity-50"
        />
      </div>
    );
  }

  if (field.type === "tags") {
    const tags = Array.isArray(value) ? (value as string[]) : [];
    return (
      <div className="space-y-1">
        <label className="text-[10px] text-slate-500">{field.label}</label>
        <div className="flex flex-wrap gap-1">
          {tags.map((tag, i) => (
            <span key={i} className="flex items-center gap-1 px-1.5 py-0.5 bg-slate-800/50 border border-slate-700/40 rounded text-[9px] text-slate-300">
              {tag}
              {!readOnly && (
                <button onClick={() => onChange(tags.filter((_, ti) => ti !== i))} className="text-red-400/60 hover:text-red-400">×</button>
              )}
            </span>
          ))}
        </div>
        {!readOnly && (
          <div className="flex items-center gap-1">
            <input
              type="text"
              value={tagInputVal}
              onChange={(e) => setTagInputVal(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && tagInputVal.trim()) {
                  e.preventDefault();
                  onChange([...tags, tagInputVal.trim()]);
                  setTagInputVal("");
                }
              }}
              placeholder={field.placeholder || "Adaugă + Enter"}
              className="flex-1 bg-[#0A0F1A] border border-[#2A3548] rounded px-2 py-1 text-[10px] text-slate-200 outline-none"
            />
            <button
              onClick={() => { if (tagInputVal.trim()) { onChange([...tags, tagInputVal.trim()]); setTagInputVal(""); } }}
              className="px-2 py-1 bg-slate-700/50 hover:bg-slate-600/50 text-slate-400 rounded text-[9px] font-bold"
            >
              +
            </button>
          </div>
        )}
      </div>
    );
  }

  // Default: text
  return (
    <div className="flex items-center gap-2">
      <label className="text-[10px] text-slate-500 w-32 shrink-0">{field.label}{field.required && <span className="text-red-400">*</span>}</label>
      <input
        type="text"
        value={String(value || "")}
        onChange={(e) => onChange(e.target.value)}
        readOnly={readOnly}
        placeholder={field.placeholder || ""}
        className="flex-1 bg-[#0A0F1A] border border-[#2A3548] rounded px-2 py-1 text-[11px] text-slate-200 outline-none read-only:opacity-50"
      />
    </div>
  );
}

// ============================================================
// 1. VARIANTS EDITOR
// ============================================================

const VARIANTS_FIELDS: ListItemField[] = [
  { key: "name", label: "Nume variantă", type: "text", required: true, placeholder: "ex: culoare" },
  { key: "description", label: "Descriere", type: "text", placeholder: "Descriere opțională" },
  { key: "allowed_values", label: "Valori permise", type: "tags", placeholder: "Adaugă valoare + Enter" },
  { key: "notes", label: "Note", type: "text", placeholder: "Note adiționale" },
];

const VARIANTS_EXAMPLE = [
  { name: "Dimensiune", description: "Dimensiunea produsului", allowed_values: ["S", "M", "L", "XL"], notes: "" },
  { name: "Culoare", description: "Culoarea principală", allowed_values: ["Alb", "Negru", "Gri"], notes: "Culorile custom necesită confirmare" },
];

export function VariantsEditor({ value, onChange, readOnly }: StructuredEditorProps) {
  const parsed = useMemo(() => {
    if (!value || !value.trim()) return [];
    try {
      const data = JSON.parse(value);
      return Array.isArray(data) ? data : [];
    } catch { return []; }
  }, [value]);

  const handleChange = (items: Record<string, unknown>[]) => {
    if (items.length === 0) {
      onChange(null);
    } else {
      onChange(JSON.stringify(items, null, 2));
    }
  };

  return (
    <div className="space-y-3">
      <GenericListEditor
        items={parsed}
        onItemsChange={handleChange}
        fields={VARIANTS_FIELDS}
        readOnly={readOnly}
        itemLabel="variantă"
      />
      <SafeExampleButton readOnly={readOnly} example={VARIANTS_EXAMPLE} onInsert={(data) => onChange(JSON.stringify(data, null, 2))} />
    </div>
  );
}

// ============================================================
// 2. TASK RULES EDITOR
// ============================================================

const TASK_RULES_FIELDS: ListItemField[] = [
  { key: "task_name", label: "Nume sarcină", type: "text", required: true, placeholder: "ex: tăiere material" },
  { key: "required_or_optional", label: "Obligatoriu", type: "select", options: ["required", "optional"] },
  { key: "trigger_condition", label: "Condiție declanșare", type: "text", placeholder: "ex: dacă dimensiune > 100cm" },
  { key: "estimated_time", label: "Timp estimat (min)", type: "number", placeholder: "0" },
  { key: "notes", label: "Note", type: "text", placeholder: "Note adiționale" },
];

const TASK_RULES_EXAMPLE = [
  { task_name: "Tăiere material", required_or_optional: "required", trigger_condition: "întotdeauna", estimated_time: 30, notes: "" },
  { task_name: "Finisare specială", required_or_optional: "optional", trigger_condition: "dacă client solicită", estimated_time: 45, notes: "Necesită echipament special" },
];

export function TaskRulesEditor({ value, onChange, readOnly }: StructuredEditorProps) {
  const parsed = useMemo(() => {
    if (!value || !value.trim()) return [];
    try {
      const data = JSON.parse(value);
      return Array.isArray(data) ? data : [];
    } catch { return []; }
  }, [value]);

  const handleChange = (items: Record<string, unknown>[]) => {
    if (items.length === 0) onChange(null);
    else onChange(JSON.stringify(items, null, 2));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800/30 border border-slate-700/30 rounded-lg">
        <Info className="w-3 h-3 text-slate-500 shrink-0" />
        <span className="text-[9px] text-slate-500">Doar documentație — nu creează task-uri în producție.</span>
      </div>
      <GenericListEditor
        items={parsed}
        onItemsChange={handleChange}
        fields={TASK_RULES_FIELDS}
        readOnly={readOnly}
        itemLabel="regulă"
      />
      <SafeExampleButton readOnly={readOnly} example={TASK_RULES_EXAMPLE} onInsert={(data) => onChange(JSON.stringify(data, null, 2))} />
    </div>
  );
}

// ============================================================
// 3. TIME ASSUMPTIONS EDITOR
// ============================================================

const TIME_ASSUMPTIONS_FIELDS: ListItemField[] = [
  { key: "operation_name", label: "Operație", type: "text", required: true, placeholder: "ex: asamblare" },
  { key: "time_type", label: "Tip timp", type: "select", options: ["fixed", "per_unit", "per_m2", "per_ml", "variable"] },
  { key: "unit", label: "Unitate", type: "text", required: true, placeholder: "ex: minute, ore" },
  { key: "value", label: "Valoare", type: "number", required: true, placeholder: "0" },
  { key: "min_value", label: "Valoare min", type: "number", placeholder: "opțional" },
  { key: "max_value", label: "Valoare max", type: "number", placeholder: "opțional" },
  { key: "notes", label: "Note", type: "text", placeholder: "Condiții, excepții" },
];

const TIME_ASSUMPTIONS_EXAMPLE = [
  { operation_name: "Tăiere", time_type: "per_unit", unit: "minute", value: 15, min_value: 10, max_value: 25, notes: "Depinde de material" },
  { operation_name: "Asamblare", time_type: "fixed", unit: "ore", value: 2, min_value: null, max_value: null, notes: "" },
];

export function TimeAssumptionsEditor({ value, onChange, readOnly }: StructuredEditorProps) {
  const parsed = useMemo(() => {
    if (!value || !value.trim()) return [];
    try {
      const data = JSON.parse(value);
      return Array.isArray(data) ? data : [];
    } catch { return []; }
  }, [value]);

  const handleChange = (items: Record<string, unknown>[]) => {
    if (items.length === 0) onChange(null);
    else onChange(JSON.stringify(items, null, 2));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800/30 border border-slate-700/30 rounded-lg">
        <Info className="w-3 h-3 text-slate-500 shrink-0" />
        <span className="text-[9px] text-slate-500">Doar documentație — nu calculează cost.</span>
      </div>
      <GenericListEditor
        items={parsed}
        onItemsChange={handleChange}
        fields={TIME_ASSUMPTIONS_FIELDS}
        readOnly={readOnly}
        itemLabel="estimare"
      />
      <SafeExampleButton readOnly={readOnly} example={TIME_ASSUMPTIONS_EXAMPLE} onInsert={(data) => onChange(JSON.stringify(data, null, 2))} />
    </div>
  );
}

// ============================================================
// 4. COSTENGINE MAPPING EDITOR
// ============================================================

const CE_CATEGORIES = [
  "dimension_inputs",
  "material_inputs",
  "operation_inputs",
  "labor_inputs",
  "machine_inputs",
  "waste_inputs",
  "option_modifiers",
] as const;

const CE_ITEM_FIELDS: ListItemField[] = [
  { key: "key", label: "Cheie", type: "text", required: true, placeholder: "ex: width_mm" },
  { key: "label", label: "Etichetă", type: "text", placeholder: "ex: Lățime (mm)" },
  { key: "source", label: "Sursă", type: "text", placeholder: "ex: variants_json.dimensiune" },
  { key: "required", label: "Obligatoriu", type: "boolean" },
  { key: "notes", label: "Note", type: "text", placeholder: "Note adiționale" },
];

const CE_EXAMPLE: Record<string, unknown[]> = {
  dimension_inputs: [{ key: "width_mm", label: "Lățime (mm)", source: "variants_json", required: true, notes: "" }],
  material_inputs: [{ key: "material_type", label: "Tip material", source: "layers_json", required: true, notes: "" }],
  operation_inputs: [],
  labor_inputs: [{ key: "labor_hours", label: "Ore manoperă", source: "time_assumptions_json", required: false, notes: "" }],
  machine_inputs: [],
  waste_inputs: [],
  option_modifiers: [],
};

export function CostEngineMappingEditor({ value, onChange, readOnly }: StructuredEditorProps) {
  const parsed: Record<string, unknown[]> = useMemo(() => {
    if (!value || !value.trim()) return {};
    try {
      const data = JSON.parse(value);
      if (data && typeof data === "object" && !Array.isArray(data)) return data;
      return {};
    } catch { return {}; }
  }, [value]);

  const [expandedCat, setExpandedCat] = useState<string | null>(null);

  const updateCategory = (cat: string, items: Record<string, unknown>[]) => {
    const next = { ...parsed, [cat]: items };
    // Remove empty categories
    const cleaned: Record<string, unknown[]> = {};
    let hasContent = false;
    for (const [k, v] of Object.entries(next)) {
      if (Array.isArray(v) && v.length > 0) {
        cleaned[k] = v;
        hasContent = true;
      }
    }
    if (!hasContent) onChange(null);
    else onChange(JSON.stringify(cleaned, null, 2));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 px-2 py-1.5 bg-amber-900/10 border border-amber-800/30 rounded-lg">
        <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
        <span className="text-[9px] text-amber-300 font-semibold">
          Mapare pentru audit/viitor CostEngine — nu rulează CostEngine și nu calculează cost.
        </span>
      </div>

      {CE_CATEGORIES.map((cat) => {
        const items = Array.isArray(parsed[cat]) ? (parsed[cat] as Record<string, unknown>[]) : [];
        const isExpanded = expandedCat === cat;
        return (
          <div key={cat} className="border border-[#1E293B] rounded-lg bg-[#111827] overflow-hidden">
            <button
              onClick={() => setExpandedCat(isExpanded ? null : cat)}
              className="w-full flex items-center gap-2 px-3 py-2 hover:bg-slate-800/30 transition-colors text-left"
            >
              {isExpanded ? <ChevronUp className="w-3 h-3 text-slate-500" /> : <ChevronDown className="w-3 h-3 text-slate-500" />}
              <span className="text-[10px] text-slate-300 font-bold flex-1">{cat.replace(/_/g, " ")}</span>
              <span className="text-[9px] text-slate-600">{items.length} items</span>
            </button>
            {isExpanded && (
              <div className="px-3 pb-3 border-t border-[#1E293B]">
                <GenericListEditor
                  items={items}
                  onItemsChange={(newItems) => updateCategory(cat, newItems)}
                  fields={CE_ITEM_FIELDS}
                  readOnly={readOnly}
                  itemLabel="mapping"
                />
              </div>
            )}
          </div>
        );
      })}
      <SafeExampleButton readOnly={readOnly} example={CE_EXAMPLE} onInsert={(data) => onChange(JSON.stringify(data, null, 2))} />
    </div>
  );
}

// ============================================================
// 5. QC CHECKPOINTS EDITOR
// ============================================================

const QC_FIELDS: ListItemField[] = [
  { key: "checkpoint_name", label: "Nume checkpoint", type: "text", required: true, placeholder: "ex: verificare dimensiuni" },
  { key: "what_to_verify", label: "Ce se verifică", type: "text", required: true, placeholder: "Descriere verificare" },
  { key: "blocking_if_failed", label: "Blocant dacă pică", type: "boolean" },
  { key: "responsible_role", label: "Rol responsabil", type: "text", placeholder: "ex: QC inspector" },
  { key: "notes", label: "Note", type: "text", placeholder: "Note adiționale" },
];

const QC_EXAMPLE = [
  { checkpoint_name: "Verificare dimensiuni", what_to_verify: "Toate dimensiunile conform specificației", blocking_if_failed: true, responsible_role: "QC inspector", notes: "" },
  { checkpoint_name: "Verificare vizuală", what_to_verify: "Fără defecte vizibile pe suprafață", blocking_if_failed: false, responsible_role: "operator", notes: "Fotografiere obligatorie" },
];

export function QcCheckpointsEditor({ value, onChange, readOnly }: StructuredEditorProps) {
  const parsed = useMemo(() => {
    if (!value || !value.trim()) return [];
    try {
      const data = JSON.parse(value);
      return Array.isArray(data) ? data : [];
    } catch { return []; }
  }, [value]);

  const handleChange = (items: Record<string, unknown>[]) => {
    if (items.length === 0) onChange(null);
    else onChange(JSON.stringify(items, null, 2));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800/30 border border-slate-700/30 rounded-lg">
        <Info className="w-3 h-3 text-slate-500 shrink-0" />
        <span className="text-[9px] text-slate-500">Doar documentație — nu creează task-uri QC și nu blochează execuția.</span>
      </div>
      <GenericListEditor
        items={parsed}
        onItemsChange={handleChange}
        fields={QC_FIELDS}
        readOnly={readOnly}
        itemLabel="checkpoint"
      />
      <SafeExampleButton readOnly={readOnly} example={QC_EXAMPLE} onInsert={(data) => onChange(JSON.stringify(data, null, 2))} />
    </div>
  );
}

// ============================================================
// 6. RISKS EDITOR
// ============================================================

const RISKS_FIELDS: ListItemField[] = [
  { key: "risk_name", label: "Nume risc", type: "text", required: true, placeholder: "ex: întârziere furnizor" },
  { key: "severity", label: "Severitate", type: "select", options: ["low", "medium", "high", "critical"] },
  { key: "category", label: "Categorie", type: "text", placeholder: "ex: supply chain" },
  { key: "mitigation", label: "Mitigare", type: "text", placeholder: "Acțiuni de reducere a riscului" },
  { key: "notes", label: "Note", type: "text", placeholder: "Note adiționale" },
];

const RISKS_EXAMPLE = [
  { risk_name: "Întârziere furnizor material", severity: "medium", category: "supply_chain", mitigation: "Stoc tampon 2 săptămâni", notes: "" },
  { risk_name: "Eroare dimensiuni la tăiere", severity: "high", category: "production", mitigation: "Dublu control înainte de tăiere", notes: "Frecvent la comenzi custom" },
];

export function RisksEditor({ value, onChange, readOnly }: StructuredEditorProps) {
  const parsed = useMemo(() => {
    if (!value || !value.trim()) return [];
    try {
      const data = JSON.parse(value);
      return Array.isArray(data) ? data : [];
    } catch { return []; }
  }, [value]);

  const handleChange = (items: Record<string, unknown>[]) => {
    if (items.length === 0) onChange(null);
    else onChange(JSON.stringify(items, null, 2));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800/30 border border-slate-700/30 rounded-lg">
        <Info className="w-3 h-3 text-slate-500 shrink-0" />
        <span className="text-[9px] text-slate-500">Doar documentație — nu creează incidente și nu blochează comenzi.</span>
      </div>
      <GenericListEditor
        items={parsed}
        onItemsChange={handleChange}
        fields={RISKS_FIELDS}
        readOnly={readOnly}
        itemLabel="risc"
      />
      <SafeExampleButton readOnly={readOnly} example={RISKS_EXAMPLE} onInsert={(data) => onChange(JSON.stringify(data, null, 2))} />
    </div>
  );
}

// ============================================================
// 7. PRODUCTION NOTES EDITOR
// ============================================================

const NOTES_FIELDS: ListItemField[] = [
  { key: "category", label: "Categorie", type: "text", required: true, placeholder: "ex: asamblare, finisare" },
  { key: "note", label: "Notă", type: "text", required: true, placeholder: "Conținutul notei" },
  { key: "warning", label: "Avertisment", type: "boolean" },
  { key: "role", label: "Rol", type: "text", placeholder: "ex: operator, supervizor" },
];

const NOTES_EXAMPLE = [
  { category: "asamblare", note: "Verifică orientarea pieselor înainte de lipire", warning: true, role: "operator" },
  { category: "finisare", note: "Timp de uscare minim 4 ore", warning: false, role: "supervizor" },
];

export function ProductionNotesEditor({ value, onChange, readOnly }: StructuredEditorProps) {
  const parsed = useMemo(() => {
    if (!value || !value.trim()) return [];
    try {
      const data = JSON.parse(value);
      return Array.isArray(data) ? data : [];
    } catch { return []; }
  }, [value]);

  const handleChange = (items: Record<string, unknown>[]) => {
    if (items.length === 0) onChange(null);
    else onChange(JSON.stringify(items, null, 2));
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800/30 border border-slate-700/30 rounded-lg">
        <Info className="w-3 h-3 text-slate-500 shrink-0" />
        <span className="text-[9px] text-slate-500">Note structurate — nu modifică inventarul sau execuția.</span>
      </div>
      <GenericListEditor
        items={parsed}
        onItemsChange={handleChange}
        fields={NOTES_FIELDS}
        readOnly={readOnly}
        itemLabel="notă"
      />
      <SafeExampleButton readOnly={readOnly} example={NOTES_EXAMPLE} onInsert={(data) => onChange(JSON.stringify(data, null, 2))} />
    </div>
  );
}

// ============================================================
// 8. COMPLETION STATE EDITOR
// ============================================================

const COMPLETION_STATUSES: SectionCompletionState[] = ["not_started", "draft", "needs_review", "complete", "blocked", "deprecated"];

interface CompletionStateEditorProps {
  value: string | null;
  onChange: (val: string | null) => void;
  readOnly: boolean;
  sectionKeys: string[];
}

export function CompletionStateEditor({ value, onChange, readOnly, sectionKeys }: CompletionStateEditorProps) {
  const parsed: Record<string, { status: SectionCompletionState }> = useMemo(() => {
    if (!value || !value.trim()) return {};
    try {
      const data = JSON.parse(value);
      if (data && typeof data === "object" && !Array.isArray(data)) return data;
      return {};
    } catch { return {}; }
  }, [value]);

  const updateSection = (key: string, status: SectionCompletionState) => {
    const next = { ...parsed, [key]: { status } };
    onChange(JSON.stringify(next, null, 2));
  };

  const bulkSetEmpty = (targetStatus: SectionCompletionState) => {
    const next = { ...parsed };
    sectionKeys.forEach((key) => {
      if (!next[key] || next[key].status === "not_started") {
        next[key] = { status: targetStatus };
      }
    });
    onChange(JSON.stringify(next, null, 2));
  };

  // Summary
  const counts: Record<SectionCompletionState, number> = { not_started: 0, draft: 0, needs_review: 0, complete: 0, blocked: 0, deprecated: 0 };
  sectionKeys.forEach((key) => {
    const st = parsed[key]?.status || "not_started";
    if (counts[st] !== undefined) counts[st]++;
  });

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-1.5 px-2 py-1 bg-slate-800/30 border border-slate-700/30 rounded-lg">
        <Info className="w-3 h-3 text-slate-500 shrink-0" />
        <span className="text-[9px] text-slate-500">Progress tracking only — does not block quotes/orders or calculate readiness score.</span>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-6 gap-1">
        {COMPLETION_STATUSES.map((st) => {
          const cfg = SECTION_STATE_CONFIG[st];
          return (
            <div key={st} className="text-center px-1 py-1.5 bg-slate-800/30 rounded-lg border border-slate-700/30">
              <span className="text-sm block">{cfg.emoji}</span>
              <span className={`text-[12px] font-bold block ${cfg.color}`}>{counts[st]}</span>
              <span className="text-[7px] text-slate-600 uppercase block">{cfg.label}</span>
            </div>
          );
        })}
      </div>

      {/* Bulk actions */}
      {!readOnly && (
        <div className="flex items-center gap-2">
          <span className="text-[9px] text-slate-600 uppercase font-bold">Bulk:</span>
          <button
            onClick={() => bulkSetEmpty("draft")}
            className="px-2 py-1 bg-slate-800/50 hover:bg-slate-700/50 text-slate-400 rounded text-[9px] font-bold border border-slate-700/40"
          >
            Set neîncepute → Ciornă
          </button>
        </div>
      )}

      {/* Per-section status */}
      <div className="space-y-1">
        {sectionKeys.map((key) => {
          const currentStatus = parsed[key]?.status || "not_started";
          const cfg = SECTION_STATE_CONFIG[currentStatus];
          return (
            <div key={key} className="flex items-center gap-2 px-2 py-1.5 bg-[#111827] border border-[#1E293B] rounded-lg">
              <span className="text-[10px] text-slate-400 font-mono flex-1 truncate">{key}</span>
              <div className="flex items-center gap-1">
                {COMPLETION_STATUSES.map((st) => {
                  const stCfg = SECTION_STATE_CONFIG[st];
                  const isActive = currentStatus === st;
                  return (
                    <button
                      key={st}
                      onClick={() => !readOnly && updateSection(key, st)}
                      disabled={readOnly}
                      title={stCfg.label}
                      className={`w-5 h-5 rounded flex items-center justify-center text-[9px] transition-all border disabled:opacity-50 disabled:cursor-not-allowed ${
                        isActive
                          ? `${stCfg.color} bg-white/5 border-current`
                          : "text-slate-700 border-transparent hover:text-slate-500"
                      }`}
                    >
                      {stCfg.emoji}
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// DOSSIER VALIDATION SUMMARY PANEL
// ============================================================

interface ValidationSummaryProps {
  localSections: Record<string, string | null>;
  completionStates: Record<string, { status: SectionCompletionState }>;
  dossierStatus: string;
  backendError: string | null;
  deferredKeys: Set<string>;
  allSectionKeys: string[];
}

export function DossierValidationSummary({
  localSections,
  completionStates,
  dossierStatus,
  backendError,
  deferredKeys,
  allSectionKeys,
}: ValidationSummaryProps) {
  let valid = 0;
  let invalid = 0;
  let empty = 0;
  let deferred = 0;

  allSectionKeys.forEach((key) => {
    if (key === "completion_state_json") return;
    if (deferredKeys.has(key)) { deferred++; return; }
    const val = localSections[key] ?? null;
    if (!val || !val.trim()) { empty++; return; }
    try { JSON.parse(val); valid++; } catch { invalid++; }
  });

  // Completion states summary
  let complete = 0;
  let inProgress = 0;
  let blocked = 0;
  const cleanKeys = allSectionKeys
    .filter((k) => k !== "completion_state_json" && !deferredKeys.has(k))
    .map((k) => k.replace("_json", ""));
  cleanKeys.forEach((k) => {
    const st = completionStates[k]?.status || "not_started";
    if (st === "complete") complete++;
    else if (st === "draft" || st === "needs_review") inProgress++;
    else if (st === "blocked") blocked++;
  });

  return (
    <div className="bg-[#111827] border border-[#1E293B] rounded-xl p-3 space-y-2">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[10px] text-slate-500 uppercase tracking-wide font-bold">JSON & Progres Editorial</span>
        {dossierStatus === "approved" && (
          <span className="px-1.5 py-0.5 text-[8px] font-bold bg-emerald-900/30 text-emerald-400 border border-emerald-700/40 rounded">
            APROBAT
          </span>
        )}
      </div>

      <div className="grid grid-cols-4 gap-2">
        <div className="text-center px-2 py-1.5 bg-emerald-500/5 border border-emerald-700/20 rounded-lg">
          <span className="text-[14px] font-bold text-emerald-400 block">{valid}</span>
          <span className="text-[8px] text-slate-500 uppercase">Valid</span>
        </div>
        <div className="text-center px-2 py-1.5 bg-red-500/5 border border-red-700/20 rounded-lg">
          <span className="text-[14px] font-bold text-red-400 block">{invalid}</span>
          <span className="text-[8px] text-slate-500 uppercase">Invalid</span>
        </div>
        <div className="text-center px-2 py-1.5 bg-slate-500/5 border border-slate-700/20 rounded-lg">
          <span className="text-[14px] font-bold text-slate-400 block">{empty}</span>
          <span className="text-[8px] text-slate-500 uppercase">Gol</span>
        </div>
        <div className="text-center px-2 py-1.5 bg-slate-500/5 border border-slate-700/20 rounded-lg">
          <span className="text-[14px] font-bold text-slate-600 block">{deferred}</span>
              <span className="text-[8px] text-slate-500 uppercase">Amânate</span>
        </div>
      </div>

      {/* Completion progress */}
      <div className="flex items-center gap-2 text-[9px] pt-1">
        <span className="text-emerald-400">✅ {complete} complete</span>
        <span className="text-amber-400">📝 {inProgress} în lucru</span>
        <span className="text-red-400">🚫 {blocked} blocate</span>
      </div>

      {/* Status impact */}
      {dossierStatus === "approved" && (
        <div className="flex items-start gap-1.5 px-2 py-1.5 bg-emerald-900/10 border border-emerald-800/20 rounded-lg">
          <Info className="w-3 h-3 text-emerald-400 shrink-0 mt-0.5" />
          <span className="text-[9px] text-emerald-300">
            Status &quot;Aprobat&quot; — acest panou verifică doar JSON-ul și progresul editorial. Readiness Authority decide dacă șablonul intră în ofertare.
          </span>
        </div>
      )}
      {dossierStatus === "draft" && (
        <div className="flex items-start gap-1.5 px-2 py-1.5 bg-slate-800/30 border border-slate-700/30 rounded-lg">
          <Info className="w-3 h-3 text-slate-500 shrink-0 mt-0.5" />
          <span className="text-[9px] text-slate-500">
            Status &quot;Ciornă&quot; — editare permisivă, validarea este informativă.
          </span>
        </div>
      )}

      {/* Backend error */}
      {backendError && (
        <div className="flex items-start gap-1.5 px-2 py-1.5 bg-red-900/10 border border-red-800/20 rounded-lg">
          <AlertTriangle className="w-3 h-3 text-red-400 shrink-0 mt-0.5" />
          <div>
            <span className="text-[9px] text-red-400 font-bold">Ultima eroare backend:</span>
            <span className="text-[9px] text-red-300 block">{backendError}</span>
          </div>
        </div>
      )}

      {/* Safety note */}
      <div className="text-[8px] text-slate-600 pt-1 border-t border-[#1E293B]">
        Acesta nu este readiness score. Materialele, operațiile și prețurile sunt autoritate în Product Template + Pricing Registry.
      </div>
    </div>
  );
}