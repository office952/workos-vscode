/**
 * Execution job closure API — F3/F4 backend contracts.
 * UI must not invent readiness or margin; it only displays backend facts.
 */
import { getAPIBaseURL } from "@/lib/config";

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as { detail?: { error?: string } | string };
    if (typeof body.detail === "string") return body.detail;
    if (body.detail && typeof body.detail === "object" && body.detail.error) {
      return String(body.detail.error);
    }
  } catch {
    /* ignore */
  }
  return `http_${res.status}`;
}

export type ClosureReadiness = {
  ready: boolean;
  reason?: string | null;
  checklist?: Record<string, boolean>;
};

export async function getClosureReadiness(orderId: number): Promise<ClosureReadiness> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/actual-cost-policy/orders/${orderId}/closure-readiness`,
    { credentials: "include" },
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as ClosureReadiness;
}

export async function closeExecutionJob(
  orderId: number,
  checklist: Record<string, unknown>,
): Promise<{ order_id: number; status: string }> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/actual-cost-policy/orders/${orderId}/close`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ checklist }),
    },
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as { order_id: number; status: string };
}

export async function reopenExecutionJob(
  orderId: number,
  reason: string,
): Promise<{ order_id: number; status: string }> {
  const res = await fetch(
    `${getAPIBaseURL()}/api/v1/actual-cost-policy/orders/${orderId}/reopen`,
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason }),
    },
  );
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as { order_id: number; status: string };
}
