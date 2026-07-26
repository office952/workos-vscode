import { useCallback, useEffect, useState } from "react";
import {
  fetchEmployeeMobileTaskTruth,
  type EmployeeMobileTaskTruthResponse,
} from "@/api/employeeMobileTasks";
import {
  buildEmployeeMobileV2TaskTruthView,
  type EmployeeMobileV2TaskTruthView,
} from "@/lib/employeeMobileV2TaskTruth";
import {
  isContractError,
  isEmployeeLinkError,
  mapMobileTaskErrorMessage,
} from "@/lib/employeeMobileV2TaskErrors";

export interface EmployeeMobileV2TaskTruthState {
  view: EmployeeMobileV2TaskTruthView | null;
  loading: boolean;
  error: string | null;
  errorCode: string | null;
  employeeLinkMissing: boolean;
  contractError: boolean;
  reload: () => Promise<void>;
}

export function useEmployeeMobileV2TaskTruth(): EmployeeMobileV2TaskTruthState {
  const [view, setView] = useState<EmployeeMobileV2TaskTruthView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorCode, setErrorCode] = useState<string | null>(null);

  const reload = useCallback(async (options?: { background?: boolean }) => {
    const background = options?.background === true;
    if (!background) {
      setLoading(true);
    }
    setError(null);
    setErrorCode(null);
    try {
      const response = (await fetchEmployeeMobileTaskTruth()) as EmployeeMobileTaskTruthResponse;
      setView(buildEmployeeMobileV2TaskTruthView(response));
    } catch (err) {
      if (!background) {
        setView(null);
      }
      setError(mapMobileTaskErrorMessage(err));
      setErrorCode((err as { code?: string })?.code ?? null);
    } finally {
      if (!background) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  return {
    view,
    loading,
    error,
    errorCode,
    employeeLinkMissing: Boolean(
      error && isEmployeeLinkError({ code: errorCode ?? undefined, message: error }),
    ),
    contractError: Boolean(
      error && isContractError({ code: errorCode ?? undefined, message: error }),
    ),
    reload,
  };
}
