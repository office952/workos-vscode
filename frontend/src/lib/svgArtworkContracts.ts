export type SvgArtworkExecutionType =
  | "none_raw_plexi"
  | "print_laminate"
  | "print_only"
  | "cut_vinyl"
  | "translucent_vinyl"
  | "needs_decision";

export type SvgArtworkColorMode =
  | "none"
  | "polychrome"
  | "monochrome"
  | "unknown";

export interface SvgArtworkFinishAssignment {
  layerKey: string;
  executionType: SvgArtworkExecutionType;
  colorMode: SvgArtworkColorMode;
  materialCode?: string | null;
  confirmedByOperator?: boolean;
}

export const SVG_ARTWORK_EXECUTION_OPTIONS: Array<{
  value: SvgArtworkExecutionType;
  label: string;
}> = [
  { value: "none_raw_plexi", label: "Fără finisaj — plexiglas brut" },
  { value: "print_laminate", label: "Printat / Laminat" },
  { value: "print_only", label: "Print" },
  { value: "cut_vinyl", label: "Colant tăiat" },
  { value: "translucent_vinyl", label: "Colant translucid" },
  { value: "needs_decision", label: "Necesită decizie" },
];

export const SVG_ARTWORK_COLOR_MODE_OPTIONS: Array<{
  value: SvgArtworkColorMode;
  label: string;
}> = [
  { value: "none", label: "Fără culoare suplimentară" },
  { value: "polychrome", label: "Policromie" },
  { value: "monochrome", label: "Monocrom" },
  { value: "unknown", label: "Necunoscut" },
];