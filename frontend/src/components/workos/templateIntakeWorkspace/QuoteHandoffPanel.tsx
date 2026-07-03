import VolumetricLettersQuoteFlow from "@/components/workos/VolumetricLettersQuoteFlow";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import type { IntakeSiteAuditJson } from "@/lib/intakeSiteAudit";
import type { IntakeRequest } from "@/lib/mockData";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";

export interface QuoteHandoffPanelProps {
  request: IntakeRequest;
  productSpec: IntakeProductSpec | null;
  intakeDbId?: number;
  siteAuditJson: IntakeSiteAuditJson | null;
  deliveryTypeLabel?: string;
  onClose: () => void;
}

/** Embedded preliminary quote — volumetric-specific handoff. */
export default function QuoteHandoffPanel({
  request,
  productSpec,
  intakeDbId,
  siteAuditJson,
  deliveryTypeLabel,
  onClose,
}: QuoteHandoffPanelProps) {
  return (
    <div role="tabpanel" data-testid="volumetric-quote-panel">
      <VolumetricLettersQuoteFlow
        embedded
        onClose={onClose}
        initialProductSpec={productSpec}
        preferredTemplateCode={TPL_VOLUMETRIC_LETTERS}
        initialClientName={request.client}
        intakeRequestId={request.id}
        intakeDbId={intakeDbId}
        openedFromIntake
        intakeDescription={request.description}
        deliveryTypeLabel={deliveryTypeLabel}
        siteAuditJson={siteAuditJson}
        intakeStatus={request.status}
      />
    </div>
  );
}
