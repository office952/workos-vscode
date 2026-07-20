/**
 * Component contract editor — child/dual-role PT used-by map (no CT table).
 */

import { useCallback, useEffect, useState } from "react";
import {
  getComponentContract,
  patchComponentContractLink,
  type ProductTemplateComponentContractView,
} from "@/api/productTemplateComponentContracts";

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
      className="rounded-xl border border-cyan-800/40 bg-cyan-950/10 p-3"
      data-testid="component-contract-used-by-panel"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-cyan-100">Contracte componente</h3>
          <p className="mt-0.5 text-[11px] text-cyan-200/80">
            Child / dual-role Product Template + usage_mode + schema instanță. Fără tabel component_templates.
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
            <span className="rounded border border-cyan-800/50 px-2 py-0.5 text-cyan-100">
              Rol: {view.role}
            </span>
            <span className="rounded border border-slate-700 px-2 py-0.5 text-slate-300">
              no CT table: {view.no_component_templates_table ? "da" : "nu"}
            </span>
          </div>

          <div>
            <h4 className="mb-1 font-medium text-slate-200">Folosit de (used-by)</h4>
            {view.used_by.length === 0 ? (
              <p className="text-slate-500">Niciun părinte activ.</p>
            ) : (
              <ul className="space-y-1" data-testid="component-contract-used-by-list">
                {view.used_by.map((edge) => (
                  <li
                    key={`${edge.parent_template_code}-${edge.link_id ?? "x"}`}
                    className="rounded border border-slate-800 bg-slate-950/40 px-2 py-1.5 text-slate-300"
                  >
                    <div className="font-medium text-slate-100">{edge.parent_template_code}</div>
                    <div className="text-slate-500">
                      {edge.relation_type ?? "—"} · usage_mode={edge.usage_mode ?? "policy"} · schema=
                      {edge.instance_schema_id ?? "—"}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div>
            <h4 className="mb-1 font-medium text-slate-200">Copii / module</h4>
            {view.children.length === 0 ? (
              <p className="text-slate-500">Nicio legătură copil.</p>
            ) : (
              <ul className="space-y-2" data-testid="component-contract-children-list">
                {view.children.map((edge) => {
                  const linkId = edge.link_id;
                  return (
                    <li
                      key={`${edge.module_template_code}-${linkId ?? "x"}`}
                      className="rounded border border-slate-800 bg-slate-950/40 px-2 py-2"
                    >
                      <div className="font-medium text-slate-100">{edge.module_template_code}</div>
                      <p className="mt-0.5 text-slate-500">{edge.policy_reason ?? edge.relation_type ?? ""}</p>
                      {typeof linkId === "number" ? (
                        <div className="mt-2 flex flex-wrap items-end gap-2">
                          <label className="flex flex-col gap-0.5 text-slate-400">
                            usage_mode
                            <input
                              className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-slate-200"
                              defaultValue={edge.usage_mode ?? ""}
                              data-testid={`component-contract-usage-${linkId}`}
                              id={`usage-${linkId}`}
                            />
                          </label>
                          <label className="flex flex-col gap-0.5 text-slate-400">
                            instance_schema_id
                            <input
                              className="rounded border border-slate-700 bg-slate-950 px-2 py-1 text-slate-200"
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

          {view.instance_schema_hints.length > 0 ? (
            <p className="text-slate-500">
              Hint schema: {view.instance_schema_hints.join(", ")}
            </p>
          ) : null}
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
