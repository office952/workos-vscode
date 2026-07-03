import { getAPIBaseURL } from "@/lib/config";

export type ReadinessStatus = "ready" | "needs_review" | "blocked" | "draft" | "deprecated";

export interface ReadinessSection {
  status: ReadinessStatus;
  blockers: string[];
  warnings: string[];
}

export interface ReadinessPolicy {
  authority: "backend";
  compute_mode: "read_only";
  quote_gate: "enforced";
  order_snapshot: "quote_snapshot_frozen";
  requires_warning_acknowledgement?: boolean;
}

export interface ProductReadinessDto {
  entity_type: "blueprint";
  entity_id: string;
  blueprint_id: string;
  overall_status: ReadinessStatus;
  ready_for_quote: boolean;
  technical_readiness: ReadinessSection;
  costengine_readiness: ReadinessSection;
  document_output_readiness: ReadinessSection;
  visual_prompt_readiness: ReadinessSection;
  execution_preparation_readiness: ReadinessSection;
  policy: ReadinessPolicy;
  source: "backend";
  contract_version: string;
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (typeof body?.message === "string") return body.message;
  } catch {
    // ignore parse errors
  }
  return `HTTP ${res.status}`;
}

export async function getProductReadiness(templateId: number | string): Promise<ProductReadinessDto> {
  const encodedId = encodeURIComponent(String(templateId));
  const res = await fetch(`${getAPIBaseURL()}/api/v1/product-readiness/blueprints/${encodedId}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });

  if (!res.ok) {
    throw new Error(await parseErrorBody(res));
  }

  return (await res.json()) as ProductReadinessDto;
}
