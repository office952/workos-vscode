/**
 * Single pricing registry entry — card row (Oferte-like separation).
 */
import { History, Pencil } from "lucide-react";
import type { PricingRegistryItem } from "@/api/pricingRegistry";
import {
  quoteImpactLabel,
  statusDisplayText,
} from "@/lib/pricingRegistry";
import { StatusBadge } from "@/components/workos/design-system";
import { entryRowClass } from "./pricingRegistryUi";

function pricingRegistryItemStatusKey(item: PricingRegistryItem): string {
  if (item.status === "missing_price" || item.confidence === "missing") {
    return "missing_price";
  }
  if (item.status === "needs_review") {
    return "needs_review";
  }
  if (item.confidence === "estimated") {
    return "estimated";
  }
  if (item.confidence === "owner_confirmed") {
    return "owner_confirmed";
  }
  if (item.status === "active") {
    return "active";
  }
  return item.status || item.confidence || "unknown";
}

function fmtCost(n: number | null | undefined, currency?: string | null): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "Lipsă";
  const formatted = n.toLocaleString("ro-RO", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
  return currency ? `${formatted} ${currency}` : formatted;
}

export interface PricingEntryRowProps {
  item: PricingRegistryItem;
  selected: boolean;
  onSelect: () => void;
  onEditMaterial?: (item: PricingRegistryItem) => void;
  onEditRate?: (item: PricingRegistryItem) => void;
  loadingRate?: boolean;
  showCategory?: boolean;
  showTemplates?: boolean;
}

export function PricingEntryRow({
  item,
  selected,
  onSelect,
  onEditMaterial,
  onEditRate,
  loadingRate = false,
  showCategory = true,
  showTemplates = false,
}: PricingEntryRowProps) {
  const status = statusDisplayText(item);
  const impact = quoteImpactLabel(item);
  const isMaterial = item.pricing_kind === "material";
  const isRate = ["operation_rate", "workcenter_rate", "service"].includes(item.pricing_kind);
  const canEditMaterial = isMaterial && item.editable !== false && onEditMaterial;
  const canEditRate = isRate && item.editable !== false && onEditRate;

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={(e) => e.key === "Enter" && onSelect()}
      className={entryRowClass(selected)}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-3">
            <p className="text-[13px] font-semibold text-slate-100 truncate">{item.display_name}</p>
            <p className="text-[15px] font-bold text-slate-100 shrink-0">
              {item.base_cost != null ? fmtCost(item.base_cost, item.currency) : "Lipsă"}
            </p>
          </div>
          <div className="flex items-center justify-between gap-3 mt-1">
            <div className="flex items-center gap-2 min-w-0 flex-wrap">
              <StatusBadge
                domain="pricing"
                status={pricingRegistryItemStatusKey(item)}
                label={status.text}
              />
              <span className="font-mono text-[11px] text-blue-400/90 truncate">{item.pricing_code}</span>
            </div>
            <p className="text-[10px] text-slate-500 shrink-0">{item.unit}</p>
          </div>
          <div className="flex items-center gap-2 mt-1.5 text-[11px] text-slate-500 flex-wrap">
            {showCategory && <span>{item.registry_category}</span>}
            {showCategory && <span>·</span>}
            <span className="text-slate-400">{impact}</span>
          </div>
          {showTemplates && item.used_by_templates.length > 0 && (
            <p className="text-[10px] text-slate-600 mt-1 font-mono truncate">
              {item.used_by_templates.join(", ")}
            </p>
          )}
        </div>

        <div
          className="flex gap-1 shrink-0 self-center"
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
        >
          {canEditMaterial && (
            <button
              type="button"
              onClick={() => onEditMaterial(item)}
              className="p-2 rounded-md border border-[#2A3548] bg-[#0F1629] hover:border-blue-600/40 hover:text-blue-300 text-slate-400 transition-colors"
              title="Editare preț"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
          )}
          {canEditRate && (
            <button
              type="button"
              onClick={() => onEditRate(item)}
              disabled={loadingRate}
              className="p-2 rounded-md border border-[#2A3548] bg-[#0F1629] hover:border-blue-600/40 hover:text-blue-300 text-slate-400 transition-colors disabled:opacity-50"
              title="Editare rată"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            type="button"
            onClick={onSelect}
            className="p-2 rounded-md border border-[#2A3548] bg-[#0F1629] hover:border-purple-600/40 hover:text-purple-300 text-slate-400 transition-colors"
            title="Detalii / istoric"
          >
            <History className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
