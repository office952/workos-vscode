import type { IntakeV6StepId } from "@/lib/intakeV6/intakeV6Contracts";

const STEPS: Array<{ id: IntakeV6StepId; label: string }> = [
	{ id: "layers", label: "Straturi" },
	{ id: "review", label: "Review" },
	{ id: "confirm", label: "Confirmare" },
];

interface IntakeV6ProgressBarProps {
	currentStep: IntakeV6StepId;
	canAccessStep?: (step: IntakeV6StepId) => boolean;
	onStepClick?: (step: IntakeV6StepId) => void;
	compact?: boolean;
}

export default function IntakeV6ProgressBar({
	currentStep,
	canAccessStep,
	onStepClick,
	compact = false,
}: IntakeV6ProgressBarProps) {
	const currentIndex = STEPS.findIndex((s) => s.id === currentStep);

	return (
		<nav
			className={`flex items-center gap-0 border-t border-[#2A3548]/80 bg-[#111827] ${
				compact ? "px-5 py-1.5 sm:px-6" : "px-7 py-4"
			}`}
			data-testid="intake-v6-progress"
			aria-label="Workspace steps"
		>
			{STEPS.map((step, index) => {
				const done = index < currentIndex;
				const active = step.id === currentStep;
				const accessible = canAccessStep?.(step.id) ?? true;
				const circleClass = compact ? "h-6 w-6 text-[11px]" : "h-9 w-9 text-[13px]";
				return (
					<div key={step.id} className="flex flex-1 items-center">
						<button
							type="button"
							className="flex items-center gap-1.5 bg-transparent p-0 disabled:cursor-not-allowed disabled:opacity-40"
							disabled={!accessible}
							onClick={() => onStepClick?.(step.id)}
							data-testid={`intake-v6-progress-step-${step.id}`}
						>
							<span
								className={`flex items-center justify-center rounded-full border-2 font-bold ${circleClass} ${
									done
										? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
										: active
											? "border-sky-500/40 bg-sky-500/10 text-sky-300"
											: "border-[#2A3548] bg-[#1E293B] text-slate-500"
								}`}
							>
								{done ? "✓" : index + 1}
							</span>
							<span
								className={`font-semibold tracking-wide ${
									compact ? "text-[11px]" : "text-[12px]"
								} ${active ? "text-sky-300" : done ? "text-emerald-400" : "text-slate-500"}`}
							>
								{step.label}
							</span>
						</button>
						{index < STEPS.length - 1 ? (
							<div
								className={`mx-2 h-0.5 flex-1 rounded ${compact ? "mx-1.5" : "mx-3"} ${
									done ? "bg-emerald-500/40" : "bg-[#2A3548]"
								}`}
							/>
						) : null}
					</div>
				);
			})}
		</nav>
	);
}


