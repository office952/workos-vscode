/**
 * ReviewStep layout mount for product component list + AcmPanel inspector.
 * Owns no AcmPanel domain semantics — delegates to uiReadModel + operatorPatch.
 */

import { useCallback, useMemo, useState } from "react";
import IntakeV6ProductComponentList, {
  buildProductComponentListItems,
} from "./IntakeV6ProductComponentList";
import IntakeV6AcmPanelInspector, {
  type AcmPanelInspectorActions,
} from "./IntakeV6AcmPanelInspector";
import IntakeV6AcmPanelValidationRail from "./IntakeV6AcmPanelValidationRail";
import {
  buildAcmPanelConfirmConstructionPatch,
  buildAcmPanelConfirmFieldPatch,
  buildAcmPanelConfirmRelationPatch,
  buildAcmPanelConfirmTechnicalPatch,
  buildAcmPanelUpdateFieldPatch,
  type AcmOperatorFieldKey,
} from "@/lib/intakeV6/acmPanel/operatorPatch";
import {
  buildAcmPanelUiReadModel,
  type AcmPanelIssue,
} from "@/lib/intakeV6/acmPanel/uiReadModel";
import type { IntakeV6ProductComponentId } from "@/lib/intakeV6/useIntakeV6ProductComponentSelection";
import type { IntakeV6FinishSetup } from "@/lib/intakeV6/intakeV6Api";
import type { SegmentedBackground } from "@/lib/intakeV6/segmentedBackground";

export default function IntakeV6AcmPanelConfigRegion({
  payload,
  finishSetup,
  hasLetters,
  hasLogo,
  selectedId,
  onSelect,
  onApplyFinishPatch,
  onNavigateLetters,
  onNavigateLogo,
}: {
  payload: Record<string, unknown> | null | undefined;
  finishSetup: Record<string, unknown> | null | undefined;
  hasLetters: boolean;
  hasLogo: boolean;
  selectedId: IntakeV6ProductComponentId | null;
  onSelect: (id: IntakeV6ProductComponentId) => void;
  onApplyFinishPatch: (patch: Partial<IntakeV6FinishSetup>) => void;
  onNavigateLetters: () => void;
  onNavigateLogo: () => void;
}) {
  const acmModel = useMemo(
    () =>
      buildAcmPanelUiReadModel({
        finishSetup,
        payload: payload ?? null,
      }),
    [finishSetup, payload],
  );

  const items = useMemo(
    () =>
      buildProductComponentListItems({
        payload,
        finishSetup,
        hasLetters,
        hasLogo,
        acmModel,
      }),
    [payload, finishSetup, hasLetters, hasLogo, acmModel],
  );

  const [focusIssue, setFocusIssue] = useState<AcmPanelIssue | null>(null);

  const handleSelect = useCallback(
    (id: IntakeV6ProductComponentId) => {
      onSelect(id);
      if (id === "letters") onNavigateLetters();
      if (id === "logo") onNavigateLogo();
    },
    [onSelect, onNavigateLetters, onNavigateLogo],
  );

  const applyPatch = useCallback(
    (patch: Partial<IntakeV6FinishSetup> | null) => {
      if (!patch) return;
      onApplyFinishPatch(patch);
    },
    [onApplyFinishPatch],
  );

  const actions: AcmPanelInspectorActions = useMemo(
    () => ({
      onUpdateField: (field: AcmOperatorFieldKey, value: number | boolean | 1 | 2 | null) => {
        applyPatch(
          buildAcmPanelUpdateFieldPatch({
            finishSetup,
            field,
            value,
          }),
        );
      },
      onConfirmField: (fieldKeys: string[]) => {
        applyPatch(buildAcmPanelConfirmFieldPatch({ finishSetup, fieldKeys }));
      },
      onConfirmConstruction: () => {
        applyPatch(buildAcmPanelConfirmConstructionPatch({ finishSetup }));
      },
      onConfirmTechnical: () => {
        applyPatch(buildAcmPanelConfirmTechnicalPatch({ finishSetup }));
      },
      onConfirmRelation: (relationId: string) => {
        applyPatch(
          buildAcmPanelConfirmRelationPatch({
            finishSetup,
            relationId,
            status: "confirmed",
          }),
        );
      },
      onSegmentedPatch: (patch: { segmented_background: SegmentedBackground }) => {
        applyPatch(patch as Partial<IntakeV6FinishSetup>);
      },
    }),
    [applyPatch, finishSetup],
  );

  if (!items.length) return null;

  const showInspector = selectedId === "acm_panel" && acmModel.exists;

  return (
    <div
      className="mb-3 grid gap-2 lg:grid-cols-[minmax(200px,240px)_minmax(0,1fr)_minmax(200px,240px)]"
      data-testid="intake-v6-acm-panel-config-region"
    >
      <IntakeV6ProductComponentList
        items={items}
        selectedId={selectedId}
        onSelect={handleSelect}
      />
      <div className="min-w-0">
        {showInspector ? (
          <IntakeV6AcmPanelInspector
            model={acmModel}
            finishSetup={finishSetup}
            actions={actions}
            focusIssue={focusIssue}
            onFocusConsumed={() => setFocusIssue(null)}
          />
        ) : (
          <div
            className="rounded border border-[#2A3548]/50 bg-[#111827]/30 px-3 py-4 text-[12px] text-slate-400"
            data-testid="intake-v6-product-component-inspector-placeholder"
          >
            {selectedId === "letters"
              ? "Litere — folosește tab-ul Finisaje pentru configurare."
              : selectedId === "logo"
                ? "Vector Logo — folosește tab-ul Finisaje pentru configurare."
                : acmModel.exists
                  ? "Selectează Panou Alucobond casetat pentru inspector."
                  : "Selectează o componentă din listă."}
          </div>
        )}
      </div>
      {acmModel.exists ? (
        <IntakeV6AcmPanelValidationRail
          model={acmModel}
          onIssueClick={(issue) => {
            onSelect("acm_panel");
            setFocusIssue(issue);
          }}
        />
      ) : (
        <div />
      )}
    </div>
  );
}

export function openAcmPanelInspectorFromLegacy(args: {
  onSelect: (id: IntakeV6ProductComponentId) => void;
  setFocusSection?: (sectionId: string) => void;
  sectionId?: string;
}) {
  args.onSelect("acm_panel");
  args.setFocusSection?.(args.sectionId ?? "summary");
}
