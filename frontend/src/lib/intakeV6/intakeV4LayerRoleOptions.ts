import { LAYER_ROLE_OPTIONS, type LayerAutoRole } from "@/lib/svgAnalyzer";

const INTAKE_V4_ROLE_LABEL_OVERRIDES: Partial<Record<LayerAutoRole, string>> = {
  face: "Vector Litere",
  printed_artwork: "Vector Atipic",
  logo: "Vector Atipic",
};

/** Intake V4 operator layer-role labels — internal `return` value preserved for payload compat. */
export const INTAKE_V4_LAYER_ROLE_OPTIONS = LAYER_ROLE_OPTIONS.map((option) => {
  if (option.value === "return") {
    return { ...option, label: "Cant / volum" };
  }
  const override = INTAKE_V4_ROLE_LABEL_OVERRIDES[option.value];
  return override ? { ...option, label: override } : option;
});
