import type { LucideIcon } from "lucide-react";
import { ChevronDown } from "lucide-react";
import type { ReactNode } from "react";
import {
  REVIEW_LAYER_CARD_CANT_SUMMARY_CLASS,
  REVIEW_LAYER_CARD_FACE_SUMMARY_CLASS,
  REVIEW_LAYER_CARD_HEADER_GRID,
  REVIEW_LAYER_CARD_NAME_CLASS,
  REVIEW_LAYER_CARD_SPATE_SUMMARY_CLASS,
} from "./layerCardCollapsedLayout";

export default function IntakeV6LayerCardCollapsedHeader({
  layerIcon: LayerIcon,
  accentColor,
  layerName,
  faceSummary,
  cantSummary,
  spateSummary,
  faceSummaryTestId,
  cantSummaryTestId,
  spateSummaryTestId,
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
  spateSummary?: string;
  faceSummaryTestId?: string;
  cantSummaryTestId?: string;
  spateSummaryTestId?: string;
  swatchTestId?: string;
  status: ReactNode;
  expanded: boolean;
  headerTestId?: string;
  layerIconClassName?: string;
}) {
  return (
    <div className={`${REVIEW_LAYER_CARD_HEADER_GRID} px-2.5 py-1.5`} data-testid={headerTestId}>
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
        <span className="mr-1 text-slate-600">Față:</span>
        {faceSummary}
      </p>
      <p
        className={REVIEW_LAYER_CARD_CANT_SUMMARY_CLASS}
        data-testid={cantSummaryTestId}
        title={cantSummary}
      >
        <span className="mr-1 text-slate-600">Cant:</span>
        {cantSummary}
      </p>
      <p
        className={REVIEW_LAYER_CARD_SPATE_SUMMARY_CLASS}
        data-testid={spateSummaryTestId}
        title={spateSummary ?? "—"}
      >
        <span className="mr-1 text-slate-600">Spate:</span>
        {spateSummary ?? "—"}
      </p>
      <span className="flex shrink-0 justify-end">{status}</span>
      <ChevronDown
        className={`h-3.5 w-3.5 shrink-0 text-slate-500 transition ${expanded ? "rotate-180" : ""}`}
        aria-hidden
      />
    </div>
  );
}
