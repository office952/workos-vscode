import { getAPIBaseURL } from "@/lib/config";

export type CostBomStatus = "ready" | "partial" | "blocked";
export type ParityStatus = "aligned" | "partial" | "blocked";

export interface CostBomModuleRef {
  module_code: string;
  module_name?: string | null;
  state: string;
  included_in_cost_bom: boolean;
  exclusion_reason?: string | null;
}

export interface CostBomPricingBlocker {
  blocker_code: string;
  item_type: string;
  code: string;
  reason: string;
  module_code?: string | null;
}

export interface CostBomSkippedItem {
  item_type: string;
  item_key: string;
  reason: string;
  detail: string;
}

export interface ExternalizationRequirement {
  code: string;
  label: string;
  selected_now: boolean;
  production_mode: string;
  creates_external_task_now: boolean;
}

export interface CostBomPreview {
  preview_version: string;
  template_code: string;
  bom_status: CostBomStatus;
  production_mode: string;
  source_context: {
    template_code: string;
    workspace_id?: string | null;
    uses_parent_bom_as_structural_truth: boolean;
    legacy_parent_bom_note?: string | null;
  };
  active_modules: CostBomModuleRef[];
  inactive_modules: CostBomModuleRef[];
  costable_components: unknown[];
  costable_materials: unknown[];
  costable_operations: unknown[];
  skipped_items: CostBomSkippedItem[];
  missing_pricing: Array<{ item_type: string; code: string; reason: string }>;
  missing_geometry: string[];
  pricing_blockers: CostBomPricingBlocker[];
  missing_inventory_materials: string[];
  unused_inventory_candidates: string[];
  legacy_inventory_references: string[];
  externalization_requirements: ExternalizationRequirement[];
  reseller_requirements: unknown[];
  warnings: string[];
  notes: string[];
}

export class CostBomPreviewNotFoundError extends Error {
  constructor(public templateCode: string) {
    super(`Cost BOM preview not found for ${templateCode}`);
    this.name = "CostBomPreviewNotFoundError";
  }
}

const VOLUMETRIC_V2 = "TPL-VOLUMETRIC-LETTERS_v2";

export function isVolumetricAggregateTemplate(templateCode: string): boolean {
  return templateCode.trim() === VOLUMETRIC_V2;
}

export function deriveCostPreviewSource(templateCode: string): string {
  return isVolumetricAggregateTemplate(templateCode) ? "v2_aggregate" : "legacy_or_other";
}

export function deriveAggregateCostSource(preview: CostBomPreview): boolean {
  return !preview.source_context.uses_parent_bom_as_structural_truth;
}

export function deriveParityStatus(preview: CostBomPreview): ParityStatus {
  if (preview.bom_status === "blocked" || preview.pricing_blockers.length > 0) {
    return preview.bom_status === "blocked" ? "blocked" : "partial";
  }
  if (preview.bom_status === "partial" || preview.missing_geometry.length > 0) {
    return "partial";
  }
  return "aligned";
}

export async function getCostBomPreview(
  templateCode: string,
  workspaceId?: string | null,
): Promise<CostBomPreview> {
  const params = new URLSearchParams();
  if (workspaceId?.trim()) {
    params.set("workspace_id", workspaceId.trim());
  }
  const qs = params.toString();
  const url = `${getAPIBaseURL()}/api/v1/product-system/cost-bom-preview/${encodeURIComponent(templateCode)}${qs ? `?${qs}` : ""}`;
  const response = await fetch(url, { credentials: "include" });
  if (response.status === 404) {
    throw new CostBomPreviewNotFoundError(templateCode);
  }
  if (!response.ok) {
    const raw = await response.text();
    throw new Error(raw || `Cost BOM preview failed (${response.status})`);
  }
  return response.json() as Promise<CostBomPreview>;
}
