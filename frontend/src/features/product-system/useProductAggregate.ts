import { useEffect, useState } from "react";
import {
  getProductAggregate,
  ProductAggregateNotFoundError,
  type ProductAggregate,
} from "@/api/productAggregate";

export type ProductAggregateLoadStatus = "idle" | "loading" | "ready" | "fallback";

export function useProductAggregate(templateCode: string | null | undefined) {
  const [aggregate, setAggregate] = useState<ProductAggregate | null>(null);
  const [status, setStatus] = useState<ProductAggregateLoadStatus>("idle");
  const [fallbackReason, setFallbackReason] = useState<string | null>(null);

  useEffect(() => {
    const code = templateCode?.trim();
    if (!code) {
      setAggregate(null);
      setStatus("idle");
      setFallbackReason(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setFallbackReason(null);

    getProductAggregate(code)
      .then((data) => {
        if (cancelled) return;
        setAggregate(data);
        setStatus("ready");
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setAggregate(null);
        setStatus("fallback");
        if (error instanceof ProductAggregateNotFoundError) {
          setFallbackReason("ProductAggregate unavailable; falling back to legacy template display.");
        } else {
          setFallbackReason("ProductAggregate unavailable; falling back to legacy template display.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  return {
    aggregate,
    status,
    fallbackReason,
    usingFallback: status === "fallback",
    isLoading: status === "loading",
  };
}
