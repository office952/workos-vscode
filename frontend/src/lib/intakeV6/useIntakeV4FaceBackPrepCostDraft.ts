import { useEffect, useState } from "react";

import {
  getIntakeV4FaceBackPrepCostDraft,
  type IntakeV4FaceBackPrepCostDraftResponse,
} from "@/lib/intakeV6/intakeV4Api";

export interface IntakeV4FaceBackPrepCostDraftViewModel {
  shanfrenForex: boolean;
  setShanfrenForex: (value: boolean) => void;
  draft: IntakeV4FaceBackPrepCostDraftResponse | null;
  loading: boolean;
  error: string | null;
}

export function useIntakeV4FaceBackPrepCostDraft(
  workspaceId: string | null,
  analysisReady: boolean,
  enabled = true,
): IntakeV4FaceBackPrepCostDraftViewModel {
  const [shanfrenForex, setShanfrenForex] = useState(false);
  const [draft, setDraft] = useState<IntakeV4FaceBackPrepCostDraftResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled || !workspaceId || !analysisReady) {
      setDraft(null);
      setError(null);
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    void getIntakeV4FaceBackPrepCostDraft(workspaceId, { shanfrenForex })
      .then((response) => {
        if (!cancelled) setDraft(response);
      })
      .catch(() => {
        if (!cancelled) {
          setDraft(null);
          setError("Nu s-a putut încărca draftul CNC față/spate.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [workspaceId, analysisReady, shanfrenForex, enabled]);

  return {
    shanfrenForex,
    setShanfrenForex,
    draft,
    loading,
    error,
  };
}
