/**
 * AcmPanel production DXF upload — V6 workspace component-owned binding.
 * Not Work Intake work-file ownership.
 */

import { getAPIBaseURL } from "@/lib/config";
import { IntakeV4ApiError } from "@/lib/intakeV6/intakeV4Api";

const intakeV6ApiBase = () => `${getAPIBaseURL()}/api/v1/intake-v6`;

export type AcmProductionGeometryUploadResult = {
  ok: boolean;
  duplicate?: boolean;
  bound?: boolean;
  attachment?: Record<string, unknown>;
  measurement_preview?: {
    measurement_status?: string;
    cut_length_ml?: number | null;
    v_groove_l1_ml?: number | null;
    v_groove_l2_ml?: number | null;
    v_groove_total_ml?: number | null;
    warnings?: string[];
    config_fingerprint?: string;
    semantic_mapping_version?: string;
  } | null;
  workspace_id?: string;
  note?: string;
};

function parseError(status: number, text: string): string {
  try {
    const j = JSON.parse(text) as { detail?: unknown };
    if (typeof j.detail === "string") return j.detail;
    if (j.detail && typeof j.detail === "object") return JSON.stringify(j.detail);
  } catch {
    /* ignore */
  }
  return text || `HTTP ${status}`;
}

export async function uploadAcmPanelProductionDxf(args: {
  workspaceId: string;
  file: File;
  componentInstanceId: string;
  panelId?: string | null;
  geometryRole?: string;
  bind?: boolean;
}): Promise<AcmProductionGeometryUploadResult> {
  const params = new URLSearchParams();
  params.set("component_instance_id", args.componentInstanceId);
  if (args.panelId) params.set("panel_id", args.panelId);
  params.set("geometry_role", args.geometryRole || "production_geometry");
  params.set("bind", args.bind === false ? "false" : "true");

  const form = new FormData();
  form.append("file", args.file);

  const url =
    `${intakeV6ApiBase()}/workspaces/${encodeURIComponent(args.workspaceId)}` +
    `/acm-panel/production-geometry/dxf?${params.toString()}`;

  const response = await fetch(url, {
    method: "POST",
    body: form,
    credentials: "include",
    cache: "no-store",
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new IntakeV4ApiError(response.status, parseError(response.status, text));
  }
  return (await response.json()) as AcmProductionGeometryUploadResult;
}

export function activeProductionGeometryAttachments(
  instance: Record<string, unknown> | null | undefined,
): Array<Record<string, unknown>> {
  const pg = instance?.production_geometry;
  if (!pg || typeof pg !== "object") return [];
  const atts = (pg as { attachments?: unknown }).attachments;
  if (!Array.isArray(atts)) return [];
  return atts.filter((a): a is Record<string, unknown> => {
    if (!a || typeof a !== "object") return false;
    const st = String((a as { measurement_status?: string }).measurement_status || "");
    return st !== "replaced" && st !== "archived";
  });
}
