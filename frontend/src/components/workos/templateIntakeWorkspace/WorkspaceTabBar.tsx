import { Calculator, FileText } from "lucide-react";
import type { WorkspaceTab } from "./types";

export interface WorkspaceTabBarProps {
  activeTab: WorkspaceTab;
  onTabChange: (tab: WorkspaceTab) => void;
}

export default function WorkspaceTabBar({
  activeTab,
  onTabChange,
}: WorkspaceTabBarProps) {
  return (
    <div
      className="flex flex-wrap items-center gap-2"
      role="tablist"
      data-testid="volumetric-workspace-tabs"
    >
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === "spec"}
        onClick={() => onTabChange("spec")}
        data-testid="volumetric-tab-spec"
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-[12px] font-semibold border transition-colors ${
          activeTab === "spec"
            ? "bg-blue-600/20 text-blue-200 border-blue-500/50"
            : "bg-wo-surface-inset text-slate-400 border-wo-border-strong hover:text-slate-200"
        }`}
      >
        <FileText className="w-3.5 h-3.5" />
        Specificație
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={activeTab === "quote"}
        onClick={() => onTabChange("quote")}
        data-testid="volumetric-tab-quote"
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-md text-[12px] font-semibold border transition-colors ${
          activeTab === "quote"
            ? "bg-emerald-600/20 text-emerald-200 border-emerald-500/50"
            : "bg-wo-surface-inset text-slate-400 border-wo-border-strong hover:text-slate-200"
        }`}
      >
        <Calculator className="w-3.5 h-3.5" />
        Simulare ofertă
      </button>
    </div>
  );
}
