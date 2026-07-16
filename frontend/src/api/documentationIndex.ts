/**
 * Minimal W0-B2 documentation index client for truth pages (read-only).
 * Does not implement a Documentation Center.
 */

import { getAPIBaseURL } from "@/lib/config";

export interface DocumentationIndexItem {
  document_id: string;
  title: string;
  authority: string;
  status: string;
  last_validated_at: string | null;
  drift_status: string;
  technical_id: string;
  path?: string;
}

export interface DocumentationIndexResponse {
  index_version: string;
  count: number;
  items: DocumentationIndexItem[];
  notes?: string[];
}

export type DocumentationIndexFetchResult =
  | { state: "ok"; data: DocumentationIndexResponse }
  | { state: "forbidden" }
  | { state: "unavailable"; message: string }
  | { state: "empty" };

export async function fetchDocumentationIndex(): Promise<DocumentationIndexFetchResult> {
  const base = getAPIBaseURL() || "";
  try {
    const resp = await fetch(`${base}/api/v1/system/documentation`, {
      method: "GET",
      credentials: "include",
    });
    if (resp.status === 401 || resp.status === 403) {
      return { state: "forbidden" };
    }
    if (!resp.ok) {
      return { state: "unavailable", message: `HTTP ${resp.status}` };
    }
    const data = (await resp.json()) as DocumentationIndexResponse;
    if (!data.items?.length) {
      return { state: "empty" };
    }
    return { state: "ok", data };
  } catch (err) {
    return {
      state: "unavailable",
      message: err instanceof Error ? err.message : "Network error",
    };
  }
}
