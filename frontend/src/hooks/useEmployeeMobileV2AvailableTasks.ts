import { useEmployeeMobileV2TaskTruthContext } from "@/contexts/EmployeeMobileV2TaskTruthContext";

export function useEmployeeMobileV2AvailableTasks() {
  const { view, loading, error, reload } = useEmployeeMobileV2TaskTruthContext();
  return {
    tasks: view?.availableTasks ?? [],
    loading,
    error,
    reload,
  };
}
