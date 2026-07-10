import type { IntakeV6StepId } from "./intakeV6Contracts";

/** Visible operator progress — internal `confirm` maps to configurare. */
export const INTAKE_V6_VISIBLE_PROGRESS_STEPS: ReadonlyArray<{
  id: "layers" | "review";
  label: string;
}> = [
  { id: "layers", label: "Straturi" },
  { id: "review", label: "Configurare" },
];

export function resolveIntakeV6VisibleProgressStep(step: IntakeV6StepId): "layers" | "review" {
  return step === "layers" ? "layers" : "review";
}

export function intakeV6VisibleStepIndex(step: IntakeV6StepId): number {
  return resolveIntakeV6VisibleProgressStep(step) === "layers" ? 0 : 1;
}

export const INTAKE_V6_VISIBLE_STEP_COUNT = INTAKE_V6_VISIBLE_PROGRESS_STEPS.length;
