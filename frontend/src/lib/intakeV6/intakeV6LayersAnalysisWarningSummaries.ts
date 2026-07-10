import type { LayerRoleConfirmation, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";

const PSEUDO_LAYER_HINT =
  /pseudo-layer generated from solid vector fill/i;
const STROKE_VECTOR_HINT = /stroke-only vector isolated/i;

export function buildIntakeV6LayersAnalysisWarningSummaries(input: {
  report: SvgAnalysisCoreReport | null;
  confirmation: LayerRoleConfirmation | null;
  parseWarning?: string | null;
  scopeWarnings: string[];
}): string[] {
  const { report, parseWarning, scopeWarnings } = input;
  const summaries: string[] = [];

  if (parseWarning) {
    summaries.push(`Parse SVG: ${parseWarning}`);
  }

  for (const warning of scopeWarnings) {
    summaries.push(warning);
  }

  if (!report) return summaries.slice(0, 8);

  let pseudoCount = 0;
  let atypicalCount = 0;
  for (const layer of report.layers) {
    const messages = (layer.warnings ?? []).map((warning) =>
      typeof warning === "string" ? warning : warning.message,
    );
    if (messages.some((message) => PSEUDO_LAYER_HINT.test(message))) pseudoCount += 1;
    const isAtypical =
      layer.autoRole === "printed_artwork" ||
      layer.autoRole === "logo" ||
      messages.some((message) => STROKE_VECTOR_HINT.test(message));
    if (isAtypical) atypicalCount += 1;
  }

  if (pseudoCount > 0) {
    summaries.push(
      `${pseudoCount} ${pseudoCount === 1 ? "strat propus" : "straturi propuse"} ca Vector Litere — confirmă rolurile.`,
    );
  }
  if (atypicalCount > 0) {
    summaries.push(
      `${atypicalCount} ${atypicalCount === 1 ? "strat atipic" : "straturi atipice"} (logo/emblemă) — verifică rolul.`,
    );
  }

  const seen = new Set<string>();
  for (const layer of report.layers) {
    for (const warning of layer.warnings ?? []) {
      const message = typeof warning === "string" ? warning : warning.message;
      if (PSEUDO_LAYER_HINT.test(message) || STROKE_VECTOR_HINT.test(message)) continue;
      if (seen.has(message)) continue;
      seen.add(message);
      summaries.push(message);
    }
  }

  return summaries.slice(0, 8);
}
