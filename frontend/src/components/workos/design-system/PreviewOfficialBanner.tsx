import { cn } from "@/lib/utils";
import { Eye, FileCheck, PenLine, Lock, ShieldAlert, Briefcase } from "lucide-react";
import type { ReactNode } from "react";

export type DocumentStage =
  | "draft"
  | "preview"
  | "official"
  | "internal"
  | "commercial"
  | "frozen"
  | "blocked";

export interface PreviewOfficialBannerProps {
  stage: DocumentStage;
  label?: string;
  detail?: string;
  className?: string;
  compact?: boolean;
}

const stageConfig: Record<
  DocumentStage,
  { icon: ReactNode; defaultLabel: string; bg: string; text: string; border: string }
> = {
  draft: {
    icon: <PenLine className="w-3.5 h-3.5" />,
    defaultLabel: "Draft",
    bg: "bg-slate-50 dark:bg-slate-800/60",
    text: "text-slate-700 dark:text-slate-300",
    border: "border-slate-200 dark:border-slate-700",
  },
  preview: {
    icon: <Eye className="w-3.5 h-3.5" />,
    defaultLabel: "Preview",
    bg: "bg-blue-50 dark:bg-blue-900/30",
    text: "text-blue-700 dark:text-blue-300",
    border: "border-blue-200 dark:border-blue-700",
  },
  official: {
    icon: <FileCheck className="w-3.5 h-3.5" />,
    defaultLabel: "Official",
    bg: "bg-emerald-50 dark:bg-emerald-900/30",
    text: "text-emerald-700 dark:text-emerald-300",
    border: "border-emerald-200 dark:border-emerald-700",
  },
  internal: {
    icon: <Lock className="w-3.5 h-3.5" />,
    defaultLabel: "Internal (cost intern)",
    bg: "bg-purple-50 dark:bg-purple-900/30",
    text: "text-purple-700 dark:text-purple-300",
    border: "border-purple-200 dark:border-purple-700",
  },
  commercial: {
    icon: <Briefcase className="w-3.5 h-3.5" />,
    defaultLabel: "Commercial (tarif client)",
    bg: "bg-cyan-50 dark:bg-cyan-900/30",
    text: "text-cyan-700 dark:text-cyan-300",
    border: "border-cyan-200 dark:border-cyan-700",
  },
  frozen: {
    icon: <Lock className="w-3.5 h-3.5" />,
    defaultLabel: "Frozen — Owner GO required",
    bg: "bg-indigo-50 dark:bg-indigo-900/30",
    text: "text-indigo-700 dark:text-indigo-300",
    border: "border-indigo-200 dark:border-indigo-700",
  },
  blocked: {
    icon: <ShieldAlert className="w-3.5 h-3.5" />,
    defaultLabel: "Blocked",
    bg: "bg-red-50 dark:bg-red-900/30",
    text: "text-red-700 dark:text-red-300",
    border: "border-red-200 dark:border-red-700",
  },
};

export function PreviewOfficialBanner({
  stage,
  label,
  detail,
  className,
  compact = false,
}: PreviewOfficialBannerProps) {
  const config = stageConfig[stage] ?? stageConfig.draft;
  const displayLabel = label ?? config.defaultLabel;

  if (compact) {
    return (
      <span
        data-stage={stage}
        className={cn(
          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border text-xs font-semibold",
          config.bg,
          config.text,
          config.border,
          className,
        )}
      >
        {config.icon}
        {displayLabel}
      </span>
    );
  }

  return (
    <div
      data-stage={stage}
      className={cn(
        "flex items-center gap-3 px-4 py-2.5 rounded-lg border",
        config.bg,
        config.text,
        config.border,
        className,
      )}
    >
      <span className="shrink-0">{config.icon}</span>
      <div className="min-w-0">
        <span className="text-sm font-semibold">{displayLabel}</span>
        {detail && (
          <p className="text-[11px] opacity-80 mt-0.5">{detail}</p>
        )}
      </div>
    </div>
  );
}