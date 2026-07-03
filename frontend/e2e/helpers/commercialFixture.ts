/**
 * Live-db commercial E2E fixture helpers.
 * Reads manifest from seed_commercial_e2e_fixture.py or probes backend directly.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const FIXTURE_QUOTE_CODE = "QT-E2E-COMMERCIAL-001";
export const FIXTURE_INTAKE_CODE = "WI-E2E-COMMERCIAL-001";
export const FIXTURE_WARN_QUOTE_CODE = "QT-E2E-COMMERCIAL-WARN-001";
export const FIXTURE_WARN_INTAKE_CODE = "WI-E2E-COMMERCIAL-WARN-001";
export const FIXTURE_FINISH_DISPLAY_INTAKE_CODE =
  "WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001";

export interface WarnFixtureManifest {
  intake_code: string;
  intake_id: number;
  quote_code: string;
  quote_id: number;
  can_create_commercial_quote: boolean;
  requires_acknowledgement: boolean;
  quote_gate_ack_pending: string[];
}

export interface FinishDisplayFixtureManifest {
  intake_code: string;
  intake_id: number;
  template_code: string;
}

export interface CommercialFixtureManifest {
  quote_code: string;
  quote_id: number;
  quote_status: string;
  intake_code: string;
  intake_id: number;
  template_code: string;
  grand_total: number;
  can_create_commercial_quote?: boolean;
  live_gate_can_create_commercial_quote?: boolean;
  requires_acknowledgement?: boolean;
  quote_gate_warnings?: string[];
  quote_gate_blockers?: string[];
  readiness_overlay?: string | null;
  order_code?: string | null;
  order_id?: number | null;
  warn_fixture?: WarnFixtureManifest;
  finish_display_fixture?: FinishDisplayFixtureManifest;
}

export interface LiveDbProbe {
  backendHealthy: boolean;
  fixtureAvailable: boolean;
  manifest: CommercialFixtureManifest | null;
  reason?: string;
}

export interface WarnLiveDbProbe {
  backendHealthy: boolean;
  fixtureAvailable: boolean;
  manifest: WarnFixtureManifest | null;
  readiness_overlay: string | null;
  reason?: string;
}

export interface FinishDisplayLiveDbProbe {
  backendHealthy: boolean;
  fixtureAvailable: boolean;
  manifest: FinishDisplayFixtureManifest | null;
  reason?: string;
}

const BACKEND_URL = process.env.PW_BACKEND_URL ?? "http://localhost:8000";
const MANIFEST_PATH = path.join(__dirname, "..", ".commercial-fixture.json");

function readManifestFile(): CommercialFixtureManifest | null {
  try {
    if (!fs.existsSync(MANIFEST_PATH)) return null;
    const raw = fs.readFileSync(MANIFEST_PATH, "utf8");
    const parsed = JSON.parse(raw) as CommercialFixtureManifest;
    if (!parsed?.quote_code || !parsed?.quote_id) return null;
    return parsed;
  } catch {
    return null;
  }
}

async function fetchJson<T>(url: string): Promise<T | null> {
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(8_000) });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

/** Probe backend health and fixture quote presence (db source required). */
export async function probeLiveDbFixture(): Promise<LiveDbProbe> {
  const health = await fetchJson<{ status?: string }>(`${BACKEND_URL}/health`);
  if (!health || health.status !== "healthy") {
    return {
      backendHealthy: false,
      fixtureAvailable: false,
      manifest: null,
      reason: `Backend not healthy at ${BACKEND_URL}/health`,
    };
  }

  const manifest = readManifestFile();
  const query = encodeURIComponent(JSON.stringify({ code: FIXTURE_QUOTE_CODE }));
  const quotes = await fetchJson<{
    items?: Array<{
      id: number;
      code: string;
      status: string;
      grand_total?: number;
      intake_code?: string;
    }>;
  }>(`${BACKEND_URL}/api/v1/entities/quotes?query=${query}&limit=1&skip=0`);

  const quote = quotes?.items?.[0];
  if (!quote) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest,
      reason: `Fixture quote ${FIXTURE_QUOTE_CODE} not in DB — run: python backend/scripts/seed_commercial_e2e_fixture.py`,
    };
  }

  if (quote.status !== "priced" && quote.status !== "accepted" && quote.status !== "sent") {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest,
      reason: `Fixture quote status is '${quote.status}' — re-run seed script to reset to priced`,
    };
  }

  const resolved: CommercialFixtureManifest = {
    quote_code: quote.code,
    quote_id: quote.id,
    quote_status: quote.status,
    intake_code: quote.intake_code ?? manifest?.intake_code ?? FIXTURE_INTAKE_CODE,
    intake_id: manifest?.intake_id ?? 0,
    template_code: manifest?.template_code ?? "TPL-VOLUMETRIC-LETTERS",
    grand_total: Number(quote.grand_total ?? manifest?.grand_total ?? 0),
    can_create_commercial_quote: manifest?.can_create_commercial_quote,
    live_gate_can_create_commercial_quote: manifest?.live_gate_can_create_commercial_quote,
    requires_acknowledgement: manifest?.requires_acknowledgement,
    quote_gate_warnings: manifest?.quote_gate_warnings,
    quote_gate_blockers: manifest?.quote_gate_blockers,
    readiness_overlay: manifest?.readiness_overlay ?? null,
    order_code: manifest?.order_code ?? null,
    order_id: manifest?.order_id ?? null,
  };

  return {
    backendHealthy: true,
    fixtureAvailable: true,
    manifest: resolved,
  };
}

async function fetchFixtureQuoteByCode(code: string) {
  const query = encodeURIComponent(JSON.stringify({ code }));
  const quotes = await fetchJson<{
    items?: Array<{
      id: number;
      code: string;
      status: string;
      grand_total?: number;
      intake_code?: string;
    }>;
  }>(`${BACKEND_URL}/api/v1/entities/quotes?query=${query}&limit=1&skip=0`);
  return quotes?.items?.[0] ?? null;
}

/** Probe backend health and WARN fixture quote (acknowledgement path). */
export async function probeWarnLiveDbFixture(): Promise<WarnLiveDbProbe> {
  const health = await fetchJson<{ status?: string }>(`${BACKEND_URL}/health`);
  if (!health || health.status !== "healthy") {
    return {
      backendHealthy: false,
      fixtureAvailable: false,
      manifest: null,
      readiness_overlay: null,
      reason: `Backend not healthy at ${BACKEND_URL}/health`,
    };
  }

  const fileManifest = readManifestFile();
  const warnMeta = fileManifest?.warn_fixture;
  if (!warnMeta?.quote_code || !warnMeta.quote_id) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: null,
      readiness_overlay: fileManifest?.readiness_overlay ?? null,
      reason:
        "warn_fixture missing from .commercial-fixture.json — run: python backend/scripts/seed_commercial_e2e_fixture.py",
    };
  }

  if (warnMeta.quote_code !== FIXTURE_WARN_QUOTE_CODE) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: null,
      readiness_overlay: fileManifest?.readiness_overlay ?? null,
      reason: `Expected warn quote ${FIXTURE_WARN_QUOTE_CODE}, got ${warnMeta.quote_code}`,
    };
  }

  if (!warnMeta.requires_acknowledgement) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: null,
      readiness_overlay: fileManifest?.readiness_overlay ?? null,
      reason: "warn_fixture.requires_acknowledgement is not true — re-run seed",
    };
  }

  if (!warnMeta.can_create_commercial_quote) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: null,
      readiness_overlay: fileManifest?.readiness_overlay ?? null,
      reason: "warn_fixture.can_create_commercial_quote is false — re-run seed",
    };
  }

  if (!Array.isArray(warnMeta.quote_gate_ack_pending) || warnMeta.quote_gate_ack_pending.length === 0) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: null,
      readiness_overlay: fileManifest?.readiness_overlay ?? null,
      reason: "warn_fixture.quote_gate_ack_pending is empty — re-run seed",
    };
  }

  const quote = await fetchFixtureQuoteByCode(warnMeta.quote_code);
  if (!quote) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: warnMeta,
      readiness_overlay: fileManifest?.readiness_overlay ?? null,
      reason: `WARN fixture quote ${warnMeta.quote_code} not in DB — re-run seed`,
    };
  }

  if (quote.status !== "priced" && quote.status !== "accepted") {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: warnMeta,
      readiness_overlay: fileManifest?.readiness_overlay ?? null,
      reason: `WARN fixture quote status is '${quote.status}' — re-run seed to reset (priced/accepted required)`,
    };
  }

  if (quote.id !== warnMeta.quote_id) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: warnMeta,
      readiness_overlay: fileManifest?.readiness_overlay ?? null,
      reason: `WARN fixture quote_id mismatch manifest=${warnMeta.quote_id} db=${quote.id}`,
    };
  }

  return {
    backendHealthy: true,
    fixtureAvailable: true,
    manifest: warnMeta,
    readiness_overlay: fileManifest?.readiness_overlay ?? null,
  };
}

/** Probe backend health and WorkIntake V2 finish-display intake fixture. */
export async function probeFinishDisplayLiveDbFixture(): Promise<FinishDisplayLiveDbProbe> {
  const health = await fetchJson<{ status?: string }>(`${BACKEND_URL}/health`);
  if (!health || health.status !== "healthy") {
    return {
      backendHealthy: false,
      fixtureAvailable: false,
      manifest: null,
      reason: `Backend not healthy at ${BACKEND_URL}/health`,
    };
  }

  const fileManifest = readManifestFile();
  const finishMeta = fileManifest?.finish_display_fixture;
  if (!finishMeta?.intake_code || !finishMeta.intake_id) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: null,
      reason:
        "finish_display_fixture missing from .commercial-fixture.json — run: python backend/scripts/seed_commercial_e2e_fixture.py",
    };
  }

  if (finishMeta.intake_code !== FIXTURE_FINISH_DISPLAY_INTAKE_CODE) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: null,
      reason: `Expected finish intake ${FIXTURE_FINISH_DISPLAY_INTAKE_CODE}, got ${finishMeta.intake_code}`,
    };
  }

  const query = encodeURIComponent(JSON.stringify({ code: finishMeta.intake_code }));
  const intakes = await fetchJson<{
    items?: Array<{
      id: number;
      code: string;
      status: string;
      confirmed_template_code?: string;
    }>;
  }>(`${BACKEND_URL}/api/v1/entities/intake_requests?query=${query}&limit=1&skip=0`);

  const intake = intakes?.items?.[0];
  if (!intake) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: finishMeta,
      reason: `Finish-display intake ${finishMeta.intake_code} not in DB — re-run seed`,
    };
  }

  if (intake.id !== finishMeta.intake_id) {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: finishMeta,
      reason: `Finish-display intake_id mismatch manifest=${finishMeta.intake_id} db=${intake.id}`,
    };
  }

  if ((intake.confirmed_template_code ?? finishMeta.template_code) !== "TPL-VOLUMETRIC-LETTERS") {
    return {
      backendHealthy: true,
      fixtureAvailable: false,
      manifest: finishMeta,
      reason: "Finish-display intake template is not TPL-VOLUMETRIC-LETTERS — re-run seed",
    };
  }

  return {
    backendHealthy: true,
    fixtureAvailable: true,
    manifest: finishMeta,
  };
}

/** Resolve numeric order db id after conversion by order code. */
export async function resolveOrderDbId(orderCode: string): Promise<number | null> {
  const query = encodeURIComponent(JSON.stringify({ code: orderCode }));
  const data = await fetchJson<{ items?: Array<{ id: number; code: string }> }>(
    `${BACKEND_URL}/api/v1/entities/orders?query=${query}&limit=1&skip=0`
  );
  const row = data?.items?.[0];
  return row?.id ?? null;
}
