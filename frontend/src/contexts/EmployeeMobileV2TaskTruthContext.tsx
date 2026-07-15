import { createContext, useContext, type ReactNode } from "react";
import {
  useEmployeeMobileV2TaskTruth,
  type EmployeeMobileV2TaskTruthState,
} from "@/hooks/useEmployeeMobileV2TaskTruth";

const EmployeeMobileV2TaskTruthContext = createContext<EmployeeMobileV2TaskTruthState | null>(null);

export function EmployeeMobileV2TaskTruthProvider({ children }: { children: ReactNode }) {
  const value = useEmployeeMobileV2TaskTruth();
  return (
    <EmployeeMobileV2TaskTruthContext.Provider value={value}>
      {children}
    </EmployeeMobileV2TaskTruthContext.Provider>
  );
}

export function useEmployeeMobileV2TaskTruthContext(): EmployeeMobileV2TaskTruthState {
  const context = useContext(EmployeeMobileV2TaskTruthContext);
  if (!context) {
    throw new Error("EmployeeMobileV2TaskTruthProvider is required");
  }
  return context;
}
