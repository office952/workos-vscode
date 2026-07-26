/**
 * Composition authoring — product_template_module_links.
 * Soft-remove via active=false (no DELETE). Never auto-activates Aluminiu.
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  productTemplateModuleLinksApi,
  type ProductTemplateModuleLinkEntity,
} from "@/api/productTemplateModuleLinks";
import { patchComponentContractLink } from "@/api/productTemplateComponentContracts";
import { humanTemplateName, relationTypeLabelRo } from "./productSystemAdminDisplay";
import { displayModuleTemplateWireLabel } from "./productTemplateModulesVocabulary";
import {
  PS_SURFACE_INPUT,
  PS_SURFACE_PANEL,
  PS_SURFACE_ROW,
} from "./productSystemSurfaces";

const RELATION_OPTIONS = [
  "required_child",
  "optional_addon",
  "conditional_child",
  "composition_link",
] as const;

export function TemplateCompositionAuthoringPanel({
  parentTemplateCode,
  parentTemplateId,
}: {
  parentTemplateCode: string;
  parentTemplateId: number;
}) {
  const [links, setLinks] = useState<ProductTemplateModuleLinkEntity[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [showInactive, setShowInactive] = useState(true);

  const reload = useCallback(async () => {
    setError(null);
    try {
      const res = await productTemplateModuleLinksApi.list({
        query: { parent_template_code: parentTemplateCode },
        sort: "id",
        limit: 500,
      });
      setLinks(res.items ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Nu s-au putut încărca legăturile");
    }
  }, [parentTemplateCode]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const visible = useMemo(
    () => (showInactive ? links : links.filter((l) => l.active)),
    [links, showInactive],
  );

  const updateLink = async (id: number, patch: Parameters<typeof productTemplateModuleLinksApi.update>[1]) => {
    setBusyId(id);
    setError(null);
    try {
      await productTemplateModuleLinksApi.update(id, patch);
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Actualizare eșuată");
    } finally {
      setBusyId(null);
    }
  };

  const saveContractEdge = async (id: number, usage_mode: string, instance_schema_id: string) => {
    setBusyId(id);
    setError(null);
    try {
      await patchComponentContractLink(id, { usage_mode, instance_schema_id });
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Salvare contract eșuată");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section
      className={`space-y-3 ${PS_SURFACE_PANEL} px-4 py-4`}
      data-testid="template-composition-authoring-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-slate-100">Compoziție</h3>
          <p className="mt-0.5 text-[11px] text-slate-400">
            <span className="font-medium text-slate-200">{humanTemplateName(parentTemplateCode)}</span>
            <span className="ml-1.5 font-mono text-[10px] text-slate-500">{parentTemplateCode}</span>
          </p>
          <p className="mt-0.5 text-[10px] text-slate-500">
            {displayModuleTemplateWireLabel("product_template_module_links")}
          </p>
          <p className="mt-1 text-[11px] text-slate-500">
            Editează roluri și includerea soft. Aluminiu inactiv rămâne blocker real — nu se
            auto-activează.
          </p>
          <p
            className="mt-2 rounded border border-amber-800/40 bg-amber-950/20 px-2 py-1.5 text-[11px] text-amber-100/90"
            data-testid="composition-authoring-lab-limitation"
          >
            Limitare laborator (finish line Option 2): panoul actualizează legături existente.
            Adăugarea unui child nou se face via API/seed — fără Template Factory în acest build.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => setShowInactive(e.target.checked)}
              data-testid="composition-show-inactive"
            />
            Include inactive
          </label>
          <button
            type="button"
            className="rounded border border-slate-700 px-2 py-1 text-[11px] text-slate-300"
            onClick={() => void reload()}
            data-testid="composition-reload"
          >
            Reîncarcă
          </button>
        </div>
      </div>

      {error ? (
        <p className="rounded border border-rose-800/40 bg-rose-950/20 px-2 py-1.5 text-[11px] text-rose-200" data-testid="composition-error">
          {error}
        </p>
      ) : null}

      {visible.length === 0 ? (
        <p className="text-sm text-slate-500" data-testid="composition-empty">
          Nicio legătură de compoziție pentru acest șablon.
        </p>
      ) : (
        <ul className="space-y-2" data-testid="composition-link-list">
          {visible.map((link, index) => (
            <li
              key={link.id}
              className={`${PS_SURFACE_ROW} px-3 py-2.5`}
              data-testid={`composition-link-${link.id}`}
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <div>
                  <p className="text-xs font-medium text-slate-100">
                    {humanTemplateName(link.module_template_code)}
                  </p>
                  <p className="font-mono text-[10px] text-slate-500">{link.module_template_code}</p>
                </div>
                <span
                  className={`rounded border px-1.5 py-0.5 text-[10px] font-semibold ${
                    link.active
                      ? "border-emerald-800/50 text-emerald-200"
                      : "border-slate-700 text-slate-500"
                  }`}
                >
                  {link.active ? "inclus" : "eliminat soft"}
                </span>
              </div>

              <div className="mt-2 grid gap-2 sm:grid-cols-2">
                <label className="flex flex-col gap-0.5 text-[10px] text-slate-400">
                  Rol
                  <select
                    className={`${PS_SURFACE_INPUT} px-2 py-1 text-[11px]`}
                    defaultValue={link.relation_type}
                    disabled={busyId === link.id}
                    data-testid={`composition-relation-${link.id}`}
                    onChange={(e) => void updateLink(link.id, { relation_type: e.target.value })}
                  >
                    {[link.relation_type, ...RELATION_OPTIONS.filter((r) => r !== link.relation_type)].map(
                      (opt) => (
                        <option key={opt} value={opt}>
                          {relationTypeLabelRo(opt)}
                        </option>
                      ),
                    )}
                  </select>
                </label>
                <label className="flex flex-col gap-0.5 text-[10px] text-slate-400">
                  Includere (soft)
                  <select
                    className={`${PS_SURFACE_INPUT} px-2 py-1 text-[11px]`}
                    value={link.active ? "included" : "removed"}
                    disabled={busyId === link.id}
                    data-testid={`composition-active-${link.id}`}
                    onChange={(e) =>
                      void updateLink(link.id, { active: e.target.value === "included" })
                    }
                  >
                    <option value="included">inclus</option>
                    <option value="removed">eliminat soft</option>
                  </select>
                </label>
              </div>

              <details className="mt-2">
                <summary className="cursor-pointer text-[10px] text-slate-500 hover:text-slate-400">
                  Contract instanță · diagnostic #{index + 1}
                </summary>
                <div className="mt-2 flex flex-wrap items-end gap-2">
                  <label className="flex flex-col gap-0.5 text-[10px] text-slate-400">
                    Mod utilizare
                    <input
                      className={`${PS_SURFACE_INPUT} px-2 py-1 text-[11px]`}
                      defaultValue={link.usage_mode ?? ""}
                      id={`comp-usage-${link.id}`}
                      data-testid={`composition-usage-${link.id}`}
                    />
                  </label>
                  <label className="flex flex-col gap-0.5 text-[10px] text-slate-400">
                    Schema instanță (inputuri geometrie)
                    <input
                      className={`min-w-[12rem] ${PS_SURFACE_INPUT} px-2 py-1 text-[11px]`}
                      defaultValue={link.instance_schema_id ?? ""}
                      id={`comp-schema-${link.id}`}
                      data-testid={`composition-schema-${link.id}`}
                    />
                  </label>
                  <button
                    type="button"
                    className="rounded border border-cyan-800/50 bg-cyan-950/30 px-2 py-1 text-[11px] font-semibold text-cyan-100 disabled:opacity-50"
                    disabled={busyId === link.id}
                    data-testid={`composition-save-contract-${link.id}`}
                    onClick={() => {
                      const usage =
                        (document.getElementById(`comp-usage-${link.id}`) as HTMLInputElement | null)
                          ?.value ?? "";
                      const schema =
                        (document.getElementById(`comp-schema-${link.id}`) as HTMLInputElement | null)
                          ?.value ?? "";
                      void saveContractEdge(link.id, usage, schema);
                    }}
                  >
                    Salvează contract
                  </button>
                </div>
                <p className="mt-1.5 font-mono text-[10px] text-slate-600">
                  link #{link.id} · parent #{parentTemplateId} · pricing={link.pricing_mode} ·
                  execution={link.execution_mode} · trigger={link.trigger_field}
                </p>
              </details>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
