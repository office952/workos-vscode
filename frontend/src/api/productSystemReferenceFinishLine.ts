/**
 * PRODUCT_SYSTEM_REFERENCE_FINISH_LINE_V1 — frozen reference contracts.
 */

import { getAPIBaseURL } from "@/lib/config";
import { formatApiErrorResponse } from "@/lib/apiError";

export interface FinishLineContractResponse {
  contract_version: string;
  finish_line_name: string;
  modularity_verdict: string;
  form_system_verdict: string;
  scalability_verdict: string;
  authoring_decision: string;
  overall_verdict: string;
  warnings: string[];
  production_cost_boundary: Record<string, unknown>;
  form_field_map_summary: Record<string, unknown>;
  critical_materials_summary: Record<string, unknown>;
  modularity: Record<string, unknown>;
}

export async function fetchReferenceFinishLineContract(): Promise<FinishLineContractResponse> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/product-system/reference-finish-line/contract`,
    { credentials: "include", headers: { "Content-Type": "application/json" } },
  );
  if (!res.ok) {
    const detail = await formatApiErrorResponse(
      res,
      `reference finish line failed: HTTP ${res.status}`,
    );
    throw new Error(detail);
  }
  return (await res.json()) as FinishLineContractResponse;
}
