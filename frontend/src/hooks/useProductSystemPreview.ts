/**
 * S30 — Read-only hook for ProductSystem Execution Preview.
 *
 * Fetches GET /api/v1/product_system/preview/{order_id}.
 * No mutations. No writes. Pure read-only.
 */

import { useCallback, useEffect, useState } from "react";
import type { ProductSystemExecutionPreview } from "@/types/preview.types";
import { getAPIBaseURL } from "@/lib/config";

interface UseProductSystemPreviewState {
  data: ProductSystemExecutionPreview | null;
  loading: boolean;
  error: string | null;
}

export function useProductSystemPreview(orderId: number | null) {
  const [state, setState] = useState<UseProductSystemPreviewState>({
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
        `${base}/api/v1/product_system/preview/${orderId}`,
        { credentials: "include" }
      );
      if (res.status === 404 || res.status === 422) {
        // Template not found or inactive — not a crash, just no preview available
        setState({ data: null, loading: false, error: null });
        return;
      }
      if (!res.ok) {
        throw new Error(
          `GET /product_system/preview/${orderId} failed: ${res.status} ${res.statusText}`
        );
      }
      const json = (await res.json()) as ProductSystemExecutionPreview;
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