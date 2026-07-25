/**
 * BoundaryBadge — indicates ownership boundary domain.
 * Used to clarify which system/module owns a piece of data.
 */
import { Shield } from "lucide-react";

export type BoundaryDomain =
  | "product-definition"
  | "product-aggregate"
  | "pricing"
  | "hr"
  | "machines"
  | "execution"
  | "governance"
  | "intake"
  | "inventory"
  | "collaborators";

export interface BoundaryBadgeProps {
  domain: BoundaryDomain;
  /** Optional custom label override */
  label?: string;
  /** Optional detail text shown after the badge */
  detail?: string;
  compact?: boolean;
}

const DOMAIN_META: Record<BoundaryDomain, { label: string; color: string }> = {
  "product-definition": {
    label: "Product Definition",
    color: "bg-violet-100 text-violet-700 border-violet-200 dark:bg-violet-900/30 dark:text-violet-300 dark:border-violet-700",
  },
  "product-aggregate": {
    label: "Product Aggregate",
    color: "bg-indigo-100 text-indigo-700 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-700",
  },
  pricing: {
    label: "Pricing Registry",
    color: "bg-emerald-100 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-700",
  },
  hr: {
    label: "HR / Pontaj",
    color: "bg-sky-100 text-sky-700 border-sky-200 dark:bg-sky-900/30 dark:text-sky-300 dark:border-sky-700",
  },
  machines: {
    label: "Utilaje / Capacity",
    color: "bg-amber-100 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-700",
  },
  execution: {
    label: "Execution Plan",
    color: "bg-orange-100 text-orange-700 border-orange-200 dark:bg-orange-900/30 dark:text-orange-300 dark:border-orange-700",
  },
  governance: {
    label: "Governance / Owner GO",
    color: "bg-rose-100 text-rose-700 border-rose-200 dark:bg-rose-900/30 dark:text-rose-300 dark:border-rose-700",
  },
  intake: {
    label: "Intake",
    color: "bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-300 dark:border-teal-700",
  },
  inventory: {
    label: "Inventory",
    color: "bg-lime-100 text-lime-700 border-lime-200 dark:bg-lime-900/30 dark:text-lime-300 dark:border-lime-700",
  },
  collaborators: {
    label: "Colaboratori (HUB extern)",
    color: "bg-teal-100 text-teal-700 border-teal-200 dark:bg-teal-900/30 dark:text-teal-300 dark:border-teal-700",
  },
};

export function BoundaryBadge({ domain, label, detail, compact = false }: BoundaryBadgeProps) {
  const meta = DOMAIN_META[domain];
  const displayLabel = label ?? meta.label;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded border font-medium ${meta.color} ${
        compact ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-0.5 text-[11px]"
      }`}
      title={`Boundary: ${meta.label}`}
    >
      <Shield className={compact ? "w-2.5 h-2.5" : "w-3 h-3"} />
      {displayLabel}
      {detail && <span className="font-normal ml-1 opacity-80">— {detail}</span>}
    </span>
  );
}