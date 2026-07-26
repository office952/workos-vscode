import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import IntakeV6LayerCardCollapsedHeader from "./IntakeV6LayerCardCollapsedHeader";
import { REVIEW_LAYER_CARD_EXPANDED_STACK_CLASS } from "./layerCardCollapsedLayout";

/**
 * Shared Step2 layer card shell — collapsed summaries + expanded stacked body.
 * Letter/logo adapters supply summary strings and expanded section nodes.
 */
export default function IntakeV6LayerCardShell({
  cardTestId,
  headerTestId,
  expanded,
  onToggle,
  accentColor,
  layerIcon,
  layerIconClassName,
  layerName,
  faceSummary,
  cantSummary,
  spateSummary,
  faceSummaryTestId,
  cantSummaryTestId,
  spateSummaryTestId,
  swatchTestId,
  status,
  statusAttr,
  cardTitle,
  expandedChildren,
}: {
  cardTestId: string;
  headerTestId: string;
  expanded: boolean;
  onToggle: () => void;
  accentColor: string;
  layerIcon: LucideIcon;
  layerIconClassName?: string;
  layerName: string;
  faceSummary: string;
  cantSummary: string;
  spateSummary: string;
  faceSummaryTestId?: string;
  cantSummaryTestId?: string;
  spateSummaryTestId?: string;
  swatchTestId?: string;
  status: ReactNode;
  statusAttr?: "ok" | "warning" | null;
  cardTitle?: string;
  expandedChildren: ReactNode;
}) {
  return (
    <div
      className="overflow-hidden rounded-md border border-wo-border-strong bg-wo-surface-inset/55"
      style={{ borderLeftWidth: 3, borderLeftColor: accentColor }}
      data-testid={cardTestId}
      data-layer-card-expanded={expanded ? "true" : "false"}
      title={cardTitle}
      {...(statusAttr ? { "data-layer-card-status": statusAttr } : {})}
    >
      <button
        type="button"
        className="min-h-[40px] w-full min-w-0 text-left transition hover:bg-wo-surface-raised/40"
        onClick={onToggle}
        data-testid={headerTestId}
        aria-expanded={expanded}
      >
        <IntakeV6LayerCardCollapsedHeader
          layerIcon={layerIcon}
          layerIconClassName={layerIconClassName}
          accentColor={accentColor}
          layerName={layerName}
          faceSummary={faceSummary}
          cantSummary={cantSummary}
          spateSummary={spateSummary}
          faceSummaryTestId={faceSummaryTestId}
          cantSummaryTestId={cantSummaryTestId}
          spateSummaryTestId={spateSummaryTestId}
          swatchTestId={swatchTestId}
          expanded={expanded}
          status={status}
        />
      </button>
      {expanded ? (
        <div className={REVIEW_LAYER_CARD_EXPANDED_STACK_CLASS} data-testid={`${cardTestId}-expanded`}>
          {expandedChildren}
        </div>
      ) : null}
    </div>
  );
}
