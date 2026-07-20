/**
 * Thin selection state for Configurare product components.
 * Does not write payload. Persists per workspace in sessionStorage.
 */

import { useCallback, useEffect, useState } from "react";

export type IntakeV6ProductComponentId = "letters" | "logo" | "acm_panel";

const storageKey = (workspaceId: string) =>
  `workos.intakeV6.selectedProductComponent:${workspaceId}`;

export function useIntakeV6ProductComponentSelection(workspaceId: string | null | undefined) {
  const [selectedId, setSelectedIdState] = useState<IntakeV6ProductComponentId | null>(null);

  useEffect(() => {
    if (!workspaceId) {
      setSelectedIdState(null);
      return;
    }
    try {
      const raw = sessionStorage.getItem(storageKey(workspaceId));
      if (raw === "letters" || raw === "logo" || raw === "acm_panel") {
        setSelectedIdState(raw);
      }
    } catch {
      /* ignore */
    }
  }, [workspaceId]);

  const setSelectedId = useCallback(
    (id: IntakeV6ProductComponentId | null) => {
      setSelectedIdState(id);
      if (!workspaceId) return;
      try {
        if (id) sessionStorage.setItem(storageKey(workspaceId), id);
        else sessionStorage.removeItem(storageKey(workspaceId));
      } catch {
        /* ignore */
      }
    },
    [workspaceId],
  );

  return { selectedId, setSelectedId };
}
