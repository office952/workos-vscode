/**
 * ReviewStep layout mount for product component list + AcmPanel inspector.
 * Owns no AcmPanel domain semantics — delegates to uiReadModel + operatorPatch drafts.
 *
 * variant="lab" — 3-col list | inspector | validation (legacy)
 * variant="workbench" — flat form in Panou/carcasă (no nested component list)
 */

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import IntakeV6ProductComponentList, {
  buildProductComponentListItems,
} from "./IntakeV6ProductComponentList";
import IntakeV6AcmPanelInspector, {
  type AcmPanelInspectorActions,
  type IntakeV6AcmPanelInspectorHandle,
} from "./IntakeV6AcmPanelInspector";
import IntakeV6AcmPanelValidationRail from "./IntakeV6AcmPanelValidationRail";
import IntakeV6AcmPanelBlueprintPreview from "./IntakeV6AcmPanelBlueprintPreview";
import {
  canContinueAfterAcmPanelFlush,
  useAcmPanelDraftFlushBridge,
} from "./AcmPanelDraftFlushContext";
import {
  buildAcmPanelUiReadModel,
  type AcmPanelIssue,
} from "@/lib/intakeV6/acmPanel/uiReadModel";
import type { IntakeV6ProductComponentId } from "@/lib/intakeV6/useIntakeV6ProductComponentSelection";
import type { IntakeV6FinishSetup } from "@/lib/intakeV6/intakeV6Api";
import type { SegmentedBackground } from "@/lib/intakeV6/segmentedBackground";
import { emptyFlushResult } from "@/lib/intakeV6/acmPanel/commitSemantics";
import { intakeV6ShowOperatorConfigStatusBadges } from "@/lib/intakeV6/intakeV6OperatorConfigStatusChrome";

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
  workspaceId,
  onProductionGeometryBound,
  variant = "lab",
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
  workspaceId?: string | null;
  onProductionGeometryBound?: () => void;
  /** workbench = flat Panou/carcasă form; lab = nested 3-col sheet/legacy */
  variant?: "lab" | "workbench";
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
  const inspectorRef = useRef<IntakeV6AcmPanelInspectorHandle | null>(null);
  const { registerFlush } = useAcmPanelDraftFlushBridge();

  useEffect(() => {
    registerFlush(() => {
      if (!inspectorRef.current) return emptyFlushResult("nothing_to_commit");
      return inspectorRef.current.flushAll();
    });
    return () => registerFlush(null);
  }, [registerFlush]);

  useEffect(() => {
    if (variant !== "workbench") return;
    if (!acmModel.exists) return;
    if (selectedId === "acm_panel") return;
    onSelect("acm_panel");
  }, [variant, acmModel.exists, selectedId, onSelect]);

  const handleSelect = useCallback(
    (id: IntakeV6ProductComponentId) => {
      if (selectedId === "acm_panel" && id !== "acm_panel") {
        const result = inspectorRef.current?.flushAll() ?? emptyFlushResult("nothing_to_commit");
        if (!canContinueAfterAcmPanelFlush(result)) return;
      }
      onSelect(id);
      if (id === "letters") onNavigateLetters();
      if (id === "logo") onNavigateLogo();
    },
    [onSelect, onNavigateLetters, onNavigateLogo, selectedId],
  );

  const actions: AcmPanelInspectorActions = useMemo(
    () => ({
      onApplyFinishPatch,
      onSegmentedPatch: (patch: { segmented_background: SegmentedBackground }) => {
        onApplyFinishPatch(patch as Partial<IntakeV6FinishSetup>);
      },
      onProductionGeometryBound,
    }),
    [onApplyFinishPatch, onProductionGeometryBound],
  );

  if (!items.length && !acmModel.exists) return null;

  const showInspector =
    variant === "workbench"
      ? acmModel.exists
      : selectedId === "acm_panel" && acmModel.exists;

  if (variant === "workbench") {
    if (!acmModel.exists) return null;
    const onValidationIssue = (issue: AcmPanelIssue) => {
      const result =
        inspectorRef.current?.flushAll() ?? emptyFlushResult("nothing_to_commit");
      if (!canContinueAfterAcmPanelFlush(result)) return;
      onSelect("acm_panel");
      setFocusIssue(issue);
    };
    const validationClean = acmModel.issues.length === 0;
    return (
      <div
        className="space-y-2"
        data-testid="intake-v6-acm-panel-config-region"
        data-acm-layout="workbench"
      >
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <p className="text-[13px] font-semibold text-slate-100">Panou Alucobond</p>
            <p className="text-[11px] text-slate-500">Geometrie, construcție și finisaj</p>
          </div>
          {intakeV6ShowOperatorConfigStatusBadges() ? (
            <p
              className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-0.5 text-[11px] font-medium text-cyan-100"
              data-testid="intake-v6-acm-workbench-status"
            >
              {acmModel.primaryStatus.label}
            </p>
          ) : null}
        </div>
        <div
          className="overflow-hidden rounded border border-[#2A3548]/55 bg-[#0B1220]/80"
          data-testid="intake-v6-acm-tech-status-strip"
        >
          <IntakeV6AcmPanelBlueprintPreview
            chrome="embedded"
            finishSetup={finishSetup}
            payload={payload ?? null}
            inlineMeta={
              validationClean ? (
                <span
                  data-testid="intake-v6-acm-validation-rail"
                  data-density="inline"
                  data-state="clean"
                >
                  <span className="font-medium text-emerald-300/90">Validare</span>
                  {" · fără probleme deschise"}
                </span>
              ) : null
            }
          />
          {!validationClean ? (
            <IntakeV6AcmPanelValidationRail
              density="inline"
              model={acmModel}
              onIssueClick={onValidationIssue}
            />
          ) : null}
        </div>
        {showInspector ? (
          <div className="min-w-0">
            <IntakeV6AcmPanelInspector
              ref={inspectorRef}
              model={acmModel}
              finishSetup={finishSetup}
              actions={actions}
              focusIssue={focusIssue}
              onFocusConsumed={() => setFocusIssue(null)}
              workspaceId={workspaceId}
              presentation="flat"
            />
          </div>
        ) : null}
      </div>
    );
  }

  return (
    <div
      className="mb-3 grid gap-2 lg:grid-cols-[minmax(200px,240px)_minmax(0,1fr)_minmax(200px,240px)]"
      data-testid="intake-v6-acm-panel-config-region"
      data-acm-layout="lab"
    >
      <IntakeV6ProductComponentList
        items={items}
        selectedId={selectedId}
        onSelect={handleSelect}
      />
      <div className="min-w-0">
        {showInspector ? (
          <div
            className="flex min-w-0 flex-col gap-2 xl:grid xl:grid-cols-[minmax(0,1fr)_minmax(220px,280px)] xl:items-start"
            data-testid="intake-v6-acm-inspector-with-blueprint"
          >
            <div className="min-w-0 order-2 xl:order-1">
              <IntakeV6AcmPanelInspector
                ref={inspectorRef}
                model={acmModel}
                finishSetup={finishSetup}
                actions={actions}
                focusIssue={focusIssue}
                onFocusConsumed={() => setFocusIssue(null)}
                workspaceId={workspaceId}
              />
            </div>
            <div className="order-1 xl:order-2 xl:sticky xl:top-2">
              <IntakeV6AcmPanelBlueprintPreview
                finishSetup={finishSetup}
                payload={payload ?? null}
              />
            </div>
          </div>
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
                  ? "Selectează Alucobond casetat pentru inspector."
                  : "Selectează o componentă din listă."}
          </div>
        )}
      </div>
      {acmModel.exists ? (
        <IntakeV6AcmPanelValidationRail
          model={acmModel}
          onIssueClick={(issue) => {
            if (selectedId === "acm_panel") {
              const result =
                inspectorRef.current?.flushAll() ?? emptyFlushResult("nothing_to_commit");
              if (!canContinueAfterAcmPanelFlush(result)) return;
            }
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
