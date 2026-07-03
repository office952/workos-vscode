import { useEffect, useState, useCallback } from "react";
import { getAPIBaseURL } from "@/lib/config";
import { isMockEnabled } from "@/lib/mockGuard";
import {
  externalCollaborators as mockCollaborators,
  type ExternalCollaborator,
  type CollabCategory,
  type CollabStatus,
} from "@/lib/mockData";

type ColabSource = "db" | "mock" | "empty" | "error" | "loading";

interface ColaboratoriDataState {
  collaborators: ExternalCollaborator[];
  loading: boolean;
  error: string | null;
  source: ColabSource;
  refresh: () => Promise<void>;
}

/** DB row shape from /api/v1/entities/suppliers */
interface SupplierRow {
  id: number;
  code: string;
  name: string;
  category?: string | null;
  lead_time_days?: number | null;
  rating?: number | null;
  active_orders?: number | null;
  last_delivery?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
}

/**
 * Map a SupplierRow from the backend to the ExternalCollaborator shape used by the UI.
 */
function mapSupplierToCollaborator(s: SupplierRow): ExternalCollaborator {
  // Map category
  const catMap: Record<string, CollabCategory> = {
    produs: "produs",
    serviciu: "serviciu",
    materii_prime: "produs",
    consumabile: "produs",
    echipamente: "produs",
  };
  const category: CollabCategory =
    catMap[(s.category ?? "produs").toLowerCase()] ?? "produs";

  // Determine status based on active_orders
  let status: CollabStatus = "activ";
  if (s.rating && s.rating >= 5) status = "preferat";
  else if (s.active_orders === 0 && !s.last_delivery) status = "inactiv";

  return {
    id: `SUP-${String(s.id).padStart(3, "0")}`,
    companyName: s.name,
    cui: s.code,
    contactPerson: "—",
    phone: "—",
    email: "—",
    category,
    specializations: s.category ? [s.category] : [],
    description: `Furnizor ${s.name} — ${s.category ?? "general"}`,
    status,
    qualityRating: Math.min(s.rating ?? 3, 5),
    avgDeliveryDays: s.lead_time_days ?? 7,
    totalOrdersCompleted: s.active_orders ?? 0,
    totalValueRON: (s.active_orders ?? 0) * 2500,
    lastOrderDate: s.last_delivery ?? new Date().toISOString().slice(0, 10),
    city: "România",
    notes: "",
  };
}

export function useColaboratoriData(): ColaboratoriDataState {
  const mockEnabled = isMockEnabled();
  const [collaborators, setCollaborators] = useState<ExternalCollaborator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [source, setSource] = useState<ColabSource>("loading");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const base = getAPIBaseURL();
      const res = await fetch(`${base}/api/v1/entities/suppliers/all?limit=500`, {
        credentials: "include",
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const items: SupplierRow[] = data.items ?? data;
      if (items && items.length > 0) {
        setCollaborators(items.map(mapSupplierToCollaborator));
        setSource("db");
      } else if (mockEnabled) {
        setCollaborators(mockCollaborators);
        setSource("mock");
      } else {
        setCollaborators([]);
        setSource("empty");
      }
    } catch (err) {
      if (mockEnabled) {
        console.warn("[useColaboratoriData] API failed, using mock data", err);
        setCollaborators(mockCollaborators);
        setSource("mock");
      } else {
        console.warn("[useColaboratoriData] API failed, mock disabled", err);
        setCollaborators([]);
        setSource("error");
      }
      setError(err instanceof Error ? err.message : "Eroare necunoscută");
    } finally {
      setLoading(false);
    }
  }, [mockEnabled]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { collaborators, loading, error, source, refresh: fetchData };
}