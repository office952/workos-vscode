/**
 * Read-only Runtime Preview for Product System authoring.
 * Human summary first; technical diagnostics collapsed.
 */

import { useCallback, useEffect, useState } from "react";
import {
  getProductDefinitionPreview,
  type ProductDefinitionPreview,
} from "@/api/productDefinitionPreview";
import { humanTemplateName } from "./productSystemAdminDisplay";

function readinessLabelRo(status: string): string {
  switch (status) {
    case "ready":
      return "Pregătit (preview)";
    case "partial":
      return "Parțial";
    case "blocked":
      return "Blocat";
    default:
      return status;
  }
}

export function TemplateRuntimePreviewPanel({ templateCode }: { templateCode: string }) {
  const [preview, setPreview] = useState<ProductDefinitionPreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [workspaceId, setWorkspaceId] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProductDefinitionPreview(templateCode, workspaceId.trim() || null);
      setPreview(data);
    } catch (e) {
      setPreview(null);
      setError(e instanceof Error ? e.message : "Preview eșuat");
    } finally {
      setLoading(false);
    }
  }, [templateCode, workspaceId]);

  useEffect(() => {
    void load();
  }, [load]);

  const humanName = humanTemplateName(templateCode);

  return (
    <section
      className="space-y-3 rounded-xl border border-slate-800/70 bg-[#0D1321]/50 px-4 py-4"
      data-testid="template-runtime-preview-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Runtime Preview</h3>
          <p className="mt-0.5 text-[11px] text-slate-400">
            <span className="font-medium text-slate-200">{humanName}</span>
            <span className="ml-1.5 font-mono text-[10px] text-slate-500">{templateCode}</span>
          </p>
          <p className="mt-0.5 text-[11px] text-slate-500">
            Read-only ProductDefinition — fără scriere Product Truth. Analiza externă apare doar ca
            provenance, nu ca autoritate.
          </p>
        </div>
        <button
          type="button"
          className="rounded border border-slate-700 px-2 py-1 text-[11px] text-slate-300"
          onClick={() => void load()}
          disabled={loading}
          data-testid="runtime-preview-reload"
        >
          {loading ? "Se încarcă…" : "Reîncarcă"}
        </button>
      </div>

      <label className="flex max-w-md flex-col gap-0.5 text-[11px] text-slate-400">
        Fixture workspace (opțional)
        <input
          className="rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-[11px] text-slate-200"
          value={workspaceId}
          onChange={(e) => setWorkspaceId(e.target.value)}
          placeholder="gol = doar șablon"
          data-testid="runtime-preview-workspace-id"
        />
      </label>

      {error ? (
        <p
          className="rounded border border-rose-800/40 bg-rose-950/20 px-2 py-1.5 text-[11px] text-rose-200"
          data-testid="runtime-preview-error"
        >
          {error}
        </p>
      ) : null}

      {preview ? (
        <div className="space-y-3 text-[12px] text-slate-300" data-testid="runtime-preview-body">
          <div
            className="rounded-lg border border-slate-700/60 bg-slate-950/40 px-3 py-2.5"
            data-testid="runtime-preview-human-summary"
          >
            <p className="text-[12px] font-medium text-slate-100">Rezumat operator</p>
            <dl className="mt-2 grid gap-1.5 sm:grid-cols-2">
              <div>
                <dt className="text-[10px] uppercase text-slate-500">Readiness preview</dt>
                <dd>{readinessLabelRo(preview.validation.readiness_status)}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase text-slate-500">Sursă</dt>
                <dd>
                  {preview.source_context.source_payload_type === "template_only"
                    ? "Doar șablon"
                    : preview.source_context.source_payload_type}
                </dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase text-slate-500">Module active</dt>
                <dd>{preview.selected_modules.length}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase text-slate-500">Componente / materiale / operații</dt>
                <dd>
                  {preview.components.length} / {preview.material_roles.length} /{" "}
                  {preview.operation_roles.length}
                </dd>
              </div>
            </dl>
            {preview.composition?.blockers && preview.composition.blockers.length > 0 ? (
              <p className="mt-2 text-[11px] text-amber-200/90" data-testid="runtime-preview-blockers-summary">
                Blocaje compoziție: {preview.composition.blockers.length}
              </p>
            ) : null}
            {preview.validation.missing_required_fields.length > 0 ? (
              <p className="mt-1 text-[11px] text-amber-200/80">
                Câmpuri lipsă: {preview.validation.missing_required_fields.length}
              </p>
            ) : null}
          </div>

          <details data-testid="runtime-preview-modules">
            <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Modules ({preview.selected_modules.length} selected / {preview.optional_modules.length}{" "}
              optional / {preview.inactive_modules.length} inactive)
            </summary>
            <ul className="mt-1 space-y-1 pl-1 font-mono text-[11px]">
              {preview.selected_modules.slice(0, 12).map((m) => (
                <li key={m.module_code}>
                  {m.module_code} · {m.state}
                </li>
              ))}
            </ul>
          </details>

          <details data-testid="runtime-preview-components">
            <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Components ({preview.components.length})
            </summary>
            <ul className="mt-1 space-y-1 pl-1 text-[11px]">
              {preview.components.slice(0, 16).map((c) => (
                <li key={c.component_id}>
                  <span className="font-mono text-slate-200">{c.component_id}</span>
                  {c.role ? ` · ${c.role}` : ""} · {c.provenance}
                </li>
              ))}
            </ul>
          </details>

          <details data-testid="runtime-preview-materials">
            <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Materials ({preview.material_roles.length})
            </summary>
            <ul className="mt-1 space-y-1 pl-1 font-mono text-[11px]">
              {preview.material_roles.slice(0, 16).map((m) => (
                <li key={`${m.material_code}-${m.component_ref ?? ""}`}>
                  {m.material_code}
                  {m.label ? ` · ${m.label}` : ""}
                </li>
              ))}
            </ul>
          </details>

          <details data-testid="runtime-preview-operations">
            <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Operations ({preview.operation_roles.length})
            </summary>
            <ul className="mt-1 space-y-1 pl-1 font-mono text-[11px]">
              {preview.operation_roles.slice(0, 16).map((op) => (
                <li key={op.operation_code}>
                  {op.operation_code}
                  {op.is_geometry_gate ? " · geometry_gate" : ""}
                </li>
              ))}
            </ul>
          </details>

          <details data-testid="runtime-preview-composition">
            <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Composition graph
            </summary>
            {preview.composition ? (
              <div className="mt-1 space-y-1 text-[11px] text-slate-400">
                <p>
                  mode={preview.composition.composition_mode} · status=
                  {preview.composition.solution_status} · nodes=
                  {preview.composition.nodes.length} · edges={preview.composition.edges.length}
                </p>
                {preview.composition.blockers.length > 0 ? (
                  <p className="text-amber-200/90">
                    blockers: {preview.composition.blockers.join(", ")}
                  </p>
                ) : null}
              </div>
            ) : (
              <p className="mt-1 text-[11px] text-slate-500">Fără composition payload.</p>
            )}
          </details>

          <details data-testid="runtime-preview-provenance">
            <summary className="cursor-pointer text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              Provenance / validation (diagnostic)
            </summary>
            <ul className="mt-1 space-y-1 pl-1 text-[11px] text-slate-500">
              <li className="font-mono">v={preview.preview_version}</li>
              {preview.provenance.slice(0, 12).map((p) => (
                <li key={`${p.key}-${p.source}`}>
                  {p.key}: {p.source} — {p.detail}
                </li>
              ))}
              {preview.validation.missing_required_fields.length > 0 ? (
                <li className="text-amber-200/80">
                  missing: {preview.validation.missing_required_fields.join(", ")}
                </li>
              ) : null}
            </ul>
          </details>
        </div>
      ) : !error && !loading ? (
        <p className="text-sm text-slate-500">Niciun preview.</p>
      ) : null}
    </section>
  );
}
