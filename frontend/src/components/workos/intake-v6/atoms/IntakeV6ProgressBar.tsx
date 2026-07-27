import type { IntakeV6StepId } from "@/lib/intakeV6/intakeV6Contracts";
import {
	INTAKE_V6_VISIBLE_PROGRESS_STEPS,
	resolveIntakeV6VisibleProgressStep,
} from "@/lib/intakeV6/intakeV6OperatorProgressSteps";

interface IntakeV6ProgressBarProps {
	currentStep: IntakeV6StepId;
	canAccessStep?: (step: IntakeV6StepId) => boolean;
	/** When set, ✓ only appears if the step is actually complete (not merely visited). */
	isStepComplete?: (step: IntakeV6StepId) => boolean;
	onStepClick?: (step: IntakeV6StepId) => void;
	compact?: boolean;
}

export default function IntakeV6ProgressBar({
	currentStep,
	canAccessStep,
	isStepComplete,
	onStepClick,
	compact = false,
}: IntakeV6ProgressBarProps) {
	const visibleStep = resolveIntakeV6VisibleProgressStep(currentStep);
	const currentIndex = INTAKE_V6_VISIBLE_PROGRESS_STEPS.findIndex((s) => s.id === visibleStep);

	return (
		<nav
			className={`flex items-center gap-0 border-t border-wo-border-strong/80 bg-wo-surface-raised ${
				compact ? "px-5 py-1.5 sm:px-6" : "px-7 py-4"
			}`}
			data-testid="intake-v6-progress"
			aria-label="Workspace steps"
		>
			{INTAKE_V6_VISIBLE_PROGRESS_STEPS.map((step, index) => {
				const visited = index < currentIndex;
				const complete = isStepComplete ? isStepComplete(step.id) : visited;
				const done = visited && complete;
				const active = step.id === visibleStep;
				const accessible = canAccessStep?.(step.id) ?? true;
				const circleClass = compact ? "h-6 w-6 text-[11px]" : "h-9 w-9 text-[13px]";
				const inactiveMuted = !active && !done && !(visited && !complete);
				return (
					<div key={step.id} className="flex flex-1 items-center">
						<button
							type="button"
							className={`flex items-center gap-1.5 bg-transparent p-0 ${
								accessible ? "" : "cursor-not-allowed"
							}`}
							disabled={!accessible}
							onClick={() => onStepClick?.(step.id)}
							data-testid={`intake-v6-progress-step-${step.id}`}
							data-step-complete={done ? "true" : "false"}
							aria-current={active ? "step" : undefined}
						>
							<span
								className={`flex items-center justify-center rounded-full border-2 font-bold ${circleClass} ${
									done
										? "border-wo-success/40 bg-wo-success-muted text-wo-success"
										: active
											? "border-wo-info/40 bg-wo-info-muted text-wo-info"
											: visited && !complete
												? "border-wo-warning/40 bg-wo-warning-muted text-wo-warning"
												: "border-wo-border-strong bg-wo-surface-inset text-wo-text-muted"
								}`}
							>
								{done ? "✓" : index + 1}
							</span>
							<span
								className={`font-semibold tracking-wide ${
									compact ? "text-[11px]" : "text-[12px]"
								} ${
									active
										? "text-wo-info"
										: done
											? "text-wo-success"
											: visited && !complete
												? "text-wo-warning"
												: inactiveMuted
													? "text-wo-text-muted"
													: "text-wo-text-secondary"
								}`}
							>
								{step.label}
							</span>
						</button>
						{index < INTAKE_V6_VISIBLE_PROGRESS_STEPS.length - 1 ? (
							<div
								className={`mx-2 h-0.5 flex-1 rounded ${compact ? "mx-1.5" : "mx-3"} ${
									done ? "bg-wo-success/40" : "bg-wo-border-subtle"
								}`}
							/>
						) : null}
					</div>
				);
			})}
		</nav>
	);
}
