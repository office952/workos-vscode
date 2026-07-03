import { useCallback, useEffect, useState } from "react";
import {
  employeeBalancesApi,
  type BalanceSummaryDTO,
  type BalanceTransactionDTO,
  type BalanceTransactionPayload,
} from "@/api/employeeBalances";

export interface UseEmployeeBalancesState {
  summary: BalanceSummaryDTO | null;
  transactions: BalanceTransactionDTO[];
  loading: boolean;
  transactionsLoading: boolean;
  error: string | null;
  refreshSummary: () => Promise<void>;
  loadTransactions: (filters?: {
    employee_id?: number;
    status?: string;
    transaction_type?: string;
  }) => Promise<void>;
  createTransaction: (payload: BalanceTransactionPayload) => Promise<void>;
  cancelTransaction: (id: number) => Promise<void>;
}

export function useEmployeeBalances(): UseEmployeeBalancesState {
  const [summary, setSummary] = useState<BalanceSummaryDTO | null>(null);
  const [transactions, setTransactions] = useState<BalanceTransactionDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [transactionsLoading, setTransactionsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshSummary = useCallback(async () => {
    const data = await employeeBalancesApi.summary();
    setSummary(data);
  }, []);

  const loadTransactions = useCallback(
    async (filters?: { employee_id?: number; status?: string; transaction_type?: string }) => {
      setTransactionsLoading(true);
      try {
        const rows = await employeeBalancesApi.listTransactions({
          employee_id: filters?.employee_id,
          status: filters?.status as BalanceTransactionDTO["status"] | undefined,
          transaction_type: filters?.transaction_type as BalanceTransactionDTO["transaction_type"] | undefined,
        });
        setTransactions(rows);
      } finally {
        setTransactionsLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    void employeeBalancesApi
      .summary()
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setSummary(null);
          setError(err instanceof Error ? err.message : "Nu s-au putut încărca soldurile.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    void loadTransactions();
    return () => {
      cancelled = true;
    };
  }, [loadTransactions]);

  const createTransaction = useCallback(
    async (payload: BalanceTransactionPayload) => {
      await employeeBalancesApi.createTransaction(payload);
      await refreshSummary();
      await loadTransactions();
    },
    [loadTransactions, refreshSummary]
  );

  const cancelTransaction = useCallback(
    async (id: number) => {
      await employeeBalancesApi.cancelTransaction(id);
      await refreshSummary();
      await loadTransactions();
    },
    [loadTransactions, refreshSummary]
  );

  return {
    summary,
    transactions,
    loading,
    transactionsLoading,
    error,
    refreshSummary,
    loadTransactions,
    createTransaction,
    cancelTransaction,
  };
}
