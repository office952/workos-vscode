import { getAPIBaseURL } from "@/lib/config";

export type LifecycleStatus =
  | "NOT_APPLICABLE"
  | "NOT_STARTED"
  | "DISCOVERED"
  | "CONFIGURED"
  | "WIRED"
  | "VALIDATED"
  | "PREVIEW_ONLY"
  | "OWNER_GATE_REQUIRED"
  | "BLOCKED"
  | "PASS"
  | "DEPRECATED";

export type TemplateLifecycleStage = {
  stage: string;
  owner_label: string;
  authority: string;
  required: boolean;
  status: LifecycleStatus;
  evidence: string[];
  warnings: Array<{ code: string; message: string; severity?: string }>;
  blockers: Array<{ code: string; message: string; severity?: string }>;
  owner_gate?: string | null;
};

export type TemplateLifecycleReadiness = {
  schema_version: string;
  template_code: string;
  template_status: string;
  lifecycle_status: LifecycleStatus;
  readiness_score: number;
  activation_eligible: boolean;
  stages: TemplateLifecycleStage[];
  owner_gates: Array<{ code: string; label: string; status: LifecycleStatus; reason: string }>;
  legacy_conflicts: Array<{ code: string; classification: string; message: string }>;
  impact_summary?: {
    changed: string;
    affected_product_templates: string[];
    affected_intake: string[];
    affected_product_definition: string[];
    cpp: string[];
    tasking: string[];
  } | null;
  stage_counts: Record<string, number>;
};

async function fetchLifecycleJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getAPIBaseURL()}${path}`, { credentials: "include" });
  if (!response.ok) {
    throw new Error(`Template lifecycle request failed (${response.status}).`);
  }
  return (await response.json()) as T;
}

export const templateLifecycleApi = {
  readiness: (templateCode: string) =>
    fetchLifecycleJson<TemplateLifecycleReadiness>(
      `/api/v1/product-system/templates/${encodeURIComponent(templateCode)}/lifecycle-readiness`,
    ),
};
