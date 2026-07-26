import { v6 } from "./atoms/intakeV6Presentation";
import { REVIEW_LAYER_CARD_HEADER_GRID } from "./layerCardCollapsedLayout";

export default function IntakeV6LayerCardColumnHeader({
  faceLabel = "Față",
  cantLabel = "Cant",
  showFace = true,
  showCant = true,
}: {
  faceLabel?: string;
  cantLabel?: string;
  showFace?: boolean;
  showCant?: boolean;
}) {
  return (
    <div
      className={`${REVIEW_LAYER_CARD_HEADER_GRID} mb-1 hidden px-2.5 sm:grid`}
      aria-hidden
      data-testid="intake-v6-layer-card-column-header"
    >
      <span />
      <span />
      <span className={`${v6.metricLabel} truncate`}>Strat</span>
      {showFace ? <span className={`${v6.metricLabel} truncate`}>{faceLabel}</span> : <span />}
      {showCant ? <span className={`${v6.metricLabel} truncate`}>{cantLabel}</span> : <span />}
      <span />
      <span />
    </div>
  );
}
