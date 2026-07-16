/**
 * Minimal W0-B2 documentation index client for truth pages (read-only).
 * Does not implement a Documentation Center.
 */

import { getAPIBaseURL } from "@/lib/config";

export interface DocumentationDisplayMeta {
  display_label_ro?: string | null;
  technical_alias?: string | null;
  translation_key?: string | null;
  description_ro?: string | null;
}

export interface DocumentationIndexItem {
  document_id: string;
  title: string;
  path: string;
  category: string;
  authority: string;
  status: string;
  visibility_class?: string;
  last_validated_at: string | null;
  drift_status: string;
  related_systems: string[];
  related_pages: string[];
  display?: DocumentationDisplayMeta | null;
  technical_id: string;
  metadata_version?: string;
  index_version?: string;
}

export interface DocumentationIndexResponse {
  index_version: string;
  metadata_version?: string;
  count: number;
  items: DocumentationIndexItem[];
  notes?: string[];
}

export interface DocumentationIndexDetail {
  technical_id: string;
  reason_for_inclusion: string | null;
  file_exists: boolean;
  content_markdown: string | null;
  index_version: string;
  document: {
    document_id: string;
    title: string;
    path: string;
    category: string;
    authority: string;
    status: string;
    systems?: string[];
    pages?: string[];
  };
  freshness?: {
    last_validated_at: string | null;
    validation_status: string;
  };
}

export type DocumentationIndexFetchResult =
  | { state: "ok"; data: DocumentationIndexResponse }
  | { state: "forbidden" }
  | { state: "unavailable"; message: string }
  | { state: "empty" };

export type DocumentationDetailFetchResult =
  | { state: "ok"; data: DocumentationIndexDetail }
  | { state: "forbidden" }
  | { state: "unavailable"; message: string }
  | { state: "not_found" };

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

/** Lookup by document_id only — never by arbitrary path. */
export async function fetchDocumentationDetail(
  documentId: string,
  includeContent = false
): Promise<DocumentationDetailFetchResult> {
  const base = getAPIBaseURL() || "";
  const id = encodeURIComponent(documentId);
  const qs = includeContent ? "?include_content=true" : "";
  try {
    const resp = await fetch(`${base}/api/v1/system/documentation/${id}${qs}`, {
      method: "GET",
      credentials: "include",
    });
    if (resp.status === 401 || resp.status === 403) {
      return { state: "forbidden" };
    }
    if (resp.status === 404) {
      return { state: "not_found" };
    }
    if (!resp.ok) {
      return { state: "unavailable", message: `HTTP ${resp.status}` };
    }
    const data = (await resp.json()) as DocumentationIndexDetail;
    return { state: "ok", data };
  } catch (err) {
    return {
      state: "unavailable",
      message: err instanceof Error ? err.message : "Network error",
    };
  }
}

export function isAttentionStatus(status: string, authority: string, drift: string): {
  stale: boolean;
  superseded: boolean;
  ownerReview: boolean;
} {
  const s = status.toUpperCase();
  const a = authority.toUpperCase();
  const d = drift.toUpperCase();
  return {
    stale: s.includes("STALE") || d.includes("STALE") || d === "DOCUMENTATION_DRIFT",
    superseded: s.includes("SUPERSEDED"),
    ownerReview: s.includes("OWNER_REVIEW") || a.includes("OWNER_REVIEW"),
  };
}
