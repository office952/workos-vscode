import type { IntakeV6WorkspaceState } from "@/lib/intakeV6/intakeV6Contracts";

interface IntakeV6StatusBarProps {
	state: IntakeV6WorkspaceState;
	surfaceLabel?: string;
}

export default function IntakeV6StatusBar({
	state,
	surfaceLabel = "Intake V6 · Atoms shell",
}: IntakeV6StatusBarProps) {
	const total = state.layerChips.length;
	const confirmed = state.layerChips.filter((c) => c.status === "confirmed" || c.status === "ignored").length;
	const pending = total - confirmed;

	return (
		<div
			className="flex flex-wrap items-center gap-4 border-b border-wo-border-strong bg-wo-hover px-7 py-2 text-[11px] text-wo-text-muted"
			data-testid="intake-v6-status-bar"
		>
			<span className="inline-flex items-center gap-1.5">
				<span className="h-2 w-2 rounded-full bg-emerald-400" />
				{confirmed}/{total || "—"} layers confirmed
			</span>
			{pending > 0 ? (
				<span className="inline-flex items-center gap-1.5">
					<span className="h-2 w-2 rounded-full bg-amber-400" />
					{pending} pending
				</span>
			) : null}
			<span className="ml-auto text-[10px] text-wo-text-dim">{surfaceLabel}</span>
		</div>
	);
}


