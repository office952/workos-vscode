/**
 * S30 — Read-only hook for Gate Evaluation.
 *
 * Fetches GET /api/v1/execution/plan/gate/{order_id}.
 * No mutations. No writes. Pure read-only.
 */

import { useCallback, useEffect, useState } from "react";
import type { GateEvaluation } from "@/types/gate.types";
import { getAPIBaseURL } from "@/lib/config";

interface UseGateEvaluationState {
  data: GateEvaluation | null;
  loading: boolean;
  error: string | null;
}

export function useGateEvaluation(orderId: number | null) {
  const [state, setState] = useState<UseGateEvaluationState>({
    data: null,
    loading: false,
    error: null,
  });

  const fetch_ = useCallback(async () => {
    if (orderId === null || !Number.isInteger(orderId) || orderId <= 0) {
      return;
    }
    setState({ data: null, loading: true, error: null });
    try {
      const base = getAPIBaseURL();
      const res = await fetch(
        `${base}/api/v1/execution/plan/gate/${orderId}`,
        { credentials: "include" }
      );
      if (!res.ok) {
        throw new Error(
          `GET /execution/plan/gate/${orderId} failed: ${res.status} ${res.statusText}`
        );
      }
      const json = (await res.json()) as GateEvaluation;
      setState({ data: json, loading: false, error: null });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "unknown error";
      setState({ data: null, loading: false, error: msg });
    }
  }, [orderId]);

  useEffect(() => {
    void fetch_();
  }, [fetch_]);

  return { ...state, refresh: fetch_ };
}