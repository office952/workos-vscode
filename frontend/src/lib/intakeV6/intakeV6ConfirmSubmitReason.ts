export function resolveConfirmSubmitDisabledReason(args: {
  hasResult: boolean;
  submitting: boolean;
  finishSetupIncomplete: boolean;
  bindingBlockers: string[];
  handoffAllowed: boolean;
  operatorConfirmationComplete: boolean;
  confirmInternalDraft: boolean;
  confirmDraftBoundary: boolean;
  showHandoffCheckboxes: boolean;
  isReadyForQuotePreview: boolean;
  firstBlocker: string | null;
  formatBlocker: (code: string) => string;
}): string | null {
  if (args.hasResult) return null;
  if (args.submitting) return "Se creează draftul intern…";
  if (args.finishSetupIncomplete) return "Finalizează finisajele în Review.";
  if (args.bindingBlockers.length > 0) {
    return args.formatBlocker(args.bindingBlockers[0]!);
  }
  if (!args.handoffAllowed) {
    return args.firstBlocker ?? "Handoff blocat — verifică verdictul.";
  }
  if (!args.isReadyForQuotePreview) return "Workspace-ul nu este gata pentru preview.";
  if (!args.operatorConfirmationComplete) {
    return "Bifează confirmarea operatorului pentru draft intern.";
  }
  if (!args.confirmInternalDraft) {
    return "Confirmă finisajele și datele de ofertare.";
  }
  if (args.showHandoffCheckboxes && !args.confirmDraftBoundary) {
    return "Confirmă limitele draftului intern.";
  }
  return null;
}

export function resolveConfirmChecklistProgress(args: {
  finishSetupComplete: boolean;
  operatorConfirmationComplete: boolean;
  confirmInternalDraft: boolean;
  draftBoundaryAcknowledged: boolean;
  showDraftBoundaryItem: boolean;
}): { done: number; total: number } {
  const items = [
    args.finishSetupComplete,
    args.operatorConfirmationComplete && args.confirmInternalDraft,
    args.showDraftBoundaryItem ? args.draftBoundaryAcknowledged : null,
  ].filter((item) => item !== null);
  const done = items.filter(Boolean).length;
  return { done, total: items.length };
}
