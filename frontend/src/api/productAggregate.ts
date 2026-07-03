import { getAPIBaseURL } from "@/lib/config";

export type ProductAggregateProvenance =
  | "parent"
  | "dossier"
  | "linked_module"
  | "derived"
  | "registry"
  | "missing"
  | "conflict";

export type ProductAggregateSeverity = "info" | "warning" | "error";

export interface ProductAggregateMaterial {
  material_code: string;
  label?: string | null;
  unit?: string | null;
  component_ref?: string | null;
  formula_id?: string | null;
  provenance: ProductAggregateProvenance;
  source_template_code?: string | null;
  mini_module_code?: string | null;
  status?: string;
}

export interface ProductAggregateOperation {
  operation_code: string;
  label?: string | null;
  workcenter?: string | null;
  component_ref?: string | null;
  formula_id?: string | null;
  priced?: boolean;
  provenance: ProductAggregateProvenance;
  source_template_code?: string | null;
  mini_module_code?: string | null;
  status?: string;
}

export interface ProductAggregateComponent {
  component_id: string;
  label_ro?: string | null;
  role?: string | null;
  mini_module_code?: string | null;
  provenance: ProductAggregateProvenance;
  source_template_code?: string | null;
  materials?: ProductAggregateMaterial[];
  operations?: ProductAggregateOperation[];
  status?: string;
}

export interface ProductAggregateModule {
  module_code: string;
  business_name_ro?: string | null;
  child_template_code: string;
  child_template_id?: number | null;
  relation_type: string;
  trigger_field?: string | null;
  trigger_value?: unknown;
  pricing_mode?: string | null;
  execution_mode?: string | null;
  provenance?: ProductAggregateProvenance;
  active?: boolean;
  notes?: string | null;
}

export interface ProductAggregateModules {
  required: ProductAggregateModule[];
  optional: ProductAggregateModule[];
}

export interface ProductAggregateConflict {
  code: string;
  severity: ProductAggregateSeverity;
  message: string;
  field?: string | null;
  details?: Record<string, unknown>;
}

export interface ProductAggregateProvenanceSummary {
  parent?: Record<string, number>;
  dossier?: Record<string, number>;
  linked_modules?: Record<string, number>;
  aggregate_totals?: Record<string, number>;
}

export interface ProductAggregate {
  aggregate_version: string;
  template_code: string;
  template_id: number;
  family_id?: string | null;
  family_name?: string | null;
  status: string;
  business_name_ro?: string | null;
  source_layers?: string[];
  modules: ProductAggregateModules;
  components: ProductAggregateComponent[];
  materials: ProductAggregateMaterial[];
  operations: ProductAggregateOperation[];
  conflicts: ProductAggregateConflict[];
  warnings: ProductAggregateConflict[];
  provenance_summary: ProductAggregateProvenanceSummary;
}

export class ProductAggregateNotFoundError extends Error {
  constructor(templateCode: string) {
    super(`ProductAggregate not found for ${templateCode}`);
    this.name = "ProductAggregateNotFoundError";
  }
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (body?.detail && typeof body.detail === "object" && typeof body.detail.error === "string") {
      return body.detail.error;
    }
    if (typeof body?.message === "string") return body.message;
  } catch {
    // ignore
  }
  return `HTTP ${res.status}`;
}

export async function getProductAggregate(templateCode: string): Promise<ProductAggregate> {
  const encoded = encodeURIComponent(templateCode);
  const res = await fetch(`${getAPIBaseURL()}/api/v1/product-system/aggregate/${encoded}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  if (res.status === 404) {
    throw new ProductAggregateNotFoundError(templateCode);
  }

  if (!res.ok) {
    throw new Error(await parseErrorBody(res));
  }

  return (await res.json()) as ProductAggregate;
}
