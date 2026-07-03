import type { Quote, QuoteStatus } from "@/lib/mockData";
import {
  getQuoteIntakeCommercialGuard,
  getQuoteIntakeCommercialGuidanceDescription,
} from "@/lib/quoteIntakeCommercialGuard";
import { isTerminalClosedQuoteStatus } from "@/lib/commercialSpineNavigation";
import { isQuoteRevisionEligible } from "@/lib/quoteRevision";

export const QUOTE_REVISION_MECHANISM_NOTICE =
  "Revizia recalculează oferta prin mecanismul de pricing existent. Totalurile și marja nu se editează manual.";

export const QUOTE_REVISION_UNAVAILABLE_NOTICE =
  "Revizia automată necesită snapshot de pricing salvat la creare (oferte noi din QuoteWizard).";

export interface QuoteCommercialGuidance {
  title: string;
  description: string;
  nextAction: string;
}

const GUIDANCE_BY_STATUS: Record<QuoteStatus, QuoteCommercialGuidance> = {
  draft: {
    title: "Ciornă — preț nefinalizat",
    description:
      "Oferta nu are încă preț comercial calculat. Calculează prețul în QuoteWizard înainte de trimitere.",
    nextAction: "Calculează prețul în QuoteWizard",
  },
  priced: {
    title: "Ofertă calculată",
    description:
      "Oferta este calculată. Trimite clientului, ajustează discountul prin revizie sau marchează acceptarea internă.",
    nextAction: "Trimite clientului sau revizie discount",
  },
  sent: {
    title: "Ofertă trimisă",
    description:
      "Oferta a fost marcată ca trimisă. Poți crea o revizie (discount) — după revizie retrimite clientului.",
    nextAction: "Revizie discount sau marchează acceptată intern",
  },
  viewed: {
    title: "Ofertă vizualizată",
    description:
      "Oferta a fost marcată ca vizualizată. Revizia comercială este disponibilă; după revizie retrimite clientului.",
    nextAction: "Revizie discount sau marchează acceptată intern",
  },
  negotiating: {
    title: "Ofertă în negociere",
    description:
      "Oferta este în negociere. Ajustează discountul prin revizie, apoi retrimite oferta.",
    nextAction: "Revizie discount sau marchează acceptată/respinsă",
  },
  accepted: {
    title: "Ofertă acceptată",
    description:
      "Oferta este acceptată intern. Următorul pas: convertește în comandă.",
    nextAction: "Convertește în comandă",
  },
  rejected: {
    title: "Ofertă respinsă",
    description:
      "Oferta este respinsă. Nu se poate converti fără o revizie viitoare și recalcul.",
    nextAction: "Fără acțiuni comerciale — status terminal",
  },
  expired: {
    title: "Ofertă expirată",
    description:
      "Oferta este expirată. Creează o ofertă nouă sau revizie (modul viitor) înainte de conversie.",
    nextAction: "Fără acțiuni comerciale — status terminal",
  },
};

export function getQuoteCommercialGuidance(
  status: QuoteStatus,
  quote?: Quote,
): QuoteCommercialGuidance {
  if (quote) {
    const guardedDescription = getQuoteIntakeCommercialGuidanceDescription(quote);
    if (guardedDescription) {
      const guard = getQuoteIntakeCommercialGuard(quote);
      const base = GUIDANCE_BY_STATUS[status];
      return {
        ...base,
        description: guardedDescription,
        nextAction: guard.handoffPreviewReady
          ? "Production handoff preview-ready — task generation remains separate"
          : guard.orderCreated
            ? "Complete Intake V3 production readiness audit"
            : guard.guardedConvertReady
            ? "Use Intake V3 guarded convert"
            : guard.guardedAcceptCompleted
              ? "Convert requires guarded IV3 flow"
              : guard.guardedAcceptReady
                ? "Use Intake V3 guarded accept"
                : "Accept/convert requires separate guarded IV3 flow",
      };
    }
  }
  return GUIDANCE_BY_STATUS[status];
}

export interface QuoteCommercialActionVisibility {
  showAssistedSend: boolean;
  showAccept: boolean;
  showReject: boolean;
  showExpire: boolean;
  showConvert: boolean;
  showResend: boolean;
  showRevision: boolean;
  convertBlockedMessage: string | null;
}

export function getQuoteCommercialActionVisibility(
  quote: Quote,
  options?: {
    convertBlockedByGate?: boolean;
    convertNeedsAck?: boolean;
  }
): QuoteCommercialActionVisibility {
  const terminal = isTerminalClosedQuoteStatus(quote.status);
  const { status } = quote;
  const convertBlockedByGate = options?.convertBlockedByGate ?? false;
  const convertNeedsAck = options?.convertNeedsAck ?? false;
  const guard = getQuoteIntakeCommercialGuard(quote);

  let convertBlockedMessage: string | null = null;
  if (guard.convertBlockedMessage) {
    convertBlockedMessage = guard.convertBlockedMessage;
  } else if (guard.blockedMessage) {
    convertBlockedMessage = guard.blockedMessage;
  } else if (convertBlockedByGate) {
    convertBlockedMessage = "Conversie blocată — rezolvă blockers comerciale.";
  } else if (convertNeedsAck) {
    convertBlockedMessage =
      "Confirmă avertismentele comerciale înainte de conversie.";
  }

  const guardedAcceptConvertBlocked = guard.isGuardedQuote;

  return {
    showAssistedSend:
      !terminal && !guardedAcceptConvertBlocked && (status === "draft" || status === "priced"),
    showAccept:
      !terminal &&
      !guardedAcceptConvertBlocked &&
      ["sent", "viewed", "negotiating"].includes(status),
    showReject:
      !terminal && ["sent", "viewed", "negotiating"].includes(status),
    showExpire:
      !terminal && ["sent", "viewed", "negotiating"].includes(status),
    showConvert:
      !terminal &&
      !guardedAcceptConvertBlocked &&
      (status === "accepted" || status === "priced"),
    showResend:
      !terminal &&
      ["sent", "viewed", "negotiating", "accepted"].includes(status),
    showRevision: isQuoteRevisionEligible(status),
    convertBlockedMessage,
  };
}

export function formatQuoteStatusLabel(status: QuoteStatus): string {
  const labels: Record<QuoteStatus, string> = {
    draft: "Ciornă",
    priced: "Calculată",
    sent: "Trimisă",
    viewed: "Vizualizată",
    negotiating: "Negociere",
    accepted: "Acceptată",
    rejected: "Respinsă",
    expired: "Expirată",
  };
  return labels[status];
}
