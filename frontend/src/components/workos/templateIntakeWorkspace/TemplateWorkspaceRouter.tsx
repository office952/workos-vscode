import { AlertTriangle } from "lucide-react";
import { shouldUseVolumetricIntakePage } from "@/lib/volumetricIntakeRoute";
import type { TemplateWorkspaceBaseProps } from "./types";
import VolumetricLettersWorkspace from "./VolumetricLettersWorkspace";

function UnsupportedTemplateWorkspaceFallback({
  requestId,
  confirmedTemplateCode,
  productFamily,
}: {
  requestId: string;
  confirmedTemplateCode: string | null | undefined;
  productFamily: string | null | undefined;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 min-h-[40vh] px-6"
      data-testid="unsupported-template-workspace"
    >
      <AlertTriangle className="w-10 h-10 text-amber-400" />
      <p className="text-[14px] text-slate-300 text-center max-w-lg">
        Cererea <span className="font-mono text-blue-400">{requestId}</span> are
        un template neacceptat încă în workspace modular.
      </p>
      <p className="text-[11px] text-slate-500 text-center max-w-md">
        Template: <span className="font-mono">{confirmedTemplateCode || "—"}</span>
        {" · "}
        Familie: <span className="font-mono">{productFamily || "—"}</span>
      </p>
      <p className="text-[11px] text-slate-500 text-center max-w-md">
        Folosiți calea generică din Work Intake sau confirmați un template suportat.
      </p>
    </div>
  );
}

export interface TemplateWorkspaceRouterProps extends TemplateWorkspaceBaseProps {
  /** When false, router renders nothing — caller shows generic IntakeDetail. */
  enabled: boolean;
}

/**
 * Routes confirmed template codes to composed template workspaces.
 * Fallback: IntakeDetail generic path (enabled=false).
 */
export default function TemplateWorkspaceRouter({
  enabled,
  ...workspaceProps
}: TemplateWorkspaceRouterProps) {
  if (!enabled) return null;

  const useVolumetric = shouldUseVolumetricIntakePage(
    workspaceProps.confirmedTemplateCode,
    workspaceProps.request.productFamily
  );

  if (useVolumetric) {
    return <VolumetricLettersWorkspace {...workspaceProps} />;
  }

  return (
    <UnsupportedTemplateWorkspaceFallback
      requestId={workspaceProps.request.id}
      confirmedTemplateCode={workspaceProps.confirmedTemplateCode}
      productFamily={workspaceProps.request.productFamily}
    />
  );
}
