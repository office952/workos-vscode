import { useCallback, useState } from "react";
import { useLocation } from "react-router-dom";
import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";
import { promoteIntakeV6VolumetricLettersV2Template } from "@/lib/intakeV6/intakeV6Api";
import {
  INTAKE_V6_STEP_ORDER,
  INTAKE_V6_VISIBLE_STEP_COUNT,
  intakeV6VisibleStepIndex,
} from "@/lib/intakeV6/intakeV6OperatorProgressSteps";
import IntakeV6ConfirmStep from "./steps/IntakeV6ConfirmStep";
import IntakeV6SvgAnalyzerStep from "./steps/IntakeV6SvgAnalyzerStep";
import IntakeV6ReviewStep from "./steps/IntakeV6ReviewStep";
import IntakeV6Header from "./atoms/IntakeV6Header";
import IntakeV6SmartBanner from "./atoms/IntakeV6SmartBanner";
import { IntakeV6WorkspaceHeaderStatusProvider } from "./IntakeV6WorkspaceHeaderStatusContext";
import IntakeV6OperatorWorkspaceFooter from "./IntakeV6OperatorWorkspaceFooter";
import { v6 } from "./atoms/intakeV6Presentation";
import type { IntakeV6StepId } from "@/lib/intakeV6/intakeV6Contracts";

interface IntakeV6OperatorWorkspaceProps {
  hook: IntakeV6WorkspaceHook;
}

export default function IntakeV6OperatorWorkspace({ hook }: IntakeV6OperatorWorkspaceProps) {
  const location = useLocation();
  const isIntakeV6 = location.pathname.startsWith("/intake-v6") || location.pathname.startsWith("/intake-v6-app");
  const [promoteStatus, setPromoteStatus] = useState<"idle" | "running" | "success" | "error">("idle");
  const [promoteMessage, setPromoteMessage] = useState<string | null>(null);
  const {
    state,
    trySetStep,
    canAccessStep,
    continueFromAnalyzer,
    canContinueFromAnalyzer,
    canContinueFromReview,
    firstBlocker,
  } = hook;

  const visibleStepIndex = intakeV6VisibleStepIndex(state.currentStep);
  const stepIndex = INTAKE_V6_STEP_ORDER.indexOf(state.currentStep);

  const goBack = () => {
    if (stepIndex > 0) trySetStep(INTAKE_V6_STEP_ORDER[stepIndex - 1]!);
  };

  const goNext = () => {
    if (state.currentStep === "layers") {
      void continueFromAnalyzer();
      return;
    }
    if (state.currentStep === "review" && canContinueFromReview) {
      trySetStep("confirm");
    }
  };

  const nextDisabled =
    state.currentStep === "layers"
      ? !canContinueFromAnalyzer
      : state.currentStep === "review"
        ? !canContinueFromReview
        : stepIndex >= INTAKE_V6_STEP_ORDER.length - 1;

  const nextLabel =
    state.currentStep === "layers"
      ? state.phase === "persisting"
        ? "Salvez..."
        : "Continuă la Configurare"
      : state.currentStep === "review"
        ? "Continuă la Confirmare"
        : "Flux complet";

  const footerBlocker =
    state.currentStep === "layers" && !canContinueFromAnalyzer
      ? firstBlocker
      : state.currentStep === "review" && !canContinueFromReview
        ? firstBlocker
        : null;

  const promoteTemplateV2 = useCallback(async () => {
    setPromoteStatus("running");
    setPromoteMessage(null);
    try {
      const result = await promoteIntakeV6VolumetricLettersV2Template();
      setPromoteStatus("success");
      setPromoteMessage(
        `${result.template_code} ${result.template_action}; dossier ${result.dossier_status}; pricing DB ok`,
      );
    } catch (err) {
      setPromoteStatus("error");
      setPromoteMessage(err instanceof Error ? err.message : "Nu am putut actualiza template v2.");
    }
  }, []);

  const handleStepClick = useCallback(
    (step: IntakeV6StepId) => {
      trySetStep(step);
    },
    [trySetStep],
  );

  return (
    <IntakeV6WorkspaceHeaderStatusProvider
      defaultHandlers={{
        onJumpToLayers: () => trySetStep("layers"),
        onJumpToConfirm: () => trySetStep("confirm"),
      }}
    >
    <div className={v6.page} data-testid="intake-v6-operator-workspace">
      <IntakeV6SmartBanner state={state} firstBlocker={firstBlocker} />
      <IntakeV6Header
        state={state}
        onPromoteTemplateV2={isIntakeV6 ? undefined : promoteTemplateV2}
        promoteTemplateV2Status={promoteStatus}
        promoteTemplateV2Message={promoteMessage}
        canAccessStep={canAccessStep}
        onStepClick={handleStepClick}
      />

      <main
        className={v6.main}
        data-testid="intake-v6-workspace-main"
        data-intake-v6-step={state.currentStep}
      >
        {state.phase === "loading" ? (
          <div
            className="mb-4 rounded border border-sky-500/20 bg-sky-500/10 px-4 py-3 text-[12px] text-sky-100"
            data-testid="intake-v6-loading-state"
          >
            Încarc workspace-ul Intake V6 și verific analiza salvată.
          </div>
        ) : null}
        {state.phase === "error" && state.error ? (
          <p className="mb-4 text-[12px] text-red-300" data-testid="intake-v6-load-error">
            {state.error}
          </p>
        ) : null}
        {state.currentStep === "layers" ? <IntakeV6SvgAnalyzerStep hook={hook} /> : null}
        {state.currentStep === "review" ? <IntakeV6ReviewStep hook={hook} /> : null}
        {state.currentStep === "confirm" ? <IntakeV6ConfirmStep hook={hook} /> : null}
      </main>

      <IntakeV6OperatorWorkspaceFooter
        currentStep={state.currentStep}
        stepIndex={visibleStepIndex}
        stepOrderLength={INTAKE_V6_VISIBLE_STEP_COUNT}
        footerBlocker={footerBlocker}
        nextDisabled={nextDisabled}
        nextLabel={nextLabel}
        nextButtonClassName={
          state.currentStep === "layers" ? `${v6.btnConfirm} min-w-[11rem]` : v6.btnPrimary
        }
        onBack={goBack}
        onNext={goNext}
        persisting={state.phase === "persisting"}
        workspaceState={state}
        canContinueFromAnalyzer={canContinueFromAnalyzer}
      />
    </div>
    </IntakeV6WorkspaceHeaderStatusProvider>
  );
}
