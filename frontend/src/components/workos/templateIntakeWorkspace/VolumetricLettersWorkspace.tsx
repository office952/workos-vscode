import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import FlowBreadcrumb, { intakeDetailBreadcrumb } from "@/components/workos/FlowBreadcrumb";
import type { IntakeProductSpec } from "@/lib/intakeProductSpec";
import { mergeLocalVectorSpecFields } from "@/lib/vectorIntakeSpecMerge";
import {
  filterReadinessMissingForDisplay,
  getDeliveryLabel,
  getDeliveryStageNote,
} from "@/lib/intakeDeliverySemantics";
import { buildIntakeV6Path } from "@/lib/volumetricIntakeRoute";
import { TPL_VOLUMETRIC_LETTERS } from "@/lib/volumetricQuoteInput";
import type { TemplateWorkspaceBaseProps, WorkspaceTab } from "./types";
import TemplateWorkspaceLayout from "./TemplateWorkspaceLayout";
import WorkspaceMainColumn from "./WorkspaceMainColumn";
import WorkspaceSidePanel from "./WorkspaceSidePanel";
import StickyWorkspaceActions from "./StickyWorkspaceActions";
import RequestContextPanel from "./RequestContextPanel";
import TemplateStatusPanel from "./TemplateStatusPanel";
import WorkspaceTabBar from "./WorkspaceTabBar";
import WorkspaceAlerts from "./WorkspaceAlerts";
import TemplateConfirmationPanel from "./TemplateConfirmationPanel";
import ProductSpecEditorSlot from "./ProductSpecEditorSlot";
import TerrainRequirementPanel from "./TerrainRequirementPanel";
import ReadinessGatePanel from "./ReadinessGatePanel";
import QuoteHandoffPanel from "./QuoteHandoffPanel";

/**
 * TPL-VOLUMETRIC-LETTERS workspace — two-column layout using full viewport width.
 */
export default function VolumetricLettersWorkspace(props: TemplateWorkspaceBaseProps) {
  const {
    request,
    source,
    error,
    persistError,
    selectedDeliveryType,
    assignedTo,
    setAssignedTo,
    confirmedTemplateCode,
    productSpecInitial,
    actionSummary,
    readiness,
    statusConflict,
    requiresInstallAudit,
    markReadyLoading,
    markReadyMessage,
    confirmingTemplate,
    installTerrainSection,
    intakeDbId,
    siteAuditJson,
    onDeliveryTypeChange,
    onAssignedBlur,
    onSaveProductSpec,
    onMarkReadyForQuote,
    onConfirmTemplate,
  } = props;

  const [activeTab, setActiveTab] = useState<WorkspaceTab>("spec");
  const [liveProductSpec, setLiveProductSpec] = useState<IntakeProductSpec | null>(
    productSpecInitial
  );
  const templateConfirmed =
    (confirmedTemplateCode ?? "").trim() === TPL_VOLUMETRIC_LETTERS;

  useEffect(() => {
    setLiveProductSpec((prev) => {
      if (!productSpecInitial) return prev ?? null;
      if (!prev) return productSpecInitial;
      const prevAt = prev.vector_file_selected_at ?? "";
      const nextAt = productSpecInitial.vector_file_selected_at ?? "";
      const prevLayers = prev.vector_detected_layers?.length ?? 0;
      const nextLayers = productSpecInitial.vector_detected_layers?.length ?? 0;
      if (prevAt && (!nextAt || prevAt >= nextAt) && prevLayers >= nextLayers) {
        return prev;
      }
      if (prevLayers > nextLayers) {
        return mergeLocalVectorSpecFields(prev, productSpecInitial);
      }
      return productSpecInitial;
    });
  }, [productSpecInitial]);

  const openQuoteTab = useCallback(() => setActiveTab("quote"), []);

  const readinessMissing =
    !readiness.canMarkReady && request.status !== "ready_for_quote"
      ? filterReadinessMissingForDisplay(
          actionSummary.readinessMissing,
          requiresInstallAudit
        )
      : [];

  const terrainDataPreservedNote = getDeliveryStageNote({
    deliveryType: selectedDeliveryType,
    productFamily: request.productFamily,
    siteAudit: siteAuditJson,
  });

  const displayReadinessBlockers = filterReadinessMissingForDisplay(
    readiness.missing,
    requiresInstallAudit
  );

  return (
    <div className="w-full space-y-3" data-testid="volumetric-intake-page">
      <FlowBreadcrumb items={intakeDetailBreadcrumb(request.id)} />
      <p className="text-[10px] text-slate-500">
        <Link
          to={buildIntakeV6Path(request.id)}
          className="text-amber-400/90 hover:text-amber-300 underline-offset-2 hover:underline"
          data-testid="open-intake-v6-link"
        >
          Deschide Intake V6
        </Link>
        <span className="text-slate-600"> · intern / experimental</span>
      </p>

      <TemplateWorkspaceLayout
        main={
          <WorkspaceMainColumn>
            <WorkspaceTabBar activeTab={activeTab} onTabChange={setActiveTab} />
            <WorkspaceAlerts
              statusConflict={statusConflict}
              error={error}
              persistError={persistError}
              source={source}
            />

            <div
              role="tabpanel"
              className={activeTab === "spec" ? "space-y-3" : "hidden"}
              aria-hidden={activeTab !== "spec"}
              data-testid="workspace-spec-panel"
            >
              <TemplateConfirmationPanel
                templateCode={TPL_VOLUMETRIC_LETTERS}
                confirmed={templateConfirmed}
                confirming={confirmingTemplate}
                readOnly={source === "mock"}
                onConfirm={onConfirmTemplate}
              />
              <ProductSpecEditorSlot
                initialSpec={productSpecInitial}
                onSave={onSaveProductSpec}
                onSpecChange={setLiveProductSpec}
                readOnly={source === "mock"}
              />
              {activeTab === "spec" && (
                <TerrainRequirementPanel
                  requiresInstallAudit={requiresInstallAudit}
                  installTerrainSection={installTerrainSection}
                  terrainDataPreservedNote={terrainDataPreservedNote}
                />
              )}
            </div>

            <div
              role="tabpanel"
              className={activeTab === "quote" ? "space-y-3" : "hidden"}
              aria-hidden={activeTab !== "quote"}
              data-testid="workspace-quote-panel"
            >
              {activeTab === "quote" && (
                <QuoteHandoffPanel
                  request={request}
                  productSpec={liveProductSpec ?? productSpecInitial}
                  intakeDbId={intakeDbId ?? undefined}
                  siteAuditJson={siteAuditJson}
                  deliveryTypeLabel={getDeliveryLabel(selectedDeliveryType)}
                  onClose={() => setActiveTab("spec")}
                />
              )}
            </div>
          </WorkspaceMainColumn>
        }
        side={
          <WorkspaceSidePanel>
            <div data-testid="volumetric-request-context" className="space-y-3">
              <RequestContextPanel
                request={request}
                source={source}
                assignedTo={assignedTo}
                setAssignedTo={setAssignedTo}
                selectedDeliveryType={selectedDeliveryType}
                onDeliveryTypeChange={onDeliveryTypeChange}
                onAssignedBlur={onAssignedBlur}
                variant="compact"
                deliveryStageNote={terrainDataPreservedNote}
              />
              <TemplateStatusPanel
                actionSummary={actionSummary}
                readinessMissing={readinessMissing}
                variant="stacked"
              />
            </div>
            <StickyWorkspaceActions>
              <ReadinessGatePanel
                request={request}
                readiness={{
                  ...readiness,
                  missing: displayReadinessBlockers,
                }}
                actionSummary={actionSummary}
                markReadyLoading={markReadyLoading}
                markReadyMessage={markReadyMessage}
                source={source}
                onMarkReady={onMarkReadyForQuote}
                onOpenQuote={openQuoteTab}
                layout="stack"
              />
            </StickyWorkspaceActions>
          </WorkspaceSidePanel>
        }
      />
    </div>
  );
}
