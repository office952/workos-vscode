/**
 * PRODUCT_SYSTEM_REFERENCE_COMPLETE — laboratory closure read-model.
 */

import { getAPIBaseURL } from "@/lib/config";
import { formatApiErrorResponse } from "@/lib/apiError";

export interface ReferenceCompleteResponse {
  contract_version: string;
  name: string;
  overall_verdict: "PASS" | "NOT_COMPLETE";
  freeze_readiness: "READY_FOR_DOCUMENTATION_HANDOFF" | "NOT_READY";
  executive_truth_ro: string;
  live_proof: Record<string, unknown>;
  warnings: string[];
  completion_matrix: Array<{
    axis: string;
    required_verdict: string;
    actual_verdict: string;
    complete: string;
    limitation?: string | null;
  }>;
  accepted_limitations: Array<{ id: string; text_ro: string; class: string }>;
}

export async function fetchProductSystemReferenceComplete(): Promise<ReferenceCompleteResponse> {
  const res = await fetch(`${getAPIBaseURL()}/api/v1/product-system/reference-complete`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    throw new Error(
      await formatApiErrorResponse(res, `reference-complete failed: HTTP ${res.status}`),
    );
  }
  return (await res.json()) as ReferenceCompleteResponse;
}
