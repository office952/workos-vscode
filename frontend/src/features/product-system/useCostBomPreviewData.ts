import { useEffect, useState } from "react";
import {
  CostBomPreviewNotFoundError,
  getCostBomPreview,
  type CostBomPreview,
} from "@/api/costBomPreview";

export type CostBomPreviewLoadStatus = "idle" | "loading" | "ready" | "unavailable";

export function useCostBomPreviewData(templateCode: string | null | undefined) {
  const [preview, setPreview] = useState<CostBomPreview | null>(null);
  const [status, setStatus] = useState<CostBomPreviewLoadStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = templateCode?.trim();
    if (!code) {
      setPreview(null);
      setStatus("idle");
      setError(null);
      return;
    }

    let cancelled = false;
    setStatus("loading");
    setError(null);

    getCostBomPreview(code)
      .then((data) => {
        if (cancelled) return;
        setPreview(data);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setPreview(null);
        setStatus("unavailable");
        if (err instanceof CostBomPreviewNotFoundError) {
          setError("Cost BOM preview indisponibil pentru acest template.");
        } else {
          setError(err instanceof Error ? err.message : "Eroare la încărcarea cost BOM preview.");
        }
      });

    return () => {
      cancelled = true;
    };
  }, [templateCode]);

  return { preview, status, error, isLoading: status === "loading" };
}
