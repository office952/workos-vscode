import type { OperationResourceMapping } from "@/api/operationalRegistry";
import {
  resolveMappingFromList,
  type OperationResolutionKind,
} from "@/features/operational-registry/operationResolution";

const BADGE_STYLES: Record<
  OperationResolutionKind,
  { label: string; className: string }
> = {
  direct: {
    label: "Registry mapped",
    className: "bg-emerald-900/30 text-emerald-300 border-emerald-700/60",
  },
  alias: {
    label: "Alias resolved",
    className: "bg-cyan-900/30 text-cyan-300 border-cyan-700/60",
  },
  missing: {
    label: "Missing mapping",
    className: "bg-amber-900/30 text-amber-300 border-amber-700/60",
  },
};

interface Props {
  operationCode: string;
  mappings: OperationResourceMapping[];
}

export function OperationRegistryMappingBadge({ operationCode, mappings }: Props) {
  const resolved = resolveMappingFromList(operationCode, mappings);
  const style = BADGE_STYLES[resolved.resolution];

  return (
    <span
      className={`inline-flex items-center gap-1 mt-1 px-1.5 py-0.5 text-[9px] font-semibold rounded border ${style.className}`}
      title={
        resolved.resolution === "alias"
          ? `${resolved.originalOperationCode} → ${resolved.resolvedOperationCode}`
          : resolved.warning ?? style.label
      }
    >
      {style.label}
      {resolved.resolution === "alias" && resolved.resolvedOperationCode && (
        <span className="font-mono opacity-90">
          → {resolved.resolvedOperationCode}
        </span>
      )}
    </span>
  );
}
