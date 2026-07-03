import { getAPIBaseURL } from "@/lib/config";

export interface SmartBillConfigMasked {
  provider: "smartbill";
  source: "app_settings" | "env" | "none";
  enabled: boolean;
  base_url: string | null;
  username_present: boolean;
  username_hint: string | null;
  token_present: boolean;
  lookup_path: string;
  timeout_seconds: number;
  last_test_status: string;
  last_test_at: string | null;
  last_test_message: string | null;
}

export interface SmartBillConfigUpdateInput {
  enabled: boolean;
  base_url: string | null;
  username?: string | null;
  token?: string | null;
  lookup_path: string;
  timeout_seconds: number;
  clear_token?: boolean;
}

export interface SmartBillConfigTestResult {
  provider: "smartbill";
  source: "app_settings" | "env" | "none";
  status: "disabled" | "not_configured" | "configured" | "invalid_config";
  ok: boolean;
  mode: "local_config_validation";
  message: string;
  warnings: string[];
}

export interface SmartbillProviderHealthResponse {
  provider: "smartbill";
  source: "app_settings" | "env" | "none";
  enabled: boolean;
  configured: boolean;
  status: "disabled" | "not_configured" | "configured" | "invalid_config";
  missing_fields: string[];
  present_fields: {
    base_url: boolean;
    username: boolean;
    token: boolean;
    lookup_path: boolean;
    timeout_seconds: boolean;
  };
  masked: {
    base_url_host: string | null;
    username_hint: string | null;
  };
  settings: {
    timeout_seconds: number | null;
    lookup_path: string;
  };
  live_validation: {
    performed: false;
    status: "not_run";
    message: string;
  };
  warnings: string[];
}

export class IntegrationsHttpError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "IntegrationsHttpError";
    this.status = status;
  }
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (typeof body?.message === "string") return body.message;
  } catch {
    // fall through
  }
  return `HTTP ${res.status}`;
}

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const res = await fetch(`${getAPIBaseURL()}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!res.ok) {
    throw new IntegrationsHttpError(res.status, await parseErrorBody(res));
  }

  return (await res.json()) as T;
}

export async function getSmartBillConfig(): Promise<SmartBillConfigMasked> {
  return requestJson<SmartBillConfigMasked>("/api/v1/integrations/providers/smartbill/config", {
    method: "GET",
  });
}

export async function updateSmartBillConfig(input: SmartBillConfigUpdateInput): Promise<SmartBillConfigMasked> {
  return requestJson<SmartBillConfigMasked>("/api/v1/integrations/providers/smartbill/config", {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export async function testSmartBillConfig(): Promise<SmartBillConfigTestResult> {
  return requestJson<SmartBillConfigTestResult>("/api/v1/integrations/providers/smartbill/test-connection", {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function clearSmartBillToken(): Promise<SmartBillConfigMasked> {
  return requestJson<SmartBillConfigMasked>("/api/v1/integrations/providers/smartbill/secret/token", {
    method: "DELETE",
  });
}

export async function getSmartBillProviderHealth(): Promise<SmartbillProviderHealthResponse> {
  return requestJson<SmartbillProviderHealthResponse>("/api/v1/integrations/providers/smartbill/health", {
    method: "GET",
  });
}
