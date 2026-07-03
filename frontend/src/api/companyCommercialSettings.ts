import { getAPIBaseURL } from "@/lib/config";

const apiBase = () => `${getAPIBaseURL()}/api/v1`;

export interface CompanyCommercialSettingsDTO {
  default_vat_pct: number;
  eur_to_ron_rate: number;
}

async function parseError(res: Response): Promise<string> {
  const detail = await res.text().catch(() => "Unknown error");
  return `HTTP ${res.status}: ${detail}`;
}

export async function getCompanyCommercialSettings(): Promise<CompanyCommercialSettingsDTO> {
  const res = await fetch(`${apiBase()}/company-commercial-settings`, {
    credentials: "include",
  });
  if (!res.ok) {
    throw new Error(await parseError(res));
  }
  return res.json();
}

export async function updateCompanyCommercialSettings(
  payload: CompanyCommercialSettingsDTO
): Promise<CompanyCommercialSettingsDTO> {
  const res = await fetch(`${apiBase()}/company-commercial-settings`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    throw new Error(await parseError(res));
  }
  return res.json();
}
