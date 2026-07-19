import type { IntakeV6WorkspaceHook } from "@/lib/intakeV6/useIntakeV6Workspace";
import IntakeV6FinalConfigurationSummary from "../IntakeV6FinalConfigurationSummary";

export interface IntakeV6ConfirmStepProps {
	hook: IntakeV6WorkspaceHook;
}

export default function IntakeV6ConfirmStep({ hook }: IntakeV6ConfirmStepProps) {
	return (
		<IntakeV6FinalConfigurationSummary hook={hook} variant="legacyPage" defaultExpanded />
	);
}
