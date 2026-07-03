import { CheckCircle2, CircleDashed, EyeOff } from "lucide-react";
import type { LayerRoleConfirmation } from "@/lib/svgAnalyzer";

export type LayerConfirmationState =
  LayerRoleConfirmation["layers"][number]["confirmationState"] | undefined;

const STATUS_META: Record<
  NonNullable<LayerConfirmationState>,
  { label: string; className: string; Icon: typeof CheckCircle2 }
> = {
  confirmed: {
    label: "Confirmat",
    className: "text-emerald-400",
    Icon: CheckCircle2,
  },
  pending: {
    label: "De confirmat",
    className: "text-amber-400",
    Icon: CircleDashed,
  },
  ignored: {
    label: "Ignorat",
    className: "text-slate-500",
    Icon: EyeOff,
  },
};

export default function IntakeV6LayerStatusIcon({
  state,
  testId,
  size = "md",
}: {
  state: LayerConfirmationState;
  testId?: string;
  size?: "sm" | "md";
}) {
  const resolved = state ?? "pending";
  const meta = STATUS_META[resolved];
  const Icon = meta.Icon;
  const dim = size === "sm" ? "h-3.5 w-3.5" : "h-4 w-4";

  return (
    <span
      className={`inline-flex shrink-0 items-center justify-center ${meta.className}`}
      title={meta.label}
      aria-label={meta.label}
      data-testid={testId ?? `intake-v6-layer-status-${resolved}`}
      data-layer-status={resolved}
    >
      <Icon className={dim} aria-hidden />
    </span>
  );
}
