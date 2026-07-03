import { useCallback, useEffect, useState } from "react";
import {
  operationalRegistryApi,
  type OperationalCatalog,
  type RegistryEmployee,
  type RegistryResource,
} from "@/api/operationalRegistry";
import { Save, RefreshCw, AlertTriangle } from "lucide-react";

interface Props {
  employeeId: number | null;
  readOnly?: boolean;
}

function MultiCheckboxGroup({
  title,
  options,
  selected,
  onChange,
  labelKey,
  valueKey,
  disabled,
}: {
  title: string;
  options: Array<{ [key: string]: string }>;
  selected: string[];
  onChange: (next: string[]) => void;
  labelKey: string;
  valueKey: string;
  disabled?: boolean;
}) {
  const toggle = (code: string) => {
    if (disabled) return;
    onChange(
      selected.includes(code)
        ? selected.filter((s) => s !== code)
        : [...selected, code]
    );
  };

  return (
    <div className="space-y-2">
      <p className="text-xs font-semibold text-slate-300 uppercase tracking-wide">{title}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 max-h-40 overflow-y-auto pr-1">
        {options.map((opt) => {
          const code = opt[valueKey];
          const checked = selected.includes(code);
          return (
            <label
              key={code}
              className={`flex items-center gap-2 text-xs rounded border px-2 py-1.5 cursor-pointer ${
                checked
                  ? "border-cyan-700/60 bg-cyan-950/30 text-cyan-100"
                  : "border-slate-700 bg-slate-900/40 text-slate-300"
              } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
            >
              <input
                type="checkbox"
                checked={checked}
                disabled={disabled}
                onChange={() => toggle(code)}
                className="rounded border-slate-600"
              />
              <span>{opt[labelKey]}</span>
              <span className="text-[10px] text-slate-500 ml-auto font-mono">{code}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

export function EmployeeOperationalPanel({ employeeId, readOnly = false }: Props) {
  const [catalog, setCatalog] = useState<OperationalCatalog | null>(null);
  const [employee, setEmployee] = useState<RegistryEmployee | null>(null);
  const [skillCodes, setSkillCodes] = useState<string[]>([]);
  const [workcenterCodes, setWorkcenterCodes] = useState<string[]>([]);
  const [resourceCodes, setResourceCodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    if (employeeId == null) return;
    setLoading(true);
    setError(null);
    try {
      const [cat, emp] = await Promise.all([
        operationalRegistryApi.getCatalog(),
        operationalRegistryApi.getEmployee(employeeId),
      ]);
      setCatalog(cat);
      setEmployee(emp);
      setSkillCodes(emp.skill_codes ?? []);
      setWorkcenterCodes(emp.workcenter_codes ?? []);
      setResourceCodes(emp.resource_codes ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare registry");
    } finally {
      setLoading(false);
    }
  }, [employeeId]);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    if (employeeId == null || readOnly) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      await operationalRegistryApi.updateEmployeeAuthorizations(employeeId, {
        skill_codes: skillCodes,
        workcenter_codes: workcenterCodes,
        resource_codes: resourceCodes,
      });
      setSaved(true);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare salvare autorizări");
    } finally {
      setSaving(false);
    }
  };

  if (employeeId == null) return null;

  const resourceOptions = (catalog?.resources ?? []).map((r: RegistryResource) => ({
    resource_code: r.resource_code,
    label_ro: `${r.name} (${r.resource_kind})`,
  }));

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Autorizări operaționale (registry)</h3>
          <p className="text-xs text-slate-400 mt-1">
            Sursă canonicală pentru skills, workcenters și resurse. Nu folosește HR demo (
            <code className="text-[10px]">employeeRecordsData</code>).
          </p>
          {employee && (
            <p className="text-[11px] text-slate-500 mt-1">
              Salariu HR:{" "}
              {employee.salary_amount != null
                ? `${employee.salary_amount.toLocaleString("ro-RO")} ${employee.salary_currency}/lună`
                : "—"}{" "}
              · boundary CostEngine agregat, nu preț per operație.
            </p>
          )}
        </div>
        {!readOnly && (
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => void load()}
              className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded border border-slate-600 text-slate-300 hover:bg-slate-800"
            >
              <RefreshCw className="w-3 h-3" />
              Reîncarcă
            </button>
            <button
              type="button"
              onClick={() => void save()}
              disabled={saving || loading}
              className="inline-flex items-center gap-1 px-3 py-1 text-xs rounded bg-cyan-700 hover:bg-cyan-600 text-white disabled:opacity-50"
            >
              <Save className="w-3 h-3" />
              {saving ? "Salvez…" : "Salvează autorizări"}
            </button>
          </div>
        )}
      </div>

      {loading && <p className="text-xs text-slate-400">Se încarcă registry…</p>}
      {error && (
        <p className="text-xs text-red-300 flex items-center gap-1">
          <AlertTriangle className="w-3 h-3" />
          {error}
        </p>
      )}
      {saved && <p className="text-xs text-emerald-300">Autorizări salvate.</p>}

      {catalog && !loading && (
        <>
          <MultiCheckboxGroup
            title="Competențe (skills)"
            options={catalog.skills.map((s) => ({
              label_ro: s.label_ro,
              skill_code: s.skill_code,
            }))}
            selected={skillCodes}
            onChange={setSkillCodes}
            labelKey="label_ro"
            valueKey="skill_code"
            disabled={readOnly}
          />
          <MultiCheckboxGroup
            title="Workcenters autorizate"
            options={catalog.workcenters.map((w) => ({
              label_ro: w.label_ro,
              workcenter_code: w.workcenter_code,
            }))}
            selected={workcenterCodes}
            onChange={setWorkcenterCodes}
            labelKey="label_ro"
            valueKey="workcenter_code"
            disabled={readOnly}
          />
          <MultiCheckboxGroup
            title="Resurse / utilaje autorizate"
            options={resourceOptions}
            selected={resourceCodes}
            onChange={setResourceCodes}
            labelKey="label_ro"
            valueKey="resource_code"
            disabled={readOnly}
          />
        </>
      )}
    </div>
  );
}
