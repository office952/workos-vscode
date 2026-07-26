/**
 * Thin bridge: acm-panel registers flushAll; OperatorWorkspace awaits it on Back/Next.
 * Draft ownership stays in Inspector — this context holds only a flush function ref.
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  type ReactNode,
} from "react";
import {
  emptyFlushResult,
  type AcmPanelFlushResult,
} from "@/lib/intakeV6/acmPanel/commitSemantics";

type FlushFn = () => AcmPanelFlushResult;

type AcmPanelDraftFlushContextValue = {
  registerFlush: (fn: FlushFn | null) => void;
  flushAcmPanelDrafts: () => AcmPanelFlushResult;
};

const AcmPanelDraftFlushContext = createContext<AcmPanelDraftFlushContextValue | null>(
  null,
);

export function AcmPanelDraftFlushProvider({ children }: { children: ReactNode }) {
  const flushRef = useRef<FlushFn | null>(null);
  const registerFlush = useCallback((fn: FlushFn | null) => {
    flushRef.current = fn;
  }, []);
  const flushAcmPanelDrafts = useCallback((): AcmPanelFlushResult => {
    if (!flushRef.current) return emptyFlushResult("nothing_to_commit");
    return flushRef.current();
  }, []);
  const value = useMemo(
    () => ({ registerFlush, flushAcmPanelDrafts }),
    [flushAcmPanelDrafts, registerFlush],
  );
  return (
    <AcmPanelDraftFlushContext.Provider value={value}>
      {children}
    </AcmPanelDraftFlushContext.Provider>
  );
}

export function useAcmPanelDraftFlushBridge(): AcmPanelDraftFlushContextValue {
  const ctx = useContext(AcmPanelDraftFlushContext);
  if (!ctx) {
    return {
      registerFlush: () => undefined,
      flushAcmPanelDrafts: () => emptyFlushResult("nothing_to_commit"),
    };
  }
  return ctx;
}

/** Returns true when navigation/action may continue. */
export function canContinueAfterAcmPanelFlush(result: AcmPanelFlushResult): boolean {
  return result.status === "nothing_to_commit" || result.status === "committed";
}
