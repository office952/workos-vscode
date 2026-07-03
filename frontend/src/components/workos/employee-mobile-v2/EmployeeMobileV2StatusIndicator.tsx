import {
  emV2Controls,
  emV2StatusToneClass,
} from "@/lib/employeeMobileV2DesignTokens";
import type { EmV2StatusPresentation } from "@/lib/employeeMobileV2Status";
import { cn } from "@/lib/utils";

export default function EmployeeMobileV2StatusIndicator({
  presentation,
  testId,
  align = "end",
}: {
  presentation: EmV2StatusPresentation;
  testId?: string;
  align?: "end" | "start";
}) {
  const { shortLabel, detailLine, tone, Icon } = presentation;

  return (
    <span
      className={cn(
        emV2Controls.statusIndicator,
        align === "start" && "items-start text-left",
      )}
      data-testid={testId}
    >
      <span className={cn(emV2Controls.statusIconRow, emV2StatusToneClass(tone))}>
        <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
        <span>{shortLabel}</span>
      </span>
      {detailLine ? (
        <span className={emV2Controls.statusDetail}>{detailLine}</span>
      ) : null}
    </span>
  );
}
