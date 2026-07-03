/**
 * System / runtime version API client.
 *
 * Consumes GET /api/v1/system/version. Never invents data:
 * on any failure the UI shows "Version unavailable".
 *
 * Sprint #v92.1 hotfix — Base URL resolution:
 *   Previously this module read `import.meta.env.VITE_API_BASE_URL` directly,
 *   which on the live deploy pipeline can be baked in as the literal
 *   placeholder `https://$$BACKEND_DOMAIN$$` when the pipeline fails to
 *   substitute the real backend host. That produced an unreachable URL
 *   (`https://$$BACKEND_DOMAIN$$/api/v1/system/version`) and the sidebar
 *   badge fell back to "Version unavailable" even though the real
 *   same-origin backend was serving v92.1 correctly.
 *
 *   We now delegate to the canonical resolver in `@/lib/config` via
 *   `getAPIBaseURL()`, which already:
 *     1. prefers a runtime-config JSON fetched from `/api/config`;
 *     2. falls back to `VITE_API_BASE_URL` only when it is a real URL;
 *     3. detects unresolved `$$…$$` placeholders and drops to the empty
 *        string (same-origin) so relative `/api/...` paths are used.
 *
 *   This keeps behavior identical in dev/local and fixes the live badge
 *   without touching any business logic.
 */

import { getAPIBaseURL } from "@/lib/config";

export interface SystemVersionPayload {
  app_name: string | null;
  release_version: string | null;
  release_label: string | null;
  environment: string | null;
  release_scope: string | null;
  build_time: string | null;
  source: "env" | "env+file" | "file" | "unknown";
  observed_at: string;
}

export async function fetchSystemVersion(): Promise<SystemVersionPayload> {
  const base = getAPIBaseURL() || "";
  const resp = await fetch(`${base}/api/v1/system/version`, {
    method: "GET",
    credentials: "include",
  });
  if (!resp.ok) {
    throw new Error(`system/version HTTP ${resp.status}`);
  }
  const data = (await resp.json()) as SystemVersionPayload;
  return data;
}