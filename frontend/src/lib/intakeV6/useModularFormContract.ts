import { useEffect, useState } from "react";
import { getIntakeV6ModularFormContract } from "./intakeV6Api";
import type { IntakeV6ModularFormContractResponse } from "./intakeV6ModularFormContractTypes";

export interface UseModularFormContractResult {
  contract: IntakeV6ModularFormContractResponse | null;
  loading: boolean;
  error: string | null;
  templateCode: string | null;
}

export function useModularFormContract(templateCode: string | null | undefined): UseModularFormContractResult {
  const normalizedCode = templateCode?.trim() || null;
  const [contract, setContract] = useState<IntakeV6ModularFormContractResponse | null>(null);
  const [loading, setLoading] = useState(() => Boolean(normalizedCode));
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const code = normalizedCode;
    if (!code) {
      setContract(null);
      setLoading(false);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);

    getIntakeV6ModularFormContract(code)
      .then((data) => {
        if (cancelled) return;
        setContract(data);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Contract modular indisponibil.";
        setError(message);
        setContract(null);
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [normalizedCode]);

  return {
    contract,
    loading,
    error,
    templateCode: normalizedCode,
  };
}
