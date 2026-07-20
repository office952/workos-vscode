import type { AcmPanelIssue, AcmPanelUiReadModel } from "@/lib/intakeV6/acmPanel/uiReadModel";

function groupIssues(issues: AcmPanelIssue[]) {
  return {
    blockers: issues.filter((i) => i.severity === "blocker"),
    warnings: issues.filter((i) => i.severity === "warning"),
    observations: issues.filter((i) => i.severity === "observation"),
  };
}

export default function IntakeV6AcmPanelValidationRail({
  model,
  onIssueClick,
}: {
  model: AcmPanelUiReadModel;
  onIssueClick: (issue: AcmPanelIssue) => void;
}) {
  if (!model.exists) return null;
  const { blockers, warnings, observations } = groupIssues(model.issues);
  if (!blockers.length && !warnings.length && !observations.length) {
    return (
      <aside
        className="sticky top-2 rounded border border-emerald-500/25 bg-emerald-950/15 px-2.5 py-2"
        data-testid="intake-v6-acm-validation-rail"
      >
        <p className="text-[11px] font-semibold text-emerald-200">Validare panou</p>
        <p className="mt-0.5 text-[10px] text-slate-400">Fără probleme deschise pe Panoul Alucobond.</p>
      </aside>
    );
  }

  return (
    <aside
      className="sticky top-2 space-y-2 rounded border border-[#2A3548]/70 bg-[#111827]/55 px-2.5 py-2"
      data-testid="intake-v6-acm-validation-rail"
    >
      <p className="text-[11px] font-semibold text-slate-200">Validare panou</p>
      {blockers.length ? (
        <IssueGroup title="Blocante" items={blockers} tone="blocker" onIssueClick={onIssueClick} />
      ) : null}
      {warnings.length ? (
        <IssueGroup title="Avertizări" items={warnings} tone="warning" onIssueClick={onIssueClick} />
      ) : null}
      {observations.length ? (
        <IssueGroup
          title="Observații"
          items={observations}
          tone="observation"
          onIssueClick={onIssueClick}
        />
      ) : null}
    </aside>
  );
}

function IssueGroup({
  title,
  items,
  tone,
  onIssueClick,
}: {
  title: string;
  items: AcmPanelIssue[];
  tone: "blocker" | "warning" | "observation";
  onIssueClick: (issue: AcmPanelIssue) => void;
}) {
  const color =
    tone === "blocker"
      ? "text-rose-200"
      : tone === "warning"
        ? "text-amber-200"
        : "text-slate-400";
  return (
    <div data-testid={`intake-v6-acm-validation-${tone}`}>
      <p className={`text-[10px] font-semibold uppercase tracking-wide ${color}`}>{title}</p>
      <ul className="mt-1 space-y-1">
        {items.map((issue) => (
          <li key={issue.id}>
            <button
              type="button"
              className="w-full rounded border border-[#2A3548]/50 bg-[#0A0F1A]/50 px-2 py-1.5 text-left text-[11px] text-slate-300 hover:border-[#3b82f5]/40"
              data-testid={`intake-v6-acm-issue-${issue.id}`}
              onClick={() => onIssueClick(issue)}
            >
              {issue.message}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
