import { useCallback, useEffect, useMemo, useState } from "react";
import {
  operationalRegistryApi,
  type OperationResourceMapping,
  type OperationalCatalog,
  type RegistryEmployee,
} from "@/api/operationalRegistry";
import { Save, RefreshCw, AlertTriangle, Link2 } from "lucide-react";
import { OperationPoolPreviewPanel } from "./OperationPoolPreviewPanel";

export interface TemplateOperationRef {
  code: string;
  label: string;
  workcenter?: string | null;
}

interface Props {
  operations: TemplateOperationRef[];
}

function emptyMapping(code: string, aliases: string[] = []): OperationResourceMapping {
  return {
    operation_code: code,
    required_skill_codes: [],
    allowed_workcenter_codes: [],
    allowed_resource_codes: [],
    authorization_mode: "hybrid",
    default_resource_code: null,
    product_system_aliases: aliases,
    authorized_employee_ids: [],
    notes: null,
  };
}

export function TemplateOperationMappingPanel({ operations }: Props) {
  const [catalog, setCatalog] = useState<OperationalCatalog | null>(null);
  const [employees, setEmployees] = useState<RegistryEmployee[]>([]);
  const [mappings, setMappings] = useState<Record<string, OperationResourceMapping>>({});
  const [selectedCode, setSelectedCode] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const operationsKey = useMemo(
    () => operations.map((op) => op.code).join("|"),
    [operations]
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cat, empRes, mapRes] = await Promise.all([
        operationalRegistryApi.getCatalog(),
        operationalRegistryApi.listEmployees(),
        operationalRegistryApi.listOperationMappings(),
      ]);
      setCatalog(cat);
      setEmployees(empRes.items.filter((e) => e.status === "active"));

      const byCode: Record<string, OperationResourceMapping> = {};
      for (const m of mapRes.items) {
        byCode[m.operation_code] = m;
      }

      for (const op of operations) {
        const suggested = cat.suggested_operation_aliases[op.code];
        const registryCode = suggested ?? op.code;
        if (!byCode[registryCode]) {
          byCode[registryCode] = emptyMapping(registryCode, suggested ? [op.code] : []);
        } else if (suggested && !byCode[registryCode].product_system_aliases.includes(op.code)) {
          byCode[registryCode] = {
            ...byCode[registryCode],
            product_system_aliases: [...byCode[registryCode].product_system_aliases, op.code],
          };
        }
      }
      setMappings(byCode);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare încărcare mapping");
    } finally {
      setLoading(false);
    }
  }, [operations, operationsKey]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!catalog || operations.length === 0) return;
    const first = operations[0];
    const suggested = catalog.suggested_operation_aliases[first.code];
    const defaultCode = suggested ?? first.code;
    setSelectedCode((prev) => prev ?? defaultCode);
  }, [catalog, operationsKey, operations]);

  const selectedMapping = selectedCode ? mappings[selectedCode] : null;

  const selectedOp = useMemo(
    () =>
      operations.find(
        (op) =>
          op.code === selectedCode ||
          catalog?.suggested_operation_aliases[op.code] === selectedCode
      ) ?? null,
    [operations, selectedCode, catalog]
  );

  const updateSelected = (patch: Partial<OperationResourceMapping>) => {
    if (!selectedCode || !selectedMapping) return;
    setMappings((prev) => ({
      ...prev,
      [selectedCode]: { ...selectedMapping, ...patch },
    }));
  };

  const toggleListItem = (
    field: "required_skill_codes" | "allowed_workcenter_codes" | "allowed_resource_codes" | "authorized_employee_ids",
    value: string | number
  ) => {
    if (!selectedMapping) return;
    const current = selectedMapping[field] as Array<string | number>;
    const exists = current.includes(value as never);
    const next = exists
      ? current.filter((v) => v !== value)
      : [...current, value];
    updateSelected({ [field]: next } as Partial<OperationResourceMapping>);
  };

  const saveSelected = async () => {
    if (!selectedMapping) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const savedMapping = await operationalRegistryApi.upsertOperationMapping(selectedMapping);
      setMappings((prev) => ({ ...prev, [savedMapping.operation_code]: savedMapping }));
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare salvare mapping");
    } finally {
      setSaving(false);
    }
  };

  if (operations.length === 0) {
    return (
      <p className="text-xs text-slate-400">Nu există operații în șablon pentru mapping operațional.</p>
    );
  }

  return (
    <div className="rounded-lg border border-violet-800/40 bg-violet-950/10 p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-violet-100 flex items-center gap-2">
            <Link2 className="w-4 h-4" />
            Mapping operațiuni → resurse / autorizări
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Nu modifică CostEngine. Salvează în operational registry (
            <code className="text-[10px]">operation_resource_requirements</code>).
          </p>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded border border-slate-600 text-slate-300"
        >
          <RefreshCw className="w-3 h-3" />
          Reîncarcă
        </button>
      </div>

      {loading && <p className="text-xs text-slate-400">Se încarcă…</p>}
      {error && (
        <p className="text-xs text-red-300 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          {error}
        </p>
      )}
      {saved && <p className="text-xs text-emerald-300">Mapping salvat.</p>}

      {catalog && (
        <div className="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-4">
          <div className="space-y-1 max-h-72 overflow-y-auto">
            {operations.map((op) => {
              const registryCode = catalog.suggested_operation_aliases[op.code] ?? op.code;
              const active = selectedCode === registryCode;
              return (
                <button
                  key={op.code}
                  type="button"
                  onClick={() => setSelectedCode(registryCode)}
                  className={`w-full text-left px-2 py-2 rounded border text-xs ${
                    active
                      ? "border-violet-600 bg-violet-900/30 text-violet-100"
                      : "border-slate-700 bg-slate-900/30 text-slate-300 hover:bg-slate-800/40"
                  }`}
                >
                  <div className="font-mono">{op.code}</div>
                  <div className="text-[10px] text-slate-500 truncate">{op.label}</div>
                  {registryCode !== op.code && (
                    <div className="text-[10px] text-violet-300/80">→ {registryCode}</div>
                  )}
                </button>
              );
            })}
          </div>

          {selectedMapping && (
            <div className="space-y-3">
              <div className="text-xs text-slate-300">
                Registry code: <span className="font-mono text-violet-200">{selectedMapping.operation_code}</span>
                {selectedOp && selectedOp.code !== selectedMapping.operation_code && (
                  <span className="text-slate-500"> · alias PS: {selectedOp.code}</span>
                )}
              </div>

              <label className="block text-xs space-y-1">
                <span className="text-slate-400">Authorization mode</span>
                <select
                  value={selectedMapping.authorization_mode}
                  onChange={(e) => updateSelected({ authorization_mode: e.target.value })}
                  className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-slate-200"
                >
                  {catalog.authorization_modes.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </label>

              <CheckboxSection
                title="Skills necesare"
                items={catalog.skills.map((s) => ({ id: s.skill_code, label: s.label_ro }))}
                selected={selectedMapping.required_skill_codes}
                onToggle={(id) => toggleListItem("required_skill_codes", id)}
              />
              <CheckboxSection
                title="Workcenters permise"
                items={catalog.workcenters.map((w) => ({ id: w.workcenter_code, label: w.label_ro }))}
                selected={selectedMapping.allowed_workcenter_codes}
                onToggle={(id) => toggleListItem("allowed_workcenter_codes", id)}
              />
              <CheckboxSection
                title="Resurse / utilaje permise"
                items={catalog.resources.map((r) => ({
                  id: r.resource_code,
                  label: `${r.name} (${r.resource_kind})`,
                }))}
                selected={selectedMapping.allowed_resource_codes}
                onToggle={(id) => toggleListItem("allowed_resource_codes", id)}
              />
              <div className="space-y-1">
                <p className="text-xs font-semibold text-slate-300">
                  Override operațional registry — angajați expliciți
                </p>
                <p className="text-[10px] text-slate-500">
                  Nu se salvează în template-ul produsului. Acest override aparține Operational
                  Registry și este folosit doar pentru pool-ul eligibil.
                </p>
                <CheckboxSection
                  title="Angajați activi (multi-select)"
                  items={employees.map((e) => ({ id: String(e.id), label: e.name }))}
                  selected={selectedMapping.authorized_employee_ids.map(String)}
                  onToggle={(id) => toggleListItem("authorized_employee_ids", Number(id))}
                />
              </div>

              <label className="block text-xs space-y-1">
                <span className="text-slate-400">Alias-uri ProductSystem (comma separated)</span>
                <input
                  value={selectedMapping.product_system_aliases.join(", ")}
                  onChange={(e) =>
                    updateSelected({
                      product_system_aliases: e.target.value
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean),
                    })
                  }
                  className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 text-slate-200 font-mono"
                />
              </label>

              <OperationPoolPreviewPanel
                operationCode={selectedOp?.code ?? selectedMapping.operation_code}
              />

              <button
                type="button"
                onClick={() => void saveSelected()}
                disabled={saving}
                className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded bg-violet-700 hover:bg-violet-600 text-white disabled:opacity-50"
              >
                <Save className="w-3 h-3" />
                Salvează mapping
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function CheckboxSection({
  title,
  items,
  selected,
  onToggle,
}: {
  title: string;
  items: Array<{ id: string; label: string }>;
  selected: string[];
  onToggle: (id: string) => void;
}) {
  return (
    <div className="space-y-1">
      <p className="text-xs font-semibold text-slate-300">{title}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1 max-h-32 overflow-y-auto">
        {items.map((item) => (
          <label
            key={item.id}
            className="flex items-center gap-2 text-[11px] rounded border border-slate-700 px-2 py-1"
          >
            <input
              type="checkbox"
              checked={selected.includes(item.id)}
              onChange={() => onToggle(item.id)}
            />
            <span className="truncate">{item.label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}
