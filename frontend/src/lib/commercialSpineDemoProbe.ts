import { executionApi } from "@/api/execution";
import { ordersApi, quotesApi } from "@/lib/api";
import { getAPIBaseURL } from "@/lib/config";
import { extractQuoteReadinessFromLineItems } from "@/lib/volumetricQuoteReady";

export const DEMO_PRIMARY_QUOTE = "QT-E2E-COMMERCIAL-001";
export const DEMO_WARN_QUOTE = "QT-E2E-COMMERCIAL-WARN-001";
export const DEMO_TEMPLATE = "TPL-VOLUMETRIC-LETTERS";

export interface DemoScenarioSnapshot {
  quoteCode: string;
  available: boolean;
  unavailableReason?: string;
  quoteDbId?: number;
  quoteStatus?: string;
  canCreateCommercialQuote?: boolean;
  requiresAcknowledgement?: boolean;
  acknowledgementPending: string[];
  readinessOverlay: null;
  orderCode?: string;
  orderDbId?: number;
  executionPlanExists?: boolean;
  executionPlanTaskCount?: number;
}

export interface CommercialSpineDemoProbeResult {
  backendHealthy: boolean;
  backendReason?: string;
  primary: DemoScenarioSnapshot;
  warn: DemoScenarioSnapshot;
}

async function checkBackendHealth(): Promise<{ ok: boolean; reason?: string }> {
  try {
    const base = getAPIBaseURL();
    const res = await fetch(`${base}/health`, { credentials: "include" });
    if (!res.ok) {
      return { ok: false, reason: `Backend health HTTP ${res.status}` };
    }
    const body = (await res.json()) as { status?: string };
    if (body.status !== "healthy") {
      return { ok: false, reason: `Backend status: ${body.status ?? "unknown"}` };
    }
    return { ok: true };
  } catch (err) {
    return {
      ok: false,
      reason: err instanceof Error ? err.message : "Backend unreachable",
    };
  }
}

async function fetchOrderForQuote(quoteId: number, quoteCode: string) {
  const byQuoteId = await ordersApi.list({ quote_id: quoteId }, { limit: 1 });
  if (byQuoteId[0]) return byQuoteId[0];
  const byCode = await ordersApi.list({ quote_code: quoteCode }, { limit: 1 });
  return byCode[0] ?? null;
}

async function probeScenario(quoteCode: string): Promise<DemoScenarioSnapshot> {
  const empty: DemoScenarioSnapshot = {
    quoteCode,
    available: false,
    acknowledgementPending: [],
    readinessOverlay: null,
  };

  try {
    const rows = await quotesApi.list({ code: quoteCode }, { limit: 1 });
    const quote = rows[0];
    if (!quote) {
      return {
        ...empty,
        unavailableReason:
          "Quote not in DB — run backend/scripts/seed_commercial_e2e_fixture.py",
      };
    }

    const readiness = extractQuoteReadinessFromLineItems(quote.line_items);
    const gate = readiness?.quoteGate;

    let orderCode: string | undefined;
    let orderDbId: number | undefined;
    let executionPlanExists: boolean | undefined;
    let executionPlanTaskCount: number | undefined;

    const order = await fetchOrderForQuote(quote.id, quote.code);
    if (order) {
      orderCode = order.code;
      orderDbId = order.id;
      try {
        const plan = await executionApi.getExecutionPlan(order.id);
        executionPlanExists = true;
        executionPlanTaskCount = Array.isArray(plan.tasks) ? plan.tasks.length : 0;
      } catch {
        executionPlanExists = false;
        executionPlanTaskCount = 0;
      }
    }

    return {
      quoteCode,
      available: true,
      quoteDbId: quote.id,
      quoteStatus: quote.status,
      canCreateCommercialQuote: gate?.can_create_commercial_quote,
      requiresAcknowledgement: gate?.requires_acknowledgement,
      acknowledgementPending: gate?.classified?.acknowledgement_pending ?? [],
      readinessOverlay: null,
      orderCode,
      orderDbId,
      executionPlanExists,
      executionPlanTaskCount,
    };
  } catch (err) {
    return {
      ...empty,
      unavailableReason: err instanceof Error ? err.message : "Probe failed",
    };
  }
}

export async function probeCommercialSpineDemo(): Promise<CommercialSpineDemoProbeResult> {
  const health = await checkBackendHealth();
  if (!health.ok) {
    const unavailable = (code: string): DemoScenarioSnapshot => ({
      quoteCode: code,
      available: false,
      unavailableReason: health.reason,
      acknowledgementPending: [],
      readinessOverlay: null,
    });
    return {
      backendHealthy: false,
      backendReason: health.reason,
      primary: unavailable(DEMO_PRIMARY_QUOTE),
      warn: unavailable(DEMO_WARN_QUOTE),
    };
  }

  const [primary, warn] = await Promise.all([
    probeScenario(DEMO_PRIMARY_QUOTE),
    probeScenario(DEMO_WARN_QUOTE),
  ]);

  return {
    backendHealthy: true,
    primary,
    warn,
  };
}
