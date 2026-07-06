import { getAPIBaseURL } from "@/lib/config";

export type ProductDefinitionReadinessStatus = "ready" | "partial" | "blocked";

export interface ProductDefinitionModuleRef {
  module_code: string;
  module_name: string;
  activation_kind: string;
  state: string;
  activation_reason?: string | null;
  missing_fields: string[];
}

export interface ProductDefinitionComponentRole {
  component_id: string;
  label_ro?: string | null;
  role?: string | null;
  mini_module_code?: string | null;
  module_active: boolean;
  provenance: string;
  source_template_code?: string | null;
}

export interface ProductDefinitionMaterialRole {
  material_code: string;
  label?: string | null;
  unit?: string | null;
  component_ref?: string | null;
  mini_module_code?: string | null;
  module_active: boolean;
  provenance: string;
}

export interface ProductDefinitionOperationRole {
  operation_code: string;
  label?: string | null;
  workcenter?: string | null;
  component_ref?: string | null;
  mini_module_code?: string | null;
  module_active: boolean;
  is_geometry_gate: boolean;
  is_priced: boolean;
  provenance: string;
}

export interface ProductDefinitionLinkedRuntimeSegmentReadiness {
  ready_for_pricing?: boolean;
  ready_for_quote?: boolean;
  ready_for_order?: boolean;
  ready_for_execution?: boolean;
}

export interface ProductDefinitionLinkedRuntimeSegment {
  segment_key: string;
  parent_root_template_code: string;
  owning_template_code: string;
  composition_role: string;
  binding_status: string;
  product_truth_readiness?: ProductDefinitionLinkedRuntimeSegmentReadiness | null;
}

export interface ProductDefinitionLinkedRuntimeSegmentsSummary {
  root_template_code: string;
  composition_mode?: string;
  segments: ProductDefinitionLinkedRuntimeSegment[];
}

export interface ProductDefinitionPreview {
  preview_version: string;
  template_code: string;
  business_name_ro?: string | null;
  source_context: {
    template_code: string;
    workspace_id?: string | null;
    quote_id?: string | null;
    source_payload_type: "template_only" | "workspace_payload";
  };
  selected_modules: ProductDefinitionModuleRef[];
  optional_modules: ProductDefinitionModuleRef[];
  inactive_modules: ProductDefinitionModuleRef[];
  components: ProductDefinitionComponentRole[];
  material_roles: ProductDefinitionMaterialRole[];
  operation_roles: ProductDefinitionOperationRole[];
  linked_template_runtime_segments?: ProductDefinitionLinkedRuntimeSegmentsSummary | null;
  canonical_values: Record<string, unknown>;
  geometry_inputs: Record<string, unknown>;
  validation: {
    readiness_status: ProductDefinitionReadinessStatus;
    missing_required_fields: string[];
    invalid_combinations: string[];
    unresolved_warnings: string[];
  };
  provenance: Array<{ key: string; source: string; detail: string }>;
  resource_hints?: {
    scope: "future_resource_hint";
    pricing_source: string[];
    inventory_source: string[];
    required_machine_type: string[];
    required_employee_roles: string[];
    employee_availability_dependency: string[];
    attendance_capacity_dependency: string[];
    subcontractable: string[];
    external_partner_fallback: string[];
    machine_failure_fallback: string[];
    execution_routing_notes: string[];
  } | null;
  warnings: string[];
  notes: string[];
}

export class ProductDefinitionPreviewNotFoundError extends Error {
  constructor(public templateCode: string) {
    super(`ProductDefinition preview not found for ${templateCode}`);
    this.name = "ProductDefinitionPreviewNotFoundError";
  }
}

export async function getProductDefinitionPreview(
  templateCode: string,
  workspaceId?: string | null
): Promise<ProductDefinitionPreview> {
  const params = new URLSearchParams();
  if (workspaceId?.trim()) {
    params.set("workspace_id", workspaceId.trim());
  }
  const qs = params.toString();
  const url = `${getAPIBaseURL()}/api/v1/product-system/product-definition/${encodeURIComponent(templateCode)}${qs ? `?${qs}` : ""}`;
  const response = await fetch(url, { credentials: "include" });
  if (response.status === 404) {
    throw new ProductDefinitionPreviewNotFoundError(templateCode);
  }
  if (!response.ok) {
    const raw = await response.text();
    throw new Error(raw || `ProductDefinition preview failed (${response.status})`);
  }
  return response.json() as Promise<ProductDefinitionPreview>;
}
