import { useEffect, useState } from "react";
import {
  getOwnerReadonlyVolumetricProof,
  type OwnerReadonlyVolumetricProof,
} from "@/api/ownerReadonlyVolumetricProof";

type Props = {
  templateCode: string;
  workspaceId: string;
};

/**
 * Thin owner read-only proof — assembles existing Aggregate task_rules + live materials + Build 4C.
 * Does not invent tasking, calculate money, or write snapshots.
 */
export function OwnerReadonlyVolumetricProofPanel({ templateCode, workspaceId }: Props) {
  const [proof, setProof] = useState<OwnerReadonlyVolumetricProof | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    void getOwnerReadonlyVolumetricProof(templateCode, workspaceId)
      .then((data) => {
        if (!cancelled) setProof(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Proof unavailable");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [templateCode, workspaceId]);

  return (
    <section
      className="mb-4 rounded border border-cyan-900/50 bg-cyan-950/20 p-3"
      data-testid="owner-readonly-volumetric-proof-panel"
    >
      <div className="mb-2 flex flex-wrap items-center gap-2">
        <h3 className="text-[13px] font-semibold text-cyan-200">
          Owner proof — Product / Price / Tasking (read-only)
        </h3>
        <span className="rounded border border-emerald-700/60 px-1.5 py-0.5 text-[10px] text-emerald-300">
          NO WRITE
        </span>
        <span className="rounded border border-slate-600 px-1.5 py-0.5 text-[10px] text-wo-text-secondary">
          existing task_rules
        </span>
      </div>
      <p className="mb-3 text-[10px] leading-relaxed text-wo-text-muted">
        Intake → ProductDefinition → modular resolver → Aggregate task_rules → live materials → Build 4C
        preview. Resolver is not a task engine.
      </p>

      {loading ? <p className="text-[11px] text-wo-text-muted">Se încarcă proof…</p> : null}
      {error ? (
        <p className="text-[11px] text-amber-200" data-testid="owner-readonly-proof-error">
          {error}
        </p>
      ) : null}

      {proof ? (
        <div className="grid gap-2 text-[11px] text-slate-200 sm:grid-cols-2" data-testid="owner-readonly-proof-body">
          <div className="rounded border border-wo-border-strong bg-wo-surface-inset p-2">
            <p className="mb-1 font-semibold text-wo-text-primary">1. Intake / PD</p>
            <p>cable: {proof.intake_selection.mains_cable_length_m ?? "—"} m</p>
            <p>cant: {proof.intake_selection.return_finish_type ?? "—"}</p>
            <p>support tpl: {proof.intake_selection.mounting_solution_template ?? "—"}</p>
            <p className="mt-1 text-[10px] text-slate-500">
              PD keys: {Object.keys(proof.product_definition.canonical_values).join(", ") || "—"}
            </p>
          </div>
          <div className="rounded border border-wo-border-strong bg-wo-surface-inset p-2">
            <p className="mb-1 font-semibold text-wo-text-primary">2. Process → task_rules</p>
            <p>source: {proof.process_graph.process_graph_source ?? "—"}</p>
            <p>
              processes: {proof.process_graph.process_count} · edges: {proof.process_graph.edge_count}
            </p>
            <p>rules: {proof.task_rules_projection.rule_count}</p>
            <p className="mt-1 max-h-16 overflow-auto text-[10px] text-wo-text-muted">
              {proof.task_rules_projection.task_names.slice(0, 10).join(" → ")}
              {proof.task_rules_projection.task_names.length > 10 ? " …" : ""}
            </p>
          </div>
          <div className="rounded border border-wo-border-strong bg-wo-surface-inset p-2">
            <p className="mb-1 font-semibold text-wo-text-primary">3. Live materials</p>
            <p>
              wire_supply qty: {proof.live_materials.wire_supply.quantity ?? "—"}{" "}
              ({proof.live_materials.wire_supply.quantity_source ?? "—"})
            </p>
            <p>material: {proof.live_materials.wire_supply.material_code ?? "—"}</p>
            <p>
              canal cablu:{" "}
              {proof.live_materials.cable_channel_commercial_guarded ? "GUARDED" : "n/a"}
            </p>
          </div>
          <div className="rounded border border-wo-border-strong bg-wo-surface-inset p-2">
            <p className="mb-1 font-semibold text-wo-text-primary">4. Build 4C preview</p>
            <p>candidates: {proof.execution_preview_4c.candidate_count}</p>
            <p>process edges: {proof.execution_preview_4c.process_depends_on_edges}</p>
            <p>sequence fallback: {proof.execution_preview_4c.sequence_fallback_edges}</p>
            <p>no_write: {String(proof.execution_preview_4c.no_write)}</p>
          </div>
          <div className="sm:col-span-2 rounded border border-wo-border-strong bg-wo-surface-inset p-2">
            <p className="mb-1 font-semibold text-wo-text-primary">
              Chain: {proof.chain_ok ? "OK" : "WITH GUARDS"}
            </p>
            {proof.guards.length > 0 ? (
              <p className="text-[10px] text-amber-200/90">guards: {proof.guards.join(" · ")}</p>
            ) : (
              <p className="text-[10px] text-slate-500">no guards</p>
            )}
            <p className="mt-1 text-[10px] text-slate-500">
              Intake:{" "}
              <a className="text-cyan-300 underline" href={proof.verification_path.intake_ui}>
                operator workspace
              </a>
            </p>
          </div>
        </div>
      ) : null}
    </section>
  );
}
