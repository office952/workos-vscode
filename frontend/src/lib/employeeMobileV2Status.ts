import type { LucideIcon } from "lucide-react";
import {
  Activity,
  CheckCircle2,
  CircleDot,
  Clock3,
  Hourglass,
  OctagonAlert,
  PlayCircle,
  Users,
} from "lucide-react";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";
import type { EmployeeMobileOrderBlueprintTask } from "@/api/employeeMobileOrderBlueprint";
import type { PipelineMarker } from "@/lib/employeeMobilePipelineEligibility";
import {
  buildWhyItMattersLine,
  getOperationalStatusLabel,
  getOperationalTaskBucket,
} from "@/lib/employeeMobileShopFloorPresentation";

export type EmV2StatusTone = "neutral" | "active" | "ready" | "warning" | "waiting";

export interface EmV2StatusPresentation {
  shortLabel: string;
  detailLine: string | null;
  tone: EmV2StatusTone;
  Icon: LucideIcon;
  /** Pipeline-only: de-emphasize context labels such as Alt post. */
  muted?: boolean;
  /** Pipeline-only: completed row icon styling. */
  completed?: boolean;
}

function shortenWaitingDetail(line: string | null): string | null {
  if (!line) return null;
  const trimmed = line.trim();
  if (!trimmed) return null;
  if (trimmed.startsWith("Așteaptă:")) {
    return trimmed.slice("Așteaptă:".length).trim();
  }
  if (trimmed.startsWith("Așteaptă ")) {
    return trimmed.slice("Așteaptă ".length).trim();
  }
  if (trimmed === "Așteaptă finalizarea unui task anterior.") {
    return "task anterior";
  }
  if (trimmed === "Așteaptă material înainte de start.") {
    return "material";
  }
  return trimmed;
}

function resolveFromFullLabel(
  fullLabel: string,
  detailLine: string | null,
  bucket: ReturnType<typeof getOperationalTaskBucket>,
): EmV2StatusPresentation {
  switch (fullLabel) {
    case "Așteaptă task anterior":
      return {
        shortLabel: "Așteaptă",
        detailLine: shortenWaitingDetail(detailLine) ?? "task anterior",
        tone: "waiting",
        Icon: Hourglass,
      };
    case "Așteaptă material":
      return {
        shortLabel: "Așteaptă",
        detailLine: shortenWaitingDetail(detailLine) ?? "material",
        tone: "waiting",
        Icon: Hourglass,
      };
    case "Poate începe":
      return {
        shortLabel: "Poate începe",
        detailLine: null,
        tone: "ready",
        Icon: PlayCircle,
      };
    case "În lucru":
      return {
        shortLabel: "În lucru",
        detailLine: null,
        tone: "active",
        Icon: CircleDot,
      };
    case "Blocat":
      return {
        shortLabel: "Blocat",
        detailLine: detailLine,
        tone: "warning",
        Icon: OctagonAlert,
      };
    case "Pregătit de lucru":
      return {
        shortLabel: "Pregătit",
        detailLine: null,
        tone: "ready",
        Icon: CheckCircle2,
      };
    case "Urmează":
      return {
        shortLabel: "Urmează",
        detailLine: detailLine,
        tone: "waiting",
        Icon: Clock3,
      };
    case "Mai târziu":
      return {
        shortLabel: "Mai târziu",
        detailLine: null,
        tone: "neutral",
        Icon: Clock3,
      };
    default:
      if (bucket === "in_progress") {
        return {
          shortLabel: "În lucru",
          detailLine: null,
          tone: "active",
          Icon: Activity,
        };
      }
      return {
        shortLabel: fullLabel.length > 18 ? `${fullLabel.slice(0, 16)}…` : fullLabel,
        detailLine: detailLine,
        tone: bucket === "waiting" ? "waiting" : "neutral",
        Icon: Clock3,
      };
  }
}

export function resolveEmployeeMobileV2StatusPresentation(
  task: EmployeeMobileTaskDTO,
  blueprintTask?: EmployeeMobileOrderBlueprintTask | null,
): EmV2StatusPresentation {
  const fullLabel = getOperationalStatusLabel(task, blueprintTask);
  const detailLine = buildWhyItMattersLine({ personalTask: task, blueprintTask });
  const bucket = getOperationalTaskBucket(task);
  return resolveFromFullLabel(fullLabel, detailLine, bucket);
}

function shortenPipelineMarkerDetail(markerLabel: string | null): string | null {
  if (!markerLabel) return null;
  const trimmed = markerLabel.trim();
  if (trimmed === "Așteaptă task anterior") return "task anterior";
  if (trimmed === "Așteaptă material") return "material";
  if (trimmed === "În lucru la alt post") return "în lucru";
  if (trimmed.startsWith("Așteaptă:")) return trimmed.slice("Așteaptă:".length).trim();
  if (trimmed.length > 24) return `${trimmed.slice(0, 22)}…`;
  return trimmed.length > 0 && trimmed !== "Alt post" ? trimmed : null;
}

const PIPELINE_LEGEND_ORDER: PipelineMarker[] = [
  "acum",
  "blocat",
  "asteapta",
  "urmeaza",
  "finalizat",
  "alt_post",
];

/** Reference legend entries shown under the pipeline timeline. */
export const PIPELINE_LEGEND_REFERENCE: PipelineMarker[] = [...PIPELINE_LEGEND_ORDER];

export function collectPipelineLegendMarkers(
  markers: Array<PipelineMarker | null>,
): PipelineMarker[] {
  const seen = new Set<PipelineMarker>();
  for (const marker of markers) {
    if (!marker) continue;
    seen.add(marker === "neatribuit" ? "alt_post" : marker);
  }
  return PIPELINE_LEGEND_ORDER.filter((marker) => seen.has(marker));
}

export function getPipelineRowContextLine(
  marker: PipelineMarker | null,
  markerLabel: string | null,
  waitingDetail: string | null,
  blockedReason: string | null = null,
): string | null {
  if (marker === "asteapta") {
    const detail = waitingDetail ?? shortenPipelineMarkerDetail(markerLabel);
    return detail ? `Așteaptă: ${detail}` : "Așteaptă";
  }
  if (marker === "blocat") {
    const detail =
      blockedReason?.trim() || shortenPipelineMarkerDetail(markerLabel);
    return detail ? `Blocat: ${detail}` : "Blocat";
  }
  return null;
}

export type PipelineRowVisualState =
  | "current"
  | "blocked"
  | "completed"
  | "waiting"
  | "upcoming"
  | "alt-post"
  | "neutral";

export function resolvePipelineRowVisualState({
  isCurrent,
  marker,
}: {
  isCurrent: boolean;
  marker: PipelineMarker | null;
}): PipelineRowVisualState {
  if (isCurrent) return "current";
  if (marker === "finalizat") return "completed";
  if (marker === "blocat") return "blocked";
  if (marker === "alt_post" || marker === "neatribuit") return "alt-post";
  if (marker === "asteapta") return "waiting";
  if (marker === "urmeaza") return "upcoming";
  return "neutral";
}

export function resolveEmployeeMobileV2PipelineMarkerPresentation(
  marker: PipelineMarker | null,
  markerLabel: string | null,
  isCurrent: boolean,
): EmV2StatusPresentation | null {
  if (!marker) return null;

  switch (marker) {
    case "acum":
      return {
        shortLabel: "Acum",
        detailLine: null,
        tone: "active",
        Icon: CircleDot,
      };
    case "asteapta":
      return {
        shortLabel: "Așteaptă",
        detailLine: shortenPipelineMarkerDetail(markerLabel),
        tone: "waiting",
        Icon: Hourglass,
      };
    case "urmeaza":
      return {
        shortLabel: "Urmează",
        detailLine: null,
        tone: "ready",
        Icon: Clock3,
      };
    case "blocat":
      return {
        shortLabel: "Blocat",
        detailLine: shortenPipelineMarkerDetail(markerLabel),
        tone: "warning",
        Icon: OctagonAlert,
      };
    case "finalizat":
      return {
        shortLabel: "Finalizat",
        detailLine: null,
        tone: "neutral",
        Icon: CheckCircle2,
        completed: true,
      };
    case "alt_post":
    case "neatribuit":
      return {
        shortLabel: "Alt post",
        detailLine: shortenPipelineMarkerDetail(markerLabel),
        tone: "neutral",
        Icon: Users,
        muted: true,
      };
    case "in_lucru":
      return {
        shortLabel: isCurrent ? "În lucru" : "În lucru",
        detailLine: null,
        tone: "active",
        Icon: Activity,
      };
    default:
      return null;
  }
}

export function getPipelineLegendLabel(marker: PipelineMarker): string {
  switch (marker) {
    case "acum":
      return "În lucru acum";
    case "finalizat":
      return "Finalizat";
    case "blocat":
      return "Blocat";
    case "asteapta":
      return "Așteaptă";
    case "urmeaza":
      return "Urmează";
    case "alt_post":
    case "neatribuit":
      return "Alt post";
    default:
      return marker;
  }
}

export function getPipelineStepLabel(taskNumber: number): string {
  return `Pas ${taskNumber}`;
}

export function pipelineMarkerToRowState(marker: PipelineMarker): PipelineRowVisualState {
  switch (marker) {
    case "acum":
      return "current";
    case "finalizat":
      return "completed";
    case "blocat":
      return "blocked";
    case "asteapta":
      return "waiting";
    case "urmeaza":
      return "upcoming";
    case "alt_post":
    case "neatribuit":
      return "alt-post";
    default:
      return "neutral";
  }
}

export function getPipelineDependencyWarningShort(
  warning: string | null | undefined,
): string | null {
  if (!warning?.trim()) return null;
  const trimmed = warning.trim();
  const normalized = trimmed
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  if (
    normalized.includes("inainte de finalizarea dependentelor") ||
    normalized.includes("pornit inainte")
  ) {
    return "Atenție: dependențe active";
  }
  if (trimmed.length <= 36) return trimmed;
  return `${trimmed.slice(0, 34)}…`;
}
