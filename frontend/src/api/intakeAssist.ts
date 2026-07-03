import { getAPIBaseURL } from "@/lib/config";

const apiBase = () => `${getAPIBaseURL()}/api/v1/intake-assist`;

export type AssistAvailability = "backend" | "contract-missing" | "error";

export interface ProductTemplateAssistItem {
  id: string;
  name: string;
  family: string;
  category: string | null;
  status: "active" | "draft" | "deprecated" | "inactive" | "unknown";
  description: string | null;
  supported_intake_fields: string[];
  requires_review: boolean;
  warnings: string[];
}

export interface ProductTemplateAssistListResponse {
  source: "backend";
  items: ProductTemplateAssistItem[];
  warnings: string[];
  contract_version: string;
}

export interface IntakeAssistDimensions {
  width?: number;
  height?: number;
  depth?: number;
  unit: "mm" | "cm" | "m" | "unknown";
}

export interface ProductTemplateSuggestionRequest {
  intake_id?: string | null;
  title?: string | null;
  description?: string | null;
  requested_product_type?: string | null;
  dimensions?: IntakeAssistDimensions | null;
  quantity: number;
  finish_notes?: string | null;
  mounting_notes?: string | null;
}

export interface ProductTemplateSuggestionItem {
  template_id: string;
  template_name: string;
  family: string;
  confidence: "high" | "medium" | "low";
  match_reasons: string[];
  missing_inputs: string[];
  warnings: string[];
  requires_operator_confirmation: boolean;
}

export interface ProductTemplateSuggestionResponse {
  source: "backend";
  suggestions: ProductTemplateSuggestionItem[];
  warnings: string[];
  blockers: string[];
  contract_version: string;
}

export interface MaterialSheetAssistRequest {
  product_template_id?: string | null;
  material_category?: string | null;
  dimensions?: IntakeAssistDimensions | null;
  quantity: number;
  constraints?: {
    rotation_allowed?: boolean;
    indoor_outdoor?: "indoor" | "outdoor" | "unknown";
  } | null;
}

export interface MaterialSheetAssistItem {
  material_id: string;
  material_name: string;
  category: string;
  status: "active" | "missing_price" | "needs_owner_input" | "unknown";
  unit: "sqm" | "pcs" | "ml" | "sheet" | "unknown";
  sheet_format: {
    type: "none" | "sheet" | "roll" | "linear" | "piece" | "unknown";
    width: number | null;
    height: number | null;
    unit: "mm" | "cm" | "m" | "unknown";
    usable_width: number | null;
    usable_height: number | null;
    thickness: number | null;
    thickness_unit: "mm" | "cm" | "m" | "unknown";
    verified: boolean;
    source: "manual" | "supplier" | "imported" | "unknown";
  } | null;
  fit_status: "fits" | "fits_rotated" | "does_not_fit" | "unknown";
  fit_reason: string;
  warnings: string[];
  requires_review: boolean;
}

export interface MaterialSheetAssistResponse {
  source: "backend";
  assist_available: boolean;
  items: MaterialSheetAssistItem[];
  warnings: string[];
  blockers: string[];
  contract_version: string;
}

export type FiscalLookupProvider = "anaf" | "smartbill" | "auto";

export interface FiscalLookupResponse {
  available: boolean;
  provider: "anaf" | "smartbill";
  status:
    | "not_configured"
    | "invalid_input"
    | "found"
    | "not_found"
    | "provider_timeout"
    | "provider_error"
    | "rate_limited";
  message: string;
  normalized: {
    tax_id: string;
    company_name: string;
    registration_number: string | null;
    address: string | null;
    city: string | null;
    county: string | null;
    country: "RO";
    vat_payer: boolean;
    source: "anaf" | "smartbill";
  } | null;
  warnings: string[];
  requires_operator_confirmation: boolean;
}

export class IntakeAssistHttpError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = "IntakeAssistHttpError";
    this.status = status;
  }
}

async function parseErrorBody(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === "string") return body.detail;
    if (body?.detail) return JSON.stringify(body.detail);
    if (typeof body?.message === "string") return body.message;
  } catch {
    // keep fallback below
  }
  return `HTTP ${res.status}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${apiBase()}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });

  if (!res.ok) {
    const message = await parseErrorBody(res);
    throw new IntakeAssistHttpError(res.status, message);
  }

  return (await res.json()) as T;
}

export async function listProductTemplateAssist(params?: {
  family_id?: string;
  q?: string;
  include_inactive?: boolean;
  limit?: number;
}): Promise<{ status: AssistAvailability; data: ProductTemplateAssistListResponse | null; message?: string }> {
  const search = new URLSearchParams();
  if (params?.family_id) search.set("family_id", params.family_id);
  if (params?.q) search.set("q", params.q);
  if (typeof params?.include_inactive === "boolean") search.set("include_inactive", String(params.include_inactive));
  if (typeof params?.limit === "number") search.set("limit", String(params.limit));

  try {
    const data = await requestJson<ProductTemplateAssistListResponse>(`/product-templates${search.toString() ? `?${search}` : ""}`);
    return { status: "backend", data };
  } catch (error) {
    if (error instanceof IntakeAssistHttpError && (error.status === 404 || error.status === 501)) {
      return { status: "contract-missing", data: null, message: error.message };
    }
    return {
      status: "error",
      data: null,
      message: error instanceof Error ? error.message : "Template assist request failed.",
    };
  }
}

export async function suggestProductTemplates(
  body: ProductTemplateSuggestionRequest
): Promise<{ status: AssistAvailability; data: ProductTemplateSuggestionResponse | null; message?: string }> {
  try {
    const data = await requestJson<ProductTemplateSuggestionResponse>("/product-template-suggestions", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return { status: "backend", data };
  } catch (error) {
    if (error instanceof IntakeAssistHttpError && (error.status === 404 || error.status === 501)) {
      return { status: "contract-missing", data: null, message: error.message };
    }
    return {
      status: "error",
      data: null,
      message: error instanceof Error ? error.message : "Template suggestion request failed.",
    };
  }
}

export async function getMaterialSheetAssist(
  body: MaterialSheetAssistRequest
): Promise<{ status: AssistAvailability; data: MaterialSheetAssistResponse | null; message?: string }> {
  try {
    const data = await requestJson<MaterialSheetAssistResponse>("/material-sheet-assist", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return { status: "backend", data };
  } catch (error) {
    if (error instanceof IntakeAssistHttpError && (error.status === 404 || error.status === 501)) {
      return { status: "contract-missing", data: null, message: error.message };
    }
    return {
      status: "error",
      data: null,
      message: error instanceof Error ? error.message : "Material sheet assist request failed.",
    };
  }
}

export async function lookupFiscalProvider(
  cui: string,
  provider: FiscalLookupProvider = "auto"
): Promise<{ status: AssistAvailability; data: FiscalLookupResponse | null; message?: string }> {
  try {
    const data = await requestJson<FiscalLookupResponse>("/fiscal-lookup", {
      method: "POST",
      body: JSON.stringify({
        provider,
        country: "RO",
        tax_id: cui,
      }),
    });
    return { status: "backend", data };
  } catch (error) {
    if (error instanceof IntakeAssistHttpError && (error.status === 404 || error.status === 501)) {
      return { status: "contract-missing", data: null, message: error.message };
    }
    return {
      status: "error",
      data: null,
      message: error instanceof Error ? error.message : "Fiscal lookup request failed.",
    };
  }
}
