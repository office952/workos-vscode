import type { LucideIcon } from "lucide-react";
import { v6 } from "./intakeV6Presentation";

export default function IntakeV6LayerZoneTitle({
  icon: Icon,
  title,
}: {
  icon: LucideIcon;
  title: string;
}) {
  return (
    <div className="mb-1.5 flex items-center gap-1.5">
      <Icon className="h-3.5 w-3.5 shrink-0 text-slate-500" aria-hidden />
      <span className={v6.zoneTitle}>{title}</span>
    </div>
  );
}
