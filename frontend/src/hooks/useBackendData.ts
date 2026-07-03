import { useEffect, useState, useCallback } from "react";
import {
  loadIntakes,
  loadQuotes,
  loadOrders,
  loadMaterials,
  loadSuppliers,
  seedIfEmpty,
  type DataSource,
} from "@/lib/dataStore";
import type {
  IntakeRequest,
  Quote,
  Order,
  InventoryMaterial,
  Supplier,
} from "@/lib/mockData";

interface BackendDataState {
  intakes: IntakeRequest[];
  quotes: Quote[];
  orders: Order[];
  materials: InventoryMaterial[];
  suppliers: Supplier[];
  loading: boolean;
  error: string | null;
  source: DataSource | "mixed" | "loading";
  /** Per-entity source breakdown for diagnostics */
  sourcesDetail: Record<string, DataSource>;
  refresh: () => Promise<void>;
}

/**
 * Returns true ONLY when the explicit VITE_ENABLE_MOCK_DATA flag is set to "true".
 * Seeding is a no-op when this returns false (seedIfEmpty checks internally too,
 * but we skip the call entirely for clarity).
 */
function isMockDataEnabled(): boolean {
  return import.meta.env.VITE_ENABLE_MOCK_DATA === "true";
}

let seedPromise: Promise<void> | null = null;

async function ensureSeed(): Promise<void> {
  // BLOCKER FIX: Only attempt seeding when mock flag is explicitly enabled
  if (!isMockDataEnabled()) {
    return;
  }

  if (!seedPromise) {
    seedPromise = seedIfEmpty()
      .then((r) => {
        if (r.seeded) {
          console.info("[useBackendData] DB seeded from mockData (VITE_ENABLE_MOCK_DATA=true)", r.details);
        }
      })
      .catch((err) => {
        console.warn("[useBackendData] seedIfEmpty failed", err);
      });
  }
  return seedPromise;
}

/**
 * Derive aggregate source from individual sources.
 * AUDIT FIX (Task 8): source truth is derived, never hardcoded.
 */
function deriveAggregateSource(sources: DataSource[]): DataSource | "mixed" {
  const unique = new Set(sources);
  if (unique.size === 0) return "empty";
  if (unique.size === 1) return sources[0];
  // Multiple different sources = mixed
  return "mixed";
}

/**
 * Loads backend data. Mock fallback is ONLY used when VITE_ENABLE_MOCK_DATA=true.
 * AUDIT FIX (Task 8): source truth accurately reflects where data comes from.
 */
export function useBackendData(): BackendDataState {
  const [state, setState] = useState<Omit<BackendDataState, "refresh">>({
    intakes: [],
    quotes: [],
    orders: [],
    materials: [],
    suppliers: [],
    loading: true,
    error: null,
    source: "loading",
    sourcesDetail: {},
  });

  const fetchAll = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      await ensureSeed();
      const [intakesRes, quotesRes, ordersRes, materialsRes, suppliersRes] =
        await Promise.all([
          loadIntakes(),
          loadQuotes(),
          loadOrders(),
          loadMaterials(),
          loadSuppliers(),
        ]);

      const sourcesDetail: Record<string, DataSource> = {
        intakes: intakesRes.source,
        quotes: quotesRes.source,
        orders: ordersRes.source,
        materials: materialsRes.source,
        suppliers: suppliersRes.source,
      };

      const aggregateSource = deriveAggregateSource(
        Object.values(sourcesDetail)
      );

      // Collect first error if any
      const firstError =
        intakesRes.error ||
        quotesRes.error ||
        ordersRes.error ||
        materialsRes.error ||
        suppliersRes.error ||
        null;

      setState({
        intakes: intakesRes.rows,
        quotes: quotesRes.rows,
        orders: ordersRes.rows,
        materials: materialsRes.rows,
        suppliers: suppliersRes.rows,
        loading: false,
        error: firstError,
        source: aggregateSource,
        sourcesDetail,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Eroare necunoscută";
      setState((s) => ({
        ...s,
        loading: false,
        error: msg,
        source: "error",
        sourcesDetail: {},
      }));
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return { ...state, refresh: fetchAll };
}