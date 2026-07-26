import type { ReactNode } from "react";
import { AtomsBadge, v6, type AtomsBadgeTone } from "./intakeV6Presentation";

export interface IntakeV6ReviewSectionShellProps {
  title: string;
  description?: string;
  testId: string;
  badge?: { label: string; tone: AtomsBadgeTone };
  children: ReactNode;
  className?: string;
  compact?: boolean;
  /** When the active tab already names the section, skip the redundant heading. */
  hideHeading?: boolean;
}

export default function IntakeV6ReviewSectionShell({
  title,
  description,
  testId,
  badge,
  children,
  className = "",
  compact = false,
  hideHeading = false,
}: IntakeV6ReviewSectionShellProps) {
  return (
    <section
      className={`${compact || hideHeading ? "mb-0" : "mb-5"} scroll-mt-4 ${className}`.trim()}
      data-testid={testId}
      aria-labelledby={hideHeading ? undefined : `${testId}-heading`}
      aria-label={hideHeading ? title : undefined}
    >
      {!hideHeading ? (
        <div className={`flex flex-wrap items-start justify-between gap-2 ${compact ? "mb-1.5" : "mb-3"}`}>
          <div className="min-w-0">
            <h2
              id={`${testId}-heading`}
              className={compact ? v6.zoneTitle : v6.sectionTitle}
            >
              {title}
            </h2>
            {description ? (
              <p className={`${v6.sectionDesc} ${compact ? "text-[11px] text-slate-500" : ""}`}>
                {description}
              </p>
            ) : null}
          </div>
          {badge ? <AtomsBadge tone={badge.tone}>{badge.label}</AtomsBadge> : null}
        </div>
      ) : badge ? (
        <div className="mb-1.5 flex justify-end">{<AtomsBadge tone={badge.tone}>{badge.label}</AtomsBadge>}</div>
      ) : null}
      <div data-testid={`${testId}-content`}>{children}</div>
    </section>
  );
}
