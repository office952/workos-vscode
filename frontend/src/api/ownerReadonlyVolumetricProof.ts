import { getAPIBaseURL } from "@/lib/config";

export interface OwnerReadonlyVolumetricProof {
  proof_version: string;
  template_code: string;
  workspace_id: string;
  chain_ok: boolean;
  safety: {
    no_write: boolean;
    no_task_materialization: boolean;
    no_new_tasking_system: boolean;
    resolver_is_not_task_engine: boolean;
  };
  intake_selection: {
    mounting_system?: string | null;
    mounting_solution_template?: string | null;
    return_finish_type?: string | null;
    mains_cable_length_m?: number | null;
    power_supply_service_corner?: string | null;
    service_screw_finish?: string | null;
    mounting_template_enabled?: boolean | null;
  };
  product_definition: {
    template_code: string;
    canonical_values: Record<string, unknown>;
    readiness_status?: string | null;
  };
  process_graph: {
    process_graph_source?: string | null;
    process_graph_hash?: string | null;
    process_count: number;
    edge_count: number;
    processes: Array<{ process_code: string; depends_on_process_ids: string[] }>;
  };
  task_rules_projection: {
    authority: string;
    rule_count: number;
    task_names: string[];
    depends_on_preserved: boolean;
  };
  live_materials: {
    wire_supply: {
      present: boolean;
      material_code?: string | null;
      quantity?: number | null;
      quantity_source?: string | null;
      estimated_cost?: number | null;
    };
    cable_channel_commercial_guarded: boolean;
  };
  execution_preview_4c: {
    present: boolean;
    no_write: boolean;
    candidate_count: number;
    process_depends_on_edges: number;
    sequence_fallback_edges: number;
  };
  guards: string[];
  notes: string[];
  verification_path: {
    intake_ui: string;
    product_system_ui: string;
    proof_api: string;
  };
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (body?.detail?.error) return String(body.detail.error);
  } catch {
    // ignore
  }
  return `HTTP ${res.status}`;
}

export async function getOwnerReadonlyVolumetricProof(
  templateCode: string,
  workspaceId: string,
): Promise<OwnerReadonlyVolumetricProof> {
  const qs = new URLSearchParams({ workspace_id: workspaceId });
  const url =
    `${getAPIBaseURL()}/api/v1/product-system/owner-readonly-proof/` +
    `${encodeURIComponent(templateCode)}?${qs.toString()}`;
  const res = await fetch(url, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as OwnerReadonlyVolumetricProof;
}
