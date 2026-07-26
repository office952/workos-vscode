/**
 * Component contract editor — child/dual-role PT used-by map (no CT table).
 */

import { useCallback, useEffect, useState } from "react";
import {
  getComponentContract,
  patchComponentContractLink,
  type ProductTemplateComponentContractView,
} from "@/api/productTemplateComponentContracts";
import { humanTemplateName, relationTypeLabelRo } from "./productSystemAdminDisplay";
import {
  MODULE_PRODUS_CODE_LABEL,
  MODULE_PRODUS_LIST_HEADING,
  displayModuleTemplateWireLabel,
} from "./productTemplateModulesVocabulary";
import {
  PS_SURFACE_INPUT,
  PS_SURFACE_PANEL,
  PS_SURFACE_ROW,
} from "./productSystemSurfaces";

export function ComponentContractUsedByPanel({ templateCode }: { templateCode: string }) {
  const [view, setView] = useState<ProductTemplateComponentContractView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);

  const reload = useCallback(async () => {
    setError(null);
    try {
      setView(await getComponentContract(templateCode));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Eroare contract componente");
    }
  }, [templateCode]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const saveEdge = async (linkId: number, usage_mode: string, instance_schema_id: string) => {
    setSavingId(linkId);
    setError(null);
    try {
      await patchComponentContractLink(linkId, { usage_mode, instance_schema_id });
      await reload();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Salvare eșuată");
    } finally {
      setSavingId(null);
    }
  };

  return (
    <section
      className={`${PS_SURFACE_PANEL} p-3`}
      data-testid="component-contract-used-by-panel"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-wo-text-primary">Contracte componente</h3>
          <p className="mt-0.5 text-[11px] text-slate-400">
            <span className="font-medium text-slate-200">{humanTemplateName(templateCode)}</span>
            <span className="ml-1.5 font-mono text-[10px] text-slate-500">{templateCode}</span>
          </p>
          <p className="mt-1 text-[11px] text-slate-500">
            Cine folosește acest șablon și ce copii are — rol + mod utilizare + schema instanță.
          </p>
        </div>
        <button
          type="button"
          className="rounded border border-slate-700 px-2 py-1 text-[11px] text-slate-300"
          onClick={() => void reload()}
        >
          Reîncarcă
        </button>
      </div>

      {view ? (
        <div className="mt-3 space-y-3 text-[11px]" data-testid="component-contract-view">
          <div className="flex flex-wrap gap-2">
            <span className="rounded border border-slate-600/60 px-2 py-0.5 text-slate-200">
              Rol: {view.role}
            </span>
          </div>

          <div>
            <h4 className="mb-1 font-medium text-slate-200">Folosit de</h4>
            {view.used_by.length === 0 ? (
              <p className="text-slate-500">Niciun părinte activ.</p>
            ) : (
              <ul className="space-y-1" data-testid="component-contract-used-by-list">
                {view.used_by.map((edge) => (
                  <li
                    key={`${edge.parent_template_code}-${edge.link_id ?? "x"}`}
                    className={`${PS_SURFACE_ROW} px-2 py-1.5 text-slate-300`}
                  >
                    <div className="font-medium text-wo-text-primary">
                      {humanTemplateName(edge.parent_template_code)}
                    </div>
                    <div className="font-mono text-[10px] text-slate-500">
                      {edge.parent_template_code}
                    </div>
                    <div className="mt-0.5 text-slate-500">
                      {edge.relation_type ? relationTypeLabelRo(edge.relation_type) : "—"}
                      {" · "}
                      {edge.usage_mode ?? "policy"}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <h4 className="mb-1 font-medium text-slate-200">Copii / {MODULE_PRODUS_LIST_HEADING}</h4>
            {view.children.length === 0 ? (
              <p className="text-slate-500">Nicio legătură copil.</p>
            ) : (
              <ul className="space-y-2" data-testid="component-contract-children-list">
                {view.children.map((edge) => {
                  const linkId = edge.link_id;
                  return (
                    <li
                      key={`${edge.module_template_code}-${linkId ?? "x"}`}
                      className={`${PS_SURFACE_ROW} px-2 py-2`}
                    >
                      <div className="font-medium text-wo-text-primary">
                        {humanTemplateName(edge.module_template_code)}
                      </div>
                      <div className="font-mono text-[10px] text-slate-500" title={MODULE_PRODUS_CODE_LABEL}>
                        {edge.module_template_code}
                      </div>
                      <p className="mt-0.5 text-slate-500">
                        {edge.policy_reason ??
                          (edge.relation_type ? relationTypeLabelRo(edge.relation_type) : "")}
                      </p>
                      {typeof linkId === "number" ? (
                        <div className="mt-2 flex flex-wrap items-end gap-2">
                          <label className="flex flex-col gap-0.5 text-slate-400">
                            {displayModuleTemplateWireLabel("usage_mode")}
                            <input
                              className={`${PS_SURFACE_INPUT} px-2 py-1 text-[11px]`}
                              defaultValue={edge.usage_mode ?? ""}
                              data-testid={`component-contract-usage-${linkId}`}
                              id={`usage-${linkId}`}
                            />
                          </label>
                          <label className="flex flex-col gap-0.5 text-slate-400">
                            {displayModuleTemplateWireLabel("instance_schema_id")}
                            <input
                              className={`${PS_SURFACE_INPUT} px-2 py-1 text-[11px]`}
                              defaultValue={edge.instance_schema_id ?? ""}
                              data-testid={`component-contract-schema-${linkId}`}
                              id={`schema-${linkId}`}
                            />
                          </label>
                          <button
                            type="button"
                            disabled={savingId === linkId}
                            className="rounded border border-cyan-800/50 px-2 py-1 text-cyan-100 hover:bg-cyan-950/40 disabled:opacity-40"
                            data-testid={`component-contract-save-${linkId}`}
                            onClick={() => {
                              const usage = (
                                document.getElementById(`usage-${linkId}`) as HTMLInputElement | null
                              )?.value;
                              const schema = (
                                document.getElementById(`schema-${linkId}`) as HTMLInputElement | null
                              )?.value;
                              void saveEdge(linkId, usage ?? "", schema ?? "");
                            }}
                          >
                            Salvează
                          </button>
                        </div>
                      ) : null}
                    </li>
                  );
                })}
              </ul>
            )}
          </div>

          <details className="text-slate-500">
            <summary className="cursor-pointer select-none hover:text-slate-400">
              Diagnostic contract
            </summary>
            <p className="mt-1">
              Fără tabel component_templates:{" "}
              {view.no_component_templates_table ? "da" : "nu"}
            </p>
            {view.instance_schema_hints.length > 0 ? (
              <p className="mt-1">Hint schema: {view.instance_schema_hints.join(", ")}</p>
            ) : null}
          </details>
        </div>
      ) : null}

      {error ? (
        <p className="mt-2 text-[11px] text-rose-300" data-testid="component-contract-error">
          {error}
        </p>
      ) : null}
    </section>
  );
}
