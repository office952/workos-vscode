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
  density = "rail",
}: {
  model: AcmPanelUiReadModel;
  onIssueClick: (issue: AcmPanelIssue) => void;
  /**
   * rail — standalone sticky card (lab column)
   * inline — borderless footer for shared tech strip (workbench clean merge)
   */
  density?: "rail" | "inline";
}) {
  if (!model.exists) return null;
  const { blockers, warnings, observations } = groupIssues(model.issues);
  const clean = !blockers.length && !warnings.length && !observations.length;

  if (clean) {
    if (density === "inline") {
      return (
        <div
          className="border-t border-[#2A3548]/50 px-2.5 py-1.5"
          data-testid="intake-v6-acm-validation-rail"
          data-density="inline"
          data-state="clean"
        >
          <p className="text-[10px] leading-snug text-slate-400">
            <span className="font-medium text-emerald-300/90">Validare</span>
            {" · "}
            fără probleme deschise pe Panoul Alucobond
          </p>
        </div>
      );
    }
    return (
      <aside
        className="sticky top-2 px-2.5 py-1.5"
        data-testid="intake-v6-acm-validation-rail"
        data-density="rail"
        data-state="clean"
      >
        <p className="text-[10px] leading-snug text-slate-400">
          <span className="font-medium text-emerald-300/90">Validare panou</span>
          {" · "}
          fără probleme deschise
        </p>
      </aside>
    );
  }

  if (density === "inline") {
    return (
      <div
        className="space-y-1.5 border-t border-[#2A3548]/50 px-2.5 py-1.5"
        data-testid="intake-v6-acm-validation-rail"
        data-density="inline"
        data-state="issues"
      >
        <p className="text-[10px] font-medium text-slate-300">Validare panou</p>
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
      </div>
    );
  }

  return (
    <aside
      className="sticky top-2 space-y-1.5 rounded border border-[#2A3548]/60 bg-[#111827]/40 px-2.5 py-1.5"
      data-testid="intake-v6-acm-validation-rail"
      data-density="rail"
      data-state="issues"
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
              className="w-full rounded border border-[#2A3548]/50 bg-[#0A0F1A]/50 px-2 py-1 text-left text-[11px] text-slate-300 hover:border-[#3b82f5]/40"
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
