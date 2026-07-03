import { RefreshCw } from "lucide-react";
import { emV2Controls } from "@/lib/employeeMobileV2DesignTokens";
import { cn } from "@/lib/utils";
import {
  EMPLOYEE_REQUEST_STATUS_FILTERS,
  type EmployeeRequestStatusFilter,
} from "@/lib/employeeRequestListUi";

type EmployeeRequestStatusFiltersProps = {
  filter: EmployeeRequestStatusFilter;
  onFilterChange: (filter: EmployeeRequestStatusFilter) => void;
  counts: Record<EmployeeRequestStatusFilter, number>;
  onRefresh: () => void;
  refreshing: boolean;
  testIdPrefix: "employee-mobile-requests" | "employee-mobile-review";
  /** When true, emphasize the submitted/pending filter chip in review inbox. */
  highlightPendingFilter?: boolean;
  filterStyle?: "pills" | "segmented";
};

export default function EmployeeRequestStatusFilters({
  filter,
  onFilterChange,
  counts,
  onRefresh,
  refreshing,
  testIdPrefix,
  highlightPendingFilter = false,
  filterStyle = "pills",
}: EmployeeRequestStatusFiltersProps) {
  const segmented = filterStyle === "segmented";

  return (
    <div
      className="flex flex-wrap items-center gap-2"
      data-testid={`${testIdPrefix}-toolbar`}
    >
      <div
        className={cn(
          "flex flex-1 gap-1.5",
          segmented
            ? cn(emV2Controls.segmentedTabs, "flex-nowrap overflow-x-auto")
            : "flex-wrap",
        )}
        role="group"
        aria-label="Filtru status"
        data-testid={`${testIdPrefix}-status-filters`}
      >
        {EMPLOYEE_REQUEST_STATUS_FILTERS.map((option) => {
          const active = filter === option.value;
          const count = counts[option.value];
          const isPendingChip =
            highlightPendingFilter && option.value === "submitted" && count > 0;
          return (
            <button
              key={option.value}
              type="button"
              className={cn(
                segmented
                  ? cn(
                      emV2Controls.segmentedTab,
                      "shrink-0 px-2.5 text-[12px]",
                      active && emV2Controls.segmentedTabActive,
                      !active &&
                        isPendingChip &&
                        "text-amber-300",
                    )
                  : cn(
                      "px-2.5 py-1.5 text-[10px] font-medium rounded-full border transition-colors min-h-[32px]",
                      active
                        ? "bg-blue-900/40 text-blue-200 border-blue-700/50"
                        : isPendingChip
                          ? "bg-amber-950/30 text-amber-200 border-amber-700/45 hover:border-amber-600/60"
                          : "bg-[#0A1020] text-slate-400 border-[#243044] hover:border-slate-600",
                    ),
              )}
              data-testid={`${testIdPrefix}-filter-${option.value}`}
              aria-pressed={active}
              onClick={() => onFilterChange(option.value)}
            >
              {option.label}
              {count > 0 ? ` (${count})` : ""}
            </button>
          );
        })}
      </div>
      <button
        type="button"
        className="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-[10px] font-medium rounded-lg border border-[#243044] text-slate-300 hover:border-slate-600 disabled:opacity-50 min-h-[32px]"
        data-testid={`${testIdPrefix}-refresh`}
        disabled={refreshing}
        onClick={onRefresh}
      >
        <RefreshCw className={cn("w-3 h-3", refreshing && "animate-spin")} aria-hidden />
        Refresh
      </button>
    </div>
  );
}
