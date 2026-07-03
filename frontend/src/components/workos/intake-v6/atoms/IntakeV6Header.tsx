import type { IntakeV6StepId, IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";
import { useIntakeV6WorkspaceHeaderStatusOptional } from "../IntakeV6WorkspaceHeaderStatusContext";
import IntakeV6ProgressBar from "./IntakeV6ProgressBar";
import { v6 } from "./intakeV6Presentation";

const STEP_LABELS: Record<IntakeV6StepId, string> = {
  layers: "Straturi",
  review: "Review",
  confirm: "Confirmare",
};

interface IntakeV6HeaderProps {
  state: IntakeV6WorkspaceState;
  onPromoteTemplateV2?: () => void;
  promoteTemplateV2Status?: "idle" | "running" | "success" | "error";
  promoteTemplateV2Message?: string | null;
  canAccessStep?: (step: IntakeV6StepId) => boolean;
  onStepClick?: (step: IntakeV6StepId) => void;
}

export default function IntakeV6Header({
  state,
  onPromoteTemplateV2,
  promoteTemplateV2Status = "idle",
  promoteTemplateV2Message,
  canAccessStep,
  onStepClick,
}: IntakeV6HeaderProps) {
  const statusCtx = useIntakeV6WorkspaceHeaderStatusOptional();
  const ws = state.workspace;
  const code = ws?.workspace_code ?? "—";
  const payload = ws?.payload;
  const binding = payload?.product_binding;
  const template =
    (binding != null && typeof binding === "object" && !Array.isArray(binding)
      ? (binding as { template_label?: string; template_code?: string }).template_label ??
        (binding as { template_code?: string }).template_code
      : undefined) ??
    ws?.template_code ??
    "—";

  return (
    <header className="border-b border-[#2A3548] bg-[#111827]" data-testid="intake-v6-header">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 px-5 py-2 sm:px-6">
        <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-2 gap-y-1 text-[12px]">
          <span
            className={`${v6.mono} font-semibold text-sky-300`}
            data-testid="intake-v6-header-workspace-code"
          >
            {code}
          </span>
          <span className="text-slate-600" aria-hidden>
            ·
          </span>
          <span className="truncate text-slate-400" data-testid="intake-v6-header-template">
            {template}
          </span>
          <span className="text-slate-600" aria-hidden>
            ·
          </span>
          <span className="text-slate-500" data-testid="intake-v6-header-step">
            {STEP_LABELS[state.currentStep]}
          </span>
        </div>

        {onPromoteTemplateV2 ? (
          <div className="flex shrink-0 items-center gap-2">
            <button
              type="button"
              className={`${v6.btnGhost} px-2 py-0.5 text-[11px]`}
              onClick={onPromoteTemplateV2}
              disabled={promoteTemplateV2Status === "running"}
              data-testid="intake-v6-promote-template-v2"
            >
              {promoteTemplateV2Status === "running" ? "Actualizez…" : "Template v2"}
            </button>
            {promoteTemplateV2Message ? (
              <span
                className={`text-[11px] ${
                  promoteTemplateV2Status === "error" ? "text-red-300" : "text-emerald-300"
                }`}
                data-testid="intake-v6-promote-template-v2-message"
              >
                {promoteTemplateV2Message}
              </span>
            ) : null}
          </div>
        ) : null}
      </div>

      <IntakeV6ProgressBar
        compact
        currentStep={state.currentStep}
        canAccessStep={canAccessStep}
        onStepClick={onStepClick}
      />
    </header>
  );
}
