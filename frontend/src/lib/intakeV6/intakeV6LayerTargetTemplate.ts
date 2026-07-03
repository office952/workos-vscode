import type { LayerAutoRole, SvgAnalysisCoreReport } from "@/lib/svgAnalyzer";

export const INTAKE_V6_LETTERS_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2";
export const INTAKE_V6_LOGO_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO_v1";

const LOGO_ROLE_VALUES = new Set<string>(["printed_artwork", "logo"]);
const LOGO_LAYER_NAME_RE = /(logo|sigla|siglă|emblem|emblema)/i;

export interface IntakeV6LayerTargetTemplate {
  templateCode: string;
  templateLabel: string;
  statusLabel: string;
  moduleStatusLabel: string;
}

function normalizeTemplateCode(code: string | null | undefined): string {
  return String(code ?? "").trim() || INTAKE_V6_LETTERS_TEMPLATE_CODE;
}

export function isLogoAssemblyLayer(args: {
  layer: SvgAnalysisCoreReport["layers"][number];
  selectedRole: LayerAutoRole | string | null | undefined;
}): boolean {
  const { layer, selectedRole } = args;
  if (selectedRole && LOGO_ROLE_VALUES.has(selectedRole)) return true;
  if (LOGO_LAYER_NAME_RE.test(layer.name)) return true;
  return layer.layerKind === "raster_artwork";
}

export function resolveIntakeV6LayerTargetTemplate(args: {
  layer: SvgAnalysisCoreReport["layers"][number];
  selectedRole: LayerAutoRole | string | null | undefined;
  workspaceTemplateCode?: string | null;
}): IntakeV6LayerTargetTemplate {
  if (isLogoAssemblyLayer(args)) {
    return {
      templateCode: INTAKE_V6_LOGO_TEMPLATE_CODE,
      templateLabel: "Logo volumetric",
      statusLabel: `Target propus: ${INTAKE_V6_LOGO_TEMPLATE_CODE}`,
      moduleStatusLabel: "Template logo read-only pregătit în registry",
    };
  }

  const lettersTemplateCode = normalizeTemplateCode(args.workspaceTemplateCode);
  return {
    templateCode: lettersTemplateCode,
    templateLabel: "Litere volumetrice",
    statusLabel: `Template activ: ${lettersTemplateCode}`,
    moduleStatusLabel: "Ansamblu litere activ",
  };
}