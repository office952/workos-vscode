import { getAPIBaseURL } from "@/lib/config";

export interface ProfitabilityActualReadModel {
  status: string;
  order_id: number;
  model_version: string;
  commercial_truth: Record<string, unknown>;
  estimated_internal_truth: Record<string, unknown>;
  actual_operational_truth: Record<string, unknown>;
  actual_cost_truth: Record<string, unknown>;
  profitability_result: Record<string, unknown>;
  access: Record<string, unknown>;
  mutated: Record<string, unknown>;
}

export async function getProfitabilityActualReadModel(
  orderId: number,
): Promise<ProfitabilityActualReadModel> {
  const response = await fetch(
    `${getAPIBaseURL()}/api/v1/profitability-actual/order/${orderId}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const detail = await response.json();
      if (detail?.detail?.error) message = String(detail.detail.error);
    } catch {
      // ignore
    }
    throw new Error(message);
  }
  return response.json();
}
