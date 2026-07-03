import { getAPIBaseURL } from "@/lib/config";

export type CanonicalOutputBlockPreviewRequest = {
  block_ids?: string[];
  block_types?: string[];
  context: "quote_preview";
  source_payload: Record<string, unknown>;
};

export type CanonicalOutputBlockPreviewIssue = {
  code?: string;
  message?: string;
  field?: string;
  source_field?: string;
  variable_key?: string;
  [key: string]: unknown;
};

export type CanonicalRenderedOutputBlock = {
  block_id: string;
  block_type: string;
  title?: string | null;
  approval_status: string;
  rendered_text?: string | null;
  variables_used: Record<string, unknown>;
  source_fields_used: string[];
  skipped: boolean;
  skip_reason?: string | null;
  warnings: CanonicalOutputBlockPreviewIssue[];
  blockers: CanonicalOutputBlockPreviewIssue[];
};

export type CanonicalOutputBlockPreviewResponse = {
  preview_only: true;
  context: "quote_preview";
  rendered_blocks: CanonicalRenderedOutputBlock[];
  warnings: CanonicalOutputBlockPreviewIssue[];
  blockers: CanonicalOutputBlockPreviewIssue[];
};

export async function previewCanonicalOutputBlocks(
  request: CanonicalOutputBlockPreviewRequest
): Promise<CanonicalOutputBlockPreviewResponse> {
  const url = `${getAPIBaseURL()}/api/v1/product-system/output-blocks/preview`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "Unknown error");
    throw new Error(
      `Failed to preview canonical output blocks: ${response.status} - ${detail}`
    );
  }

  return response.json() as Promise<CanonicalOutputBlockPreviewResponse>;
}
