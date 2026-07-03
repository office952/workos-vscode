import { useCallback, useEffect, useMemo, useState } from "react";
import {
  operationalRegistryApi,
  type OperationalCatalog,
  type RegistryResource,
} from "@/api/operationalRegistry";
import { Save, RefreshCw, AlertTriangle, Database } from "lucide-react";

interface Props {
  resourceCode: string | null;
}

export function RegistryResourceEditor({ resourceCode }: Props) {
  const [catalog, setCatalog] = useState<OperationalCatalog | null>(null);
  const [resource, setResource] = useState<RegistryResource | null>(null);
  const [metadataJson, setMetadataJson] = useState("{}");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    if (!resourceCode) return;
    setLoading(true);
    setError(null);
    try {
      const [cat, res] = await Promise.all([
        operationalRegistryApi.getCatalog(),
        operationalRegistryApi.getResource(resourceCode),
      ]);
      setCatalog(cat);
      setResource(res);
      setMetadataJson(JSON.stringify(res.capacity_metadata ?? {}, null, 2));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare resursă registry");
    } finally {
      setLoading(false);
    }
  }, [resourceCode]);

  useEffect(() => {
    void load();
  }, [load]);

  const workcenterLabel = useMemo(() => {
    if (!resource || !catalog) return resource?.workcenter_code ?? "—";
    return (
      catalog.workcenters.find((w) => w.workcenter_code === resource.workcenter_code)
        ?.label_ro ?? resource.workcenter_code
    );
  }, [resource, catalog]);

  const saveMetadata = async () => {
    if (!resource) return;
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const parsed = JSON.parse(metadataJson) as Record<string, unknown>;
      await operationalRegistryApi.upsertResource({
        machine_code: resource.resource_code,
        name: resource.name,
        machine_type: resource.machine_type,
        resource_kind: resource.resource_kind,
        workcenter_code: resource.workcenter_code,
        description: resource.description,
        operational_status: resource.operational_status,
        is_available: resource.is_available,
        is_active: resource.is_active,
        capabilities: resource.capabilities,
        capacity_metadata: parsed,
      });
      setSaved(true);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "JSON invalid sau eroare salvare");
    } finally {
      setSaving(false);
    }
  };

  if (!resourceCode) return null;

  return (
    <div className="rounded-lg border border-emerald-800/40 bg-emerald-950/10 p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-emerald-400" />
          <h4 className="text-sm font-semibold text-emerald-100">Registry resursă (canonical)</h4>
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
      {saved && <p className="text-xs text-emerald-300">capacity_metadata salvat (merge non-destructiv).</p>}

      {resource && !loading && (
        <>
          <dl className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <dt className="text-slate-500">Cod</dt>
              <dd className="font-mono text-slate-200">{resource.resource_code}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Tip</dt>
              <dd className="text-slate-200">{resource.resource_kind}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Workcenter</dt>
              <dd className="text-slate-200">{workcenterLabel}</dd>
            </div>
            <div>
              <dt className="text-slate-500">Status</dt>
              <dd className="text-slate-200">{resource.operational_status}</dd>
            </div>
          </dl>
          <label className="block space-y-1">
            <span className="text-xs font-semibold text-slate-300">capacity_metadata (JSON)</span>
            <textarea
              value={metadataJson}
              onChange={(e) => setMetadataJson(e.target.value)}
              rows={8}
              className="w-full font-mono text-xs rounded border border-slate-700 bg-slate-950 text-slate-200 p-2"
            />
          </label>
          <button
            type="button"
            onClick={() => void saveMetadata()}
            disabled={saving}
            className="inline-flex items-center gap-1 px-3 py-1.5 text-xs rounded bg-emerald-700 hover:bg-emerald-600 text-white disabled:opacity-50"
          >
            <Save className="w-3 h-3" />
            Salvează metadata
          </button>
        </>
      )}
    </div>
  );
}
