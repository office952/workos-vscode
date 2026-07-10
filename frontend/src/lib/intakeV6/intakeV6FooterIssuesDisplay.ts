import type { ReviewHeaderStatusAction, ReviewHeaderStatusDetail } from "./intakeV6ReviewHeaderStatus";

export type FooterIssueGroupId = "actions" | "warnings" | "information" | "technical";

export interface FooterIssueEntry {
  id: string;
  title: string;
  description?: string;
  actionId?: string;
}

export interface FooterIssueGroup {
  id: FooterIssueGroupId;
  label: string;
  entries: FooterIssueEntry[];
}

export interface IntakeV6FooterIssuesDisplay {
  totalCount: number;
  actionCount: number;
  warningCount: number;
  informationCount: number;
  technicalCount: number;
  primaryActionReason: string | null;
  groups: FooterIssueGroup[];
}

const GROUP_LABELS: Record<FooterIssueGroupId, string> = {
  actions: "Acțiuni necesare",
  warnings: "Avertizări",
  information: "Informații",
  technical: "Detalii tehnice",
};

function isLikelyTechnicalWarning(message: string): boolean {
  const token = message.trim();
  if (!token) return false;
  if (/^[a-z0-9_]+:/i.test(token)) return true;
  if (/pseudo-layer|stroke-only vector|unclassified_vector|operator_confirmation_missing/i.test(token)) {
    return true;
  }
  return false;
}

function pushUniqueEntry(group: FooterIssueEntry[], entry: FooterIssueEntry): void {
  if (group.some((item) => item.id === entry.id || item.title === entry.title)) return;
  group.push(entry);
}

export function buildIntakeV6FooterIssuesDisplay(input: {
  primaryActionReason?: string | null;
  problemDetails?: ReviewHeaderStatusDetail[];
  reviewWarnings?: readonly string[];
  secondaryWarnings?: readonly string[];
  statusActions?: ReviewHeaderStatusAction[];
}): IntakeV6FooterIssuesDisplay {
  const actions: FooterIssueEntry[] = [];
  const warnings: FooterIssueEntry[] = [];
  const information: FooterIssueEntry[] = [];
  const technical: FooterIssueEntry[] = [];

  if (input.primaryActionReason) {
    pushUniqueEntry(actions, {
      id: "primary-action-reason",
      title: input.primaryActionReason,
    });
  }

  for (const row of input.problemDetails ?? []) {
    const entry: FooterIssueEntry = {
      id: `detail-${row.id}`,
      title: `${row.label}: ${row.value}`,
      description: row.label,
    };
    if (row.tone === "bad") {
      pushUniqueEntry(actions, entry);
    } else if (row.tone === "warn") {
      pushUniqueEntry(warnings, entry);
    } else {
      pushUniqueEntry(information, entry);
    }
  }

  for (const warning of input.reviewWarnings ?? []) {
    const entry: FooterIssueEntry = {
      id: `review-warning-${warning}`,
      title: warning,
    };
    if (isLikelyTechnicalWarning(warning)) {
      pushUniqueEntry(technical, entry);
    } else {
      pushUniqueEntry(warnings, entry);
    }
  }

  for (const note of input.secondaryWarnings ?? []) {
    const entry: FooterIssueEntry = {
      id: `secondary-${note}`,
      title: note,
    };
    if (isLikelyTechnicalWarning(note)) {
      pushUniqueEntry(technical, entry);
    } else {
      pushUniqueEntry(warnings, entry);
    }
  }

  for (const action of input.statusActions ?? []) {
    pushUniqueEntry(actions, {
      id: `action-${action.id}`,
      title: action.label,
      actionId: action.id,
    });
  }

  const groups: FooterIssueGroup[] = (
    [
      { id: "actions" as const, entries: actions },
      { id: "warnings" as const, entries: warnings },
      { id: "information" as const, entries: information },
      { id: "technical" as const, entries: technical },
    ] as const
  )
    .filter((group) => group.entries.length > 0)
    .map((group) => ({
      id: group.id,
      label: GROUP_LABELS[group.id],
      entries: group.entries,
    }));

  const actionCount = actions.length;
  const warningCount = warnings.length;
  const informationCount = information.length;
  const technicalCount = technical.length;
  const totalCount = actionCount + warningCount + informationCount + technicalCount;

  return {
    totalCount,
    actionCount,
    warningCount,
    informationCount,
    technicalCount,
    primaryActionReason: input.primaryActionReason ?? null,
    groups,
  };
}
