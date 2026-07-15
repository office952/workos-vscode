import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import { resolveTaskDisplayTitle, resolveTaskComponentLine } from "@/lib/employeeMobileV2TaskTruth";

export type ElapsedDisplayClassification = "BACKEND_START_TIME_CLIENT_DISPLAY";

export function formatSessionStartTime(startedAt: string | null | undefined): string | null {
  if (!startedAt) return null;
  const parsed = new Date(startedAt);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toLocaleString("ro-RO");
}

export function computePresentationElapsedMinutes(startedAt: string | null | undefined): number | null {
  if (!startedAt) return null;
  const startMs = new Date(startedAt).getTime();
  if (Number.isNaN(startMs)) return null;
  const diff = Date.now() - startMs;
  if (diff < 0) return 0;
  return Math.floor(diff / 60_000);
}

export function formatPresentationElapsed(minutes: number | null): string | null {
  if (minutes == null) return null;
  if (minutes < 1) return "sub 1 min";
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const rem = minutes % 60;
  return rem > 0 ? `${hours} h ${rem} min` : `${hours} h`;
}

export function shouldShowActiveSessionPanel(task: EmployeeMobileTaskDTO): boolean {
  return (
    task.can_complete === true ||
    task.status === "in_progress" ||
    task.status === "paused" ||
    task.status === "done" ||
    Boolean(task.completed_at)
  );
}

export function buildActiveSessionSummary(task: EmployeeMobileTaskDTO) {
  return {
    title: resolveTaskDisplayTitle(task),
    component: resolveTaskComponentLine(task),
    startedAtLabel: formatSessionStartTime(task.started_at),
    elapsedClassification: "BACKEND_START_TIME_CLIENT_DISPLAY" as ElapsedDisplayClassification,
    elapsedDisclaimer:
      "Timpul afișat este orientativ pe dispozitiv — nu reprezintă pontaj sau cost.",
    statusLabel: task.status === "done" ? "Finalizat" : "În lucru",
    completedAtLabel: task.completed_at ? formatSessionStartTime(task.completed_at) : null,
  };
}
