import type { IntakeV6StepId } from "./intakeV6Contracts";

export type IntakeV6VisibleProgressStepId = "layers" | "review" | "confirm";

/** Visible operator progress — three steps through final confirmation. */
export const INTAKE_V6_VISIBLE_PROGRESS_STEPS: ReadonlyArray<{
  id: IntakeV6VisibleProgressStepId;
  label: string;
}> = [
  { id: "layers", label: "Straturi" },
  { id: "review", label: "Configurare" },
  { id: "confirm", label: "Confirmare" },
];

export function resolveIntakeV6VisibleProgressStep(step: IntakeV6StepId): IntakeV6VisibleProgressStepId {
  if (step === "layers") return "layers";
  if (step === "confirm") return "confirm";
  return "review";
}

export function intakeV6VisibleStepIndex(step: IntakeV6StepId): number {
  const visible = resolveIntakeV6VisibleProgressStep(step);
  return INTAKE_V6_VISIBLE_PROGRESS_STEPS.findIndex((entry) => entry.id === visible);
}

export const INTAKE_V6_VISIBLE_STEP_COUNT = INTAKE_V6_VISIBLE_PROGRESS_STEPS.length;

export const INTAKE_V6_STEP_ORDER: readonly IntakeV6StepId[] = ["layers", "review", "confirm"];
