import type { IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";
import { shouldShowIntakeV6SmartBanner } from "@/lib/intakeV6/intakeV6WorkspaceHeaderStatus";
import { hasUnsavedAnalysis } from "@/lib/intakeV6/intakeV6AnalysisIdentity";

interface IntakeV6SmartBannerProps {
	state: IntakeV6WorkspaceState;
	firstBlocker?: string | null;
}

export default function IntakeV6SmartBanner({ state, firstBlocker }: IntakeV6SmartBannerProps) {
	if (!shouldShowIntakeV6SmartBanner(state, firstBlocker)) {
		return null;
	}

	let message = "Încarc workspace-ul Intake V6…";

	if (state.analyzerStatus === "analyzing") {
		message = "Analizez SVG (motor nest2)…";
	} else if (hasUnsavedAnalysis(state)) {
		message = "Analiză nesalvată sau fișier schimbat — salvează din Pas 1 înainte de Review/Confirm.";
	} else if (firstBlocker) {
		message = firstBlocker;
	}

	return (
		<div
			className="flex items-center gap-2 border-b border-amber-500/20 bg-amber-500/5 px-5 py-1.5 text-[11px] text-amber-100/90 sm:px-6"
			data-testid="intake-v6-smart-banner"
		>
			<span aria-hidden>◇</span>
			<span className="flex-1 font-medium">{message}</span>
		</div>
	);
}


