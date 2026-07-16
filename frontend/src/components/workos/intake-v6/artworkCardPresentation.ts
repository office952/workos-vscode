import type { IntakeV6ArtworkFinish } from "@/lib/intakeV6/intakeV6ArtworkFinish";
import { normalizeArtworkFinishState } from "@/lib/intakeV6/intakeV4ArtworkFinish";
import { cantFinishLabel } from "./letterGroupCardPresentation";

export const INTAKE_V6_ARTWORK_LAYER_ACCENT = "#0891b2";

const EXECUTION_LABEL: Record<string, string> = {
  none_raw_plexi: "Fără finisaj — plexiglas brut",
  print_laminate: "Print + laminare",
  print_only: "Print",
  vinyl_only: "Vinyl",
  cut_vinyl: "Oracal",
  translucent_vinyl: "Oracal 8500 — translucid",
  needs_decision: "Fără finisaj — plexiglas brut",
};

const ARTWORK_MATERIAL_LABEL: Record<string, string> = {
  ORACAL_641: "Oracal 641",
  ORACAL_651: "Oracal 651",
  ORACAL_8500: "Oracal 8500 — translucid",
  ORAFOL_PRINT_LAMINATION: "Print + laminare",
};

export function artworkExecutionLabel(row: IntakeV6ArtworkFinish): string {
  const normalized = normalizeArtworkFinishState(row);
  return EXECUTION_LABEL[normalized.execution_type] ?? "Print + laminare";
}

export function artworkTransparencyLabel(row: IntakeV6ArtworkFinish): string | null {
  if (row.print_transparency === "translucent") return "Translucid";
  if (row.print_transparency === "transparent") return "Transparent";
  return null;
}

export function buildArtworkFaceSummaryLine(row: IntakeV6ArtworkFinish): string {
  const normalized = normalizeArtworkFinishState(row);
  const materialLabel = normalized.material_code ? ARTWORK_MATERIAL_LABEL[normalized.material_code] : null;
  const parts = [materialLabel ?? artworkExecutionLabel(normalized)];
  if (normalized.color_mode === "polychrome") parts.push("Policrom");
  return parts.join(" · ");
}

export function buildArtworkCantSummaryLine(row: IntakeV6ArtworkFinish): string {
  const cantFinish = cantFinishLabel(row.return_finish_type);
  const depth = row.return_depth_mm != null ? `${row.return_depth_mm} mm` : "60 mm";
  return `${cantFinish} · ${depth}`;
}

export { buildSpateSummaryLine } from "./letterGroupCardPresentation";

export function buildArtworkSummaryLine(row: IntakeV6ArtworkFinish): string {
  return `${buildArtworkFaceSummaryLine(row)} · ${buildArtworkCantSummaryLine(row)}`;
}
