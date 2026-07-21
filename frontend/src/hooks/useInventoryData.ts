import { useState, useEffect, useCallback, useRef } from "react";
import { getAPIBaseURL } from "@/lib/config";
import { isMockEnabled } from "@/lib/mockGuard";
import {
  inventoryMaterials as mockMaterials,
  suppliers as mockSuppliers,
  type InventoryMaterial,
  type Supplier,
} from "@/lib/mockData";
import {
  classifyInventoryUiTab,
  computeInventoryStockStatus,
} from "@/lib/inventory/inventoryMaterialClassification";

export type DataSource = "db" | "mock" | "empty" | "error" | "loading";

/** DB row shape from /api/v1/entities/inventory_materials */
interface DBMaterial {
  id: number;
  code: string;
  name: string;
  category: string | null;
  unit: string;
  stock_current: number | null;
  stock_min: number | null;
  stock_max: number | null;
  unit_cost: number | null;
  supplier: string | null;
  last_restocked: string | null;
  consumption_rate: number | null;
  location: string | null;
  status?: string | null;
  created_at: string | null;
  updated_at: string | null;
}

/** DB row shape from /api/v1/entities/suppliers */
interface DBSupplier {
  id: number;
  code: string;
  name: string;
  category: string | null;
  lead_time_days: number | null;
  rating: number | null;
  active_orders: number | null;
  last_delivery: string | null;
  created_at: string | null;
  updated_at: string | null;
}

function computeDaysUntilEmpty(
  current: number | null,
  consumptionRate: number
): number {
  if (current === null || consumptionRate <= 0 || current <= 0) return 0;
  return Math.round(current / consumptionRate);
}

function mapDBToMaterial(db: DBMaterial): InventoryMaterial {
  const stockCurrent = db.stock_current;
  const stockMin = db.stock_min ?? 0;
  const stockMax =
    db.stock_max ??
    (stockCurrent !== null ? Math.max(stockCurrent * 2, 100) : 100);
  const unitCost = db.unit_cost;
  const consumptionRate = db.consumption_rate ?? 0;
  const uiTabCategory = classifyInventoryUiTab({
    category: db.category,
    unit: db.unit,
    code: db.code,
  });

  return {
    id: db.code,
    name: db.name,
    category: db.category || "Altele",
    unit: db.unit,
    stockCurrent,
    stockMin,
    stockMax,
    unitCost,
    supplier: db.supplier || "N/A",
    lastRestocked: db.last_restocked || "N/A",
    consumptionRate,
    daysUntilEmpty: computeDaysUntilEmpty(stockCurrent, consumptionRate),
    stockStatus: computeInventoryStockStatus({
      stockCurrent,
      stockMin,
    }),
    location: db.location || "",
    registryStatus: db.status ?? null,
    uiTabCategory,
  };
}

function mapDBToSupplier(db: DBSupplier): Supplier {
  return {
    id: db.code,
    name: db.name,
    category: db.category || "General",
    leadTimeDays: db.lead_time_days ?? 7,
    rating: db.rating ?? 3,
    activeOrders: db.active_orders ?? 0,
    lastDelivery: db.last_delivery || "N/A",
  };
}

function annotateMockMaterial(m: InventoryMaterial): InventoryMaterial {
  return {
    ...m,
    uiTabCategory:
      m.uiTabCategory ??
      classifyInventoryUiTab({
        category: m.category,
        unit: m.unit,
        code: m.id,
      }),
    registryStatus: m.registryStatus ?? (m.unitCost == null ? "missing_price" : "active"),
  };
}

interface InventoryDataState {
  materials: InventoryMaterial[];
  suppliers: Supplier[];
  source: DataSource;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

export function useInventoryData(): InventoryDataState {
  const mockEnabled = isMockEnabled();
  const [materials, setMaterials] = useState<InventoryMaterial[]>(
    mockEnabled ? mockMaterials.map(annotateMockMaterial) : []
  );
  const [suppliers, setSuppliers] = useState<Supplier[]>(mockEnabled ? mockSuppliers : []);
  const [source, setSource] = useState<DataSource>(mockEnabled ? "mock" : "loading");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const base = getAPIBaseURL();

      const [matRes, supRes] = await Promise.all([
        fetch(`${base}/api/v1/entities/inventory_materials/all?limit=500`, {
          signal: AbortSignal.timeout(8000),
        }),
        fetch(`${base}/api/v1/entities/suppliers/all?limit=500`, {
          signal: AbortSignal.timeout(8000),
        }),
      ]);

      if (!matRes.ok) throw new Error(`Materials HTTP ${matRes.status}`);
      if (!supRes.ok) throw new Error(`Suppliers HTTP ${supRes.status}`);

      const matData = await matRes.json();
      const supData = await supRes.json();

      if (!mountedRef.current) return;

      const dbMaterials: DBMaterial[] = matData.items || [];
      const dbSuppliers: DBSupplier[] = supData.items || [];

      if (dbMaterials.length > 0) {
        setMaterials(dbMaterials.map(mapDBToMaterial));
        setSource("db");
      } else if (mockEnabled) {
        setMaterials(mockMaterials.map(annotateMockMaterial));
        setSource("mock");
      } else {
        setMaterials([]);
        setSource("empty");
      }

      if (dbSuppliers.length > 0) {
        setSuppliers(dbSuppliers.map(mapDBToSupplier));
      }

      setError(null);
    } catch (err) {
      if (!mountedRef.current) return;
      if (mockEnabled) {
        console.warn("[useInventoryData] API unavailable, using mock data:", err);
        setMaterials(mockMaterials.map(annotateMockMaterial));
        setSuppliers(mockSuppliers);
        setSource("mock");
      } else {
        console.warn("[useInventoryData] API unavailable, mock disabled:", err);
        setMaterials([]);
        setSuppliers([]);
        setSource("error");
      }
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [mockEnabled]);

  useEffect(() => {
    mountedRef.current = true;
    fetchData();
    return () => {
      mountedRef.current = false;
    };
  }, [fetchData]);

  return {
    materials,
    suppliers,
    source,
    loading,
    error,
    refresh: fetchData,
  };
}
