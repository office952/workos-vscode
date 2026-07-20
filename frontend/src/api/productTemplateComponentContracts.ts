import { getAPIBaseURL } from "@/lib/config";

export interface ComponentContractUsedByEdge {
  parent_template_code: string;
  link_id?: number | null;
  relation_type?: string | null;
  usage_mode?: string | null;
  instance_schema_id?: string | null;
  active: boolean;
}

export interface ComponentContractChildEdge {
  module_template_code: string;
  link_id?: number | null;
  relation_type?: string | null;
  usage_mode?: string | null;
  instance_schema_id?: string | null;
  active: boolean;
  policy_component_only?: boolean;
  policy_root_offerable?: boolean;
  policy_reason?: string | null;
}

export interface ProductTemplateComponentContractView {
  template_code: string;
  template_id: number;
  db_active: boolean;
  publication_status?: string | null;
  role: string;
  usage_mode_policy: Record<string, unknown>;
  used_by: ComponentContractUsedByEdge[];
  children: ComponentContractChildEdge[];
  instance_schema_hints: string[];
  no_component_templates_table: boolean;
  contract_version: string;
}

function base(): string {
  return `${getAPIBaseURL()}/api/v1/product-system`;
}

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { credentials: "include", ...init });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

export async function getComponentContract(
  templateCode: string,
): Promise<ProductTemplateComponentContractView> {
  return fetchJson(
    `${base()}/templates/${encodeURIComponent(templateCode)}/component-contract`,
  );
}

export async function patchComponentContractLink(
  linkId: number,
  body: { usage_mode?: string | null; instance_schema_id?: string | null },
): Promise<ComponentContractChildEdge> {
  return fetchJson(`${base()}/module-links/${linkId}/component-contract`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
