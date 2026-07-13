import { createContext, useContext, useMemo, type ReactNode } from "react";
import { useCurrentPermissions } from "@/hooks/useCurrentPermissions";
import { PRODUCT_SYSTEM_ADVANCED_PERMISSION } from "./productSystemShellConfig";

export type ProductSystemShellContextValue = {
  /** True when user lacks admin governance permission — catalog/editor actions hidden. */
  operatorReadOnly: boolean;
  /** True when existing RBAC grants Advanced nav (view:governance). */
  canViewAdvanced: boolean;
  /** Shell layout is active (nested Product System routes). */
  shellMode: boolean;
};

const ProductSystemShellContext = createContext<ProductSystemShellContextValue>({
  operatorReadOnly: true,
  canViewAdvanced: false,
  shellMode: false,
});

export function ProductSystemShellProvider({
  shellMode = true,
  children,
}: {
  shellMode?: boolean;
  children: ReactNode;
}) {
  const { can } = useCurrentPermissions();
  const canViewAdvanced = can(PRODUCT_SYSTEM_ADVANCED_PERMISSION);

  const value = useMemo<ProductSystemShellContextValue>(
    () => ({
      operatorReadOnly: !canViewAdvanced,
      canViewAdvanced,
      shellMode,
    }),
    [canViewAdvanced, shellMode],
  );

  return (
    <ProductSystemShellContext.Provider value={value}>
      {children}
    </ProductSystemShellContext.Provider>
  );
}

export function useProductSystemShell(): ProductSystemShellContextValue {
  return useContext(ProductSystemShellContext);
}
