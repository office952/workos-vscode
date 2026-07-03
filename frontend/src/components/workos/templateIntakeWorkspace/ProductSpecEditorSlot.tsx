import Product001IntakeSpecEditor from "@/components/workos/Product001IntakeSpecEditor";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { INTAKE_SECTION_IDS } from "@/lib/intakeActionSummary";

export interface ProductSpecEditorSlotProps {
  initialSpec: IntakeProductSpec | null;
  onSave: (
    spec: IntakeProductSpec | null,
    options?: { skipRefresh?: boolean }
  ) => Promise<void>;
  onSpecChange?: (spec: IntakeProductSpec) => void;
  readOnly?: boolean;
}

/**
 * Slot for template-specific product specification editors.
 * TPL-VOLUMETRIC-LETTERS uses Product001IntakeSpecEditor without contract changes.
 */
export default function ProductSpecEditorSlot({
  initialSpec,
  onSave,
  onSpecChange,
  readOnly = false,
}: ProductSpecEditorSlotProps) {
  return (
    <div
      id={INTAKE_SECTION_IDS["product-spec"]}
      className="scroll-mt-4"
      data-testid="product-spec-editor-slot"
    >
      <Product001IntakeSpecEditor
        initialSpec={initialSpec}
        onSave={onSave}
        onSpecChange={onSpecChange}
        readOnly={readOnly}
        showQuotePrepPanel={false}
      />
    </div>
  );
}
