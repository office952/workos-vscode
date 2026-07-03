import { useMemo } from "react";
import {
  buildModuleActivationPreview,
  modularContractLoadStatus,
  type ModuleActivationPreviewResult,
} from "./intakeV6ModuleActivationPreview";
import type { IntakeV6ModularFormContractResponse } from "./intakeV6ModularFormContractTypes";

export interface UseModularFormAwarenessInput {
  contract: IntakeV6ModularFormContractResponse | null;
  loading: boolean;
  error: string | null;
  finishSetup: Record<string, unknown> | null | undefined;
  quoteGeometry: Record<string, unknown> | null | undefined;
  svgSource: Record<string, unknown> | null | undefined;
  analysisReady: boolean;
}

export function useModularFormAwareness(input: UseModularFormAwarenessInput): {
  loadStatus: ReturnType<typeof modularContractLoadStatus>;
  preview: ModuleActivationPreviewResult | null;
} {
  const preview = useMemo(
    () =>
      buildModuleActivationPreview(input.contract, {
        finishSetup: input.finishSetup,
        quoteGeometry: input.quoteGeometry,
        svgSource: input.svgSource,
        analysisReady: input.analysisReady,
      }),
    [
      input.contract,
      input.finishSetup,
      input.quoteGeometry,
      input.svgSource,
      input.analysisReady,
    ],
  );

  const loadStatus = modularContractLoadStatus(input.loading, input.error, input.contract);

  return { loadStatus, preview };
}
