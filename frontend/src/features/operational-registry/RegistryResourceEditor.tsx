import { useCallback, useEffect, useMemo, useState } from "react";
import {
  operationalRegistryApi,
  type OperationalCatalog,
  type RegistryResource,
} from "@/api/operationalRegistry";
import { Save, RefreshCw, AlertTriangle, Database } from "lucide-react";
import { chromeBanner } from "@/components/workos/design-system";

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
    <div
      className="rounded-lg border border-wo-border-strong bg-wo-surface-raised p-4 space-y-3"
      data-testid="registry-resource-editor"
    >
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-wo-success shrink-0" />
          <h4 className="text-[13px] font-bold text-wo-text-primary">Registry manual (control)</h4>
        </div>
        <button
          type="button"
          onClick={() => void load()}
          className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded-md border border-wo-border-strong bg-wo-surface-inset text-wo-text-secondary hover:bg-wo-hover transition-colors"
        >
          <RefreshCw className="w-3 h-3" />
          Reîncarcă
        </button>
      </div>

      {loading && <p className="text-[11px] text-wo-text-muted">Se încarcă…</p>}
      {error && (
        <p className={`text-[11px] flex items-center gap-1 rounded-md px-2 py-1.5 ${chromeBanner.error}`}>
          <AlertTriangle className="w-3 h-3 shrink-0" />
          {error}
        </p>
      )}
      {saved && (
        <p className={`text-[11px] rounded-md px-2 py-1.5 ${chromeBanner.success}`}>
          capacity_metadata salvat (merge non-destructiv).
        </p>
      )}

      {resource && !loading && (
        <>
          <dl className="grid grid-cols-2 gap-3 text-[11px]">
            <div>
              <dt className="text-[10px] font-bold uppercase tracking-wide text-wo-text-primary mb-0.5">
                Cod
              </dt>
              <dd className="font-mono text-[12px] text-wo-text-primary">{resource.resource_code}</dd>
            </div>
            <div>
              <dt className="text-[10px] font-bold uppercase tracking-wide text-wo-text-primary mb-0.5">
                Tip
              </dt>
              <dd className="text-[12px] text-wo-text-primary">{resource.resource_kind}</dd>
            </div>
            <div>
              <dt className="text-[10px] font-bold uppercase tracking-wide text-wo-text-primary mb-0.5">
                Workcenter
              </dt>
              <dd className="text-[12px] text-wo-text-primary">{workcenterLabel}</dd>
            </div>
            <div>
              <dt className="text-[10px] font-bold uppercase tracking-wide text-wo-text-primary mb-0.5">
                Status
              </dt>
              <dd className="text-[12px] text-wo-text-primary">{resource.operational_status}</dd>
            </div>
          </dl>
          <label className="block space-y-1.5">
            <span className="text-[10px] font-bold uppercase tracking-wide text-wo-text-primary">
              capacity_metadata (JSON)
            </span>
            <textarea
              value={metadataJson}
              onChange={(e) => setMetadataJson(e.target.value)}
              rows={8}
              spellCheck={false}
              className="w-full font-mono text-[11px] rounded-md border border-wo-border-strong bg-wo-surface-inset text-wo-text-primary placeholder:text-wo-text-dim p-2.5 outline-none focus:border-wo-info/50 focus:ring-1 focus:ring-[hsl(var(--wo-focus-ring))]"
            />
          </label>
          <button
            type="button"
            onClick={() => void saveMetadata()}
            disabled={saving}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-[11px] font-semibold rounded-md border border-wo-success/40 bg-wo-success-muted text-wo-success hover:bg-wo-hover disabled:opacity-50 transition-colors"
          >
            <Save className="w-3 h-3" />
            Salvează metadata
          </button>
        </>
      )}
    </div>
  );
}
