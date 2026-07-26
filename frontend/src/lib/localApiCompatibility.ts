/**
 * Local DEV API truth — fail-loud when Vite points at a stale/wrong backend.
 * Production: no-op (never blocks writes, never shows banner).
 */

import { getAPIBaseURL } from "@/lib/config";

export const LOCAL_COMPAT_CONTRACT = "workos-frontend-local-compat/v1";
export const LOCAL_COMPAT_REQUIRED_CAPABILITIES = [
  "system.version",
  "system.local_compatibility",
  "intake_v6.workspaces",
  "openapi.finish_setup_schema",
] as const;

export type LocalCompatKind = "ok" | "unavailable" | "incompatible" | "skipped";

export type LocalCompatSnapshot = {
  kind: LocalCompatKind;
  apiBase: string;
  httpStatus: number | null;
  service: string | null;
  contract: string | null;
  apiVersion: string | null;
  capabilities: string[];
  missingCapabilities: string[];
  detail: string;
  recommendedStep: string;
  probedAt: string;
};

const WRITE_GUARD_FLAG = "__workosLocalApiWriteGuardPatched";

let snapshot: LocalCompatSnapshot = {
  kind: "skipped",
  apiBase: "",
  httpStatus: null,
  service: null,
  contract: null,
  apiVersion: null,
  capabilities: [],
  missingCapabilities: [],
  detail: "",
  recommendedStep: "",
  probedAt: "",
};

const listeners = new Set<() => void>();

function emit() {
  for (const listener of listeners) listener();
}

export function getLocalApiCompatibilitySnapshot(): LocalCompatSnapshot {
  return snapshot;
}

export function subscribeLocalApiCompatibility(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function isLocalApiWriteBlocked(): boolean {
  if (!import.meta.env.DEV) return false;
  return snapshot.kind === "unavailable" || snapshot.kind === "incompatible";
}

export function resolveCompatProbeUrl(apiBase: string): string {
  const base = (apiBase || "").replace(/\/$/, "");
  const path = "/api/v1/system/local-compatibility";
  return base ? `${base}${path}` : path;
}

function missingCaps(capabilities: string[]): string[] {
  return LOCAL_COMPAT_REQUIRED_CAPABILITIES.filter((c) => !capabilities.includes(c));
}

export function evaluateLocalCompatibilityPayload(
  apiBase: string,
  httpStatus: number,
  payload: unknown,
): LocalCompatSnapshot {
  const probedAt = new Date().toISOString();
  if (httpStatus === 404 || httpStatus === 405) {
    return {
      kind: "incompatible",
      apiBase,
      httpStatus,
      service: null,
      contract: null,
      apiVersion: null,
      capabilities: [],
      missingCapabilities: [...LOCAL_COMPAT_REQUIRED_CAPABILITIES],
      detail:
        "Backendul raspunde, dar nu expune contractul local-compatibility (proces stale sau schema veche).",
      recommendedStep:
        "Inventariaza listenerii (`npm run diag:local-listeners`), opreste procesul stale, porneste backendul din acest repo.",
      probedAt,
    };
  }
  if (httpStatus < 200 || httpStatus >= 300) {
    return {
      kind: "incompatible",
      apiBase,
      httpStatus,
      service: null,
      contract: null,
      apiVersion: null,
      capabilities: [],
      missingCapabilities: [...LOCAL_COMPAT_REQUIRED_CAPABILITIES],
      detail: `Raspuns neasteptat de la local-compatibility (HTTP ${httpStatus}).`,
      recommendedStep: "Verifica ca API base indica un backend WorkOS din acest checkout.",
      probedAt,
    };
  }

  const row = payload && typeof payload === "object" ? (payload as Record<string, unknown>) : null;
  const service = typeof row?.service === "string" ? row.service : null;
  const contract = typeof row?.contract === "string" ? row.contract : null;
  const apiVersion = typeof row?.api_version === "string" ? row.api_version : null;
  const capabilities = Array.isArray(row?.capabilities)
    ? row.capabilities.filter((c): c is string => typeof c === "string")
    : [];
  const missing = missingCaps(capabilities);

  if (service !== "workos-backend") {
    return {
      kind: "incompatible",
      apiBase,
      httpStatus,
      service,
      contract,
      apiVersion,
      capabilities,
      missingCapabilities: missing,
      detail: "Raspunsul nu identifica service=workos-backend.",
      recommendedStep: "Schimba VITE_API_BASE_URL / BACKEND_PORT catre backendul WorkOS corect.",
      probedAt,
    };
  }
  if (contract !== LOCAL_COMPAT_CONTRACT) {
    return {
      kind: "incompatible",
      apiBase,
      httpStatus,
      service,
      contract,
      apiVersion,
      capabilities,
      missingCapabilities: missing,
      detail: `Contract local necunoscut sau vechi (primit: ${contract ?? "null"}).`,
      recommendedStep: "Actualizeaza/reporneste backendul din acest repo.",
      probedAt,
    };
  }
  if (missing.length) {
    return {
      kind: "incompatible",
      apiBase,
      httpStatus,
      service,
      contract,
      apiVersion,
      capabilities,
      missingCapabilities: missing,
      detail: `Lipsesc capabilitati: ${missing.join(", ")}.`,
      recommendedStep: "Backendul nu are schema/capabilitatile cerute de frontendul local.",
      probedAt,
    };
  }

  return {
    kind: "ok",
    apiBase,
    httpStatus,
    service,
    contract,
    apiVersion,
    capabilities,
    missingCapabilities: [],
    detail: "Backend local compatibil.",
    recommendedStep: "",
    probedAt,
  };
}

export async function probeLocalApiCompatibility(options?: {
  apiBase?: string;
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
}): Promise<LocalCompatSnapshot> {
  if (!import.meta.env.DEV) {
    snapshot = {
      kind: "skipped",
      apiBase: options?.apiBase ?? getAPIBaseURL(),
      httpStatus: null,
      service: null,
      contract: null,
      apiVersion: null,
      capabilities: [],
      missingCapabilities: [],
      detail: "Verificarea locala este activa doar in development.",
      recommendedStep: "",
      probedAt: new Date().toISOString(),
    };
    emit();
    return snapshot;
  }

  const apiBase = options?.apiBase ?? getAPIBaseURL();
  const fetchImpl = options?.fetchImpl ?? fetch;
  const timeoutMs = options?.timeoutMs ?? 2500;
  const url = resolveCompatProbeUrl(apiBase);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetchImpl(url, {
      method: "GET",
      credentials: "include",
      signal: controller.signal,
      headers: { Accept: "application/json" },
    });
    let payload: unknown = null;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    snapshot = evaluateLocalCompatibilityPayload(apiBase, response.status, payload);
  } catch {
    snapshot = {
      kind: "unavailable",
      apiBase,
      httpStatus: null,
      service: null,
      contract: null,
      apiVersion: null,
      capabilities: [],
      missingCapabilities: [...LOCAL_COMPAT_REQUIRED_CAPABILITIES],
      detail: "Backendul local nu raspunde la adresa API configurata.",
      recommendedStep:
        "Porneste backendul (`npm run dev:backend`) sau seteaza VITE_API_BASE_URL la instanța corecta.",
      probedAt: new Date().toISOString(),
    };
  } finally {
    clearTimeout(timer);
  }

  emit();
  return snapshot;
}

function resolveRequestUrl(input: RequestInfo | URL): string {
  try {
    if (typeof input === "string") {
      return new URL(input, globalThis.location?.origin || "http://127.0.0.1").href;
    }
    if (input instanceof URL) return input.href;
    if (typeof Request !== "undefined" && input instanceof Request) return input.url;
  } catch {
    return "";
  }
  return "";
}

function isApiBoundRequest(url: string): boolean {
  if (!url) return false;
  // When local compatibility fails, block any mutating API-shaped request —
  // not only those whose host matches the configured base (ghost dual-port case).
  return url.includes("/api/v1/") || /\/api\//.test(url);
}

export function installLocalApiWriteGuard(): void {
  if (!import.meta.env.DEV) return;
  const g = globalThis as typeof globalThis & { [WRITE_GUARD_FLAG]?: boolean };
  if (g[WRITE_GUARD_FLAG]) return;
  g[WRITE_GUARD_FLAG] = true;

  const originalFetch = globalThis.fetch.bind(globalThis);
  globalThis.fetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    const method = (init?.method || (typeof Request !== "undefined" && input instanceof Request ? input.method : "GET") || "GET")
      .toString()
      .toUpperCase();
    const mutating = method === "POST" || method === "PUT" || method === "PATCH" || method === "DELETE";
    if (mutating && isLocalApiWriteBlocked()) {
      const url = resolveRequestUrl(input);
      if (isApiBoundRequest(url)) {
        const message =
          snapshot.kind === "unavailable"
            ? "Scriere blocata: backend local indisponibil."
            : "Scriere blocata: backend local incompatibil.";
        throw new Error(`${message} API=${snapshot.apiBase || "(same-origin)"}`);
      }
    }
    return originalFetch(input, init);
  };
}

/** Test helper — reset module state between Vitest cases. */
export function __resetLocalApiCompatibilityForTests(next?: LocalCompatSnapshot): void {
  snapshot =
    next ||
    ({
      kind: "skipped",
      apiBase: "",
      httpStatus: null,
      service: null,
      contract: null,
      apiVersion: null,
      capabilities: [],
      missingCapabilities: [],
      detail: "",
      recommendedStep: "",
      probedAt: "",
    } satisfies LocalCompatSnapshot);
  emit();
}
