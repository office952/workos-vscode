/**
 * Vector assets API — SVG metrics and layer analysis (read-only).
 */

import { getAPIBaseURL } from "@/lib/config";
import type { SvgLayerAnalysisResult } from "@/lib/svgLayerAnalysis";

export const vectorAssetsApi = {
  analyzeLayers: async (
    svgText: string,
    options?: {
      knownTemplateCodes?: string[];
      sourceFileName?: string;
      manualLayerMappings?: Record<string, string>;
    }
  ): Promise<SvgLayerAnalysisResult> => {
    const res = await fetch(
      `${getAPIBaseURL()}/api/v1/vector-assets/analyze-layers`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          svg_text: svgText,
          known_template_codes: options?.knownTemplateCodes,
          source_file_name: options?.sourceFileName,
          manual_layer_mappings: options?.manualLayerMappings,
        }),
      }
    );
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(
        body?.detail ?? `analyze-layers failed: HTTP ${res.status}`
      );
    }
    return res.json();
  },
};
