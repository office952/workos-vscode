import { useEmployeeMobileV2TaskTruthContext } from "@/contexts/EmployeeMobileV2TaskTruthContext";
import type { EmployeeMobileTaskDTO } from "@/api/employeeMobileTasks";

export function useEmployeeMobileV2Tasks() {
  const { view, loading, error, reload } = useEmployeeMobileV2TaskTruthContext();
  return {
    tasks: view?.assignedTasks ?? [],
    loading,
    error,
    reload,
  };
}

export function useEmployeeMobileV2AssignedTasks(): {
  tasks: EmployeeMobileTaskDTO[];
  inProgressTasks: EmployeeMobileTaskDTO[];
  loading: boolean;
  error: string | null;
  reload: () => Promise<void>;
} {
  const { view, loading, error, reload } = useEmployeeMobileV2TaskTruthContext();
  return {
    tasks: view?.assignedTasks ?? [],
    inProgressTasks: view?.inProgressTasks ?? [],
    loading,
    error,
    reload,
  };
}
