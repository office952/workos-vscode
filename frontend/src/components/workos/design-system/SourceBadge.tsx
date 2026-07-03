import {
  AlertTriangle,
  Database,
  GitBranch,
  HardDrive,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getSourceTone,
  getToneClasses,
  normalizeSourceLabel,
  normalizeStatusKey,
  sourceEmptyToneClasses,
  sourceMixedToneClasses,
  type SourceState,
} from "./tokens";

export type { SourceState };

export type SourceBadgeProps = {
  source: SourceState;
  label?: string;
  className?: string;
  title?: string;
};

function SourceIcon({ source }: { source: SourceState }) {
  const key = normalizeStatusKey(source);
  const iconClass = "w-3 h-3 shrink-0";

  switch (key) {
    case "db":
    case "empty":
      return <Database className={iconClass} aria-hidden />;
    case "mock":
    case "demo":
      return <HardDrive className={iconClass} aria-hidden />;
    case "error":
      return <AlertTriangle className={iconClass} aria-hidden />;
    case "loading":
      return <Loader2 className={cn(iconClass, "animate-spin")} aria-hidden />;
    case "mixed":
      return <GitBranch className={iconClass} aria-hidden />;
    default:
      return null;
  }
}

function resolveSourceToneClasses(source: SourceState) {
  const key = normalizeStatusKey(source);

  if (key === "empty") return sourceEmptyToneClasses;
  if (key === "mixed") return sourceMixedToneClasses;

  return getToneClasses(getSourceTone(source));
}

export function SourceBadge({
  source,
  label,
  className,
  title,
}: SourceBadgeProps) {
  const toneClasses = resolveSourceToneClasses(source);
  const displayLabel = label ?? normalizeSourceLabel(source);
  const key = normalizeStatusKey(source);

  return (
    <span
      title={title}
      data-source={key || "unknown"}
      data-source-tone={getSourceTone(source)}
      className={cn(
        "inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium rounded-full border",
        toneClasses.bg,
        toneClasses.text,
        toneClasses.border,
        className,
      )}
    >
      <SourceIcon source={source} />
      {displayLabel}
    </span>
  );
}
