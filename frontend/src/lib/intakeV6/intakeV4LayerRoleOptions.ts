import type { LayerAutoRole } from "@/lib/svgAnalyzer";
import { operatorStatusSemanticRo } from "@/lib/intakeV6/intakeV6OperatorVocabulary";

/** Operator-facing role list; values stay compatible with analyzer/backend payload. */
export const INTAKE_V4_LAYER_ROLE_OPTIONS: ReadonlyArray<{ value: LayerAutoRole; label: string }> = [
  { value: "face", label: "Litere volumetrice / Vector litere" },
  { value: "logo", label: "Logo volumetric / Vector atipic constructiv" },
  { value: "printed_artwork", label: "Logo volumetric / Vector atipic constructiv" },
  { value: "support_panel", label: "Fundal / suport / bond / caseta" },
  { value: "inner_hole", label: "Decupaj interior" },
  { value: "drill", label: "Gauri montaj" },
  { value: "reference", label: "Referinta / ghidaj" },
  { value: "ignore", label: "Ignora strat" },
  { value: "return", label: "Cant / volum" },
  { value: "backing", label: "Spate / backing" },
  { value: "vinyl", label: "Vinil aplicat" },
  { value: "unknown", label: operatorStatusSemanticRo("needs_operator") },
];
