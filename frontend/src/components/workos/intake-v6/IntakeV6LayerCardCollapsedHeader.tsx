import type { LucideIcon } from "lucide-react";
import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";
import {
  REVIEW_LAYER_CARD_CANT_SUMMARY_CLASS,
  REVIEW_LAYER_CARD_FACE_SUMMARY_CLASS,
  REVIEW_LAYER_CARD_HEADER_GRID,
  REVIEW_LAYER_CARD_NAME_CLASS,
} from "./layerCardCollapsedLayout";

export default function IntakeV6LayerCardCollapsedHeader({
  layerIcon: LayerIcon,
  accentColor,
  layerName,
  faceSummary,
  cantSummary,
  faceSummaryTestId,
  cantSummaryTestId,
  swatchTestId,
  status,
  expanded,
  headerTestId,
  layerIconClassName = "text-slate-500",
}: {
  layerIcon: LucideIcon;
  accentColor: string;
  layerName: string;
  faceSummary: string;
  cantSummary: string;
  faceSummaryTestId?: string;
  cantSummaryTestId?: string;
  swatchTestId?: string;
  status: ReactNode;
  expanded: boolean;
  layerIconClassName?: string;
}) {
  return (
    <div className={`${REVIEW_LAYER_CARD_HEADER_GRID} px-2.5 py-1.5`}>
      <LayerIcon className={`h-3.5 w-3.5 shrink-0 ${layerIconClassName}`} aria-hidden />
      <span
        className="h-3.5 w-3.5 shrink-0 rounded-sm border border-slate-600/80"
        style={{ backgroundColor: accentColor }}
        data-testid={swatchTestId}
        aria-hidden
      />
      <p className={REVIEW_LAYER_CARD_NAME_CLASS}>{layerName}</p>
      <p
        className={REVIEW_LAYER_CARD_FACE_SUMMARY_CLASS}
        data-testid={faceSummaryTestId}
        title={faceSummary}
      >
        {faceSummary}
      </p>
      <p
        className={REVIEW_LAYER_CARD_CANT_SUMMARY_CLASS}
        data-testid={cantSummaryTestId}
        title={cantSummary}
      >
        {cantSummary}
      </p>
      <span className="flex shrink-0 justify-end">{status}</span>
      <ChevronDown
        className={`h-3.5 w-3.5 shrink-0 text-slate-500 transition ${expanded ? "rotate-180" : ""}`}
        aria-hidden
      />
    </div>
  );
}
