import { useState, useCallback } from "react";
import { getAPIBaseURL } from "@/lib/config";
import type { MaterialRow } from "@/components/workos/MaterialsCapturePanel";

interface UseMaterialsCaptureReturn {
  materials: MaterialRow[];
  loading: boolean;
  error: string | null;
  fetchMaterials: (orderId: number) => Promise<void>;
  addMaterials: (orderId: number, rows: MaterialRow[]) => Promise<boolean>;
  updateMaterial: (orderId: number, index: number, row: MaterialRow) => Promise<boolean>;
  removeMaterial: (orderId: number, index: number) => Promise<boolean>;
}

export function useMaterialsCapture(): UseMaterialsCaptureReturn {
  const [materials, setMaterials] = useState<MaterialRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMaterials = useCallback(async (orderId: number) => {
    setLoading(true);
    setError(null);
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/execution/reality/${orderId}/materials`, {
        credentials: "include",
      });
      if (!res.ok) {
        if (res.status === 404) {
          // No reality row yet — that's fine, no materials
          setMaterials([]);
          return;
        }
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setMaterials(data.materials ?? []);
    } catch (err) {
      console.warn("[useMaterialsCapture] fetch failed:", err);
      setError(err instanceof Error ? err.message : "Eroare necunoscută");
      setMaterials([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const addMaterials = useCallback(async (orderId: number, rows: MaterialRow[]): Promise<boolean> => {
    setError(null);
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/execution/reality/${orderId}/materials`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ materials: rows }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData?.detail?.detail || errData?.detail?.code || "Eroare la salvare");
        return false;
      }
      const data = await res.json();
      setMaterials(data.materials ?? []);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare necunoscută");
      return false;
    }
  }, []);

  const updateMaterial = useCallback(async (orderId: number, index: number, row: MaterialRow): Promise<boolean> => {
    setError(null);
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/execution/reality/${orderId}/materials/${index}`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(row),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData?.detail?.detail || errData?.detail?.code || "Eroare la actualizare");
        return false;
      }
      const data = await res.json();
      setMaterials(data.materials ?? []);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare necunoscută");
      return false;
    }
  }, []);

  const removeMaterial = useCallback(async (orderId: number, index: number): Promise<boolean> => {
    setError(null);
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/execution/reality/${orderId}/materials/${index}`, {
        method: "DELETE",
        credentials: "include",
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        setError(errData?.detail?.detail || errData?.detail?.code || "Eroare la ștergere");
        return false;
      }
      const data = await res.json();
      setMaterials(data.materials ?? []);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eroare necunoscută");
      return false;
    }
  }, []);

  return {
    materials,
    loading,
    error,
    fetchMaterials,
    addMaterials,
    updateMaterial,
    removeMaterial,
  };
}