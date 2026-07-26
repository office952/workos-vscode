export type IntakeV6AnalysisSourceType = "svg" | "image";

export type IntakeV6AnalysisSourceStatus = "active" | "preview_only" | "disabled";

export type IntakeV6AnalysisSourceMethodId =
  | "svg_analyzer_intake_v6"
  | "image_analyzer_intake_v6_preview";

export interface IntakeV6AnalysisSourceDefinition {
  sourceType: IntakeV6AnalysisSourceType;
  methodId: IntakeV6AnalysisSourceMethodId;
  label: string;
  description: string;
  status: IntakeV6AnalysisSourceStatus;
  canCreateWorkspace: boolean;
  requiresOperatorReview: boolean;
}

export const INTAKE_V6_ANALYSIS_SOURCES: IntakeV6AnalysisSourceDefinition[] = [
  {
    sourceType: "svg",
    methodId: "svg_analyzer_intake_v6",
    label: "SVG Analyzer - Intake V6",
    description:
      "Analizeaza fisiere SVG, pregateste Product Truth si porneste formularul modular Intake V6.",
    status: "active",
    canCreateWorkspace: true,
    requiresOperatorReview: true,
  },
  {
    sourceType: "image",
    methodId: "image_analyzer_intake_v6_preview",
    label: "Image Analyzer - Intake V6",
    description:
      "Va permite prefill din analiza imagine dupa review operator. Momentan este doar preview; nu creeaza oferta, comanda sau executie.",
    status: "preview_only",
    canCreateWorkspace: false,
    requiresOperatorReview: true,
  },
];

export function getIntakeV6AnalysisSourceDefinition(
  methodId: IntakeV6AnalysisSourceMethodId,
): IntakeV6AnalysisSourceDefinition | undefined {
  return INTAKE_V6_ANALYSIS_SOURCES.find((source) => source.methodId === methodId);
}

export function getIntakeV6AnalysisSourceStatusLabel(
  status: IntakeV6AnalysisSourceStatus,
): string {
  switch (status) {
    case "active":
      return "Activ";
    case "preview_only":
      return "Preview only";
    default:
      return "Disabled";
  }
}

export function canCreateIntakeV6WorkspaceFromSource(
  source: IntakeV6AnalysisSourceDefinition,
): boolean {
  return source.status === "active" && source.canCreateWorkspace;
}