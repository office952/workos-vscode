import { useCallback, useEffect, useState } from "react";
import {
  executionApi,
  type ExecutionPlanV2MaterializationAuditResponse,
  type ExecutionPlanV2PreviewResponse,
} from "@/api/execution";

interface ExecutionPlanV2TruthState {
  preview: ExecutionPlanV2PreviewResponse | null;
  audit: ExecutionPlanV2MaterializationAuditResponse | null;
  loading: boolean;
  previewError: string | null;
  auditError: string | null;
}

export function useExecutionPlanV2Truth(orderId: number | null, enabled: boolean) {
  const [state, setState] = useState<ExecutionPlanV2TruthState>({
    preview: null,
    audit: null,
    loading: false,
    previewError: null,
    auditError: null,
  });

  const refresh = useCallback(async () => {
    if (!enabled || orderId === null || !Number.isInteger(orderId) || orderId <= 0) {
      setState({ preview: null, audit: null, loading: false, previewError: null, auditError: null });
      return;
    }

    setState((prev) => ({ ...prev, loading: true, previewError: null, auditError: null }));

    const [previewResult, auditResult] = await Promise.allSettled([
      executionApi.getExecutionPlanV2Preview(orderId),
      executionApi.getExecutionPlanV2MaterializationAudit(orderId),
    ]);

    setState({
      preview: previewResult.status === "fulfilled" ? previewResult.value : null,
      audit: auditResult.status === "fulfilled" ? auditResult.value : null,
      loading: false,
      previewError:
        previewResult.status === "rejected"
          ? previewResult.reason instanceof Error
            ? previewResult.reason.message
            : "unknown error"
          : null,
      auditError:
        auditResult.status === "rejected"
          ? auditResult.reason instanceof Error
            ? auditResult.reason.message
            : "unknown error"
          : null,
    });
  }, [enabled, orderId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return { ...state, refresh };
}