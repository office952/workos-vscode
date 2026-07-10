import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import type { WorkspaceHeaderStatusOverlay } from "@/lib/intakeV6/intakeV6WorkspaceHeaderStatus";

export type WorkspaceHeaderStatusHandlers = {
  onJumpToPending?: () => void;
  onJumpToLayers?: () => void;
  onJumpToLiveCalc?: () => void;
  onJumpToConfirm?: () => void;
};

export type ConfirmFooterState = {
  canSubmit: boolean;
  submitting: boolean;
  submitLabel: string;
  submittingLabel: string;
  disabledReason: string | null;
  checklistDone: number;
  checklistTotal: number;
  onSubmit: () => void;
};

type ContextValue = {
  overlay: WorkspaceHeaderStatusOverlay;
  setOverlay: (overlay: WorkspaceHeaderStatusOverlay) => void;
  handlers: WorkspaceHeaderStatusHandlers;
  setHandlers: (handlers: WorkspaceHeaderStatusHandlers) => void;
  confirmFooter: ConfirmFooterState | null;
  setConfirmFooter: (state: ConfirmFooterState | null) => void;
  openFooterIssues: () => void;
  registerFooterIssuesOpener: (opener: (() => void) | null) => void;
};

const IntakeV6WorkspaceHeaderStatusContext = createContext<ContextValue | null>(null);

const EMPTY_HANDLERS: WorkspaceHeaderStatusHandlers = {};

function confirmFooterStateEqual(
  a: ConfirmFooterState | null,
  b: ConfirmFooterState | null,
): boolean {
  if (a === b) return true;
  if (a == null || b == null) return false;
  return (
    a.canSubmit === b.canSubmit &&
    a.submitting === b.submitting &&
    a.submitLabel === b.submitLabel &&
    a.submittingLabel === b.submittingLabel &&
    a.disabledReason === b.disabledReason &&
    a.checklistDone === b.checklistDone &&
    a.checklistTotal === b.checklistTotal &&
    a.onSubmit === b.onSubmit
  );
}

export function IntakeV6WorkspaceHeaderStatusProvider({
  children,
  defaultHandlers,
}: {
  children: ReactNode;
  defaultHandlers?: WorkspaceHeaderStatusHandlers;
}) {
  const baselineHandlersRef = useRef(defaultHandlers ?? EMPTY_HANDLERS);
  baselineHandlersRef.current = defaultHandlers ?? EMPTY_HANDLERS;

  const [overlay, setOverlayState] = useState<WorkspaceHeaderStatusOverlay>({});
  const [handlers, setHandlersState] = useState<WorkspaceHeaderStatusHandlers>(
    () => baselineHandlersRef.current,
  );
  const [confirmFooter, setConfirmFooterState] = useState<ConfirmFooterState | null>(null);
  const footerIssuesOpenerRef = useRef<(() => void) | null>(null);

  const registerFooterIssuesOpener = useCallback((opener: (() => void) | null) => {
    footerIssuesOpenerRef.current = opener;
  }, []);

  const openFooterIssues = useCallback(() => {
    footerIssuesOpenerRef.current?.();
  }, []);

  const setConfirmFooter = useCallback((state: ConfirmFooterState | null) => {
    setConfirmFooterState((current) =>
      confirmFooterStateEqual(current, state) ? current : state,
    );
  }, []);

  const setOverlay = useCallback((next: WorkspaceHeaderStatusOverlay) => {
    setOverlayState(next);
  }, []);

  const setHandlers = useCallback((next: WorkspaceHeaderStatusHandlers) => {
    setHandlersState({ ...baselineHandlersRef.current, ...next });
  }, []);

  const value = useMemo(
    () => ({
      overlay,
      setOverlay,
      handlers,
      setHandlers,
      confirmFooter,
      setConfirmFooter,
      openFooterIssues,
      registerFooterIssuesOpener,
    }),
    [overlay, handlers, confirmFooter, setOverlay, setHandlers, setConfirmFooter, openFooterIssues, registerFooterIssuesOpener],
  );

  return (
    <IntakeV6WorkspaceHeaderStatusContext.Provider value={value}>
      {children}
    </IntakeV6WorkspaceHeaderStatusContext.Provider>
  );
}

export function useIntakeV6WorkspaceHeaderStatus() {
  const ctx = useContext(IntakeV6WorkspaceHeaderStatusContext);
  if (!ctx) {
    throw new Error("useIntakeV6WorkspaceHeaderStatus must be used within provider");
  }
  return ctx;
}

export function useIntakeV6WorkspaceHeaderStatusOptional() {
  return useContext(IntakeV6WorkspaceHeaderStatusContext);
}
