export type SvgArtworkExecutionType =
  | "print_laminate"
  | "print_only"
  | "cut_vinyl"
  | "translucent_vinyl"
  | "needs_decision";

export type SvgArtworkColorMode =
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
  { value: "print_laminate", label: "Print + laminare" },
  { value: "print_only", label: "Print" },
  { value: "cut_vinyl", label: "Colant tăiat" },
  { value: "translucent_vinyl", label: "Colant translucid" },
  { value: "needs_decision", label: "Necesită decizie" },
];

export const SVG_ARTWORK_COLOR_MODE_OPTIONS: Array<{
  value: SvgArtworkColorMode;
  label: string;
}> = [
  { value: "polychrome", label: "Policromie" },
  { value: "monochrome", label: "Monocrom" },
  { value: "unknown", label: "Necunoscut" },
];